# Documentation Guide

This document serves as an index to the project documentation, organized by user need and reading level.

## Getting Started Quickly

**Primary:** [QUICKSTART.md](QUICKSTART.md) (5 minutes)
- Installation steps
- First command to run
- Common examples
- Troubleshooting

**Secondary:** [README.md](README.md) - "Quick Start" section

---

## Understanding the Simulator

**Primary:** [README.md](README.md)
- Problem overview
- How to run the simulator
- Command-line parameters
- GUI controls
- Common workflows

**Secondary:** [QUICKSTART.md](QUICKSTART.md) for practical examples

---

## Understanding System Design

**Primary:** [ARCHITECTURE.md](ARCHITECTURE.md)
- Architectural components
- Data flow diagrams

**Secondary:** Review code structure in `src/` directory

---

## Extending or Modifying

**Read in order:**
1. [CONTRIBUTING.md](CONTRIBUTING.md) - Guidelines and setup
2. [ARCHITECTURE.md](ARCHITECTURE.md) - System design
3. [DOCUMENTATION.md](DOCUMENTATION.md) - Technical details
4. Relevant code files in `src/`

**Then:** Follow the "Adding New Features" section in [CONTRIBUTING.md](CONTRIBUTING.md)

---

## Troubleshooting

**Check:**
1. [QUICKSTART.md](QUICKSTART.md) - "Troubleshooting" section
2. [README.md](README.md) - "Troubleshooting" section
3. Code comments in relevant source file
4. Create an issue in the repository

---

## Quick Reference

### Files and Their Purpose

| File | Purpose | Read Time | Best For |
|------|---------|-----------|----------|
| [QUICKSTART.md](QUICKSTART.md) | Get running fast | 5 min | First-time users |
| [README.md](README.md) | Full user guide | 15 min | Understanding features |
| [DOCUMENTATION.md](DOCUMENTATION.md) | Technical details | 30 min | Algorithms & math |
| [ARCHITECTURE.md](ARCHITECTURE.md) | System design | 25 min | Developers & extenders |
| [CONTRIBUTING.md](CONTRIBUTING.md) | Development guide | 20 min | Contributors |
| [requirements.txt](requirements.txt) | Dependencies | 1 min | Installation |

### Source Code Files

| File | Lines | Purpose |
|------|-------|---------|
| `src/main.py` | ~70 | Demonstration and CLI interface |
| `src/mapfBenchmarkProvider.py` | ~150 | Map loading and graph construction |
| `src/simulation.py` | ~200 | Core: evaluation, interpolation, visualization |
| `src/gui.py` | ~100 | Interactive visualization interface |

---

## Common Tasks and Help

### Installation & Setup
- **Problem**: Can't install packages
- **Solution**: [QUICKSTART.md](QUICKSTART.md) - Installation section

### Running the Simulator
- **Problem**: Don't know what command to run
- **Solution**: [QUICKSTART.md](QUICKSTART.md) - First Run section

### Understanding Parameters
- **Problem**: What do the `-d`, `-mt`, etc. parameters mean?
- **Solution**: [README.md](README.md) - Command-Line Arguments table

### Interpreting Results
- **Problem**: What do the path times mean?
- **Solution**: [README.md](README.md) - Path Planning Strategies section

### Using the GUI
- **Problem**: How do I use the visualization?
- **Solution**: [README.md](README.md) - GUI Usage section

### Modifying Code
- **Problem**: How do I add my own algorithm?
- **Solution**: [CONTRIBUTING.md](CONTRIBUTING.md) - Adding a Path Planning Algorithm

### Understanding Algorithms
- **Problem**: What's the difference between SIP and SCP?
- **Solution**: [DOCUMENTATION.md](DOCUMENTATION.md) - Algorithm Details section

### Performance Issues
- **Problem**: Simulation is too slow
- **Solution**: [ARCHITECTURE.md](ARCHITECTURE.md) - Performance Optimization Opportunities section

### Extending to Multiple Agents
- **Problem**: How do I support 3+ agents?
- **Solution**: [ARCHITECTURE.md](ARCHITECTURE.md) - Extensibility Points section

---

## Documentation Map

```
START
  │
  ├─ New user?
  │  └─→ QUICKSTART.md (5 min)
  │      └─→ README.md Quick Start (10 min)
  │
  ├─ Want to understand algorithms?
  │  └─→ DOCUMENTATION.md
  │      └─→ Algorithm Details (20 min)
  │
  ├─ Want to understand system?
  │  └─→ ARCHITECTURE.md
  │      └─→ Component Architecture (15 min)
  │
  ├─ Want to extend/modify code?
  │  └─→ CONTRIBUTING.md
  │      └─→ Development Setup (10 min)
  │      └─→ Your specific task guide (variable)
  │
  └─ Stuck?
     ├─→ Check README.md Troubleshooting
     ├─→ Check QUICKSTART.md Troubleshooting
     ├─→ Review code comments
     └─→ Create an issue
```

---

## Estimated Reading Time

| Goal | Time | Documents |
|------|------|-----------|
| Get it running | 5-10 min | QUICKSTART, README (Quick Start) |
| Use it effectively | 20-30 min | README, DOCUMENTATION |
| Understand deeply | 1-2 hours | All documents |
| Extend features | 2-4 hours | CONTRIBUTING, ARCHITECTURE, Code review |

---

## FAQ

**Q: I'm totally new, where do I start?**
A: Start with [QUICKSTART.md](QUICKSTART.md). It's designed for first-time users and will get you running in minutes.

**Q: I want to understand the math behind the algorithms.**
A: Go to [DOCUMENTATION.md](DOCUMENTATION.md) and find the "Mathematical Formulations" section.

**Q: I want to add a new path planning algorithm. Where do I start?**
A: Read [CONTRIBUTING.md](CONTRIBUTING.md) then [ARCHITECTURE.md](ARCHITECTURE.md), then look at the "Adding New Features" section.

**Q: What if I disagree with something in the documentation?**
A: Documentation improvements are welcome! See [CONTRIBUTING.md](CONTRIBUTING.md) for how to contribute improvements.

**Q: Can I print these documents?**
A: Yes! All documents are in Markdown format and can be printed or converted to PDF:
```bash
# On macOS with pandoc installed:
pandoc README.md -o README.pdf
```

---

## Document Cross-References

- **README** ↔ **QUICKSTART**: For quick examples
- **README** ↔ **DOCUMENTATION**: For parameter details and algorithms  
- **ARCHITECTURE** ↔ **CONTRIBUTING**: For extending the system
- **ARCHITECTURE** ↔ **DOCUMENTATION**: For understanding current design
- **CONTRIBUTING** ↔ **ARCHITECTURE**: For development guidelines

---

## Getting Help

If documentation doesn't answer your question:

1. **Search existing documentation** - Use Ctrl+F
2. **Check code comments** - Often contain implementation details
3. **Review examples** - Run different command variations
4. **Consult the troubleshooting sections** - In README and QUICKSTART
5. **Create an issue** - Include what you've tried and what you expected

---

## Authors

Itay Shedlezki (i.shedlezki@gmail.com)
Noa Agmon (agmon@cs.biu.ac.il)

Department of Computer Science and Artificial Intelligence
Bar-Ilan University, Ramat Gan, Israel

---

**Last Updated:** June 2026
**Documentation Version:** 1.0
