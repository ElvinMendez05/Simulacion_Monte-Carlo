# io_utils.py
import csv
from pathlib import Path

def save_times_csv(path, rows):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    write_header = not Path(path).exists()
    with open(path, 'a', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        if write_header:
            writer.writeheader()
        for r in rows:
            writer.writerow(r)

def append_time_csv(path, row_dict):
    save_times_csv(path, [row_dict])
