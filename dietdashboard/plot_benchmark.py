# %%
import json
from pathlib import Path

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
fig, ax = plt.subplots(figsize=(10, 6))
for method in methods:
    times = [resluts[n][method][0] for n in limits]
    ax.plot(limits, times, label=method, marker="x", markersize=4)
ax.set_xlabel("Number of rows", fontsize=8)
ax.set_ylabel("Time (s)", fontsize=8)
ax.legend(fontsize=7)
ax.tick_params(axis="both", which="major", labelsize=7)
ax.set_yscale("log")
ax.set_xscale("log")
ax.grid()
plt.tight_layout()

# %%
