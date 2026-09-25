import networkx as nx
import pytest

from iscpp_simulator.simulation import (
    AGENT_COLORS,
    get_agent_colors,
    node_delay,
    validate_joint_strategy,
)


def make_graph():
    G = nx.DiGraph()
    G.add_edge("s_1", "c", tau=1)
    G.add_edge("c", "g_1", tau=1)
    G.add_edge("s_2", "c", tau=1)
    G.add_edge("c", "g_2", tau=1)
    G.nodes["s_1"]["delay"] = [0, 0]
    G.nodes["g_1"]["delay"] = [0, 0]
    G.nodes["s_2"]["delay"] = [0, 0]
    G.nodes["g_2"]["delay"] = [0, 0]
    G.nodes["c"]["delay"] = [8, 3]
    return G


def test_node_delay_basic_and_clamped():
    G = make_graph()
    assert node_delay(G, "c", 1) == 8
    assert node_delay(G, "c", 2) == 3
    assert node_delay(G, "c", 5) == 3  # clamped to tau_v(k)
    assert node_delay(G, "c", 0) == 0


def test_validate_joint_strategy_accepts_valid_strategy():
    G = make_graph()
    joint_strategy = {
        1: [("s_1", frozenset({2})), ("c", frozenset()), ("g_1", frozenset())],
        2: [("s_2", frozenset()), ("c", frozenset({1})), ("g_2", frozenset())],
    }
    validate_joint_strategy(G, joint_strategy)  # should not raise


def test_validate_joint_strategy_allows_revisits():
    G = nx.DiGraph()
    G.add_edge("s_1", "c", tau=1)
    G.add_edge("c", "d", tau=1)
    G.add_edge("d", "c", tau=1)
    G.add_edge("c", "g_1", tau=1)
    joint_strategy = {
        1: [
            ("s_1", frozenset()),
            ("c", frozenset()),
            ("d", frozenset()),
            ("c", frozenset()),
            ("g_1", frozenset()),
        ]
    }
    validate_joint_strategy(G, joint_strategy)  # should not raise


def test_validate_joint_strategy_allows_arbitrary_start_goal_names():
    # v_0/v_last need not be literally named "s_i"/"g_i" - that's a
    # mapf_benchmark_provider.py naming convention, not a model requirement
    # (e.g. the visualizer's $-decorated node names must still validate).
    G = make_graph()
    joint_strategy = {1: [("c", frozenset()), ("g_1", frozenset())]}
    validate_joint_strategy(G, joint_strategy)  # should not raise


def test_validate_joint_strategy_rejects_nonempty_final_wait():
    G = make_graph()
    joint_strategy = {1: [("s_1", frozenset()), ("g_1", frozenset({2}))]}
    with pytest.raises(ValueError):
        validate_joint_strategy(G, joint_strategy)


def test_validate_joint_strategy_rejects_self_wait():
    G = make_graph()
    joint_strategy = {1: [("s_1", frozenset({1})), ("g_1", frozenset())]}
    with pytest.raises(ValueError):
        validate_joint_strategy(G, joint_strategy)


def test_validate_joint_strategy_rejects_unknown_agent_wait():
    G = make_graph()
    joint_strategy = {1: [("s_1", frozenset({99})), ("g_1", frozenset())]}
    with pytest.raises(ValueError):
        validate_joint_strategy(G, joint_strategy)


def test_validate_joint_strategy_rejects_non_edge_step():
    G = make_graph()
    joint_strategy = {1: [("s_1", frozenset()), ("g_2", frozenset()), ("g_1", frozenset())]}
    with pytest.raises(ValueError):
        validate_joint_strategy(G, joint_strategy)


def test_get_agent_colors_small_k_uses_palette():
    assert get_agent_colors(3) == AGENT_COLORS[:3]


def test_get_agent_colors_large_k_falls_back_and_is_distinct():
    colors = get_agent_colors(12)
    assert len(colors) == 12
    assert len(set(colors)) == 12
