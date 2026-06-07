import networkx as nx  # type: ignore[import-untyped]
import numpy as np
import random
import concurrent.futures
import time
from importlib import resources
from pathlib import Path

PACKAGE_GRAPHS = resources.files("iscpp_simulator").joinpath("data", "graphs")


def _graph_root(data_dir=None):
    if data_dir is not None:
        path = Path(data_dir).expanduser()
        if (path / "mapf-map").exists():
            return path / "mapf-map"
        return path
    return PACKAGE_GRAPHS.joinpath("mapf-map")


def _scenario_root(scenario_dir=None):
    if scenario_dir is not None:
        return Path(scenario_dir).expanduser()

    dev_scenario_root = Path.cwd() / "graphs" / "scen-even"
    if dev_scenario_root.exists():
        return dev_scenario_root

    return None


def _map_file(map_name, data_dir=None):
    return _graph_root(data_dir).joinpath(f"{map_name}.map")


def _scenario_file(map_name, scene_name, scenario_dir=None):
    scenario_root = _scenario_root(scenario_dir)
    if scenario_root is None:
        raise FileNotFoundError(
            "Scenario files are not bundled in the PyPI package. "
            "Use --scenario-dir to point at a directory containing .scen files."
        )
    return scenario_root / f"{map_name}-{scene_name}.scen"


# Return a random map name from the mapf-by-size folder for the given size.
def get_random_map_by_size(size, data_dir=None):
    folder_path = _graph_root(data_dir).joinpath("mapf-by-size", size)
    files = [f for f in folder_path.iterdir() if f.is_file()]
    if not files:
        return None
    basename = Path(random.choice(files).name).stem
    return f"mapf-by-size/{size}/{basename}"


# Return the graph, positions, grid, and selected map with timeout retries.
def get_graph_with_timeout(
    map_name,
    scenario_name,
    density,
    magnitude,
    correlation,
    extent,
    timeout=1,
    size=None,
    data_dir=None,
    scenario_dir=None,
):
    if size is not None:
        map_name = get_random_map_by_size(size, data_dir)
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
        while True:
            future = executor.submit(
                get_graph,
                map_name,
                scenario_name,
                ratio=density,
                coopertion_strength=magnitude,
                distance=correlation,
                length=extent,
                use_scenario=scenario_name is not None,
                data_dir=data_dir,
                scenario_dir=scenario_dir,
            )
            try:
                G, pos, grid = future.result(timeout=timeout)
                return G, pos, grid, map_name
            except concurrent.futures.TimeoutError:
                print("Timeout! Retrying...")
                time.sleep(0.1)


# Generate a grid from the map file.
def _map_file_to_grid(filepath):
    with filepath.open("r") as f:
        lines = f.readlines()
    height = int([line for line in lines if line.startswith("height")][0].split()[1])
    width = int([line for line in lines if line.startswith("width")][0].split()[1])
    map_start_index = lines.index("map\n") + 1
    grid_lines = lines[map_start_index: map_start_index + height]
    grid = np.zeros((height, width))
    for i, line in enumerate(grid_lines):
        for j, char in enumerate(line.strip()):
            if char == "@" or char == "T":
                grid[i, j] = 1  # 1 = obstacle, 0 = free, -1 = cooperation node
            elif char == "X":
                grid[i, j] = -1
    return grid


# Create a graph from the grid with edges between adjacent free cells.
def _get_grid_graph(grid):
    G = nx.DiGraph()
    rows, cols = len(grid), len(grid[0])
    for i in range(rows):
        for j in range(cols):
            if grid[i][j] <= 0:
                G.add_node((i, j), coop=(grid[i][j] == -1))
                for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:  # 4-neighborhood
                    ni, nj = i + dx, j + dy
                    if 0 <= ni < rows and 0 <= nj < cols and grid[ni][nj] <= 0:
                        G.add_edge((i, j), (ni, nj), weight=1, tau=1)
    pos = {node: (node[1], -node[0]) for node in G.nodes()}
    return G, pos


# Generate node weights for the time it takes each player to traverse the node.
# The ratio parameter determines the probability of a node being a cooperation node.
# The even parameter determines whether cooperation nodes share the same waiting time.
# The standard_time parameter determines non-cooperation node traversal time.
# The cooperation_time parameter determines cooperation node traversal time.
# The use_scenario parameter selects scenario-defined or randomly generated cooperation nodes.
def _add_node_weights(
    G: nx.Graph,
    ratio=0.5,
    even=True,
    standard_time=10,
    cooperation_time=1,
    use_scenario=False,
):
    for node in G.nodes:
        if node == "s_1" or node == "s_2" or node == "g_1" or node == "g_2":
            t1 = 0
            t2 = 0
        elif (random.random() <= ratio and not use_scenario) or (
            use_scenario and G.nodes[node]["coop"]
        ):
            if even:
                t1 = standard_time
                t2 = cooperation_time
            else:
                t1 = standard_time
                t2 = random.randrange(cooperation_time, standard_time)
        else:
            t1 = standard_time
            if use_scenario:
                t1 = cooperation_time
            t2 = t1

        G.nodes[node]["tau_1"] = max(t1, t2)
        G.nodes[node]["tau_2"] = min(t1, t2)
    return G


def _random_cell_within_manhattan(grid, x, y, d):
    while True:
        # d = random.randint(0, max_distance)
        di = random.randint(-d, d)
        dj = d - abs(di)
        if random.choice([True, False]):
            dj = -dj
        new_i = y + di
        new_j = x + dj
        if (
            0 <= new_i < len(grid)
            and 0 <= new_j < len(grid[0])
            and grid[new_j][new_i] == 0
        ):
            return (new_j, new_i)


def _random_cell_in_grid(grid):
    while True:
        i = random.randint(0, len(grid) - 1)
        j = random.randint(0, len(grid[0]) - 1)

        if grid[i][j] == 0:
            return (i, j)


def _generate_scenario_points(grid, length, s=None, g=None, distance=-1):
    if s is None or g is None or distance == -1:
        start_x, start_y = _random_cell_in_grid(grid)
        goal_x, goal_y = _random_cell_within_manhattan(grid, start_x, start_y, length)
    else:
        start_x, start_y = s
        while (start_x, start_y) == g or (start_x, start_y) == s:
            start_x, start_y = _random_cell_within_manhattan(grid, s[0], s[1], distance)
        goal_x, goal_y = start_x, start_y
        while (
            (start_x, start_y) == (goal_x, goal_y)
            or (goal_x, goal_y) == g
            or (goal_x, goal_y) == s
        ):
            goal_x, goal_y = _random_cell_within_manhattan(grid, g[0], g[1], distance)

    return (start_x, start_y), (goal_x, goal_y)


# Get starting and target nodes from the given scenario line, or a random line.
def _get_scenario_points(scene_file, line_number):
    with open(scene_file, "r") as f:
        lines = f.readlines()

    if line_number > len(lines) - 1 or line_number < 0:
        line_number = random.randint(0, len(lines) - 1)

    line = lines[line_number + 1]  # +1 to skip the 'version' header
    parts = line.strip().split()
    if len(parts) < 8:
        raise ValueError("Invalid scenario line format.")

    start_x, start_y = int(parts[4]), int(parts[5])
    goal_x, goal_y = int(parts[6]), int(parts[7])
    return (start_x, start_y), (goal_x, goal_y)


def _add_or_set(G, pos, node, name):
    if G.has_node(node):
        G = nx.relabel_nodes(G, {node: name})
        pos[name] = (node[1], -node[0])
        pos.pop(node)
    else:
        print("else")
        pass

    return G, pos


# adding starting and target nodes to the graph from a given scene file
def _add_start_and_target_nodes(G: nx.Graph, pos, scene_file, line1=-1, line2=-1):
    s1, g1 = _get_scenario_points(scene_file, line1)
    s2, g2 = s1, g1

    while s2 == s1 and g2 == g1:
        s2, g2 = _get_scenario_points(scene_file, line2)

    G, pos = _add_or_set(G, pos, s1, "s_1")
    G, pos = _add_or_set(G, pos, s2, "s_2")
    G, pos = _add_or_set(G, pos, g1, "g_1")
    G, pos = _add_or_set(G, pos, g2, "g_2")

    return G, pos


# Add generated starting and target nodes following distance and length constraints.
def _generate_and_add_start_and_target_nodes(G: nx.Graph, pos, grid, distance, length):
    s1, g1 = _generate_scenario_points(grid, length=length)
    s2, g2 = _generate_scenario_points(
        grid, length=length, s=s1, g=g1, distance=distance
    )

    G, pos = _add_or_set(G, pos, s1, "s_1")
    G, pos = _add_or_set(G, pos, s2, "s_2")
    G, pos = _add_or_set(G, pos, g1, "g_1")
    G, pos = _add_or_set(G, pos, g2, "g_2")

    return G, pos


def _draw_grid_and_graph(grid, G, pos):
    import matplotlib.pyplot as plt

    rows, cols = len(grid), len(grid[0])
    fig, ax = plt.subplots(figsize=(cols / 5, rows / 5))

    # Draw the grid: obstacles in black, free in white
    for i in range(rows):
        for j in range(cols):
            color = "white" if grid[i][j] == 0 else "black"
            ax.add_patch(
                plt.Rectangle(
                    (j, rows - 1 - i),
                    1,
                    1,
                    facecolor=color,
                    edgecolor="gray",
                    linewidth=0.2,
                )
            )

    # Graph node positions centered in each cell
    pos = {
        node: (pos[node][0] + 0.5, rows - 1 + pos[node][1] + 0.5) for node in G.nodes()
    }
    node_colors = [
        (
            "purple"
            if node == "s_1" or node == "g_1"
            else (
                "green"
                if node == "s_2" or node == "g_2"
                else (
                    "blue"
                    if G.nodes[node]["tau_1"] > G.nodes[node]["tau_2"]
                    else "black"
                )
            )
        )
        for node in G.nodes()
    ]

    # Draw graph edges and nodes on top
    nx.draw_networkx_edges(G, pos, ax=ax, width=0.5, edge_color="red", alpha=0.7)
    nx.draw_networkx_nodes(G, pos, ax=ax, node_size=8, node_color=node_colors)

    ax.set_xlim(0, cols)
    ax.set_ylim(0, rows)
    ax.set_aspect("equal")
    ax.axis("off")
    plt.tight_layout()
    plt.show()


# generates a graphs with the provided paramters
def get_graph(
    map_name,
    scene,
    type="grid",
    ratio=0.5,
    coopertion_strength=10,
    distance=3,
    length=20,
    use_scenario=False,
    data_dir=None,
    scenario_dir=None,
):
    grid = _map_file_to_grid(_map_file(map_name, data_dir))

    if type == "grid":
        G, pos = _get_grid_graph(grid)

    if use_scenario:
        G, pos = _add_start_and_target_nodes(
            G, pos, _scenario_file(map_name, scene, scenario_dir)
        )
    else:
        G, pos = _generate_and_add_start_and_target_nodes(
            G, pos, grid, distance, length
        )

    G = _add_node_weights(G, ratio, True, coopertion_strength, 1, use_scenario)

    return G, pos, grid


# not used in the main code
def generate_weights(G):
    labels = {}
    for n in G.nodes():
        labels[n] = f"v_{n}"
    v_s1, v_s2, v_g1, v_g2 = random.sample(list(G.nodes()), k=4)
    labels[v_s1] = "s_1"
    labels[v_s2] = "s_2"
    labels[v_g1] = "g_1"
    labels[v_g2] = "g_2"
    G = nx.relabel_nodes(G, labels)
    for node in G.nodes():
        if node == "s_1" or node == "s_2" or node == "g_1" or node == "g_2":
            t1 = 0
            t2 = 0
        elif random.choice([True, False]):
            t1 = random.randrange(10)
            t2 = random.randrange(10)
        else:
            t1 = random.randrange(10)
            t2 = t1
        G.nodes[node]["tau_1"] = max(t1, t2)
        G.nodes[node]["tau_2"] = min(t1, t2)
    for u, v, data in G.edges(data=True):
        data["tau"] = random.randrange(10)
    return G


if __name__ == "__main__":
    from . import simulation

    map_name = "empty-8-8"
    scene = "even-1"

    grid = _map_file_to_grid(_map_file(map_name))
    G, pos = _get_grid_graph(grid)
    G, pos = _add_start_and_target_nodes(
        G, pos, _scenario_file(map_name, scene)
    )
    G = _add_node_weights(G, 0.5, True, 3, 1)

    simulation.visualize(G, pos, None, grid)
