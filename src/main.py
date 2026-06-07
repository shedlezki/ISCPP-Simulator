import mapfBenchmarkProvider
import gui
import argparse
import networkx as nx  # type: ignore[import-untyped]


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

    return parser.parse_args()


# Add node travel time to edge travel time for use with nx shortest path algorithms.
def get_waits_included_graph(G, tau):
    G_mod = G.copy()
    for node in G.nodes:
        for neighbor in G.neighbors(node):
            if "visited" not in G_mod[node][neighbor]:
                G_mod[node][neighbor]["visited"] = True
                G_mod[node][neighbor]["tau"] += G_mod.nodes[node][tau]
    return G_mod


# Find shortest paths from a source node to all other nodes.
def shortest_paths(G, s, tau):
    G_mod = get_waits_included_graph(G, tau)

    shortest_paths = dict(nx.single_source_dijkstra_path(G_mod, s, weight="tau"))
    shortest_path_lengths = dict(
        nx.single_source_dijkstra_path_length(G_mod, s, weight="tau")
    )
    return {
        key: {"path": shortest_paths[key], "length": shortest_path_lengths[key]}
        for key in shortest_paths.keys()
    }


# Find the shortest independent path from v_s to v_g.
def shortest_independent_path(G, v_s, v_g):
    return shortest_paths(G, v_s, "tau_1")[v_g]


# Find the shortest cooperation path from v_s to v_g.
def shortest_cooperated_path(G, v_s, v_g):
    return shortest_paths(G, v_s, "tau_2")[v_g]


if __name__ == "__main__":
    args = parse_args()
    G, pos, grid, map = mapfBenchmarkProvider.get_graph_with_timeout(
        args.map,
        args.scenario,
        args.density,
        args.magnitude,
        args.seperation,
        args.extent,
        3,
        args.size,
    )
    SIP1, SIP2 = (
        shortest_independent_path(G, "s_1", "g_1"),
        shortest_independent_path(G, "s_2", "g_2"),
    )
    SCP1, SCP2 = (
        shortest_cooperated_path(G, "s_1", "g_1"),
        shortest_cooperated_path(G, "s_2", "g_2"),
    )
    paths = {
        "Shortest Independent Paths": (SIP1, SIP2),
        "Shortest Cooperation Paths": (SCP1, SCP2),
    }
    g = gui.GUI(G, pos, grid, paths, args, "123456789")
    g.show()
