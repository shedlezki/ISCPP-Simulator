# Technical Documentation: Intermittent Cooperation Path Planning

This document describes the technical implementation of the ICPP simulator. The core functionality is provided by `simulation.py`, which implements path evaluation, interpolation, and visualization. Supporting modules provide data interfaces and demonstration usage.

## Table of Contents

1. [System Overview](#system-overview)
2. [Core Simulation Module](#core-simulation-module)
3. [Algorithm Details](#algorithm-details)
4. [Data Structures](#data-structures)
5. [Module Reference](#module-reference)
6. [Mathematical Formulations](#mathematical-formulations)
7. [Performance Considerations](#performance-considerations)
8. [Extension Guide](#extension-guide)

---

## System Overview

### Problem Formulation

The Intermittent Cooperation Path Planning problem is defined over a graph-based environment:

**Input:**
- A graph G = (V, E) with edge weights representing distances
- Node labels: travel times τ₁(v) (individual) and τ₂(v) (cooperative)
- Two agents with start positions s₁, s₂ ∈ V and goal positions g₁, g₂ ∈ V

**Output:**
- Paths P₁ and P₂ for agents 1 and 2 respectively
- Total path time for each agent

### Core Simulation Model

The `simulation.py` module implements the core evaluation framework:

- **Path Evaluation**: Computes completion times given discrete paths
- **Path Interpolation**: Converts discrete paths to time-indexed state sequences
- **Event Tracking**: Identifies and records cooperation, synchronization, and task completion events
- **Visualization**: Renders the graph topology and agent states for analysis

#### Agent State Space

At any point in time, an agent can be in one of these states:

| State | Description | Duration |
|-------|-------------|----------|
| **Executing** | Traveling a node alone | τ₁ |
| **Cooperating** | Cooperating with another agent | τ₂ |
| **Waiting** | Idle at a node, waiting for partner | Variable |
| **Traveling** | Moving along an edge | Edge weight |
| **Finished** | Reached goal | 0 |

#### Cooperation Nodes

Certain nodes in the graph support cooperation:
- **Individual travel time**: τ₁(v) (agent processes alone)
- **Cooperative travel time**: τ₂(v) = τ₁(v) - Δ (agents process together)
- **Cooperation benefit**: Δ(v) = τ₁(v) - τ₂(v) (time savings from cooperation)

---

## Core Simulation Module

### GraphVisualizer Class

The `GraphVisualizer` class in `simulation.py` is the primary interface for path evaluation and visualization.

#### Constructor
```python
def __init__(self, G, pos, grid, paths, args, eid):
    """
    Initialize visualization of multi-agent path execution.
    
    Args:
        G: NetworkX DiGraph with node attributes tau_1, tau_2, coop
        pos: Dict mapping nodes to (x, y) positions
        grid: Grid representation (optional, for heatmap visualization)
        paths: Dict mapping strategy names to (path_1, path_2) tuples
        args: Configuration arguments (density, magnitude, extent, correlation)
        eid: Experiment identifier for tracking
    """
```

#### Key Methods

**interpolate_paths(G, path1, path2)**

Converts discrete multi-agent paths to time-indexed state sequences, computing when cooperation occurs and agent waiting times.

Algorithm:
1. Initialize time counters for both agents at t=0
2. For each edge in respective paths:
   - Compute travel time along edge
   - Record agent position at each time step
3. At each node, determine cooperation opportunity:
   - Check if both agents arrive within relevant time for cooperation
   - If synchronous: apply τ₂ (cooperative time)
   - Otherwise apply τ₁ (individual time)
4. Continue until both agents reach goals

Returns: Time-indexed state sequence enabling frame-by-frame animation

**get_edges_in_path(path)**

Extracts edges from abstract path representation, handling special WAIT labels inserted during path computation.

**generate_text(state, other)**

Produces human-readable state descriptions for each agent at each time step, supporting analysis and debugging.

#### Visualization Pipeline

```
Discrete Paths (P₁, P₂)
    ↓
Path Interpolation (time-indexed states)
    ↓
Event Detection (cooperation, waiting, completion)
    ↓
Animation Frames
    ↓
Matplotlib Rendering
```

---

## Data Structures

### Graph Representation

Graphs are represented as NetworkX DiGraph with:

**Node Attributes:**
- `tau_1`: Individual travel time (float)
- `tau_2`: Cooperative travel time (float)
- `coop`: Boolean flag indicating cooperation capability
- `x`, `y`: Position coordinates for visualization

**Edge Attributes:**
- `weight`: Traversal time (default = 1.0)

Example:
```python
import networkx as nx

G = nx.DiGraph()
G.add_node('v1', tau_1=5.0, tau_2=3.0, coop=True, x=0, y=0)
G.add_node('v2', tau_1=4.0, tau_2=4.0, coop=False, x=1, y=0)
G.add_edge('v1', 'v2', weight=1.0)
```

### Path Representation

Paths are represented as lists of node identifiers:

```python
path_1 = ['s_1', 'v1', 'v3', 'g_1']  # Path for agent 1
path_2 = ['s_2', 'v2', 'v3', 'g_2']  # Path for agent 2
```

### State Sequence

Time-indexed states track each agent's position and activity:

```python
state = {
    'time': 5,
    'agent_1': {'node': 'v3', 'status': 'cooperating'},
    'agent_2': {'node': 'v3', 'status': 'cooperating'}
}
```

---

## Module Reference

### simulation.py

**Class: GraphVisualizer**

| Method | Input | Output | Purpose |
|--------|-------|--------|---------|
| `interpolate_paths()` | Graph, path1, path2 | State sequence | Convert discrete paths to time-indexed states |
| `get_edges_in_path()` | Path | Edge list | Extract edges from path |
| `generate_text()` | State dict | String | Generate human-readable state description |
| `relabel_nodes()` | Graph | Graph | Apply LaTeX formatting to node labels |

### mapfBenchmarkProvider.py

| Function | Input | Output | Purpose |
|----------|-------|--------|---------|
| `get_random_map_by_size()` | Size string | Filename | Load random map of specified size |
| `get_graph_with_timeout()` | Map file, params | NetworkX graph | Load map with timeout mechanism |
| `_map_file_to_grid()` | Map file path | 2D list | Parse .map format |
| `_get_grid_graph()` | Grid | NetworkX graph | Convert grid to graph |

### gui.py

| Method | Purpose |
|--------|---------|
| `show()` | Display interactive visualization interface |
| `copy_to_clipboard()` | Copy experiment ID |

### main.py

| Function | Input | Output | Purpose |
|----------|-------|--------|---------|
| `shortest_paths()` | Graph, source, goal, tau | Dijkstra result | Compute shortest path with node weights |
| `shortest_independent_path()` | Graph, s, g | Path, time | SIP computation |
| `shortest_cooperated_path()` | Graph, s, g | Path, time | SCP computation |

---

## Performance Considerations

### Computational Complexity

**Path Computation:**
- Dijkstra's algorithm: O((V + E) log V)
- Applied independently to each agent: O(2((V + E) log V))

**Path Interpolation:**
- Linear in total path length: O(|P₁| + |P₂|)


---

## Extension Guide

### Adding New Path Planning Strategies

To add a custom strategy:

1. Implement function with signature:
   ```python
   def new_strategy(G, s, g):
       # Custom algorithm
       return {'path': path, 'length': cost}
   ```

2. Register in main.py:
   ```python
   paths["Strategy Name"] = (
       new_strategy(G, 's_1', 'g_1'),
       new_strategy(G, 's_2', 'g_2')
   )
   ```

3. Strategy automatically appears in GUI for comparison

## References

[To be populated with academic references]

---

## Authors

Itay Shedlezki (i.shedlezki@gmail.com)
Noa Agmon (agmon@cs.biu.ac.il)

Department of Computer Science and Artificial Intelligence
Bar-Ilan University, Ramat Gan, Israel

**Last Updated:** June 2026
