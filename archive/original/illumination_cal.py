import subprocess, os, itertools, numpy as np, matplotlib.pyplot as plt
from scipy.interpolate import griddata



class RadianceCalculator:
    def __init__(self, lights, walls, materials):
        self.lights, self.walls, self.materials = lights, walls, materials


    def generate_material_file(self, filename="materials.mat"):
        with open(filename, 'w') as f:
            for name, props in self.materials.items():
                if props["type"] == "plastic":
                    r, g, b = props["reflectance"]
                    rough = props["roughness"]
                    f.write(f"void plastic {name}\n0\n0\n5 {r} {g} {b} {rough} 0\n\n")
        return filename

    def generate_geometry_file(self, filename="scene.rad"):
        with open(filename, 'w') as f:
            for wall in self.walls:
                mat, name = wall["material"], wall["name"]
                f.write(f"{mat} polygon {name}\n0\n0\n12")
                for v in wall["vertices"]:
                    f.write(f" {v[0]} {v[1]} {v[2]}")
                f.write("\n\n")
        return filename

    def generate_light_file(self, filename="lights.rad"):
        with open(filename, 'w') as f:
            for idx, light in enumerate(self.lights, 1):
                name = f"{light['name']}_{idx}"        
                pos  = light["position"]
                flux = [x/179.0 for x in light["flux"]]
                half = light["size"] / 2.0
                f.write(f"void light {name}_src\n0\n0\n3 {flux[0]} {flux[1]} {flux[2]}\n\n")
                f.write(f"{name}_src polygon {name}\n0\n0\n12")
                for dx, dy in [(-half, -half), (half, -half), (half, half), (-half, half)]:
                    f.write(f" {pos[0]+dx} {pos[1]+dy} {pos[2]}")
                f.write("\n\n")
        return filename

    
    @staticmethod
    def run_command(cmd):
        try:
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, check=True)
            return result.stdout
        except subprocess.CalledProcessError as e:
            print("Radiance 运行失败：", e.stderr)
            raise
        except FileNotFoundError:
            print("找不到 Radiance 命令，请确认已安装并把 oconv/rtrace 加入 PATH")
            raise

    
    @staticmethod
    def frange(a, b, step):
        v = a
        while v <= b + 1e-9:
            yield round(v, 3)
            v = round(v + step, 6)

    def gen_grid(self, xmin, xmax, ymin, ymax, z, step):
        xs = list(self.frange(xmin, xmax, step))
        ys = list(self.frange(ymin, ymax, step))
        return [(x, y, z, 0, 0, 1) for x, y in itertools.product(xs, ys)]

    def calculate_illuminance(self, height=0.75, grid_step=0.25,
                              xmin=0, xmax=3.9, ymin=0, ymax=4.5):
        mat = self.generate_material_file()
        geo = self.generate_geometry_file()
        lgt = self.generate_light_file()

        oct_file = "scene.oct"
        if os.path.exists(oct_file):
            os.remove(oct_file)
        self.run_command(f"oconv {mat} {geo} {lgt} > {oct_file}")

        pts = self.gen_grid(xmin, xmax, ymin, ymax, height, grid_step)
        pts_file = "points.txt"
        with open(pts_file, 'w') as f:
            for p in pts:
                f.write(f"{p[0]} {p[1]} {p[2]} 0 0 1\n")

        out = self.run_command(f"rtrace -I -h -ab 2 {oct_file} < {pts_file}")

        ill = []
        for ln in out.strip().splitlines():
            if ln:
                r, g, b = map(float, ln.split())
                lux = 179 * (0.265*r + 0.670*g + 0.065*b)
                ill.append(round(lux, 4))
        return pts, ill

    
    def analyze_results(self, ill):
        return dict(mean=np.mean(ill), min=np.min(ill),
                    max=np.max(ill),
                    uniformity=np.min(ill)/np.mean(ill))
    
    def extract_coords(self,lights):
      x1 = lights[0]['position'][0]
      y1 = lights[0]['position'][1]

      x2 = lights[2]['position'][0]
      y2 = lights[2]['position'][1]

      x3 = lights[3]['position'][0]
      y3 = lights[3]['position'][1]

      x4 = lights[5]['position'][0]
      y4 = lights[5]['position'][1]

      return x1, y1, x2, y2, x3, y3, x4, y4
    
   
    def visualize(self,pts, ill, lights):
        x = np.array([p[0] for p in pts])
        y = np.array([p[1] for p in pts])
        z = np.array(ill)

        x_range = max(x) - min(x)
        y_range = max(y) - min(y)
        num_x = int(x_range / 0.1)  
        num_y = int(y_range / 0.1)

        xi = np.linspace(min(x), max(x), num_x)
        yi = np.linspace(min(y), max(y), num_y)
        xi, yi = np.meshgrid(xi, yi)

        zi = griddata((x, y), z, (xi, yi), method='cubic')
    
        zi_class = np.full_like(zi, np.nan)
        zi_class[zi < 0.5028]   = 2      
        zi_class[(zi >= 0.5028) & (zi <= 1.1173)] = 1   
        zi_class[zi > 1.1173]   = 0

        colors = ["#edfe8b", "#1a965a", "#4945b4"]   
        labels = ['> 1.1173', '0.5028 - 1.1173', '< 0.5028']

        plt.figure(figsize=(8, 6))
        cf = plt.contourf(xi, yi, zi_class,
                      levels=[-0.5, 0.5, 1.5, 2.5],
                      colors=colors,
                      extend='both')

        cbar = plt.colorbar(cf, ticks=[0, 1, 2])
        cbar.ax.set_yticklabels(labels)
        cbar.set_label('Illuminance Range')

        plt.title('Illuminance Distribution')
        plt.xlabel('X (m)')
        plt.ylabel('Y (m)')
        plt.gca().set_aspect('equal')

        x1, y1, x2, y2, x3, y3, x4, y4 = self.extract_coords(lights)
        w = 3.9
        for lx, ly in [(x1, y1), (x2, y2), (x3, y3), (x4, y4), (w-x1, y1), (w-x3, y3), (w-x4, y4)]:
             plt.plot(lx, ly, 's', color='black', markersize=6, label='Luminaire')

        handles, labels = plt.gca().get_legend_handles_labels()
        by_label = dict(zip(labels, handles))
        plt.legend(by_label.values(), by_label.keys(), loc='upper right')

        plt.tight_layout()
        plt.show()
      
        

def build_scene(L, W, H, X1, Y1, X2, Y2, X3, Y3, X4, Y4):
    lights = [
        {"name": "lamp1", "position": [X1, Y1, 2.8], "flux": [466, 466, 466], "size": 0.5},
        {"name": "lamp2", "position": [W - X1, Y1, 2.8], "flux": [466, 466, 466], "size": 0.5},
        {"name": "lamp3", "position": [X2, Y2, 2.8], "flux": [466, 466, 466], "size": 0.5},
        {"name": "lamp4", "position": [X3, Y3, 2.8], "flux": [466, 466, 466], "size": 0.5},
        {"name": "lamp5", "position": [W - X3, Y3, 2.8], "flux": [466, 466, 466], "size": 0.5},
        {"name": "lamp6", "position": [X4, Y4, 2.8], "flux": [466, 466, 466], "size": 0.5},
        {"name": "lamp7", "position": [W - X4, Y4, 2.8], "flux": [466, 466, 466], "size": 0.5},
    ]
    walls = [
        {"name": "wall0", "vertices": [(0,0,0), (W,0,0), (W,0,H), (0,0,H)],   "material": "wall_mat"},
        {"name": "wall1", "vertices": [(0,0,0), (0,L,0), (0,L,H), (0,0,H)],   "material": "wall_mat"},
        {"name": "wall2", "vertices": [(W,0,0), (W,L,0), (W,L,H), (W,0,H)],   "material": "wall_mat"},
        {"name": "wall3", "vertices": [(0,L,0), (W,L,0), (W,L,H), (0,L,H)],   "material": "wall_mat"},
        {"name": "floor","vertices": [(0,0,0), (W,0,0), (W,L,0), (0,L,0)],    "material": "floor_mat"},
    ]
    materials = {
        "wall_mat": {"type": "plastic", "reflectance": [0.6, 0.6, 0.6], "roughness": 0},
        "floor_mat": {"type": "plastic", "reflectance": [0.3, 0.3, 0.3], "roughness": 0},
    }
    return lights, walls, materials


def main():
    L, W, H = 4.5, 3.9, 3.0
    X1, Y1, X2, Y2, X3, Y3, X4, Y4 = 0.45, 0.7, 1.95, 1.68, 0.45, 2.7, 1.25, 4
    lights, walls, materials = build_scene(L, W, H, X1, Y1, X2, Y2, X3, Y3, X4, Y4)

    calc = RadianceCalculator(lights, walls, materials)
    pts, ill = calc.calculate_illuminance()
    print("照度值 :", ill)
    print("分析结果:", calc.analyze_results(ill))
    calc.visualize(pts, ill, lights)

if __name__ == "__main__":
    main()