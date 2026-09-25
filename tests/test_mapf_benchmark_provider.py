import random

import pytest

from iscpp_simulator import mapf_benchmark_provider as provider


def test_make_delay_curve_is_weakly_non_increasing_across_seeds():
    for seed in range(50):
        random.seed(seed)
        curve = provider._make_delay_curve(
            k=6, standard_time=10, cooperation_time=1, even=False
        )
        assert len(curve) == 6
        assert curve[0] == 10
        assert all(curve[i] >= curve[i + 1] for i in range(len(curve) - 1))
        assert all(1 <= v <= 10 for v in curve)


def test_make_delay_curve_even_is_flat_after_solo():
    curve = provider._make_delay_curve(k=5, standard_time=8, cooperation_time=2, even=True)
    assert curve == [8, 2, 2, 2, 2]


def test_make_delay_curve_k1():
    assert provider._make_delay_curve(k=1, standard_time=7, cooperation_time=1, even=True) == [7]


@pytest.fixture
def empty_8_8_grid():
    return provider._map_file_to_grid(provider._map_file("empty-8-8"))


def test_generated_start_goal_nodes_are_k_distinct(empty_8_8_grid):
    grid = empty_8_8_grid
    for k in (2, 3, 5):
        random.seed(k)
        G, pos = provider._get_grid_graph(grid)
        G, pos = provider._generate_and_add_start_and_target_nodes(
            G, pos, grid, distance=3, length=4, k=k
        )
        boundary_names = [f"s_{i}" for i in range(1, k + 1)] + [
            f"g_{i}" for i in range(1, k + 1)
        ]
        for name in boundary_names:
            assert G.has_node(name), f"missing {name} for k={k}"
        # all boundary nodes must map to physically distinct grid cells
        assert len(set(boundary_names)) == len(boundary_names)


def test_add_node_weights_delay_arrays(empty_8_8_grid):
    grid = empty_8_8_grid
    k = 4
    random.seed(0)
    G, pos = provider._get_grid_graph(grid)
    G, pos = provider._generate_and_add_start_and_target_nodes(
        G, pos, grid, distance=3, length=4, k=k
    )
    G = provider._add_node_weights(G, k, ratio=0.5, even=True, standard_time=10, cooperation_time=1)

    boundary = provider._boundary_nodes(k)
    for node in G.nodes:
        delay = G.nodes[node]["delay"]
        assert len(delay) == k
        if node in boundary:
            assert delay == [0] * k
        else:
            assert delay[0] == 10  # solo delay is always standard_time
            assert all(delay[i] >= delay[i + 1] for i in range(len(delay) - 1))


def test_scenario_based_start_goal_nodes_are_k_distinct_and_collision_free():
    scene_file = provider._scenario_file("empty-8-8", "even-1")
    grid = provider._map_file_to_grid(provider._map_file("empty-8-8"))
    for k in (2, 3, 4):
        random.seed(k)
        G, pos = provider._get_grid_graph(grid)
        G, pos = provider._add_start_and_target_nodes(G, pos, scene_file, k=k)
        names = [f"s_{i}" for i in range(1, k + 1)] + [f"g_{i}" for i in range(1, k + 1)]
        for name in names:
            assert G.has_node(name)
        # every name maps to a distinct physical cell (no collisions)
        cell_of = {name: pos[name] for name in names}
        assert len(set(cell_of.values())) == len(names)
