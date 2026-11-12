import math
import random as rd
import numpy as np
import matplotlib.pyplot as plt
import illumination_cal as ic   


def objective(lights, walls, materials):
    calc = ic.RadianceCalculator(lights, walls, materials)
    _, ill = calc.calculate_illuminance(height=0.75,
                                        grid_step=0.25,
                                        xmin=0, xmax=3.9,
                                        ymin=0, ymax=4.5)
    return sum(abs(lux - 0.5587) for lux in ill)


def extract_coords(lights, W):
    x1 = lights[0]['position'][0]
    y1 = lights[0]['position'][1]

    x2 = lights[2]['position'][0]
    y2 = lights[2]['position'][1]

    x3 = lights[3]['position'][0]
    y3 = lights[3]['position'][1]

    x4 = lights[5]['position'][0]
    y4 = lights[5]['position'][1]

    return x1, y1, x2, y2, x3, y3, x4, y4

def perturb(lights, L, W, max_shift=0.5):
    x1, y1, x2, y2, x3, y3, x4, y4 = extract_coords(lights, W)
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
    tFinal   = 1.0
    alfa     = 0.8
    T        = tInitial
    iters    = 20    
    nLights  = len(lights)

    current = lights
    cur_val = objective(current, walls, materials)
    best    = [l.copy() for l in current]
    best_val = cur_val
    history = [best_val]

    step = 1
    while T >= tFinal:
        for _ in range(iters):
            cand = perturb(current, L, W)
            cand_val = objective(cand, walls, materials)
            delta = cand_val - cur_val

            if delta <= 0 or math.exp(-delta / T) > rd.random():
                current, cur_val = cand, cand_val
                if cur_val < best_val:
                    best, best_val = [l.copy() for l in current], cur_val

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

    for r in range(5):
        cand_lights, cand_score, hist = SA_LIGHTING(lights, walls, materials, L, W, run_id=r)
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
    print('\n最终最优目标值 =', best_score)
    calc = ic.RadianceCalculator(best_lights, walls, materials)
    points, illuminances = calc.calculate_illuminance(height=0.75,
                                                  grid_step=0.25,
                                                  xmin=0, xmax=3.9,
                                                  ymin=0, ymax=4.5)
    print("退火后计算点的照度 (lux):", illuminances)


