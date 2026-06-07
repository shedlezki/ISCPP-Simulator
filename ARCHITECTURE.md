# System Architecture

## Overview

This document describes the architecture of the ICPP simulator implementation. The core evaluation and visualization functionality is centralized in `simulation.py`.

## Architectural Layers

### Core Simulation Engine (simulation.py)

**Responsibility:** Path evaluation, interpolation, and visualization

**Key Components:**
- `GraphVisualizer` class: Primary simulation interface
- Path interpolation algorithm: Converts discrete paths to time-indexed state sequences
- Event detection system: Tracks cooperation, synchronization, and completion events
- Visualization pipeline: Renders graph and agent states

**Data Model:**
- Input: Discrete paths, graph with travel times
- Processing: Time-stepping simulation with cooperation detection
- Output: Time-indexed state sequences, event records, visualization frames

### Data Interface (mapfBenchmarkProvider.py)

**Responsibility:** Load and convert map data from benchmark formats

**Functions:**
- `get_graph()`: Load maps
- `get_graph_with_timeout()`: Load maps with timeout protection


**Data Flow:**
```
.map file → Grid representation → NetworkX DiGraph → Annotated with cooperation nodes
```
### User Interface (gui.py)

**Responsibility:** Interactive visualization and control

**Components:**
- `GUI` class: Tkinter-based interface
- Canvas rendering: Graph visualization
- Control widgets: Path selection, animation controls
- Metadata display: Experiment information

### Demonstration (main.py)

**Responsibility:** Example path planning integration and command-line interface

**Functions:**
- `parse_args()`: Command-line argument parsing
- `shortest_independent_path()`: Dijkstra-based SIP path
- `shortest_cooperated_path()`: Dijkstra-based SCP path
- `get_waits_included_graph()`: Modify edge weights by node travel times

---

## Module Dependencies

### Dependency Graph

```
main.py
├── mapfBenchmarkProvider (map loading)
├── gui.py (UI instantiation)
│   └── simulation.py (core visualization)
│       ├── networkx (graph operations)
│       ├── matplotlib (rendering)
│       └── numpy (numerical operations)
└── networkx (path computation)
```

### External Dependencies

| Package | Version | Usage |
|---------|---------|-------|
| networkx | ≥2.6 | Graph representation and algorithms |
| matplotlib | ≥3.5.0 | Visualization and animation |
| numpy | ≥1.21.0 | Numerical operations, grid representation |

---

## State Management

### Agent States

At any time, agent i is in exactly one state:

```
{Traveling, Executing, Cooperating, Waiting, Finished}
```

State transitions based on:
- Graph topology (edges, nodes)
- Agent's position
- Other agent's position (for cooperation and waiting)

### Global State

Simulation state = (time_t, state_agent_1, state_agent_2)

Invariants:
- Agents cannot teleport (only move along edges or stay at nodes)
- Cooperation requires both agents at same node
- Traveling a node takes τ₁ or τ₂ time depending on cooperation

---

## Configuration and Parameterization

### Runtime Parameters

| Parameter | Range | Effect |
|-----------|-------|--------|
| Density (-d) | [0.0, 1.0] | Cooperation node distribution density |
| Magnitude (-mt) | Positive int | Cooperation time benefit amount |
| Extent (-e) | Positive int | Spatial clustering of cooperation nodes |
| Correlation (-c) | Positive int | Agent correlation in cooperation opportunities |

---

## Authors

Itay Shedlezki (i.shedlezki@gmail.com)
Noa Agmon (agmon@cs.biu.ac.il)

Department of Computer Science and Artificial Intelligence
Bar-Ilan University, Ramat Gan, Israel

**Document Version:** 1.0
**Last Updated:** June 2026
