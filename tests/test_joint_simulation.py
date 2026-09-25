import math

import networkx as nx

from iscpp_simulator.simulation import evaluate_paths, interpolate_paths, simulate_joint_strategy


def add_node(G, name, k):
    G.add_node(name, delay=[0] * k)


def test_two_agent_mutual_cooperation():
    k = 2
    G = nx.DiGraph()
    for name in ["s_1", "s_2", "g_1", "g_2"]:
        add_node(G, name, k)
    G.add_node("c", delay=[10, 4])
    G.add_edge("s_1", "c", tau=1)
    G.add_edge("s_2", "c", tau=3)
    G.add_edge("c", "g_1", tau=1)
    G.add_edge("c", "g_2", tau=1)

    joint_strategy = {
        1: [("s_1", frozenset()), ("c", frozenset({2})), ("g_1", frozenset())],
        2: [("s_2", frozenset()), ("c", frozenset({1})), ("g_2", frozenset())],
    }

    times = evaluate_paths(G, joint_strategy)
    assert times == {1: 8, 2: 8}

    result = simulate_joint_strategy(G, joint_strategy)
    assert result.coalition[1][1] == frozenset({1, 2})
    assert result.coalition[2][1] == frozenset({1, 2})
    assert result.departure[1][1] == 7  # t_ready(=3) + tau_v(2)(=4)

    anim = interpolate_paths(G, joint_strategy)
    assert ("C", "c", 1, 4) in anim[1]
    assert ("C", "c", 1, 4) in anim[2]
    assert ("F", "g_1", 1, 1) == anim[1][-1]
    assert ("F", "g_2", 1, 1) == anim[2][-1]


def test_stuck_agent_reports_indefinite_wait():
    # Mirrors the Figure-1-style instability: a1 explicitly waits for a2,
    # who is itself locked into a tight, rigid mutual pair with a3 that has
    # no incentive to extend to include a1.
    k = 3
    G = nx.DiGraph()
    for i in (1, 2, 3):
        add_node(G, f"s_{i}", k)
        add_node(G, f"g_{i}", k)
    G.add_node("c", delay=[10, 6, 5])
    G.add_edge("s_1", "c", tau=5)
    G.add_edge("s_2", "c", tau=0)
    G.add_edge("s_3", "c", tau=0)
    G.add_edge("c", "g_1", tau=1)
    G.add_edge("c", "g_2", tau=1)
    G.add_edge("c", "g_3", tau=1)

    joint_strategy = {
        1: [("s_1", frozenset()), ("c", frozenset({2})), ("g_1", frozenset())],
        2: [("s_2", frozenset()), ("c", frozenset({3})), ("g_2", frozenset())],
        3: [("s_3", frozenset()), ("c", frozenset({2})), ("g_3", frozenset())],
    }

    times = evaluate_paths(G, joint_strategy)
    assert times[1] == math.inf
    assert times[2] == 7
    assert times[3] == 7

    result = simulate_joint_strategy(G, joint_strategy)
    assert result.stuck_step == {1: 1}
    assert 1 not in result.finished_at

    anim = interpolate_paths(G, joint_strategy)
    assert anim[1][-1] == ("WI", "c", 1, 1)
    assert ("F", "g_1", 1, 1) not in anim[1]
    assert anim[2][-1] == ("F", "g_2", 1, 1)
    assert anim[3][-1] == ("F", "g_3", 1, 1)


def test_revisit_forms_independent_episodes():
    # Agent 1 passes through node "c" twice: first cooperating with agent 2,
    # then later (after a detour through "mid") cooperating with agent 3.
    # The two visits must resolve as independent episodes - agent 2 must not
    # leak into the second episode, nor agent 3 into the first.
    k = 3
    G = nx.DiGraph()
    for i in (1, 2, 3):
        add_node(G, f"s_{i}", k)
        add_node(G, f"g_{i}", k)
    add_node(G, "mid", k)
    G.add_node("c", delay=[10, 3, 3])
    G.add_edge("s_1", "c", tau=1)
    G.add_edge("c", "mid", tau=1)
    G.add_edge("mid", "c", tau=1)
    G.add_edge("c", "g_1", tau=1)
    G.add_edge("s_2", "c", tau=1)
    G.add_edge("c", "g_2", tau=1)
    G.add_edge("s_3", "c", tau=6)
    G.add_edge("c", "g_3", tau=1)

    joint_strategy = {
        1: [
            ("s_1", frozenset()),
            ("c", frozenset({2})),
            ("mid", frozenset()),
            ("c", frozenset({3})),
            ("g_1", frozenset()),
        ],
        2: [("s_2", frozenset()), ("c", frozenset({1})), ("g_2", frozenset())],
        3: [("s_3", frozenset()), ("c", frozenset({1})), ("g_3", frozenset())],
    }

    result = simulate_joint_strategy(G, joint_strategy)
    assert result.coalition[1][1] == frozenset({1, 2})  # first visit: with agent 2
    assert result.coalition[1][3] == frozenset({1, 3})  # second visit: with agent 3
    assert 2 not in result.coalition[1][3]
    assert 3 not in result.coalition[1][1]

    times = evaluate_paths(G, joint_strategy)
    assert times == {1: 10, 2: 5, 3: 10}
