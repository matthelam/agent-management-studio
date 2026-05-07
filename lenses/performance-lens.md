---
name: performance-lens
description: Overlay applied on top of any harness. Adds performance-focused review concerns — hot paths, memory pressure, network round-trips, render cost, computational complexity. Use for performance reviews, latency-sensitive code, and any work where speed matters.
applies_on_top_of: any_harness
---

# Performance Lens

Overlay that augments any harness with performance-specific review concerns.

## Concerns surfaced

- **Hot paths** — what runs on every request, every render, every iteration?
  What's the multiplier on this code?
- **Memory pressure** — allocations, retention, leak surfaces, large object
  copies, cache eviction.
- **Network round-trips** — N+1 patterns, sequential when parallel would do,
  payload size, pagination.
- **Render cost** — unnecessary re-renders, layout thrash, blocking main
  thread, image loading without dimensions.
- **Computational complexity** — O(n²) where O(n) would do, repeated work
  inside loops, missing memoization where stable.
- **I/O surfaces** — disk reads, database queries, file system traversal,
  shell-out to subprocesses.
- **Concurrency hazards** — locks held across I/O, lock granularity, thread
  pool exhaustion.

## Prompt overlay

Append to the harness's posture_anchor:

> *In addition to your primary lens, evaluate every claim against these
> performance concerns: hot paths, memory pressure, network round-trips,
> render cost, computational complexity, I/O surfaces, concurrency hazards.
> Quantify where possible — "this runs N times per request" is more useful
> than "this is a hot path." Distinguish theoretical inefficiency (does it
> matter at this scale?) from observable inefficiency (does the trace show
> it as a problem?).*

## Combinations

- **Architect + Performance** — structural performance review. Surface
  systemic patterns that bound scaling.
- **Specifist + Performance** — find every concrete performance hazard in
  this code.
- **Empiricist + Performance** — evidence-driven; cite the trace, the
  benchmark, the profiler output.
- **Skeptic + Performance** — challenge claims of "fast enough"; demand
  evidence of measured performance, not assumed.

## Default-on triggers

The Performance lens is always-on when:
- The project's `assembly.default_lenses` includes `performance`
- The current work touches: render-critical paths, database queries, large
  data transformations, real-time/streaming code, build pipelines
- The dev's prompt mentions performance, latency, slow, optimization,
  bottleneck, scaling

## Routing implication

Findings produced under the Performance lens route to the specialist with
the relevant domain (frontend-dev for render, backend-dev for query/IO,
docker-ops for infrastructure).
