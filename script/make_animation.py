# make_animation.py
from utils.viz import make_side_by_side_gif
import yaml

with open('seq/params.yaml') as f:
    params = yaml.safe_load(f)
days = params.get('days', 365)
make_side_by_side_gif('results/animations/seq_day_{day:03d}.png', 'results/animations/par_day_{day:03d}.png', days, 'results/animations/seq_vs_par.gif')
print('Saved results/animations/seq_vs_par.gif')
