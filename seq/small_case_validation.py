# small_case_validation.py
import subprocess
from pathlib import Path
import yaml

def make_small_params(path='params.yaml'):
    p = {
        'grid_size': 10,
        'days': 3,
        'p_infect': 1.0,
        'p_recover': 0.0,
        'p_death': 0.0,
        'initial_infected': 1,
        'seed': 123,
        'boundary': 'periodic',
        'frame_interval': 1
    }
    with open(path, 'w') as f:
        yaml.dump(p, f)
    return p

if __name__ == '__main__':
    Path('results').mkdir(exist_ok=True)
    make_small_params('params.yaml')
    print('Ejecutando secuencial...')
    subprocess.run(['python', 'sequential.py'], cwd='.', check=True)
    print('Ejecutando paralelo (1 proc)...')
    subprocess.run(['mpiexec', '-n', '1', 'python', '../par/parallel.py'], cwd='seq', check=True)
    print('Comparar manualmente los arrays guardados.')

