# Contributing

Guidelines for contributing to the ICPP simulator implementation.

## Ways to Contribute

### 1. Bug Reports
- Found a bug? Submit an issue with:
  - Clear description of the problem
  - Steps to reproduce
  - Expected vs. actual behavior
  - Your environment (OS, Python version, package versions)

### 2. Feature Suggestions
- Have an idea? Submit a feature request with:
  - Description of the feature
  - Use cases and benefits
  - Proposed implementation approach
  - Examples or references if applicable

### 3. Documentation Improvements
- Fix typos, clarify explanations, add examples
- Documentation files:
  - `README.md` - Main documentation
  - `DOCUMENTATION.md` - Technical details
  - `ARCHITECTURE.md` - System design
  - `QUICKSTART.md` - Getting started
  - Code comments in `*.py` files

### 4. Code Contributions
- Implement new algorithms
- Optimize performance
- Extend to multi-agent scenarios
- Improve visualization
- Write tests

## Development Setup

### Prerequisites
- Python 3.7+
- pip (Python package manager)
- Git

### Local Setup
```bash
# Clone or download the repository
cd Intermittent\ Cooperation\ Multiagent\ Path\ Planing\ Simulation

# Create a virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Project Structure
```
src/
├── main.py                      # Entry point
├── mapfBenchmarkProvider.py       # Map loading
├── simulation.py                # Animation & visualization
└── gui.py                       # GUI interface

graphs/                          # Benchmark data
requirements.txt                 # Dependencies
README.md                        # Main documentation
DOCUMENTATION.md                 # Technical docs
ARCHITECTURE.md                  # System design
QUICKSTART.md                    # Getting started
```

## Code Style Guidelines

### General Principles
- Clear, readable code over clever code
- Meaningful variable/function names
- Comments for non-obvious logic

### Formatting
```python
# Follow PEP 8 style guide
# Use black for auto-formatting:
black src/

# Check style with flake8:
flake8 src/ --max-line-length=100

# Type checking with mypy:
mypy src/
```

### Documentation
```python
def compute_shortest_path(G: nx.DiGraph, s: str, g: str) -> Dict:
    """
    Compute shortest path from source to goal.
    
    This function uses Dijkstra's algorithm to find the shortest
    path in a weighted directed graph.
    
    Args:
        G: NetworkX directed graph with node attributes
           'tau_1' (individual time) and 'tau_2' (cooperative time)
        s: Source node identifier
        g: Goal node identifier
    
    Returns:
        Dictionary with keys:
        - 'path': List of nodes forming the path
        - 'length': Total cost/distance
        - 'cooperation_nodes': Nodes where cooperation occurs
    
    Raises:
        NetworkXError: If s or g not in G
        NetworkXNoPath: If no path exists from s to g
    
    Example:
        >>> G = nx.DiGraph()
        >>> G.add_node('a', tau_1=5)
        >>> result = compute_shortest_path(G, 'a', 'b')
        >>> print(result['length'])
    """
    pass
```


## Submitting Changes

### Before Submitting

1. **Check code style:**
   ```bash
   black src/
   flake8 src/
   mypy src/
   ```

2. **Update documentation:**
   - Add docstrings to new functions
   - Update README if user-facing changes
   - Update DOCUMENTATION.md if algorithmic changes

43 **Test manually:**
   ```bash
   cd src
   python main.py  # Quick test with defaults
   python main.py --size medium  # Test with real map
   ```

### Creating a Pull Request

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Make your changes with clear commit messages
4. Push to your branch: `git push origin feature/my-feature`
5. Create a Pull Request with:
   - Clear title and description
   - Reference to related issues
   - List of changes made
   - Any breaking changes or migration notes

## Communication

- **Issues**: For bug reports and feature requests
- **Discussions**: For questions and design decisions
- **Emails**: For private concerns

## Recognition

Contributors will be recognized in:
- README.md contributors section
- GitHub contributors page
- Release notes for significant contributions

## Questions?

- Check existing documentation
- Search issues for similar questions
- Create a new issue with your question
- Review code comments and docstrings

## Authors

Itay Shedlezki (i.shedlezki@gmail.com)
Noa Agmon (agmon@cs.biu.ac.il)

Department of Computer Science and Artificial Intelligence
Bar-Ilan University, Ramat Gan, Israel

---

**Last Updated:** June 2026
