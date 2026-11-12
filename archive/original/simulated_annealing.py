import math
import random as rd
import numpy as np
import matplotlib.pyplot as plt
import illumination_cal as ic   
from scipy.interpolate import griddata
from matplotlib.patches import Polygon
from matplotlib.path import Path
import matplotlib.image as mpimg
import cv2
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas



def objective(lights, walls, materials):
    calc = ic.RadianceCalculator(lights, walls, materials)
    _, ill = calc.calculate_illuminance(height=0.75,
                                        grid_step=0.25,
                                        xmin=0, xmax=3.9,
                                        ymin=0, ymax=4.5)
    
    total_points = len(ill)
    qualified_points = sum(1 for lux in ill if 0.5028 <= lux <= 1.1173)
    ratio = qualified_points/total_points

    return ratio



def visualize(pts, ill, lights):
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

    zi = griddata((x, y), z, (xi, yi), method='linear')
    
    zi_class = np.full_like(zi, np.nan)
    zi_class[zi < 0.5028]   = 0     
    zi_class[(zi >= 0.5028) & (zi <= 1.1173)] = 1   
    zi_class[zi > 1.1173]   = 2

    colors = ["#4945b4", "#1a965a", "#edfe8b"]  
    labels = ['< 90', '90 - 200', '> 200']

    plt.figure(figsize=(8, 6))
    cf = plt.contourf(xi, yi, zi_class,
                      levels=[-0.5, 0.5, 1.5, 2.5],
                      colors=colors,
                      extend='both')

    cbar = plt.colorbar(cf, ticks=[0, 1, 2])
    cbar.ax.set_yticklabels(labels)
    cbar.set_label('Illuminance Range (lux)')

    plt.title('Illuminance Distribution')
    plt.xlabel('X (m)')
    plt.ylabel('Y (m)')
    plt.gca().set_aspect('equal')

    
    x1, y1, x2, y2, x3, y3, x4, y4 = extract_coords(lights)
    w = 3.9
    for lx, ly in [(x1, y1), (x2, y2), (x3, y3), (x4, y4), (w-x1, y1), (w-x3, y3), (w-x4, y4)]:
        plt.plot(lx, ly, 's', color='black', markersize=6, label='Luminaire', zorder=4)

    handles, labels = plt.gca().get_legend_handles_labels()
    by_label = dict(zip(labels, handles))
    plt.legend(by_label.values(), by_label.keys(), loc='upper right')

    
    plt.axis('off')

    plt.tight_layout()



def extract_coords(lights):
    x1 = lights[0]['position'][0]
    y1 = lights[0]['position'][1]

    x2 = lights[2]['position'][0]
    y2 = lights[2]['position'][1]

    x3 = lights[3]['position'][0]
    y3 = lights[3]['position'][1]

    x4 = lights[5]['position'][0]
    y4 = lights[5]['position'][1]

    return x1, y1, x2, y2, x3, y3, x4, y4

def perturb(lights, L, W, max_shift=0.4):
    x1, y1, x2, y2, x3, y3, x4, y4 = extract_coords(lights)
    pairs = [(0, 1, x1, y1),
             (3, 4, x3, y3),
             (5, 6, x4, y4)]
    idx1, idx2, cx, cy = rd.choice(pairs)

    dx = rd.uniform(-max_shift, max_shift)
    dy = rd.uniform(-max_shift, max_shift)

    new_x = max(0, min(W, cx + dx))
    new_y = max(0, min(L, cy + dy))

    new_lights = [l.copy() for l in lights]
    new_lights[idx1]['position'][0] = new_x
    new_lights[idx1]['position'][1] = new_y
    new_lights[idx2]['position'][0] = W - new_x
    new_lights[idx2]['position'][1] = new_y

    return new_lights

def SA_LIGHTING(lights, walls, materials, L, W, run_id):
    tInitial = 100
    tfinal = 1.0
    alfa = 0.6
    T = tInitial
    iters = 1
    nlights = len(lights)

    current = lights
    cur_val = objective(current, walls, materials)
    best = [l.copy() for l in current] 
    best_val = cur_val
    history = [best_val]

    step = 1
    while T >= tfinal:
        for i in range(iters): 
            cand = perturb(current, L, W)
            cand_val = objective(cand, walls, materials)
            delta = cand_val - cur_val

            if delta >= 0 or math.exp(-delta / T) > rd.random():
                current, cur_val = cand, cand_val
                if cur_val > best_val:
                    best, best_val = [l.copy() for l in current], cur_val
                    best_calc = ic.RadianceCalculator(best, walls, materials)
                    
                    if (step == 1 and i == iters - 1) or step > 1: 
                        best_points, best_ill = best_calc.calculate_illuminance(height=0.75,
                                                  grid_step=0.25,
                                                  xmin=0, xmax=3.9,
                                                  ymin=0, ymax=4.5)

                        fig = plt.figure()  
                        try:
                            visualize(best_points, best_ill, best)           
                            filename = f'SA_run{run_id}_step{step}_iter{i}_T{T:.1f}.png'
                            plt.savefig(filename, dpi=150, bbox_inches='tight')
                            plt.close()  
                            print(f'已保存: {filename}')
                        finally:
                            plt.close(fig)
                            del fig
                
        history.append(best_val)
        
        print(f'迭代轮次:{run_id + 1}, 第{step}轮, T={T:.2f}, 当前最优目标值={best_val:.4f}')
        T *= alfa
        
        step += 1
    return best, best_val, history


if __name__ == '__main__':
    L, W, H = 4.5, 3.9, 3.0
    X1, Y1, X2, Y2, X3, Y3, X4, Y4 = 0.45, 0.7, 1.95, 1.68, 0.45, 2.7, 1.25, 4
    lights, walls, materials = ic.build_scene(L, W, H, X1, Y1, X2, Y2, X3, Y3, X4, Y4)

    best_lights, best_score = None, float('inf')
    all_hists = []                         

   
    cand_lights, cand_score, hist = SA_LIGHTING(lights, walls, materials, L, W, run_id=0)
    all_hists.append(hist)            
    if cand_score < best_score:
            best_lights, best_score = cand_lights, cand_score

    
    plt.figure()
    for idx, h in enumerate(all_hists, 1):
        plt.plot(h, linewidth=1, label=f'run {idx}')
    plt.title('Objective Function vs. Annealing Descent Curve (5 runs)')
    plt.xlabel('Outer-loop Iterations')
    plt.ylabel('Objective Function Value')
    plt.grid(True)
    plt.legend()
    plt.show()



    print('\n最终最优灯光布局 =', best_lights)
    print('\n最终达标区域比例 =', best_score)
    calc = ic.RadianceCalculator(best_lights, walls, materials)
    points, illuminances = calc.calculate_illuminance(height=0.75,
                                                  grid_step=0.25,
                                                  xmin=0, xmax=3.9,
                                                  ymin=0, ymax=4.5)
    print("退火后计算点的照度 (lux):", illuminances)
    fig = plt.figure()  
    try:
        visualize(points, illuminances, best_lights)           
        filename = f'最终优化结果.png'
        plt.savefig(filename, dpi=150, bbox_inches='tight')
        plt.close()  
        print(f'已保存: {filename}')
    finally:
        plt.close(fig)
        del fig
                


