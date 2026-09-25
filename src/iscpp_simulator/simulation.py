import heapq
import itertools
import math
from dataclasses import dataclass, field
from typing import Callable, Dict, FrozenSet, Hashable, List, Mapping, Tuple

import networkx as nx  # type: ignore[import-untyped]
import matplotlib.animation as animation
import matplotlib.colors as mcolors
from matplotlib.patches import Wedge
import matplotlib.pyplot as plt

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

AGENT_COLORS = [
    "#FFB84C",
    "#F266AB",
    "#A459D1",
    "#2CD3E1",
    "#0079FF",
    "#00DFA2",
    "#F6FA70",
    "#FF0060",
]


# ---------------------------------------------------------------------------
# k-agent strategy representation (ISCMPP, paper Section 2 "Problem Definition")
# ---------------------------------------------------------------------------
#
# A strategy is no longer a bare path: it is a sequence of (node, omega) steps,
# where omega is the set of agents this agent *explicitly* commits to waiting
# for at that node. Coalition formation (Section 3) is derived entirely from
# these waiting declarations via Algorithm 1 below - there is no automatic
# "merge if colocated" behavior anymore.

StrategyStep = Tuple[Hashable, FrozenSet[int]]
Strategy = List[StrategyStep]
JointStrategy = Dict[int, Strategy]


def get_agent_colors(k):
    """Return k visually distinct hex colors, one per agent."""
    if k <= len(AGENT_COLORS):
        return AGENT_COLORS[:k]
    cmap = plt.get_cmap("hsv")
    return [mcolors.to_hex(cmap(i / k)) for i in range(k)]


def node_delay(G, v, n):
    """tau_v(n): delay for a coalition of n synchronized agents visiting node v.

    Clamped to tau_v(k) for n beyond the stored curve length - safe since
    tau_v is required to be weakly non-increasing in n.
    """
    if n <= 0:
        return 0
    delays = G.nodes[v]["delay"]
    return delays[min(n, len(delays)) - 1]


def validate_joint_strategy(G, joint_strategy):
    """Structural validation of a JointStrategy against graph G.

    Node revisits within one agent's strategy are allowed (each occurrence is
    resolved as its own independent coalition-formation episode by the
    simulator - see simulate_joint_strategy). Raises ValueError on any
    structural violation.
    """
    agent_ids = set(joint_strategy.keys())
    for i, strategy in joint_strategy.items():
        if not strategy:
            raise ValueError(f"agent {i}: strategy must contain at least one step")
        start_node, _ = strategy[0]
        goal_node, last_wait = strategy[-1]
        if start_node != f"s_{i}":
            raise ValueError(f"agent {i}: strategy must start at s_{i}, got {start_node!r}")
        if goal_node != f"g_{i}":
            raise ValueError(f"agent {i}: strategy must end at g_{i}, got {goal_node!r}")
        if last_wait:
            raise ValueError(
                f"agent {i}: waiting set at the final node must be empty, got {last_wait!r}"
            )
        for step_index, (node, wait_set) in enumerate(strategy):
            for other in wait_set:
                if other == i:
                    raise ValueError(
                        f"agent {i}: cannot wait for itself at step {step_index} ({node!r})"
                    )
                if other not in agent_ids:
                    raise ValueError(
                        f"agent {i}: waits for unknown agent {other} at step "
                        f"{step_index} ({node!r})"
                    )
        for (node_a, _), (node_b, _) in zip(strategy, strategy[1:]):
            if not G.has_edge(node_a, node_b):
                raise ValueError(f"agent {i}: no edge {node_a!r}->{node_b!r} in graph")


def _waiting_closure(agent, wait_sets):
    """Reachability set of `agent` in WDG_v (waiting-dependency graph), self included."""
    seen = {agent}
    stack = [agent]
    while stack:
        current = stack.pop()
        for successor in wait_sets.get(current, ()):
            if successor not in seen:
                seen.add(successor)
                stack.append(successor)
    return frozenset(seen)


def compute_local_departure_times(arrivals, wait_sets, delay_fn):
    """Algorithm 1 (paper Section 3): local coalition formation at a single node.

    arrivals: agent_id -> arrival time r_i at this node.
    wait_sets: agent_id -> omega_i, the set of agents this agent explicitly
        waits for at this node (missing keys default to an empty set).
    delay_fn: n -> tau_v(n), weakly non-increasing in n.

    Returns agent_id -> departure time D_i. D_i == float('inf') means the
    agent waits indefinitely (its coalition is not locally stable and no
    committed partner ever actually departs with it).
    """
    agents = list(arrivals.keys())
    for i, omega in wait_sets.items():
        for j in omega:
            if j not in arrivals:
                raise ValueError(
                    f"agent {i} waits for agent {j}, which is not present in arrivals"
                )

    closure = {i: _waiting_closure(i, wait_sets) for i in agents}
    t_ready = {i: max(arrivals[j] for j in closure[i]) for i in agents}
    D = {i: t_ready[i] + delay_fn(len(closure[i])) for i in agents}
    C_star: Dict[int, FrozenSet[int]] = {i: closure[i] for i in agents}

    # Process agents in ascending (t_ready, agent_id) order - ties broken by
    # agent_id, an assumption the paper does not specify. Earlier-ready
    # agents/coalitions are always fully resolved (extension + stability)
    # before a later agent's computation can depend on them.
    order = sorted(agents, key=lambda a: (t_ready[a], a))
    for i in order:
        original_closure = closure[i]  # Omega_i, fixed - NOT C_star[i], which may grow
        a_post = sorted(
            (
                j
                for j in agents
                if j not in original_closure and t_ready[i] <= t_ready[j] <= D[i]
            ),
            key=lambda a: (t_ready[a], a),
        )
        a_post_set = set(a_post)
        pending: FrozenSet[int] = frozenset()
        for j in a_post:
            # Pending accumulates monotonically across rejected candidates and
            # resets only on acceptance - this is what lets "a3 alone: not
            # worth it" become "a3+a4 together: worth it" without losing a3.
            pending = pending | closure[j]
            candidate = C_star[i] | pending
            if t_ready[j] + delay_fn(len(candidate)) <= D[i]:
                C_star[i] = candidate
                D[i] = t_ready[j] + delay_fn(len(candidate))
                for m in C_star[i] & a_post_set:
                    C_star[m] = C_star[i]
                    D[m] = D[i]
                pending = frozenset()

        # Stability sweep for a_i's (possibly extended) coalition: if any
        # member strictly prefers an earlier departure, a_i's expectation of
        # cooperating with it is not honored, and a_i waits indefinitely.
        if any(D[j] < D[i] for j in C_star[i] if j != i):
            D[i] = float("inf")
            for m in C_star[i] & a_post_set:
                D[m] = float("inf")

    return D



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
