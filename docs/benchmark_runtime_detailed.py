import time
import statistics as stats
import pandas as pd

import bib_dedupe.bib_dedupe as bd
from pathlib import Path

BENCHMARK_DIR = Path("../tests/ldd-full-benchmark")

def timed(label, fn, *args, **kwargs):
    t0 = time.perf_counter()
    out = fn(*args, **kwargs)
    dt = time.perf_counter() - t0
    return out, dt


def benchmark_pipeline(records_df, *, cpu=-1, repeats=5, warmup=1):
    # warmup (important for caches, process pools, etc.)
    for _ in range(warmup):
        prepped = bd.prep(records_df, verbosity_level=0, cpu=cpu)
        pairs = bd.block(prepped, verbosity_level=0, cpu=cpu)
        _ = bd.match(pairs, verbosity_level=0, cpu=cpu)

    prep_times, block_times, match_times = [], [], []
    for _ in range(repeats):
        prepped, t_prep = timed("prep", bd.prep, records_df, verbosity_level=0, cpu=cpu)
        pairs, t_block = timed("block", bd.block, prepped, verbosity_level=0, cpu=cpu)
        matched, t_match = timed("match", bd.match, pairs, verbosity_level=0, cpu=cpu)

        prep_times.append(t_prep)
        block_times.append(t_block)
        match_times.append(t_match)

    def summ(xs):
        return {
            "n": len(xs),
            "mean_s": stats.mean(xs),
            "median_s": stats.median(xs),
            "min_s": min(xs),
            "max_s": max(xs),
        }

    return {
        "prep": summ(prep_times),
        "block": summ(block_times),
        "match_total": summ(match_times),
    }


dataset = "cardiac"
df = pd.read_csv(BENCHMARK_DIR / dataset / "records_pre_merged.csv")

print(benchmark_pipeline(df, cpu=-1, repeats=10, warmup=2))
