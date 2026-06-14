---
title: Intermittent Strategic Cooperation of Selfish Agents on Graphs
---



# Intermittent Strategic Cooperation of Selfish Agents on Graphs

Intermittent Strategic Cooperation-Based Path Planning studies how self-interested agents
move through a graph when cooperation is possible at selected locations. Each
agent has its own start and target, and each agent seeks to minimize its own
path time. Cooperation can reduce execution time at specific nodes, but it
may also require waiting, synchronization, or a detour from an individually
shortest path.

The problem combines multi-agent path planning with strategic decision-making:
agents must reason not only about graph distances, but also about whether a
temporary cooperative interaction is individually worthwhile.

## Problem intuition

In classical path planning, each agent can often be planned independently or
coordinated under a shared team objective. Intermittent strategic cooperation
occupies a different space. Agents are selfish, but the environment contains
local opportunities where cooperation can benefit both agents.

A cooperation opportunity is useful only when the agents can meet at the relevant
node at compatible times. An agent may therefore prefer to:

- follow its shortest independent path
- wait for another agent at a cooperation node
- take a longer route to gain a cooperative speedup
- ignore a cooperation opportunity if the delay or detour is too costly

The central question is when cooperation emerges from individual incentives and
how those incentives shape the resulting paths.

## Formal model

An instance is defined over a graph \(G = (V, E)\), a set of agents \(A\), start
and target vertices for each agent, and node execution costs.

For each node \(v \in V\):

- \(\tau_1(v)\) is the cost of traversing \(v\) independently.
- \(\tau_2(v)\) is the cost when two agents cooperate at \(v\).

For cooperation nodes, \(\tau_2(v) < \tau_1(v)\).

Agents choose paths and timing strategies that minimize their own completion
times. A cooperative execution can occur only when the relevant agents are
co-located at a cooperation node at compatible times.

## Core concepts

- **Selfish agents:** each agent optimizes its own path time.
- **Cooperation nodes:** selected graph vertices where joint traveling is faster
  than independent traveling.
- **Intermittent cooperation:** cooperation is local and temporary.
- **Synchronization:** agents may need to wait or adjust routes to cooperate.
- **Strategic path choice:** a path is evaluated by both travel cost and expected
  cooperative benefit.

## Research questions

Intermittent strategic cooperation raises questions at the intersection of
multi-agent planning, algorithms, and game theory:

- When is cooperation individually rational for selfish agents?
- Which paths form stable outcomes when each agent can choose independently?
- How do waiting, detours, and cooperative speedups trade off?
- How does graph structure affect the emergence and value of cooperation?
- What is the efficiency gap between selfish outcomes and socially optimal plans?
- Which algorithms can compute beneficial or stable cooperative path profiles?

## Related repositories

- [ISC2PP](https://github.com/shedlezki/ISC2PP#) contains algorithms and
  computational methods for the Intermittent Strategic Cooperation of Two
  Selfish Agents Path Planning problem.
- [ISCPP-Simulator](https://github.com/shedlezki/ISCPP-Simulator) provides a
  simulator and visualization environment for constructing instances, evaluating
  path profiles, and demonstrating cooperative interactions on graph-based maps.

Together, these repositories support both the algorithmic study of the problem
and empirical exploration through simulation and visualization.

## Applications

The ISCPP model is relevant to domains where autonomous or human-controlled
agents are primarily self-interested but can occasionally benefit from local
coordination:

- robotic navigation with shared manipulation or charging opportunities
- logistics and warehouse routing with temporary resource sharing
- transportation networks with coordination points
- distributed computing or communication tasks with local collaboration benefits
- evacuation, rescue, and service-routing settings with opportunistic teamwork

## Future directions

Potential extensions include:

- generalizing from two agents to larger populations
- online planning under uncertainty and dynamic graph conditions
- stochastic cooperation availability and variable execution times
- congestion, capacity limits, and resource contention
- heterogeneous agents with different costs and cooperation abilities

## Collaboration and contact

Researchers interested in multi-agent planning, algorithmic game theory,
incentive-aware coordination, and cooperative decision-making are welcome to
contribute ideas, algorithms, experiments, and extensions.

Please direct inquiries and collaboration proposals to:

- `i.shedlezki@gmail.com`
- `agmon@cs.biu.ac.il`

## Citation

If you use the ISCPP model, associated algorithms, simulator, or datasets in
academic work, please cite the relevant repository and accompanying publication.
