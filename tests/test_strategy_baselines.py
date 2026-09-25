import random

from iscpp_simulator import mapf_benchmark_provider as provider
from iscpp_simulator.main import (
    build_independent_strategies,
    optimistic_bounds,
    path_to_strategy,
    shortest_path_optimistic,
)
from iscpp_simulator.simulation import evaluate_paths, validate_joint_strategy


def make_k_agent_graph(k, seed=0):
    random.seed(seed)
    grid = provider._map_file_to_grid(provider._map_file("empty-8-8"))
    G, pos = provider._get_grid_graph(grid)
    G, pos = provider._generate_and_add_start_and_target_nodes(
        G, pos, grid, distance=3, length=4, k=k
    )
    G = provider._add_node_weights(G, k, ratio=0.5, even=True, standard_time=10, cooperation_time=1)
    return G, pos


def test_path_to_strategy_default_empty_waits():
    strategy = path_to_strategy(["s_1", "a", "g_1"])
    assert strategy == [("s_1", frozenset()), ("a", frozenset()), ("g_1", frozenset())]


def test_path_to_strategy_with_explicit_waits():
    strategy = path_to_strategy(["s_1", "c", "g_1"], wait_sets={"c": {2, 3}})
    assert strategy[1] == ("c", frozenset({2, 3}))


def test_build_independent_strategies_are_valid_and_playable():
    for k in (2, 3, 4):
        G, _pos = make_k_agent_graph(k, seed=k)
        strategies = build_independent_strategies(G, k)
        assert set(strategies.keys()) == set(range(1, k + 1))
        validate_joint_strategy(G, strategies)  # should not raise
        # no agent explicitly waits for anyone -> nobody is ever stuck
        times = evaluate_paths(G, strategies)
        assert all(t < float("inf") for t in times.values())


def test_optimistic_bounds_are_weakly_decreasing_in_m():
    k = 4
    G, _pos = make_k_agent_graph(k, seed=42)
    bounds = optimistic_bounds(G, k)
    for i in range(1, k + 1):
        curve = [bounds[i][m] for m in range(1, k + 1)]
        assert all(curve[j] >= curve[j + 1] for j in range(len(curve) - 1))


def test_shortest_path_optimistic_m1_matches_independent_strategy_length():
    k = 3
    G, _pos = make_k_agent_graph(k, seed=7)
    strategies = build_independent_strategies(G, k)
    times = evaluate_paths(G, strategies)
    for i in range(1, k + 1):
        sp1 = shortest_path_optimistic(G, f"s_{i}", f"g_{i}", 1)
        assert sp1["length"] == times[i]
