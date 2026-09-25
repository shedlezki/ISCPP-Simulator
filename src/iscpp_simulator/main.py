import argparse
import networkx as nx  # type: ignore[import-untyped]

from . import mapf_benchmark_provider
from .simulation import node_delay


def parse_args():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "-m", "--map", type=str, required=False, default="empty-8-8", help="Map name"
    )
    parser.add_argument(
        "-s", "--scenario", type=str, required=False, help="Scenario name"
    )
    parser.add_argument(
        "-d", "--density", type=float, required=False, default=0.5, help="Density value"
    )
    parser.add_argument(
        "-mt",
        "--magnitude",
        type=int,
        required=False,
        default=10,
        help="Magnitude value",
    )
    parser.add_argument(
        "-e", "--extent", type=int, required=False, default=5, help="Extent value"
    )
    parser.add_argument(
        "-se",
        "--seperation",
        type=int,
        required=False,
        default=4,
        help="Seperation value",
    )
    parser.add_argument("-si", "--size", type=str, required=False, help="Map size")
    parser.add_argument(
        "-k",
        "--num-agents",
        type=int,
        required=False,
        default=2,
        help="Number of agents (k)",
    )
    parser.add_argument(
        "--data-dir",
        type=str,
        required=False,
        help="Directory containing mapf-map data, or a graphs directory containing it",
    )
    parser.add_argument(
        "--scenario-dir",
        type=str,
        required=False,
        help="Directory containing MAPF .scen files",
    )

    return parser.parse_args()


# Fold tau_v(n) into every edge's weight, for Dijkstra under the assumption
# that a coalition of n agents cooperates immediately at every node.
def get_waits_included_graph(G, n):
    G_mod = G.copy()
    for node in G.nodes:
        for neighbor in G.neighbors(node):
            if "visited" not in G_mod[node][neighbor]:
                G_mod[node][neighbor]["visited"] = True
                G_mod[node][neighbor]["tau"] += node_delay(G_mod, node, n)
    return G_mod


# Find shortest paths from a source node to all other nodes, assuming an
# n-agent coalition cooperates immediately at every node along the way.
def shortest_paths(G, s, n):
    G_mod = get_waits_included_graph(G, n)

    paths = dict(nx.single_source_dijkstra_path(G_mod, s, weight="tau"))
    lengths = dict(nx.single_source_dijkstra_path_length(G_mod, s, weight="tau"))
    return {key: {"path": paths[key], "length": lengths[key]} for key in paths.keys()}


# SP(m): the shortest path from v_s to v_g assuming a coalition of m agents
# cooperates immediately (no synchronization wait) at every node. This is a
# purely optimistic, generally infeasible reference bound - real execution
# requires agents to actually synchronize, which SP(m) for m>1 assumes away.
# m=1 is the one exception: it is both optimistic *and* trivially
# achievable, since it claims no cooperation and needs none.
def shortest_path_optimistic(G, v_s, v_g, m):
    return shortest_paths(G, v_s, m)[v_g]


# Lift a plain node list into a Strategy: a sequence of (node, omega) steps,
# where omega (default empty) is the set of agents explicitly waited for.
def path_to_strategy(node_path, wait_sets=None):
    wait_sets = wait_sets or {}
    return [(node, frozenset(wait_sets.get(node, ()))) for node in node_path]


# The only SP(m) baseline that is both optimistic and honestly executable:
# each agent's SP(1) (its ordinary shortest independent path) with no
# explicit waits anywhere - no cooperation is claimed, and none is needed.
# Real cooperative behavior is exercised via hand-authored strategies with
# genuine waiting sets, not by a solver (out of scope here - see the paper's
# draft Section 4+ for that).
def build_independent_strategies(G, k):
    return {
        i: path_to_strategy(shortest_path_optimistic(G, f"s_{i}", f"g_{i}", 1)["path"])
        for i in range(1, k + 1)
    }


# SP(m) reference lengths for m=1..k, per agent - informational lower bounds
# only, not claims about an achievable joint strategy.
def optimistic_bounds(G, k):
    return {
        i: {
            m: shortest_path_optimistic(G, f"s_{i}", f"g_{i}", m)["length"]
            for m in range(1, k + 1)
        }
        for i in range(1, k + 1)
    }


def main():
    args = parse_args()
    G, pos, grid, _map_name = mapf_benchmark_provider.get_graph_with_timeout(
        args.map,
        args.scenario,
        args.density,
        args.magnitude,
        args.seperation,
        args.extent,
        3,
        args.size,
        args.data_dir,
        args.scenario_dir,
        k=args.num_agents,
    )

    strategies = {
        "Shortest Independent Paths": build_independent_strategies(G, args.num_agents),
    }
    bounds = optimistic_bounds(G, args.num_agents)

    from . import gui

    g = gui.GUI(G, pos, grid, strategies, args, "123456789", bounds=bounds)
    g.show()


if __name__ == "__main__":
    main()
