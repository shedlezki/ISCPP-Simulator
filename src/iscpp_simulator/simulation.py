import networkx as nx  # type: ignore[import-untyped]
import matplotlib.animation as animation
from matplotlib.patches import Wedge
import matplotlib.pyplot as plt
import math

SPEED = 25

R1_COLOR = "#FF90BB"
R2_COLOR = "#4ED7F1"
R1_BASE_COLOR = "#FF0060"
R2_BASE_COLOR = "#0079FF"
EDGES_COLOR = "black"
NODES_COLOR = "#BCCCDC"
COOPERATION_NODES_COLOR = "#9AA6B2"
LIVE_PATH_COLOR = "pink"
GRID_SIZE = 15
NODE_SIZE = 50
ROBOT_SIZE = 0.1
PATH_GAP = 0.05
PATH_WIDTH = 2


# Relabel graph nodes with dollar signs for LaTeX formatting in GUI labels.
def relabel_nodes(G):
    names_map = {}
    for n in G.nodes():
        names_map[n] = rf"${n}$"
    return nx.relabel_nodes(G, names_map, copy=True)


# Relabel path nodes with dollar signs for LaTeX formatting in GUI labels.
def relabel_path(path):
    new_path = []
    for n in path:
        new_path.append(rf"${n}$")
    return new_path


# Relabel position keys with dollar signs for LaTeX formatting in GUI labels.
def relabel_pos(pos):
    new_pos = {}
    for n in pos.keys():
        new_pos[rf"${n}$"] = pos[n]
    return new_pos


# generate commantry for the players' state
def generate_text(state, other):

    if state[0] == "T":
        return rf"executes task at node {state[1]} alone: {state[2]}/{state[3]}"
    if state[0] == "C":
        return rf"cooperates with {other} at node {state[1]}: {state[2]}/{state[3]}"
    if state[0] == "W":
        return rf"waits for {other} at {state[1]}: {state[2]}/{state[3]}"
    if state[0] == "E":
        return rf"travels from {state[1][0]} to {state[1][1]}: {state[2]}/{state[3]}"
    if state[0] == "F":
        return "reached target"


# get all edges in the path
def get_edges_in_path(path):
    edges = []
    p = relabel_path(path)
    for i in range(len(p) - 1):
        if p[i + 1].startswith("$WAIT"):
            edges.append((p[i], p[i + 2]))
        elif p[i].startswith("$WAIT"):
            pass
        else:
            edges.append((p[i], p[i + 1]))
    return edges


# Simulate the path execution and generate robot states for each time step.
def interpolate_paths(G, path1, path2):
    state1 = []
    state2 = []
    t1 = 0
    t2 = 0
    node1 = 0
    node2 = 0
    while node1 < len(path1) or node2 < len(path2):
        if node1 < len(path1) - 1:
            # print(path1[node1], path1[node1+1],path1[node1+2])
            if path1[node1 + 1].startswith("$WAIT_"):
                next_node = node1 + 2
                # print("OOO")
            else:
                next_node = node1 + 1
            next1 = (
                t1
                + G.edges[(path1[node1], path1[next_node])]["tau"]
                + G.nodes[path1[next_node]]["tau_1"]
            )
            if node1 + 2 < len(path1) and path1[node1 + 2].startswith("$WAIT_"):
                next1 += int(path1[node1 + 2][len("$WAIT_"): -1])
            if (
                node1 + 1 < len(path1)
                and path1[node1 + 1].startswith("$WAIT_")
                and node1 == 0
            ):
                next1 += int(path1[node1 + 1][len("$WAIT_"): -1])
        else:
            next1 = float("inf")

        if node2 < len(path2) - 1:

            next_node = (
                (node2 + 1)
                if not path2[node2 + 1].startswith("$WAIT_")
                else (node2 + 2)
            )
            next2 = (
                t2
                + G.edges[(path2[node2], path2[next_node])]["tau"]
                + G.nodes[path2[next_node]]["tau_1"]
            )
            if node2 + 2 < len(path2) and path2[node2 + 2].startswith("$WAIT_"):
                next2 += int(path2[node2 + 2][len("$WAIT_"): -1])
            if (
                node2 + 1 < len(path2)
                and path2[node2 + 1].startswith("$WAIT_")
                and node2 == 0
            ):
                next2 += int(path2[node2 + 1][len("$WAIT_"): -1])
        else:
            next2 = float("inf")

        if next1 <= next2 and node1 < len(path1):
            if node1 < len(path1) - 1:
                next_node = (
                    (node1 + 1)
                    if not path1[node1 + 1].startswith("$WAIT_")
                    else (node1 + 2)
                )
                edge_len = G.edges[(path1[node1], path1[next_node])]["tau"]
                exec_len = G.nodes[path1[next_node]]["tau_1"]

                next_wait_len = (
                    int(path1[node1 + 2][len("$WAIT_"): -1])
                    if node1 + 2 < len(path1) and path1[node1 + 2].startswith("$WAIT_")
                    else 0
                )
                wait_len = (
                    int(path1[node1 + 1][len("$WAIT_"): -1])
                    if node1 + 1 < len(path1)
                    and path1[node1 + 1].startswith("$WAIT_")
                    and node1 == 0
                    else 0
                )
                for i in range(wait_len):
                    state1.append(("W", path1[node1], i + 1, wait_len))
                for i in range(edge_len):
                    state1.append(
                        ("E", (path1[node1], path1[next_node]), (i + 1), edge_len)
                    )
                for i in range(next_wait_len):
                    state1.append(("W", path1[node1 + 1], i + 1, next_wait_len))
                for i in range(exec_len):
                    state1.append(("T", path1[next_node], (i + 1), exec_len))
            t1 = next1
            node1 += (
                1
                if not (
                    node1 + 1 < len(path1) and path1[node1 + 1].startswith("$WAIT_")
                )
                else 2
            )

        else:
            if node2 < len(path2) - 1:
                next_node = (
                    (node2 + 1)
                    if not path2[node2 + 1].startswith("$WAIT_")
                    else node2 + 2
                )
                edge_len = G.edges[(path2[node2], path2[next_node])]["tau"]
                exec_len = G.nodes[path2[next_node]]["tau_1"]
                next_wait_len = (
                    int(path2[node2 + 2][len("$WAIT_"): -1])
                    if node2 + 2 < len(path2) and path2[node2 + 2].startswith("$WAIT_")
                    else 0
                )
                wait_len = (
                    int(path2[node2 + 1][len("$WAIT_"): -1])
                    if node2 + 1 < len(path2)
                    and path2[node2 + 1].startswith("$WAIT_")
                    and node2 == 0
                    else 0
                )
                for i in range(wait_len):
                    state2.append(("W", path2[node2], i + 1, wait_len))
                for i in range(edge_len):
                    state2.append(
                        ("E", (path2[node2], path2[next_node]), (i + 1), edge_len)
                    )
                for i in range(next_wait_len):
                    state2.append(("W", path2[node2 + 1], i + 1, next_wait_len))
                for i in range(exec_len):
                    state2.append(("T", path2[next_node], (i + 1), exec_len))
            t2 = next2
            node2 += (
                1
                if not (
                    node2 + 1 < len(path2) and path2[node2 + 1].startswith("$WAIT_")
                )
                else 2
            )

        if node2 < len(path2) and node1 < len(path1) and path1[node1] == path2[node2]:
            if (
                abs(t2 - t1)
                < G.nodes[path1[node1]]["tau_1"] - G.nodes[path1[node1]]["tau_2"]
            ):
                exec_len = G.nodes[path2[node2]]["tau_2"]
                wait_len = abs(t2 - t1)
                state1 = state1[: len(state1) - G.nodes[path2[node2]]["tau_1"]]
                state2 = state2[: len(state2) - G.nodes[path2[node2]]["tau_1"]]
                if t2 > t1:
                    for i in range(wait_len):
                        state1.append(("W", path2[node2], (i + 1), wait_len))
                else:
                    for i in range(wait_len):
                        state2.append(("W", path2[node2], (i + 1), wait_len))

                for i in range(exec_len):
                    state1.append(("C", path1[node1], (i + 1), exec_len))
                    state2.append(("C", path1[node1], (i + 1), exec_len))

                t1 = (
                    t1 - G.nodes[path1[node1]]["tau_1"] + G.nodes[path1[node1]]["tau_2"]
                )
                t2 = t1
    state1.append(("F", path1[node1 - 1], 1, 1))
    state2.append(("F", path2[node2 - 1], 1, 1))
    return state1, state2


# Interpolate the robot position based on its current state.
def interpolate(robot, num, pos):
    if robot[0] == "T" or robot[0] == "W" or robot[0] == "C" or robot[0] == "F":
        return pos[robot[1]]
    else:
        dest = (
            (1 - robot[2] / robot[3]) * pos[robot[1][0]][0]
            + (robot[2] / robot[3]) * pos[robot[1][1]][0],
            (1 - robot[2] / robot[3]) * pos[robot[1][0]][1]
            + (robot[2] / robot[3]) * pos[robot[1][1]][1],
        )

        source = (
            (1 - (robot[2] - 1) / robot[3]) * pos[robot[1][0]][0]
            + (robot[2] - 1) / robot[3] * pos[robot[1][1]][0],
            (1 - (robot[2] - 1) / robot[3]) * pos[robot[1][0]][1]
            + (robot[2] - 1) / robot[3] * pos[robot[1][1]][1],
        )
        return (
            (1 - num) * source[0] + num * dest[0],
            (1 - num) * source[1] + num * dest[1],
        )


# calculate the path times for both players given their paths of the other
def evaluate_paths(G, path1, path2):
    t1 = 0
    t2 = 0
    node1 = 0
    node2 = 0

    while node1 < len(path1) or node2 < len(path2):

        if node1 < len(path1) - 1:
            if isinstance(path1[node1 + 1], str) and path1[node1 + 1].startswith(
                "WAIT_"
            ):
                next_node = node1 + 2
                # print("OOO")
            else:
                next_node = node1 + 1
            next1 = (
                t1
                + G.edges[(path1[node1], path1[next_node])]["tau"]
                + G.nodes[path1[next_node]]["tau_1"]
            )
            if (
                node1 + 2 < len(path1)
                and isinstance(path1[node1 + 2], str)
                and path1[node1 + 2].startswith("WAIT_")
            ):
                next1 += int(path1[node1 + 2][len("WAIT_"):])
            if (
                node1 + 1 < len(path1)
                and isinstance(path1[node1 + 1], str)
                and path1[node1 + 1].startswith("WAIT_")
                and node1 == 0
            ):
                next1 += int(path1[node1 + 1][len("WAIT_"):])

        if node2 < len(path2) - 1:
            next_node = (
                (node2 + 1)
                if not (
                    isinstance(path2[node2 + 1], str)
                    and path2[node2 + 1].startswith("WAIT_")
                )
                else (node2 + 2)
            )
            next2 = (
                t2
                + G.edges[(path2[node2], path2[next_node])]["tau"]
                + G.nodes[path2[next_node]]["tau_1"]
            )
            if (
                node2 + 2 < len(path2)
                and isinstance(path2[node2 + 2], str)
                and path2[node2 + 2].startswith("WAIT_")
            ):
                next2 += int(path2[node2 + 2][len("WAIT_"):])
            if (
                node2 + 1 < len(path2)
                and isinstance(path2[node2 + 1], str)
                and path2[node2 + 1].startswith("WAIT_")
            ) and node2 == 0:
                next2 += int(path2[node2 + 1][len("WAIT_"):])

        if (next1 <= next2 and node1 < len(path1)) or node2 == len(path2):
            t1 = next1
            node1 += (
                1
                if not (
                    node1 + 1 < len(path1)
                    and isinstance(path1[node1 + 1], str)
                    and path1[node1 + 1].startswith("WAIT_")
                )
                else 2
            )
        else:
            t2 = next2
            node2 += (
                1
                if not (
                    node2 + 1 < len(path2)
                    and isinstance(path2[node2 + 1], str)
                    and path2[node2 + 1].startswith("WAIT_")
                )
                else 2
            )

        if node2 < len(path2) and node1 < len(path1) and path1[node1] == path2[node2]:
            if (
                abs(t2 - t1)
                < G.nodes[path1[node1]]["tau_1"] - G.nodes[path1[node1]]["tau_2"]
            ):
                t2 = (
                    max(t2, t1)
                    - G.nodes[path1[node1]]["tau_1"]
                    + G.nodes[path1[node1]]["tau_2"]
                )
                t1 = t2
    return t1, t2


class GraphVisualizer:
    def __init__(self, G, pos, grid):
        self.grid = grid
        self.G = G
        self.pos = pos
        self.create_plot()
        self.edge_colors = [EDGES_COLOR for edge in self.G.edges()]
        self.colored1 = False
        self.colored2 = False
        self.drawn_edges = []

        # self.G=self.create_plot(G, pos)

    def create_plot(self):
        self.G = relabel_nodes(self.G)
        self.pos = relabel_pos(self.pos)
        # edge_labels = {(u, v): data['tau'] for u, v, data in G.edges(data=True)}
        # label_pos = {node: (x, y - 0.2) for (node, (x, y)) in self.pos.items()}
        # plt.figure(figsize=(8, 6))
        # fig, ax = plt.subplots()

        rows, cols = len(self.grid), len(self.grid[0])
        self.fig, self.ax = plt.subplots(
            figsize=(cols / GRID_SIZE + 2, rows / GRID_SIZE + 2)
        )
        self.draw_grid_and_graph()
        # nx.draw(G, self.pos, with_labels=True)
        # nx.draw_networkx_labels(G, label_pos, labels=node_labels, font_size=10)
        # nx.draw_networkx_edge_labels(G, self.pos, edge_labels=edge_labels)
        # ax.set_ylim([-2, 2])
        # ax.set_xlim([-1, 5])

    def draw_grid_and_graph(self):

        rows, cols = len(self.grid), len(self.grid[0])
        # Draw the grid: obstacles in black, free in white
        for i in range(rows):
            for j in range(cols):
                color = "white" if self.grid[i][j] <= 0 else "black"
                self.ax.add_patch(
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
        self.pos = {
            node: (self.pos[node][0] + 0.5, rows - 1 + self.pos[node][1] + 0.5)
            for node in self.G.nodes()
        }
        node_colors = [
            (
                R1_BASE_COLOR
                if node == r"$s_1$" or node == r"$g_1$"
                else (
                    R2_BASE_COLOR
                    if node == r"$s_2$" or node == r"$g_2$"
                    else (
                        COOPERATION_NODES_COLOR
                        if self.G.nodes[node]["tau_1"] > self.G.nodes[node]["tau_2"]
                        else NODES_COLOR
                    )
                )
            )
            for node in self.G.nodes()
        ]

        # Draw graph edges and nodes on top
        nx.draw_networkx_edges(
            self.G,
            self.pos,
            ax=self.ax,
            width=0.5,
            edge_color=EDGES_COLOR,
            alpha=0.7,
            arrows=False,
        )
        nx.draw_networkx_nodes(
            self.G, self.pos, ax=self.ax, node_size=NODE_SIZE, node_color=node_colors
        )
        nx.draw_networkx_nodes(
            self.G,
            self.pos,
            nodelist=[r"$s_1$", r"$s_2$"],
            ax=self.ax,
            node_size=NODE_SIZE,
            node_color=[R1_BASE_COLOR, R2_BASE_COLOR],
            edgecolors="black",
            linewidths=1,
        )
        labels = {
            node: str(node) for node in [r"$s_1$", r"$s_2$", r"$g_1$", r"$g_2$"]
        }
        nx.draw_networkx_labels(
            self.G,
            self.pos,
            labels=labels,
            font_color="white",
            font_size=4,
            font_weight="bold",
        )

        # nx.draw_networkx_labels(G, label_pos, labels=node_labels, font_size=10)

        self.ax.set_xlim(0, cols)
        self.ax.set_ylim(0, rows)
        self.ax.set_aspect("equal")
        self.ax.axis("off")
        # plt.tight_layout()
        # return fig, ax
        # plt.show()

    def set_animation(self, path1, path2):
        path1 = relabel_path(path1["path"])
        path2 = relabel_path(path2["path"])
        self.state1, self.state2 = interpolate_paths(self.G, path1, path2)
        self.ani = animation.FuncAnimation(
            self.fig,
            self.update,
            interval=SPEED,
            frames=SPEED * max(len(self.state1), len(self.state2)),
            blit=False,
            repeat=False,
        )
        self.r1_1 = Wedge(
            self.pos[path1[0]], ROBOT_SIZE, 0, 180, color=R1_COLOR, zorder=10
        )  # First half
        self.r1_2 = Wedge(
            self.pos[path1[0]], ROBOT_SIZE, 180, 360, color=R1_COLOR, zorder=11
        )  # Second half
        self.r2_1 = Wedge(
            self.pos[path2[0]], ROBOT_SIZE, 0, 180, color=R2_COLOR, zorder=11
        )  # First half
        self.r2_2 = Wedge(
            self.pos[path2[0]], ROBOT_SIZE, 180, 360, color=R2_COLOR, zorder=10
        )  # Second half
        self.ax.add_patch(self.r1_1)
        self.ax.add_patch(self.r1_2)
        self.ax.add_patch(self.r2_1)
        self.ax.add_patch(self.r2_2)

        self.commentry = self.ax.text(
            0,
            len(self.grid),
            r"$r_1$",
            fontsize=5,
            verticalalignment="bottom",
            horizontalalignment="left",
        )

    def update(self, num):
        r1_state = self.state1[min(math.floor(num / SPEED), len(self.state1) - 1)]
        r2_state = self.state2[min(math.floor(num / SPEED), len(self.state2) - 1)]
        # print(r1_state, r2_state)

        if r1_state[0] == "E" and not self.colored1:
            self.colored1 = True
            self.draw_edge(r1_state[1], R1_COLOR, -PATH_GAP)
        elif (
            r1_state[0] != "E"
            or r1_state[1][0] == r"$s_2$"
            or r1_state[1][0] == r"$g_2$"
        ):
            self.colored1 = False

        if r2_state[0] == "E" and not self.colored2:
            self.colored2 = True
            self.draw_edge(r2_state[1], R2_COLOR, PATH_GAP)
        elif (
            r2_state[0] != "E"
            or r1_state[1][0] == r"$s_1$"
            or r1_state[1][0] == r"$g_1$"
        ):
            self.colored2 = False

        x1, y1 = interpolate(r1_state, (num % SPEED) / SPEED, self.pos)
        x2, y2 = interpolate(r2_state, (num % SPEED) / SPEED, self.pos)
        self.r1_1.set_center((x1, y1))
        self.r1_2.set_center((x1, y1))
        self.r2_1.set_center((x2, y2))
        self.r2_2.set_center((x2, y2))

        self.commentry.set_text(
            (
                f"t={math.floor(num / SPEED)}\n"
                f"$r_1$ {generate_text(r1_state, r'$r_2$')}\n"
                f"$r_2$ {generate_text(r2_state, r'$r_1$')}"
            )
        )
        return self.commentry, self.r1_1, self.r1_2, self.r2_1, self.r2_2

    def draw_edge(self, edge, color, path_gap):
        x = [self.pos[edge[0]][0] + path_gap, self.pos[edge[1]][0] + path_gap]
        y = [self.pos[edge[0]][1] + path_gap, self.pos[edge[1]][1] + path_gap]
        (line,) = self.ax.plot(x, y, color=color, linewidth=PATH_WIDTH)
        self.drawn_edges.append(line)
        return line

    def draw_path(self, path, color, path_gap=0):
        edges = get_edges_in_path(path)
        drawn_lines = []
        for edge in edges:
            drawn_lines.append(self.draw_edge(edge, color, path_gap))
        return drawn_lines

    def clear_path(self, drawn_lines):
        for line in drawn_lines:
            # print(line)
            line.remove()

    def show(self):
        plt.show()


def visualize(G, pos, paths, grid):
    # distances = {(u, v): d['tau'] for u, v, d in G.edges(data=True)}
    # pos = nx.kamada_kawai_layout(G, dist=distances, weight='tau')
    vis = GraphVisualizer(G, pos, grid)
    # print(paths)
    vis.set_animation(paths[0], paths[1])
    plt.show()
