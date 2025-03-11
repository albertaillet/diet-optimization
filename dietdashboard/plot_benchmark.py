# %%
import json
from pathlib import Path

import matplotlib.cm as cm
import matplotlib.colors as colors
import matplotlib.pyplot as plt

DATA_DIR = Path(__file__).parent.parent / "data"
BENCHMARK_RESULTS = DATA_DIR / "benchmark_results.json"
with BENCHMARK_RESULTS.open() as f:
    resluts = json.load(f)
    resluts = {int(n): resluts[n] for n in resluts}
# resluts: dict[int, dict[str, tuple[float, float]]]
# first key: number of rows
# second key: method
# value: tuple of (time, result)
# time: float
# result: float
# %%
limits = [int(n) for n in resluts]
methods = list(resluts[limits[0]].keys())

# Sort methods by the sum of times across all limits
method_times_sum = {method: sum(resluts[n][method][0] for n in limits) for method in methods}
sorted_methods = sorted(methods, key=lambda m: method_times_sum[m], reverse=True)

# Set up a colormap

# Normalize times for colormap
method_times_array = [method_times_sum[m] for m in sorted_methods]
norm = colors.LogNorm(vmin=min(method_times_array), vmax=max(method_times_array))
cmap = cm.tab20b  # type: ignore

fig, ax = plt.subplots(figsize=(10, 6))
for method in sorted_methods:
    times = [resluts[n][method][0] for n in limits]
    color = cmap(norm(method_times_sum[method]))
    ax.plot(limits, times, label=f"{method} (Σ={method_times_sum[method]:.2f}s)", marker="x", markersize=4, color=color)

ax.set_xlabel("Number of rows", fontsize=8)
ax.set_ylabel("Time (s)", fontsize=8)
ax.legend(fontsize=7)
ax.tick_params(axis="both", which="major", labelsize=7)
ax.set_yscale("log")
ax.set_xscale("log")
ax.grid()

# Add colorbar
sm = cm.ScalarMappable(cmap=cmap, norm=norm)
sm.set_array([])
cbar = plt.colorbar(sm, ax=ax)
cbar.set_label("Total time (s)", fontsize=8)
cbar.ax.tick_params(labelsize=7)

plt.tight_layout()

# %%
