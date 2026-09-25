import heapq
import itertools
import math
from dataclasses import dataclass, field
from typing import Callable, Dict, FrozenSet, Hashable, List, Mapping, Tuple

import networkx as nx  # type: ignore[import-untyped]
import matplotlib.animation as animation
import matplotlib.colors as mcolors
from matplotlib.patches import Circle
import matplotlib.pyplot as plt

SPEED = 25

EDGES_COLOR = "black"
NODES_COLOR = "#BCCCDC"
COOPERATION_NODES_COLOR = "#9AA6B2"
LIVE_PATH_COLOR = "pink"
CELL_INCHES = 1  # figure inches per grid cell, before clamping
MIN_FIG_INCHES = 5  # floor on the figure's longer side
MAX_FIG_INCHES = 100  # ceiling on the figure's longer side
MIN_FIG_DIM_INCHES = 3  # floor on EACH side - keeps flat/tall grids from becoming slivers
NODE_SIZE = 50
ROBOT_SIZE = 0.1
ROBOT_OFFSET_RADIUS = 0.15  # separates colocated agents' markers
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

    Note: this does NOT require v_0/v_last to be named "s_i"/"g_i" - that
    string convention belongs to mapf_benchmark_provider.py's graph
    generation, not to the strategy model itself (the paper's v_0=s_i is
    notation for "the agent's own source", not a naming requirement), and
    other legitimate graphs (e.g. the visualizer's $-decorated node names)
    don't follow it.
    """
    agent_ids = set(joint_strategy.keys())
    for i, strategy in joint_strategy.items():
        if not strategy:
            raise ValueError(f"agent {i}: strategy must contain at least one step")
        _, last_wait = strategy[-1]
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
    D, _C_star = _resolve_local_coalitions(arrivals, wait_sets, delay_fn)
    return D


def _resolve_local_coalitions(arrivals, wait_sets, delay_fn):
    """Same as compute_local_departure_times, but also returns each agent's
    resolved coalition C*_i (used by the joint simulator to size tau_v(|C*|)
    and to report who an agent actually ends up with)."""
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

    return D, C_star



def relabel_nodes(G):
    names_map = {}
    for n in G.nodes():
        names_map[n] = rf"${n}$"
    return nx.relabel_nodes(G, names_map, copy=True)


# Relabel position keys with dollar signs for LaTeX formatting in GUI labels.
def relabel_pos(pos):
    new_pos = {}
    for n in pos.keys():
        new_pos[rf"${n}$"] = pos[n]
    return new_pos


# Relabel a Strategy's node names with dollar signs for LaTeX formatting.
def relabel_strategy(strategy):
    return [(rf"${node}$", wait_set) for node, wait_set in strategy]


# Relabel every strategy in a JointStrategy.
def relabel_joint_strategy(joint_strategy):
    return {
        agent: relabel_strategy(strategy) for agent, strategy in joint_strategy.items()
    }


# generate commantry for a player's state
def generate_text(state):

    if state[0] == "T":
        return rf"executes task at node {state[1]} alone: {state[2]}/{state[3]}"
    if state[0] == "C":
        return rf"cooperates at node {state[1]}: {state[2]}/{state[3]}"
    if state[0] == "W":
        return rf"waits at {state[1]}: {state[2]}/{state[3]}"
    if state[0] == "E":
        return rf"travels from {state[1][0]} to {state[1][1]}: {state[2]}/{state[3]}"
    if state[0] == "F":
        return "reached target"
    if state[0] == "WI":
        return rf"waits indefinitely at {state[1]}"


# get all edges traversed by a Strategy (sequence of (node, omega) steps)
def get_edges_in_path(strategy):
    nodes = [node for node, _omega in strategy]
    return list(zip(nodes, nodes[1:]))


# ---------------------------------------------------------------------------
# Global joint simulator (paper Section 3.1 "Total Path Time")
# ---------------------------------------------------------------------------
#
# Algorithm 1 is a batch computation: it needs a *closed* set of arrivals at
# a node before it can resolve. Node revisits mean there's no static per-node
# visitor set to wait for - a node's participant list for a given episode has
# to be discovered dynamically, from the actual timing of the one concrete
# execution being simulated.
#
# Why this is still safe to compute correctly online: in Algorithm 1, agent
# a_j can only ever be a candidate post-readiness extension for a_i if
# t_ready_j <= D_i, and t_ready_j >= arrival_j always (readiness is a max
# over arrival times, including its own). So once every event in the global
# queue up to some time T has been processed, we know with certainty that no
# not-yet-arrived agent can have t_ready_j <= T - meaning any pending agent
# at any node whose *currently computed* tentative D_i <= T can be finalized
# immediately: nothing still in the future could possibly change that
# result. This resolves each node's episodes purely from causal/temporal
# order, with no precomputed visitor set at all - which also handles
# revisits for free (a later, unrelated pass through the same node is just a
# new episode, opened after the previous one closed).


@dataclass
class SimulationResult:
    arrival: Dict[int, List[float]] = field(default_factory=dict)
    departure: Dict[int, List[float]] = field(default_factory=dict)
    coalition: Dict[int, List[FrozenSet[int]]] = field(default_factory=dict)
    finished_at: Dict[int, float] = field(default_factory=dict)
    stuck_step: Dict[int, int] = field(default_factory=dict)


def simulate_joint_strategy(G, joint_strategy):
    """Execute a JointStrategy end to end, resolving Algorithm 1 at every
    node visit (episode) as it becomes safe to do so. Returns a
    SimulationResult with per-agent, per-strategy-step arrival/departure/
    coalition, plus finished_at / stuck_step for agents that do/don't reach
    their target.
    """
    validate_joint_strategy(G, joint_strategy)

    result = SimulationResult(
        arrival={i: [None] * len(s) for i, s in joint_strategy.items()},
        departure={i: [None] * len(s) for i, s in joint_strategy.items()},
        coalition={i: [None] * len(s) for i, s in joint_strategy.items()},
    )

    counter = itertools.count()
    queue: List[Tuple[float, int, int, int]] = []  # (time, seq, agent, step)

    # Step 0 (s_i) is exempt from coalition formation: departure from an
    # agent's own start node is defined to be 0 unconditionally (paper
    # Section 3.1), independent of anyone else's presence there.
    for agent, strategy in joint_strategy.items():
        result.arrival[agent][0] = 0.0
        result.departure[agent][0] = 0.0
        result.coalition[agent][0] = frozenset({agent})
        if len(strategy) == 1:
            result.finished_at[agent] = 0.0
        else:
            node0, node1 = strategy[0][0], strategy[1][0]
            edge_tau = G.edges[node0, node1]["tau"]
            heapq.heappush(queue, (edge_tau, next(counter), agent, 1))

    # node -> {agent: (arrival_time, step_index)}, the currently-open episode
    pending: Dict[Hashable, Dict[int, Tuple[float, int]]] = {}

    def finalize_sweep(horizon):
        """Finalize every pending agent whose tentative departure <= horizon.
        Loops since a finalization can push a new event that immediately
        unlocks another finalization elsewhere.

        An occupant's waiting closure may reach an agent who hasn't arrived
        at this node yet (that's the normal, expected case - it's exactly
        why they're waiting). Such an occupant's readiness time isn't
        determinable yet, so it - and, transitively, anyone whose own
        closure passes through it - must be excluded from this round's
        Algorithm 1 run entirely, not just barred from finalizing: letting
        an "incomplete" agent participate in someone else's post-readiness
        extension would silently use its not-yet-final data.
        """
        progressed = True
        while progressed:
            progressed = False
            for node in list(pending.keys()):
                occupants = pending[node]
                if not occupants:
                    del pending[node]
                    continue
                arrivals = {a: t for a, (t, _s) in occupants.items()}
                wait_sets = {
                    a: joint_strategy[a][step][1] for a, (_t, step) in occupants.items()
                }
                present = set(arrivals.keys())
                complete = {
                    a for a in occupants if _waiting_closure(a, wait_sets) <= present
                }
                if not complete:
                    continue
                sub_arrivals = {a: arrivals[a] for a in complete}
                sub_wait_sets = {a: wait_sets[a] for a in complete}
                tentative_D, tentative_C = _resolve_local_coalitions(
                    sub_arrivals, sub_wait_sets, lambda n, v=node: node_delay(G, v, n)
                )
                for agent in list(complete):
                    d_i = tentative_D[agent]
                    if d_i > horizon:
                        continue
                    arrival_time, step = occupants.pop(agent)
                    result.arrival[agent][step] = arrival_time
                    result.departure[agent][step] = d_i
                    result.coalition[agent][step] = tentative_C[agent]
                    progressed = True
                    strategy = joint_strategy[agent]
                    if d_i == float("inf"):
                        result.stuck_step[agent] = step
                    elif step + 1 == len(strategy):
                        result.finished_at[agent] = d_i
                    else:
                        node_here, node_next = strategy[step][0], strategy[step + 1][0]
                        edge_tau = G.edges[node_here, node_next]["tau"]
                        heapq.heappush(
                            queue, (d_i + edge_tau, next(counter), agent, step + 1)
                        )
                if not occupants:
                    del pending[node]

    while queue:
        time, _seq, agent, step = heapq.heappop(queue)
        node = joint_strategy[agent][step][0]
        pending.setdefault(node, {})[agent] = (time, step)
        horizon = queue[0][0] if queue else float("inf")
        finalize_sweep(horizon)

    # Termination: the queue is permanently empty, so no future arrival can
    # ever occur anywhere - finalize everyone still pending, unconditionally.
    finalize_sweep(float("inf"))

    # Anyone still left in `pending` at this point is permanently
    # "incomplete": directly or transitively waiting for an agent that will
    # never arrive here (e.g. stuck itself, elsewhere). Algorithm 1 can
    # never resolve them - they simply wait indefinitely.
    for node, occupants in list(pending.items()):
        for agent, (arrival_time, step) in occupants.items():
            wait_set = joint_strategy[agent][step][1]
            result.arrival[agent][step] = arrival_time
            result.departure[agent][step] = float("inf")
            result.coalition[agent][step] = _waiting_closure(agent, {agent: wait_set})
            result.stuck_step[agent] = step
    pending.clear()

    return result


def evaluate_paths(G, joint_strategy):
    """Total travel time for every agent under a JointStrategy.

    Returns agent_id -> time reached its target, or float('inf') if it
    waits indefinitely and never reaches it.
    """
    result = simulate_joint_strategy(G, joint_strategy)
    return {i: result.finished_at.get(i, float("inf")) for i in joint_strategy}


def _build_anim_states(G, strategy, result, agent):
    states = []
    n_steps = len(strategy)
    for step in range(n_steps - 1):
        node_here, node_next = strategy[step][0], strategy[step + 1][0]
        edge_len = G.edges[node_here, node_next]["tau"]
        for i in range(edge_len):
            states.append(("E", (node_here, node_next), i + 1, edge_len))

        arrival = result.arrival[agent][step + 1]
        departure = result.departure[agent][step + 1]
        if departure == float("inf"):
            states.append(("WI", node_next, 1, 1))
            return states

        coalition = result.coalition[agent][step + 1]
        exec_len = node_delay(G, node_next, len(coalition))
        wait_len = int(round(departure - arrival - exec_len))
        for i in range(wait_len):
            states.append(("W", node_next, i + 1, wait_len))
        for i in range(exec_len):
            if len(coalition) > 1:
                states.append(("C", node_next, i + 1, exec_len))
            else:
                states.append(("T", node_next, i + 1, exec_len))

    if agent in result.finished_at:
        states.append(("F", strategy[-1][0], 1, 1))
    return states


def interpolate_paths(G, joint_strategy):
    """Per-agent animation state lists for a JointStrategy - agent_id ->
    list of E/T/W/C/F/WI tuples, one per animation frame."""
    result = simulate_joint_strategy(G, joint_strategy)
    return {
        i: _build_anim_states(G, strategy, result, i)
        for i, strategy in joint_strategy.items()
    }


# Interpolate the robot position based on its current state.
def interpolate(robot, num, pos):
    if robot[0] in ("T", "W", "C", "F", "WI"):
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


class GraphVisualizer:
    def __init__(self, G, pos, grid, k=None):
        self.grid = grid
        self.G = G
        self.pos = pos
        self.k = k if k is not None else self._infer_k(G)
        self.colors = get_agent_colors(self.k)
        self.create_plot()
        self.edge_colors = [EDGES_COLOR for edge in self.G.edges()]
        self.drawn_edges = []

    @staticmethod
    def _infer_k(G):
        return sum(1 for node in G.nodes if str(node).startswith("s_"))

    def create_plot(self):
        self.G = relabel_nodes(self.G)
        self.pos = relabel_pos(self.pos)
        # edge_labels = {(u, v): data['tau'] for u, v, data in G.edges(data=True)}
        # label_pos = {node: (x, y - 0.2) for (node, (x, y)) in self.pos.items()}
        # plt.figure(figsize=(8, 6))
        # fig, ax = plt.subplots()

        rows, cols = len(self.grid), len(self.grid[0])
        fig_w, fig_h = cols * CELL_INCHES, rows * CELL_INCHES
        # Scale uniformly first, to preserve the grid's aspect ratio (avoids
        # letterboxing a non-square grid into a square figure, which would
        # otherwise waste most of the canvas as blank space around a sliver).
        longest = max(fig_w, fig_h)
        if longest < MIN_FIG_INCHES:
            fig_w, fig_h = fig_w * MIN_FIG_INCHES / longest, fig_h * MIN_FIG_INCHES / longest
        elif longest > MAX_FIG_INCHES:
            fig_w, fig_h = fig_w * MAX_FIG_INCHES / longest, fig_h * MAX_FIG_INCHES / longest
        # Only then floor each side independently, accepting minor aspect
        # distortion in extreme cases so a very flat/tall grid stays legible.
        fig_w, fig_h = max(fig_w, MIN_FIG_DIM_INCHES), max(fig_h, MIN_FIG_DIM_INCHES)
        self.fig, self.ax = plt.subplots(figsize=(fig_w, fig_h))
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
        boundary_color = {
            rf"${node}$": self.colors[(i - 1) % len(self.colors)]
            for i in range(1, self.k + 1)
            for node in (f"s_{i}", f"g_{i}")
        }
        node_colors = [
            boundary_color.get(
                node,
                (
                    COOPERATION_NODES_COLOR
                    if node_delay(self.G, node, 1) > node_delay(self.G, node, self.k)
                    else NODES_COLOR
                ),
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
        boundary_nodes = list(boundary_color.keys())
        nx.draw_networkx_nodes(
            self.G,
            self.pos,
            nodelist=boundary_nodes,
            ax=self.ax,
            node_size=NODE_SIZE,
            node_color=[boundary_color[n] for n in boundary_nodes],
            edgecolors="black",
            linewidths=1,
        )
        labels = {node: str(node) for node in boundary_nodes}
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

    def set_animation(self, joint_strategy):
        relabeled = relabel_joint_strategy(joint_strategy)
        self.strategies = relabeled
        self.states = interpolate_paths(self.G, relabeled)
        self.ani = animation.FuncAnimation(
            self.fig,
            self.update,
            interval=SPEED,
            frames=SPEED * max(len(s) for s in self.states.values()),
            blit=False,
            repeat=False,
        )
        self.robots = {}
        self.colored = {}
        for agent, strategy in relabeled.items():
            color = self.colors[(agent - 1) % len(self.colors)]
            circle = Circle(self.pos[strategy[0][0]], ROBOT_SIZE, color=color, zorder=10)
            self.ax.add_patch(circle)
            self.robots[agent] = circle
            self.colored[agent] = False

        self.commentry = self.ax.text(
            0,
            len(self.grid),
            "",
            fontsize=5,
            verticalalignment="bottom",
            horizontalalignment="left",
        )

    def update(self, num):
        n_agents = len(self.states)
        lines = [f"t={math.floor(num / SPEED)}"]
        for agent, states in self.states.items():
            state = states[min(math.floor(num / SPEED), len(states) - 1)]
            color = self.colors[(agent - 1) % len(self.colors)]

            if state[0] == "E" and not self.colored[agent]:
                self.colored[agent] = True
                gap = PATH_GAP * (agent - (n_agents + 1) / 2)
                self.draw_edge(state[1], color, gap)
            elif state[0] != "E":
                self.colored[agent] = False

            x, y = interpolate(state, (num % SPEED) / SPEED, self.pos)
            angle = 2 * math.pi * agent / max(n_agents, 1)
            x += ROBOT_OFFSET_RADIUS * math.cos(angle)
            y += ROBOT_OFFSET_RADIUS * math.sin(angle)
            self.robots[agent].center = (x, y)

            lines.append(rf"$r_{{{agent}}}$ {generate_text(state)}")

        self.commentry.set_text("\n".join(lines))
        return (self.commentry, *self.robots.values())

    def draw_edge(self, edge, color, path_gap):
        x = [self.pos[edge[0]][0] + path_gap, self.pos[edge[1]][0] + path_gap]
        y = [self.pos[edge[0]][1] + path_gap, self.pos[edge[1]][1] + path_gap]
        (line,) = self.ax.plot(x, y, color=color, linewidth=PATH_WIDTH)
        self.drawn_edges.append(line)
        return line

    def draw_path(self, strategy, color, path_gap=0):
        edges = get_edges_in_path(relabel_strategy(strategy))
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


def visualize(G, pos, joint_strategy, grid):
    vis = GraphVisualizer(G, pos, grid)
    vis.set_animation(joint_strategy)
    plt.show()
