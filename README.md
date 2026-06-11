# Intermittent Cooperation Multiagent Path Planning Simulation

This repository contains the implementation of a simulator for the **Intermittent Cooperation Path Planning (ICPP)** problem in multi-agent systems, enabling evaluation of path planning strategies where agents can benefit from selective cooperation to reduce task completion times.

The source code and dataset generator are available at https://github.com/shedlezki/ISCPP-Simulator.

## 🎯 Problem Overview

In the Intermittent Cooperation Path Planning problem, agents must navigate from their starting positions to their respective goal positions in a graph-based environment. Certain nodes provide **cooperative opportunities** where agents can work together to reduce traversal time.

### Key Concepts

- **Individual Travel Time (τ₁)**: Time to traverse a node alone
- **Cooperative Travel Time (τ₂)**: Reduced time to traverse a node when cooperating with another agent
- **Cooperation Nodes**: Specially marked nodes where agents benefit from cooperation
- **Path Planning**: Finding optimal routes that leverage cooperation strategically

## 🚀 Quick Start

### Prerequisites

- Python 3.9+
- Required packages are installed automatically when installing the package.

### Installation

```bash
pip install iscpp-simulator
```

For local development from a clone:

```bash
pip install -e .
```

### Running the Simulator

#### Basic Usage

The project includes a simple `main.py` entry point that demonstrates the basic workflow. It finds the Shortest Independent Path (SIP) and Shortest Cooperation Path (SCP) for both agents, then uses the simulator to evaluate and visualize the resulting plans.

```bash
# Run with default parameters (empty 8x8 map)
iscpp-simulator

# Specify a simple map from the bundled benchmark maps
iscpp-simulator -m "empty-16-16" -d 0.5 -mt 10

# Use a random simple map
iscpp-simulator --size small
```

#### Command-Line Arguments

| Argument | Short | Type | Required | Default | Description |
|----------|-------|------|----------|---------|-------------|
| `--map` | `-m` | str | No | `empty-8-8` | Map name/path from the [MAPF benchmark provider](MAPF_BENCHMARK_PROVIDER.md) |
| `--scenario` | `-s` | str | No | - | Scenario file with agent start/goal positions (if not prvoided - starting and target nodes are auto-generated using extent and seperation parameters) |
| `--density` | `-d` | float | No | 0.5 | Ratio of cooperation nodes to all graph nodes (0.0-1.0) |
| `--magnitude` | `-mt` | int | No | 10 | Multiplication factor between non-cooperative and cooperative travel time at cooperation nodes |
| `--extent` | `-e` | int | No | 5 | Manhattan distance between each agent's start node and target node |
| `--seperation` | `-se` | int | No | 4 | Manhattan distance between the two agents' start nodes and between their target nodes |
| `--size` | `-si` | str | No | - | Random map size: `small`, `medium`, or `large` |
| `--data-dir` | - | str | No | - | External `graphs/` or `mapf-map/` directory to use instead of bundled maps |
| `--scenario-dir` | - | str | No | - | External directory containing `.scen` files |

### Example Commands

```bash
# Default empty map simulation
iscpp-simulator

# Simple maze map with custom cooperation parameters
iscpp-simulator -m "maze-32-32-2" -d 0.6 -mt 15 -e 7

# Use external scenario files from a local checkout or downloaded benchmark set
iscpp-simulator --scenario-dir graphs/scen-even --size small -s "even-1" -d 0.5
```

## 🖥️ GUI Usage

The repository includes a GUI that can be used to see an interactive visualization of paths.

### GUI Controls

1. **Map Visualization**: The central graph display showing:
   - Regular nodes (light gray)
   - Cooperation nodes (darker gray)
   - Edges connecting nodes
   - Agents as colored circles (Agent 1: pink, Agent 2: cyan)

2. **Path Selection**: 
   - **Checkboxes** display different path options with their costs
   - Format: `path <name> (cost_agent1, cost_agent2)`
   - Click checkbox to highlight the path

3. **Animation Controls**:
   - **Play Button**: Animates agents following selected path
   - Shows real-time agent movement and cooperation events
   - Status updates show what each agent is doing

4. **Metadata**:
   - Top display shows simulation parameters (map, density, magnitude, etc.)
   - **EID** (Experiment ID) can be copied to clipboard by clicking

### Understanding the Animation

The animation displays the agents’ states at each time step, accompanied by commentary describing the current state:

- **"executes task at node X alone"**: Agent working independently
- **"cooperates with Agent Y at node X"**: Two agents cooperating
- **"waits for Agent Y at node X"**: Agent waiting for other agent to arrive
- **"travels from X to Y"**: Agent moving along edge
- **"reached target"**: Agent successfully completed journey

## 📊 Path Simulation
The simulator evaluates and visualizes path pairs supplied by the caller.
The `main.py` demonstration supplies two example path pairs:

- Shortest Independent Paths (SIP)
- Shortest Cooperation Paths (SCP)

## 🏗️ Project Architecture

### Core Components

#### `simulation.py` (Core Module)
- **Path Evaluation**: Evaluates discrete paths on graphs with node execution times (τ₁ for independent execution, τ₂ for cooperative execution)
- **Path Interpolation**: Converts abstract paths to time-indexed state sequences for event tracking
- **Visualization Engine**: Renders graph topology, node states, and agent positions
- `GraphVisualizer` class: Primary interface for visualization

#### `gui.py` (User Interface)
- Tkinter-based interactive interface for accessing simulator functionality
- Path selection and visualization controls
- Animation playback for step-by-step analysis
- Experiment metadata display and tracking

#### `mapfBenchmarkProvider.py` (Data Interface)
- Loads MAPF (Multi-Agent Path Finding) benchmark maps
- Converts map files to graph representations
- Generates cooperation node distributions based on specified parameters
- See the [MAPF benchmark provider](MAPF_BENCHMARK_PROVIDER.md) page for more details

#### `main.py` (Demonstration)
- Example usage of the simulator
- Command-line interface for common scenarios
- Handles argument parsing and map/scenario loading
- Demonstrates integration of multiple path planning strategies

### Data Flow

```
Command-line arguments
        ↓
Map/Scenario Loading (mapfBenchmarkProvider)
        ↓
Graph Construction & Cooperation Node Generation
        ↓
Path Planning
        ↓
Path Interpolation (simulation)
        ↓
GUI Creation & Visualization (gui)
        ↓
User Interaction & Animation
```

## 📁 Directory Structure

```
project/
├── README.md                          # This file
├── DOCUMENTATION.md                   # Detailed technical documentation
├── ARCHITECTURE.md                    # System architecture guide
├── pyproject.toml                     # Python package metadata
├── src/
│   └── iscpp_simulator/
│       ├── main.py                    # Main entry point
│       ├── mapf_benchmark_provider.py # Map and scenario loading
│       ├── simulation.py              # Visualization and animation
│       ├── gui.py                     # GUI interface
│       └── data/graphs/               # Bundled maps and non-scenario graphs
├── graphs/
│   ├── scen-even/                     # Even-distribution scenarios
│   └── scen-random/                   # Random scenarios
```

## � Future Work

Future extensions of this line of research include:

- formal analysis of equilibrium existence and efficiency in intermittent cooperation environments;
- algorithmic development for strategic coordination under partial observability and asynchronous timing;
- extensions to larger agent populations, heterogeneous cooperation costs, and graph classes beyond grid-like MAPF benchmarks;
- integration with learned planning heuristics and evaluation of empirical performance across benchmark suites.

## 🤝 Collaboration and Contact

We welcome collaboration from researchers working on multi-agent planning, algorithmic game theory, and cooperative decision-making. Contributions may include theoretical analysis, algorithm design, experimental benchmarking, and extensions to new domains.

Please direct inquiries and collaboration proposals to the project maintainers at:

- `i.shedlezki@gmail.com`
- `agmon@cs.biu.ac.il`

Alternative contact information and institutional affiliations are provided in the repository documentation.

## �🔧 Advanced Usage

### Custom Map Creation

Maps must be in the MAPF `.map` format:

```
type octile
height 8
width 8
map
. . . . . . . .
. @ @ . . . . .
. @ @ . . . @ @
. . . . . . . .
...
```

Where:
- `.` = free cell
- `@` or `T` = obstacle
- `X` = cooperation node (extension for ICMPP instances)

### Custom Scenarios

Scenario files (`.scen`) follow the standard MAPF scene format. After the
`version` header, each row describes one agent:

```
version 1
bucket map width height start_x start_y goal_x goal_y optimal_length
0 empty-8-8.map 8 8 0 0 7 7 14
1 empty-8-8.map 8 8 0 7 7 0 14
...
```

Where:
- `bucket` = numerical scenario ID, often arbitrary or used to number agents
- `map` = map file associated with the scenario
- `width` and `height` = grid dimensions
- `start_x` and `start_y` = agent start coordinates
- `goal_x` and `goal_y` = agent goal coordinates
- `optimal_length` = shortest start-to-goal path length for that agent when
  other agents are ignored, usually computed with octile or Manhattan distance


### Extending Path Planners
A joint path is represented as a tuple of per-agent path results. Each
agent result is a dictionary with a `path` key containing an ordered list of
node IDs from start to goal, and a `length` key containing the total path cost.

Paths may also contain synthetic wait markers in the form `WAIT_<n>`, where
`n` is the number of time steps an agent waits before continuing. These markers
are not graph nodes; they are inserted between real node IDs to encode
synchronization delays, specifically when one agent must wait for another before
cooperating at a node. Simulation and visualization code include their duration when computing the
time-indexed agent states.

To add a custom path planning strategy:

1. Create a function in `main.py`:
```python
def custom_path_strategy(G, v_s, v_g):
    # Your algorithm here
    return {'path': path, 'length': cost}
```

2. Add to paths dictionary:
```python
paths["Custom Strategy"] = (
    custom_path_strategy(G, 's_1', 'g_1'),
    custom_path_strategy(G, 's_2', 'g_2')
)
```

3. Results will appear as selectable options in the GUI

## 📈 Key Parameters Explained

### Cooperation Density (`-d`, `--density`)
- **Range**: 0.0 to 1.0
- **Effect**: Controls the ratio of cooperation nodes to all nodes in the graph
- **Higher values**: More opportunities for cooperation
- **Lower values**: Sparser cooperation opportunities

### Cooperation Magnitude (`-mt`, `--magnitude`)
- **Range**: Integer > 0
- **Effect**: Sets the multiplication factor between non-cooperative and cooperative travel time at cooperation nodes
- **Calculation**: cooperative travel time is derived from non-cooperative travel time using this factor
- **Higher values**: Greater cooperation benefit

### Extent (`-e`, `--extent`)
- **Range**: Integer > 0
- **Effect**: Manhattan distance between each agent's starting node and target node
- **Higher values**: Longer start-to-target task distance

### Separation (`-se`, `--seperation`)
- **Range**: Integer > 0
- **Effect**: Manhattan distance between the two agents' starting nodes and between the two agents' target nodes
- **Higher values**: Agents start and finish farther apart

## 🧪 Testing & Examples

### Example 1: Basic Comparison
```bash
iscpp-simulator
# Compares shortest independent vs. cooperative paths on default 8x8 map
```

### Example 2: Simple Scenario
```bash
iscpp-simulator -m "empty-16-16" -s "empty-16-16-even-1" -d 0.4 -mt 20
# Uses a simple 16x16 empty map with first even-distribution scenario
# 40% cooperation nodes with benefit of 20 time units
```

### Example 3: Parameter Sweep
```bash
for d in 0.3 0.5 0.7; do
  for mt in 5 10 15; do
    iscpp-simulator -d $d -mt $mt
  done
done
```

## 🤝 Contributing

Enhancements welcomed in:
- Additional path planning algorithms
- New visualization features
- Performance optimizations
- Support for more than 2 agents
- Integration with other MAPF research

## 📚 References

This project is based on research in Intermittent Strategic Cooperation of Two Selfish Agents on Graphs (IC2PP). The benchmark maps and scenarios are from the MAPF community benchmarks.

### Related Work
- {Link to paper}

## 📖 Citation

If you use this simulator in academic work, please cite it as:

```bibtex
@software{shedlezki_2026_icpp_simulation,
  author = {Shedlezki, Itay and Agmon, Noa},
  title = {Intermittent Cooperation Multiagent Path Planning Simulation},
  year = {2026},
  license = {MIT}
}
```

## ⚙️ System Requirements

- **Python**: 3.7+
- **Memory**: 512 MB minimum
- **Disk**: 100 MB for benchmark datasets
- **Display**: Required for GUI (X11/Wayland on Linux, native on Windows/macOS)


## 📝 License
This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.

## Authors

**Itay Shedlezki** (Corresponding Author)
- Email: i.shedlezki@gmail.com
- Affiliation: Department of Computer Science and Artificial Intelligence, Bar-Ilan University, Ramat Gan, Israel

**Noa Agmon**
- Email: agmon@cs.biu.ac.il
- Affiliation: Department of Computer Science and Artificial Intelligence, Bar-Ilan University, Ramat Gan, Israel

---

For detailed technical information, see [DOCUMENTATION.md](DOCUMENTATION.md) and [ARCHITECTURE.md](ARCHITECTURE.md).
