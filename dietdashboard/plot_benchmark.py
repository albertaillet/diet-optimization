# %%
import csv
from pathlib import Path

import matplotlib.cm as cm
import matplotlib.colors as colors
import matplotlib.pyplot as plt

BENCHMARK_DIR = max((Path(__file__).parent.parent / "tmp/benchmark").glob("*"), key=lambda p: p.name)
print(BENCHMARK_DIR.name)
with (BENCHMARK_DIR / "benchmark_results.csv").open() as f:
    resluts = list(csv.DictReader(f))
# cols: ["size", "solver", "solver_options", "time", "iterations"]
for row in resluts:
    row["solver_id"] = f"{row['library']} {row['solver']} {row['solver_options'] if row['solver_options'] != '{}' else ''}"

# %%
sizes = sorted(set(int(row["size"]) for row in resluts))
solvers = set(row["solver_id"] for row in resluts)
# assert that all solvers have the size 500
assert all(any(row["size"] == "500" for row in resluts if row["solver_id"] == s) for s in solvers)

# Sort methods by the min of times for size 500
method_times_500 = {
    m: min(float(row["time"]) for row in resluts if row["solver_id"] == m and row["size"] == "500") for m in solvers
}
sorted_methods = sorted(solvers, key=lambda m: method_times_500[m], reverse=True)

# Normalize times for colormap
method_times_array = [method_times_500[m] for m in sorted_methods]
norm = colors.LogNorm(vmin=min(method_times_array), vmax=max(method_times_array))
cmap = cm.tab20b  # type: ignore

fig, ax = plt.subplots(figsize=(10, 6))
for method in sorted_methods:
    xy = [(float(row["size"]), float(row["time"])) for row in resluts if row["solver_id"] == method]
    sizes, times = zip(*sorted(xy), strict=True)
    color = cmap(norm(method_times_500[method]))  # Use the same color for all points of the same method
    ax.plot(sizes, times, label=f"{method} ({1000 * method_times_500[method]:.2f}ms)", marker="x", markersize=4, color=color)

ax.set_xlabel("Number of rows", fontsize=8)
ax.set_ylabel("Time (s)", fontsize=8)
ax.legend(fontsize=7)
ax.tick_params(axis="both", which="major", labelsize=7)
ax.set_yscale("log")
ax.set_xscale("log")
ax.grid()

plt.tight_layout()

# %%
