import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[1]))

# sequential.py
import numpy as np
import yaml
import time
from pathlib import Path
from utils.io_utils import save_times_csv
from utils.viz import save_frame

# Estados: 0=S,1=I,2=R,3=D

def load_params(path='params.yaml'):
    # siempre buscarlo en la raíz del proyecto
    path = Path(__file__).resolve().parents[1] / path
    with open(path) as f:
        return yaml.safe_load(f)

def neighbor_infected_count(grid, periodic=True):
    rolls = [(-1,-1),(-1,0),(-1,1),(0,-1),(0,1),(1,-1),(1,0),(1,1)]
    s = np.zeros_like(grid, dtype=np.uint8)
    N = grid.shape[0]
    if periodic:
        for dx,dy in rolls:
            s += (np.roll(np.roll(grid, dx, axis=0), dy, axis=1) == 1)
    else:
        pad = np.pad(grid, pad_width=1, mode='constant', constant_values=0)
        for dx,dy in rolls:
            s += (pad[1+dx:1+dx+N, 1+dy:1+dy+N] == 1)
    return s

def run_sequential(params):
    N = params['grid_size']
    days = params['days']
    beta = params['p_infect']
    p_rec = params['p_recover']
    p_death = params['p_death']
    seed = params.get('seed', None)
    periodic = params.get('boundary', 'periodic') == 'periodic'
    frame_interval = params.get('frame_interval', 5)

    rng = np.random.default_rng(seed)
    grid = np.zeros((N,N), dtype=np.uint8)
    inds = rng.choice(N*N, params['initial_infected'], replace=False)
    grid.flat[inds] = 1

    Path('results/animations').mkdir(parents=True, exist_ok=True)
    stats = []
    cum_new = 0
    cum_resolved = 0

    t0 = time.perf_counter()
    for day in range(days):
        neigh = neighbor_infected_count(grid, periodic=periodic)
        S_mask = (grid == 0)
        prob_inf = 1.0 - (1.0 - beta)**neigh
        rand = rng.random(size=grid.shape)
        new_inf = S_mask & (rand < prob_inf)

        I_mask = (grid == 1)
        rand2 = rng.random(size=grid.shape)
        died = I_mask & (rand2 < p_death)
        recovered = I_mask & ((rand2 >= p_death) & (rand2 < p_death + p_rec))

        grid[new_inf] = 1
        grid[died] = 3
        grid[recovered] = 2

        n_new = int(np.count_nonzero(new_inf))
        n_I = int(np.count_nonzero(grid == 1))
        n_R = int(np.count_nonzero(grid == 2))
        n_D = int(np.count_nonzero(grid == 3))
        stats.append({'day': day, 'new': n_new, 'I': n_I, 'R': n_R, 'D': n_D})

        cum_new += n_new
        cum_resolved += int(np.count_nonzero(recovered) + np.count_nonzero(died))

        if day % max(1, frame_interval) == 0:
            save_frame(grid, f"results/animations/seq_day_{day:03d}.png")

    total_time = time.perf_counter() - t0
    save_times_csv('results/times_seq.csv', [{'cores': 1, 'time': total_time, 'seed': seed, 'grid_size': N, 'days': days}])

    R0_est = cum_new / max(1, cum_resolved)
    return grid, stats, total_time, R0_est

if __name__ == '__main__':
    params = load_params('params.yaml')
    grid, stats, total_time, R0_est = run_sequential(params)
    print(f'Tiempo total secuencial: {total_time:.3f}s, R0_est: {R0_est:.3f}')
