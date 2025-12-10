import sys
from pathlib import Path

# Agregar la ruta de la carpeta raíz del proyecto para importar utils
sys.path.append(str(Path(__file__).resolve().parents[1]))

# parallel.py
from mpi4py import MPI
import numpy as np
import yaml
import time
from pathlib import Path
from utils.io_utils import append_time_csv
from utils.viz import save_frame_block



comm = MPI.COMM_WORLD
rank = comm.Get_rank()
size = comm.Get_size()

def load_params(path='params.yaml'):
    with open(path) as f:
        return yaml.safe_load(f)

def allocate_block(N, size, rank):
    base = N // size
    rem = N % size
    counts = [base + (1 if r < rem else 0) for r in range(size)]
    starts = [sum(counts[:r]) for r in range(size)]
    return counts[rank], starts[rank], counts, starts

def neighbor_infected_count_block(block):
    rolls = [(-1,-1),(-1,0),(-1,1),(0,-1),(0,1),(1,-1),(1,0),(1,1)]
    s = np.zeros_like(block, dtype=np.uint8)
    for dx,dy in rolls:
        s += (np.roll(np.roll(block, dx, axis=0), dy, axis=1) == 1)
    return s

if __name__ == '__main__':
    params = load_params('params.yaml')
    N = params['grid_size']
    days = params['days']
    beta = params['p_infect']
    p_rec = params['p_recover']
    p_death = params['p_death']
    seed = params.get('seed', 42)
    frame_interval = params.get('frame_interval', 5)

    rng = np.random.default_rng(seed + rank)
    my_n, my_start, counts, starts = allocate_block(N, size, rank)
    block = np.zeros((my_n + 2, N), dtype=np.uint8)

    if rank == 0:
        full = np.zeros((N,N), dtype=np.uint8)
        inds = rng.choice(N*N, params['initial_infected'], replace=False)
        full.flat[inds] = 1
        for r in range(size):
            cnt = counts[r]
            s = starts[r]
            sub = full[s:s+cnt, :]
            if r == 0:
                block[1:1+cnt, :] = sub
            else:
                comm.Send(sub.copy(), dest=r, tag=11)
    else:
        recv = np.empty((my_n, N), dtype=np.uint8)
        comm.Recv(recv, source=0, tag=11)
        block[1:1+my_n, :] = recv

    top = rank - 1 if rank > 0 else MPI.PROC_NULL
    bot = rank + 1 if rank < size - 1 else MPI.PROC_NULL
    Path('results/animations').mkdir(parents=True, exist_ok=True)

    cum_new = 0
    cum_resolved = 0
    comm.Barrier()
    t0 = MPI.Wtime()
    for day in range(days):
        send_top = block[1, :].copy()
        send_bot = block[1+my_n-1, :].copy()
        recv_top = np.empty_like(send_top)
        recv_bot = np.empty_like(send_bot)

        comm.Sendrecv(send_top, dest=top, sendtag=0, recvbuf=recv_bot, source=bot, recvtag=0)
        comm.Sendrecv(send_bot, dest=bot, sendtag=1, recvbuf=recv_top, source=top, recvtag=1)

        if bot != MPI.PROC_NULL:
            block[-1, :] = recv_bot
        if top != MPI.PROC_NULL:
            block[0, :] = recv_top

        neigh = neighbor_infected_count_block(block)
        interior = slice(1, 1+my_n)
        S_mask = (block[interior] == 0)
        prob_inf = 1.0 - (1.0 - beta)**neigh[interior]
        rand = rng.random(size=(my_n, N))
        new_inf = S_mask & (rand < prob_inf)

        I_mask = (block[interior] == 1)
        rand2 = rng.random(size=(my_n, N))
        died = I_mask & (rand2 < p_death)
        recovered = I_mask & ((rand2 >= p_death) & (rand2 < p_death + p_rec))

        block[interior][new_inf] = 1
        block[interior][died] = 3
        block[interior][recovered] = 2

        n_new_local = int(np.count_nonzero(new_inf))
        resolved_local = int(np.count_nonzero(died) + np.count_nonzero(recovered))

        n_new = comm.reduce(n_new_local, op=MPI.SUM, root=0)
        resolved = comm.reduce(resolved_local, op=MPI.SUM, root=0)

        if rank == 0:
            cum_new += n_new
            cum_resolved += resolved

        if day % max(1, frame_interval) == 0:
            if rank == 0:
                full = np.empty((N,N), dtype=np.uint8)
                full[starts[0]:starts[0]+counts[0], :] = block[1:1+counts[0], :]
                for r in range(1, size):
                    recvbuf = np.empty((counts[r], N), dtype=np.uint8)
                    comm.Recv(recvbuf, source=r, tag=20+day)
                    full[starts[r]:starts[r]+counts[r], :] = recvbuf
                save_frame_block(full, f'results/animations/par_day_{day:03d}.png')
            else:
                comm.Send(block[1:1+counts[rank], :].copy(), dest=0, tag=20+day)

    total_time = MPI.Wtime() - t0
    if rank == 0:
        append_time_csv('results/times_par.csv', {'cores': size, 'time': float(total_time), 'seed': seed, 'grid_size': N, 'days': days})
        R0_est = cum_new / max(1, cum_resolved)
        print(f'Tiempo total paralelo (cores={size}): {total_time:.3f}s, R0_est: {R0_est:.3f}')

    comm.Barrier()
