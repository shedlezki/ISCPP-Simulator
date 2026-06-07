# MAPF Benchmark Provider

`src/mapfBenchmarkProvider.py` provides the data-construction interface between standard Multi-Agent Path Finding (MAPF) benchmark instances and the Intermittent Cooperation Path Planning (ICPP) simulator. It loads grid maps and scenario files from the benchmark dataset under `graphs/`, converts traversable grid cells into a NetworkX graph, and augments the resulting instance with cooperation-related attributes required by the ICPP model.

## Purpose

The MAPF benchmark data is used as a structural template for constructing ICPP instances. A standard MAPF instance specifies the environment geometry, obstacle locations, traversable cells, and agent start-goal assignments. It does not, however, model intermittent cooperation opportunities or the travel-time benefit obtained when agents cooperate at selected locations.

For this reason, the provider does not treat MAPF files as complete ICPP problem instances. Instead, it imports their well-defined navigation structure and enriches the generated graph with ICPP-specific metadata. This design preserves compatibility with established MAPF benchmark formats while enabling controlled experiments over cooperation density, cooperation magnitude, path length, and paths divergence.

## Inputs

The provider exposes two graph-construction entry points: `get_graph(...)`, which performs a single construction attempt, and `get_graph_with_timeout(...)`, which retries construction when start and goal augmentation takes longer than the configured timeout. The timeout wrapper is useful when procedurally generated starts and targets must satisfy the `--extent` and `--seperation` constraints, because unfavorable random samples can take longer to resolve. Both entry points use the same benchmark and augmentation parameters:

- `--map`: Name of the map under `graphs/mapf-map/`, excluding the `.map` suffix. Examples include `empty-8-8`, `empty-16-16`, and `maze-32-32-2`.
- `--size`: Optional random map selector. If set to `small`, `medium`, or `large`, the provider selects a map uniformly from `graphs/mapf-map/mapf-by-size/<size>/` and ignores the explicit `--map` value.
- `--scenario`: Optional scenario identifier. If provided, start and goal coordinates are read from `graphs/scen-even/<map>-<scenario>.scen`.
- `--density`: Probability that a traversable node is assigned a cooperation benefit when start and goal nodes are generated procedurally.
- `--magnitude`: Independent execution time assigned at cooperation-beneficial nodes. Since cooperative execution time is fixed at `1`, larger values increase the benefit of cooperation.
- `--extent`: Manhattan distance used when procedurally generating each agent's start-goal pair.
- `--seperation`: Manhattan distance used when generating the second agent's task relative to the first agent's task.

The raw data consists of MAPF `.map` and `.scen` files. In addition, this repository supports `X` as an ICPP-specific map symbol for pre-marked cooperation cells.

### Map File Input

MAPF `.map` files define grid dimensions and cell occupancy. The provider interprets map symbols as follows:

- `.` and other non-obstacle cells as traversable cells.
- `@` and `T` as blocked cells.
- `X` as traversable cells that are pre-marked as cooperation opportunities. These cells are used as cooperation locations when a scenario is supplied.

### Scenario Input

Scenario files specify agent start and goal coordinates. When `--scenario` is supplied, the provider samples scenario rows and relabels the corresponding graph nodes as `s_1`, `g_1`, `s_2`, and `g_2`.

When no scenario is supplied, the provider generates these four distinguished nodes procedurally. The first agent's start and goal are sampled according to `--extent`; the second agent's start and goal are then sampled according to `--seperation`, yielding related but non-identical tasks.

## Output Contract

The provider returns a four-tuple:

- `G`: a `networkx.DiGraph` representing the ICPP map.
- `pos`: a dictionary mapping each graph node to an `(x, y)` drawing position.
- `grid`: the numeric grid parsed from the map file.
- `map_name`: the actual map name used. This may differ from the input `--map` when `--size` is used.

Graph nodes are grid-coordinate tuples of the form `(row, col)`, except that the selected start and goal cells are relabeled as:

- `s_1`: start node for agent 1.
- `g_1`: goal node for agent 1.
- `s_2`: start node for agent 2.
- `g_2`: goal node for agent 2.

Each node is annotated with attributes used by the planning and simulation code:

- `coop`: whether the node is a pre-marked cooperation cell from the map.
- `tau_1`: travel time when the agent acts independently.
- `tau_2`: travel time when cooperation is available.

When no scenario is provided, cooperation benefits are generated randomly: each non-special node is assigned a cooperation benefit with probability `--density`. Beneficial nodes receive `tau_1 = --magnitude` and `tau_2 = 1`. Non-beneficial nodes receive equal travel times, so cooperation does not reduce execution time at those locations.

When a scenario is provided, the provider uses the map's `X` cells as cooperation opportunities instead of sampling cooperation locations according to `--density`. In this mode, `X` nodes receive `tau_1 = --magnitude` and `tau_2 = 1`; all other non-special nodes receive equal travel times. Start and goal nodes receive zero execution time in both modes.

The simulator consumes this output directly. `src/main.py` computes shortest independent paths using `tau_1`, shortest cooperated paths using `tau_2`, and passes `G`, `pos`, and `grid` to the GUI for visualization and time-stepped execution.

## Citation

The included benchmark maps and scenarios follow the MAPF benchmark format described by Stern et al.:

```bibtex
@article{stern2019mapf,
  title={Multi-Agent Pathfinding: Definitions, Variants, and Benchmarks},
  author={Stern, Roni and Sturtevant, Nathan R. and Felner, Ariel and Koenig, Sven and Ma, Hang and Walker, Thayne T. and Li, Jiaoyang and Atzmon, Dor and Cohen, Liron and Kumar, T. K. Satish and Boyarski, Eli and Bartak, Roman},
  journal={Proceedings of the International Symposium on Combinatorial Search},
  volume={10},
  number={1},
  pages={151--158},
  year={2019}
}
```