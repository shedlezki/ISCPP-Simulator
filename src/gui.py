import tkinter as tk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import simulation

social_evaluators = ["Social Sum"]


class GUI:
    def __init__(self, G, pos, grid, paths, args, eid):
        self.root = tk.Tk()
        self.vis = simulation.GraphVisualizer(G, pos, grid)
        self.paths = paths
        self.anim = None
        self.args = args
        self.eid = eid

    def copy_to_clipboard(self, event):
        text = self.eid
        self.root.clipboard_clear()
        self.root.clipboard_append(text)
        self.root.update()  # Keeps the clipboard content after the program exits

    def show(self):
        self.root.title("ICMPP Simulation GUI")
        self.canvas = FigureCanvasTkAgg(self.vis.fig, master=self.root)
        self.canvas.get_tk_widget().grid(row=0, column=0, columnspan=4)

        label = tk.Label(
            text=(
                f"Map: {self.args.map} Density: {self.args.density} "
                f"Magnitude: {self.args.magnitude} Extent: {self.args.extent} "
                f"Seperation: {self.args.seperation} EID: {self.eid}"
            ),
            fg="black",
            cursor="hand2",
        )
        label.grid(row=1, column=0)
        label.bind("<Button-1>", lambda event: self.copy_to_clipboard(event))

        colors = [
            "#FFB84C",
            "#F266AB",
            "#A459D1",
            "#2CD3E1",
            "#0079FF",
            "#00DFA2",
            "#F6FA70",
            "#FF0060",
        ]

        def on_check(var, p1, p2, i, color):
            if var.get():
                if i not in drawn_paths.keys():
                    drawn_paths[i] = []
                drawn_paths[i].extend(self.vis.draw_path(p1["path"], color, i * 0.02))
                drawn_paths[i].extend(self.vis.draw_path(p2["path"], color, i * 0.02))
            else:
                self.vis.clear_path(
                    drawn_paths[i]
                )  # optional: remove path if unchecked
                drawn_paths[i].clear()
            self.canvas.draw()

        check_states = {p: tk.BooleanVar() for p in range(len(self.paths))}
        drawn_paths = {}

        def play_animation(p1, p2):
            self.vis.set_animation(p1, p2)
            self.anim = self.vis.ani
            self.canvas.draw()

        for i, p in enumerate(self.paths.keys()):
            var = check_states[i]
            cb = tk.Checkbutton(
                self.root,
                text=f"path {p} ({self.paths[p][0]['length']},{self.paths[p][1]['length']})",
                variable=var,
                fg=colors[i],
                command=lambda v=var, p1=self.paths[p][0], p2=self.paths[p][
                    1
                ], index=i: on_check(v, p1, p2, index, colors[index]),
            )
            cb.grid(row=1 + 1 + i, column=0, sticky="w")
            play_button = tk.Button(
                self.root,
                text="Play",
                command=lambda p1=self.paths[p][0], p2=self.paths[p][1]: play_animation(
                    p1, p2
                ),
            )
            play_button.grid(row=1 + i + 1, column=0, pady=10)

        self.root.mainloop()
