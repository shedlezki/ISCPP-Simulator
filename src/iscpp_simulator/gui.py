import tkinter as tk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from . import simulation

social_evaluators = ["Social Sum"]


class GUI:
    def __init__(self, G, pos, grid, strategies, args, eid, bounds=None):
        self.root = tk.Tk()
        self.G = G
        self.k = getattr(args, "num_agents", None) or GUI._infer_k(strategies)
        self.vis = simulation.GraphVisualizer(G, pos, grid, k=self.k)
        self.strategies = strategies
        self.bounds = bounds or {}
        self.anim = None
        self.args = args
        self.eid = eid

    @staticmethod
    def _infer_k(strategies):
        return max((len(s) for s in strategies.values()), default=0)

    def copy_to_clipboard(self, event):
        text = self.eid
        self.root.clipboard_clear()
        self.root.clipboard_append(text)
        self.root.update()  # Keeps the clipboard content after the program exits

    def _format_agent_time(self, t):
        return "stuck" if t == float("inf") else str(t)

    def show(self):
        self.root.title("ICMPP Simulation GUI")
        self.canvas = FigureCanvasTkAgg(self.vis.fig, master=self.root)
        self.canvas.get_tk_widget().grid(row=0, column=0, columnspan=4)

        seperation = getattr(
            self.args, "seperation", getattr(self.args, "correlation", None)
        )
        label = tk.Label(
            text=(
                f"Map: {self.args.map} Density: {self.args.density} "
                f"Magnitude: {self.args.magnitude} Extent: {self.args.extent} "
                f"Seperation: {seperation} "
                f"Agents: {self.k} EID: {self.eid}"
            ),
            fg="black",
            cursor="hand2",
        )
        label.grid(row=1, column=0)
        label.bind("<Button-1>", lambda event: self.copy_to_clipboard(event))

        colors = simulation.get_agent_colors(self.k)

        if self.bounds:
            bounds_text = " | ".join(
                f"SP{i}: " + ", ".join(str(self.bounds[i][m]) for m in sorted(self.bounds[i]))
                for i in sorted(self.bounds)
            )
            bounds_label = tk.Label(
                text=f"Optimistic SP(1..k) lower bounds per agent - {bounds_text}",
                fg="gray",
            )
            bounds_label.grid(row=2, column=0, sticky="w")

        def on_check(var, joint_strategy, i, color):
            if var.get():
                if i not in drawn_paths:
                    drawn_paths[i] = []
                for agent, strategy in joint_strategy.items():
                    drawn_paths[i].extend(
                        self.vis.draw_path(strategy, color, i * 0.02)
                    )
            else:
                self.vis.clear_path(drawn_paths[i])
                drawn_paths[i].clear()
            self.canvas.draw()

        check_states = {p: tk.BooleanVar() for p in range(len(self.strategies))}
        drawn_paths = {}

        def play_animation(joint_strategy):
            self.vis.set_animation(joint_strategy)
            self.anim = self.vis.ani
            self.canvas.draw()

        for i, name in enumerate(self.strategies.keys()):
            var = check_states[i]
            joint_strategy = self.strategies[name]
            times = simulation.evaluate_paths(self.G, joint_strategy)
            times_text = ", ".join(
                self._format_agent_time(times[agent]) for agent in sorted(times)
            )
            color = colors[i % len(colors)]
            cb = tk.Checkbutton(
                self.root,
                text=f"{name} ({times_text})",
                variable=var,
                fg=color,
                command=lambda v=var, s=joint_strategy, index=i, c=color: on_check(
                    v, s, index, c
                ),
            )
            cb.grid(row=3 + i, column=0, sticky="w")
            play_button = tk.Button(
                self.root,
                text="Play",
                command=lambda s=joint_strategy: play_animation(s),
            )
            play_button.grid(row=3 + i, column=1, pady=10)

        self.root.mainloop()
