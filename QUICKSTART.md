# Quick Start Guide

Instructions for installing and running the ICPP simulator for the first time.

## Installation (2 minutes)

### 1. Install Python (if not already installed)
- Download from https://www.python.org/ (Python 3.7 or newer)
- Or use your system package manager:
  ```bash
  # macOS
  brew install python3
  
  # Ubuntu/Debian
  sudo apt-get install python3 python3-pip
  
  # Windows: Use installer from python.org
  ```

### 2. Install Dependencies
```bash
pip install networkx matplotlib numpy
```

Or:
```bash
pip install -r requirements.txt
```

### 3. Navigate to Source Directory
```bash
cd src
```

## First Run (1 minute)

### Default Simulation
Simply run:
```bash
python main.py
```

This will:
1. Generate an empty 8×8 grid
2. Place 2 agents at opposite corners
3. Compute shortest paths (independent and cooperative)
4. Display an interactive GUI

### What You'll See
- **Center panel**: Graph visualization with nodes and edges
- **Left side**: Path selection checkboxes
- **Top bar**: Simulation parameters and experiment ID
- **Buttons**: "Play" buttons to animate each path

## Common First Commands

### Try a Real Map
```bash
python main.py -m "Berlin_1_256"
```

### Use a Random Map of Medium Size
```bash
python main.py --size medium
```

### Increase Cooperation Opportunities
```bash
python main.py -d 0.7 -mt 20
```

### Run with Specific Scenario
```bash
python main.py -m "Boston_0_256" -s "even-1"
```

## Understanding the GUI

### The Main Panel
- **Gray nodes**: Regular nodes (all agents traverse with same time)
- **Darker nodes**: Cooperation nodes (special benefit for cooperation)
- **Black lines**: Edges connecting nodes
- **Pink circle**: Agent 1
- **Cyan circle**: Agent 2

### The Control Panel (Left Side)

**Path Options:**
```
☑ path Shortest Independent Path (85, 92)
  [Play]

☑ path Shortest Cooperated Path (72, 78)
  [Play]
```

- **First number** = Agent 1's total time
- **Second number** = Agent 2's total time

### Animation Controls

1. **Check the checkbox** to highlight the path on the map
2. **Click "Play"** to animate agents moving
3. **Watch the status** messages show what agents are doing

## Key Parameter Explanations

### Density (`-d`)
- **0.5** (default): 50% of nodes are cooperation nodes
- **0.2**: Fewer cooperation opportunities (sparser)
- **0.8**: More cooperation opportunities (dense)

### Magnitude (`-mt`)
- **10** (default): Cooperation saves 10 time units
- **5**: Small time savings
- **20**: Large time savings

### Extent (`-e`, `--extent`)
- **Range**: Integer > 0
- **Effect**: Manhattan distance between each agent's starting node and target node
- **Higher values**: Longer start-to-target task distance

### Separation (`-se`, `--seperation`)
- **Range**: Integer > 0
- **Effect**: Manhattan distance between the two agents' starting nodes and between the two agents' target nodes
- **Higher values**: Agents start and finish farther apart

## Common Workflows

### Workflow 1: Quick Demo (2 minutes)
```bash
python main.py --size small
```
Then click "Play" to see agents moving.

### Workflow 2: Comparing Strategies (5 minutes)
```bash
python main.py -d 0.3
# Check "Shortest Independent Path" - baseline performance
# Check "Shortest Cooperated Path" - potential benefit

python main.py -d 0.7
# Repeat - notice how denser cooperation changes the difference
```


## Troubleshooting

### Problem: "No module named 'networkx'"
**Solution:**
```bash
pip install networkx matplotlib numpy
```

### Problem: GUI doesn't appear
**Solution:** Try specifying a backend:
```python
# Add to top of main.py:
import matplotlib
matplotlib.use('TkAgg')  # or 'Qt5Agg' if Qt is installed
```

### Problem: "Timeout! Retrying..." loops forever
**Solution:** Try a simpler map:
```bash
python main.py --size small
```

### Problem: Map not found
**Solution:** Check that the graphs directory is in the parent folder:
```
project/
├── src/
│   └── main.py
└── graphs/           ← Must exist here
    └── mapf-map/
```

## Next Steps

1. **Read the README**: For more detailed usage information
2. **Explore Parameters**: Try different combinations of `-d`, `-mt`, `-e`
3. **Review ARCHITECTURE.md**: For system design
4. **Extend It**: Add your own path planning algorithms!

## Tips & Tricks

### Recording Results
The GUI shows an "EID" (Experiment ID) at the top. Click to copy it for tracking:
```bash
# Manual tracking
python main.py -d 0.5 > experiment_log.txt
# EID appears in console
```

## Where to Go From Here

- **Modify parameters** in command-line to explore the problem space
- **Visualize** different path planning approaches
- **Extend algorithms** to add new path planning methods
- **Modify visualization** to show additional metrics
- **Scale to N agents** for larger multi-agent systems
- **Integrate with other tools** for advanced analysis

## Quick Reference Card

```
INSTALLATION
  pip install networkx matplotlib numpy

FIRST RUN
  cd src
  python main.py

COMMON COMMANDS
  # Default 8x8 grid
  python main.py
  
  # Random small map
  python main.py --size small
  
  # High cooperation density
  python main.py -d 0.8 -mt 15
  

GUI CONTROLS
  [Checkbox] - Highlight path on map
  [Play]     - Animate agents along path
  [Top bar]  - Click EID to copy experiment ID

PARAMETERS
  -m, --map NAME         : Map to use (default: empty-8-8)
  -s, --scenario FILE    : Scenario file with agent positions
  -d, --density FLOAT    : Cooperation node density (0.0-1.0)
  -mt, --magnitude INT   : Cooperation time benefit
  -e, --extent INT       : Spatial extent of cooperation
  -c, --correlation INT  : Correlation between agents
  --size small|med|large : Random map size

FILES TO READ
  README.md              - Full user guide
  DOCUMENTATION.md       - Technical details & formulas
  ARCHITECTURE.md        - System design & extension guide
```

## Support

If you encounter issues:

1. **Check the troubleshooting section** above
2. **Read DOCUMENTATION.md** for technical details
3. **Review code comments** in the source files
4. **Check requirements** (Python 3.7+, required packages installed)

## Authors

Itay Shedlezki (i.shedlezki@gmail.com)
Noa Agmon (agmon@cs.biu.ac.il)

Department of Computer Science and Artificial Intelligence
Bar-Ilan University, Ramat Gan, Israel

---

**Last Updated:** June 2026
