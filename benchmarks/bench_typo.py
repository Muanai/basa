"""Benchmark for TypoCorrector lookup latency at 50,000-word scale."""

from __future__ import annotations

import statistics
import time

from basa.core.typo import TypoCorrector


def main() -> None:
    vocab = {f"kata{i:05d}indo" for i in range(50_000)}

    t_build_start = time.perf_counter()
    corrector = TypoCorrector(vocab=vocab, min_word_length=4)
    t_build_s = time.perf_counter() - t_build_start

    queries = [f"ktaa{i:05d}indo" for i in range(0, 50_000, 250)]
    latencies_ms: list[float] = []
    for query in queries:
        t0 = time.perf_counter()
        corrector.correct(query, max_dist=2)
        latencies_ms.append((time.perf_counter() - t0) * 1000.0)

    p50 = statistics.median(latencies_ms)
    latencies_sorted = sorted(latencies_ms)
    p95 = latencies_sorted[int(0.95 * len(latencies_sorted))]

    print(f"Vocab size: {len(corrector)}")
    print(f"Index build time: {t_build_s:.3f} s")
    print(f"Queries: {len(queries)} | p50: {p50:.3f} ms | p95: {p95:.3f} ms")


if __name__ == "__main__":
    main()
