# viz.py
from PIL import Image
from pathlib import Path

PALETTE = {
    0: (255,255,255), # S -> white
    1: (255,0,0),     # I -> red
    2: (0,255,0),     # R -> green
    3: (0,0,0),       # D -> black
}

def grid_to_image(grid):
    N = grid.shape[0]
    img = Image.new('RGB', (N, N))
    pixels = img.load()
    for i in range(N):
        for j in range(N):
            pixels[j, i] = PALETTE[int(grid[i,j])]
    return img

def save_frame(grid, path):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    img = grid_to_image(grid)
    img.save(path)

def save_frame_block(full_grid, path):
    save_frame(full_grid, path)

def make_side_by_side_gif(seq_pattern, par_pattern, days, out_path, duration=200):
    imgs = []
    from PIL import Image
    for day in range(0, days, 1):
        try:
            a = Image.open(seq_pattern.format(day=day))
            b = Image.open(par_pattern.format(day=day))
        except FileNotFoundError:
            continue
        neww = a.width + b.width
        h = max(a.height, b.height)
        new = Image.new('RGB', (neww, h))
        new.paste(a, (0,0))
        new.paste(b, (a.width,0))
        imgs.append(new)
    if imgs:
        imgs[0].save(out_path, save_all=True, append_images=imgs[1:], duration=duration, loop=0)
