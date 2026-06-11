---
title: Intermittent Strategic Cooperation of Selfish Agents on Graphs
---

# Intermittent Strategic Cooperation of Selfish Agents on Graphs

## Overview

This repository introduces a formal framework for the analysis of intermittent strategic cooperation among self-interested agents operating on graph-structured environments. The model captures scenarios in which strategic agents navigate a graph from specified start nodes to designated targets and can cooperate at some nodes.

Intermittent cooperation is characterized by its conditional nature: cooperative interactions are available only at selected graph locations and may require temporal coordination, waiting, or routing deviations. Agents are assumed to be selfish, optimizing individual completion time while considering the potential benefits of transient collaboration.

## Problem statement

Given a graph \(G = (V, E)\), a set of agents \(A\), and two cost functions per node:

- \(\tau_{1}(v)\): independent traversal cost at node \(v\), and
- \(\tau_{2}(v)\): cooperative traversal cost at node \(v\), with \(\tau_{2}(v) < \tau_{1}(v)\) for cooperation nodes.

The problem is to determine agent strategies and joint paths that optimize individual incentives by levergaing intermittent cooperative opportunities. Agents may elect to wait or detour to realize a cooperative execution, and the resulting outcome depends on both graph topology and other agents' paths.

## Formal model

- Graph: \(G = (V, E)\) with weighted edges.
- Cooperation nodes: \(C \subseteq V\).
- Nodes travel costs:
  - independent cost \(\tau_{1}(v)\) for agent \(i\) at node \(v\);
  - cooperative cost \(\tau_{2}(v)\) when two agents jointly traverse a cooperation node.
- Agent objectives: minimize individual path time.

## Research questions

This work supports exploration of the following research directions:

- Under what conditions does intermittent cooperation arise as an equilibrium among selfish agents?
- How should agents trade off waiting, detours, and cooperation to minimize their own completion time?
- How do graph structure and the density of cooperation nodes influence equilibrium efficiency and social welfare?
- What are the algorithmic implications for planning and coordination in different cooperation environments?

## Repository scope

The repository provides:

- a simulator for the Intermittent Cooperation Path Planning problem;
- benchmark maps, scenarios, and data loaders for MAPF-style graphs;
- visualization tools for path execution and cooperative interactions;
- a demonstration entry point illustrating independent and cooperative path evaluation.

The implementation is intended for researchers and practitioners studying coordination among selfish agents in structured domains.

The source code and documentation are available at: https://github.com/shedlezki/ISCPP-Simulator

## Future work

Potential directions for future work include:

- generalization to more than two agents (\(k > 2\))
- online planning for real-time strategy synthesis in dynamic environments
- stochastic systems with uncertainty in travel times, cooperation availability, and agent behavior
- capacitated systems that model congestion and resource contention at nodes and edges
- integration of learning-based planners and empirical validation on benchmark suites
- application to broader graph classes and heterogeneous cost structures

## Collaboration and contact

We welcome collaboration from researchers working on multi-agent planning, algorithmic game theory, incentive-aware coordination, and cooperative decision-making. Contributions may include theoretical analysis, algorithm design, empirical benchmarking, and extensions to new application domains.

Please direct inquiries and collaboration proposals to:

- `i.shedlezki@gmail.com`
- `agmon@cs.biu.ac.il`

We invite researchers to contribute via issues, pull requests, and joint publications in this line of work.

## Citation

If this simulator or associated datasets are used in academic work, please cite the repository and any accompanying publication.

---
