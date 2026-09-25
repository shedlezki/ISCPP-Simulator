"""Demo of the k-agent ISCMPP simulator (multiagent branch).

One small hand-built graph, three hand-authored joint strategies that
exercise the new machinery end to end:

  1. "Full Cooperation" - all three agents explicitly wait for each other
     and travel together as a single 3-agent coalition.
  2. "Revisit"           - agent 1 passes through the same node twice,
                            cooperating with a *different* partner each
                            time (independent coalition-formation episodes).
  3. "Indefinite Wait"   - agent 3 explicitly commits to waiting for
                            agent 1, but agents 1 and 2 already merge (for
                            free - no one had to declare a wait) and leave
                            before agent 3 arrives, so agent 3 waits
                            forever. This is the Figure-1-style instability
                            from Section 3 of the paper.

Run for a console summary of all three:
    python examples/multiagent_demo.py

Add --gui to also open the interactive Tkinter viewer (the same widget
`iscpp-simulator` uses) so you can hit Play on each scenario and watch it
animate:
    python examples/multiagent_demo.py --gui
"""
import argparse
import types

import networkx as nx

from iscpp_simulator.simulation import evaluate_paths, simulate_joint_strategy


def build_graph():
    G = nx.DiGraph()
    pos = {}

    # GraphVisualizer expects positions as (col, -row), 0-indexed with row 0
    # at the top - the same convention mapf_benchmark_provider._get_grid_graph
    # uses for real maps - so node markers land centered in their grid cell.
    def add(name, col, row, delay):
        G.add_node(name, delay=delay)
        pos[name] = (col, -row)

    for i, row in ((1, 0), (2, 1), (3, 2)):
        add(f"s_{i}", 0, row, [0, 0, 0])
        add(f"g_{i}", 7, row, [0, 0, 0])
    add("c", 3, 1, [10, 4, 3])  # tau_v(n): solo=10, pair=4, trio=3
    add("mid", 3, 0, [0, 0, 0])  # detour node (above c), used by "Revisit"

    for u, v, tau in [
        ("s_1", "c", 4),
        ("s_2", "c", 4),
        ("s_3", "c", 10),
        ("c", "mid", 1),
        ("c", "g_1", 3),
        ("c", "g_2", 3),
        ("c", "g_3", 3),
    ]:
        G.add_edge(u, v, tau=tau)
        G.add_edge(v, u, tau=tau)

    grid = [[0] * 8 for _ in range(3)]
    return G, pos, grid


def build_scenarios():
    return {
        "Full Cooperation": {
            1: [("s_1", frozenset()), ("c", frozenset({2, 3})), ("g_1", frozenset())],
            2: [("s_2", frozenset()), ("c", frozenset({1, 3})), ("g_2", frozenset())],
            3: [("s_3", frozenset()), ("c", frozenset({1, 2})), ("g_3", frozenset())],
        },
        "Revisit": {
            1: [
                ("s_1", frozenset()),
                ("c", frozenset({2})),
                ("mid", frozenset()),
                ("c", frozenset({3})),
                ("g_1", frozenset()),
            ],
            2: [("s_2", frozenset()), ("c", frozenset({1})), ("g_2", frozenset())],
            3: [("s_3", frozenset()), ("c", frozenset()), ("g_3", frozenset())],
        },
        "Indefinite Wait": {
            1: [("s_1", frozenset()), ("c", frozenset()), ("g_1", frozenset())],
            2: [("s_2", frozenset()), ("c", frozenset()), ("g_2", frozenset())],
            3: [("s_3", frozenset()), ("c", frozenset({1})), ("g_3", frozenset())],
        },
    }


def describe(name, G, joint_strategy):
    print(f"\n=== {name} ===")
    times = evaluate_paths(G, joint_strategy)
    for agent in sorted(times):
        t = times[agent]
        if t == float("inf"):
            print(f"  agent {agent}: stuck - waits indefinitely")
        else:
            print(f"  agent {agent}: finishes at t={t}")

    result = simulate_joint_strategy(G, joint_strategy)
    for agent, strategy in sorted(joint_strategy.items()):
        visit = 0
        for step, (node, _wait) in enumerate(strategy):
            if node != "c":
                continue
            visit += 1
            coalition = result.coalition[agent][step]
            partners = sorted(a for a in coalition if a != agent)
            if partners:
                print(f"    agent {agent}, visit #{visit} to 'c': cooperates with {partners}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--gui", action="store_true", help="also open the interactive Tkinter viewer"
    )
    args = parser.parse_args()

    G, pos, grid = build_graph()
    strategies = build_scenarios()

    for name, joint_strategy in strategies.items():
        describe(name, G, joint_strategy)

    if args.gui:
        from iscpp_simulator import gui

        fake_args = types.SimpleNamespace(
            map="demo", density=0, magnitude=0, extent=0, seperation=0, num_agents=3
        )
        g = gui.GUI(G, pos, grid, strategies, fake_args, "demo", bounds=None)
        g.show()


if __name__ == "__main__":
    main()
