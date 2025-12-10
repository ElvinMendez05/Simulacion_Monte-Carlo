# plot_speedup.py
import pandas as pd
import matplotlib.pyplot as plt
import sys

par_csv = sys.argv[1]
seq_csv = sys.argv[2]
par = pd.read_csv(par_csv)
seq = pd.read_csv(seq_csv)
seq_time = seq[seq['cores']==1]['time'].mean()
grouped = par.groupby('cores')['time'].mean().reset_index()
grouped['speedup'] = seq_time / grouped['time']
plt.figure()
plt.plot(grouped['cores'], grouped['speedup'], marker='o')
plt.xlabel('Cores')
plt.ylabel('Speed-up')
plt.title('Strong scaling')
plt.grid(True)
plt.savefig('../results/speedup.png')
print('Saved results/speedup.png')
