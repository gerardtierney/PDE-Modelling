import tkinter as tk
from tkinter import ttk, messagebox
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk

from pde_modelling import heat, wave, laplace
from pde_modelling.helpers import readNumber, checkLimits, hintText
from pde_modelling.plotting import lineColours, makeRoom, styleAxes, addLegend, drawSurface


# the window version. inputs down the left, graph on the right
# all the maths is still in heat.py, wave.py and laplace.py, this just collects the inputs,
# calls their solve() and draws whatever comes back


MODELS = {"Heat": heat, "Wave": wave, "Laplace": laplace}

GREY = "#666666"
ORANGE = "#b35900"
RED = "#c0392b"
DARK = "#222222"

STEP_DELAY = 500  # ms between lines popping on in the step through view
FRAME_DELAY = 30  # ms between frames in the animation


class App:

    def __init__(self, root):
        self.root = root
        self.model = heat
        self.result = None
        self.job = None  # the next drawing step that's been scheduled, so it can be cancelled
        self.busy = False  # True while the sums are being worked out
        self.boxes = {}  # for each input: (the text in its box, the hint label under it)
        self.presetName = None

        root.title("PDE Modelling")
        root.geometry("1280x740")
        root.minsize(1050, 620)

        style = ttk.Style()
        style.configure("Title.TLabel", font=("Segoe UI", 18, "bold"))
        style.configure("Heading.TLabel", font=("Segoe UI", 11, "bold"))
        style.configure("Equation.TLabel", font=("Cambria Math", 15))
        style.configure("Small.TLabel", font=("Segoe UI", 9))
        style.configure("Solve.TButton", font=("Segoe UI", 11, "bold"), padding=8)

        # ---------------- left side, the inputs ----------------

        side = ttk.Frame(root, padding=(18, 14))
        side.pack(side="left", fill="y")
        ttk.Separator(root, orient="vertical").pack(side="left", fill="y")

        ttk.Label(side, text="PDE Modelling", style="Title.TLabel").pack(anchor="w")
        ttk.Label(side, text="Fourier series solutions from MA2102", style="Small.TLabel",
                  foreground=GREY).pack(anchor="w", pady=(0, 12))

        # one button per equation, only one can be pressed at a time
        self.modeName = tk.StringVar(value="Heat")
        modeRow = ttk.Frame(side)
        modeRow.pack(fill="x", pady=(0, 12))

        for name in MODELS:
            ttk.Radiobutton(modeRow, text=name, value=name, variable=self.modeName, style="Toolbutton",
                            command=self.changeModel).pack(side="left", expand=True, fill="x", padx=1)

        self.equation = ttk.Label(side, style="Equation.TLabel")
        self.equation.pack(anchor="w")
        self.setup = ttk.Label(side, style="Small.TLabel", foreground=GREY, justify="left")
        self.setup.pack(anchor="w", pady=(4, 12))

        ttk.Label(side, text="Inputs", style="Heading.TLabel").pack(anchor="w")
        self.form = ttk.Frame(side)
        self.form.pack(fill="x", pady=(2, 14))

        viewRow = ttk.Frame(side)
        viewRow.pack(fill="x", pady=(0, 10))
        ttk.Label(viewRow, text="Graph", style="Heading.TLabel").pack(side="left")
        self.viewName = tk.StringVar()
        self.viewBox = ttk.Combobox(viewRow, textvariable=self.viewName, state="readonly", width=14)
        self.viewBox.pack(side="right")
        self.viewBox.bind("<<ComboboxSelected>>", lambda event: self.draw())

        buttonRow = ttk.Frame(side)
        buttonRow.pack(fill="x")
        self.solveButton = ttk.Button(buttonRow, text="Solve", style="Solve.TButton", command=self.solve)
        self.solveButton.pack(side="left", expand=True, fill="x")
        self.replayButton = ttk.Button(buttonRow, text="Replay", command=self.draw, state="disabled")
        self.replayButton.pack(side="left", padx=(6, 0), ipady=5)

        self.progress = ttk.Progressbar(side, maximum=1.0)
        self.progress.pack(fill="x", pady=(10, 6))

        self.status = ttk.Label(side, wraplength=300, justify="left")
        self.status.pack(anchor="w", fill="x")

        # ---------------- right side, the graph ----------------

        graphArea = ttk.Frame(root, padding=6)
        graphArea.pack(side="left", fill="both", expand=True)

        # matplotlib draws into this instead of opening its own window
        # the toolbar underneath has zoom, pan and a save button for the graph
        self.figure = Figure(figsize=(9, 6), dpi=100)
        self.canvas = FigureCanvasTkAgg(self.figure, master=graphArea)
        toolbar = NavigationToolbar2Tk(self.canvas, graphArea, pack_toolbar=False)
        toolbar.update()
        toolbar.pack(side="bottom", fill="x")
        self.canvas.get_tk_widget().pack(side="top", fill="both", expand=True)

        root.bind("<Return>", lambda event: self.solve())
        root.protocol("WM_DELETE_WINDOW", self.close)

        self.changeModel()

    # ---------------- switching equation ----------------

    def changeModel(self):
        if self.busy:
            # can't swap halfway through a solve, put the button back how it was
            for name in MODELS:
                if MODELS[name] == self.model:
                    self.modeName.set(name)
            return

        self.stopDrawing()
        self.model = MODELS[self.modeName.get()]
        self.result = None

        self.equation.configure(text=self.model.EQUATION)

        setupText = ""
        for line in self.model.SETUP:
            setupText += "•  " + line + "\n"
        self.setup.configure(text=setupText.strip())

        self.buildForm()

        self.viewBox.configure(values=self.model.VIEWS)
        self.viewName.set(self.model.VIEWS[0])
        self.replayButton.configure(state="disabled")
        self.progress.configure(value=0)
        self.setStatus("Check the inputs and hit Solve (or press Enter)", GREY)
        self.showPlaceholder()

    def buildForm(self):
        # clears out the old boxes and makes one row per input from the model's FIELDS
        for widget in self.form.winfo_children():
            widget.destroy()

        self.boxes = {}
        self.presetName = None
        row = 0

        for name, field in self.model.FIELDS.items():

            # if there's a list of presets (the materials for the heat one) put a dropdown above the box
            if "presets" in field:
                choices = list(field["presets"]) + ["Custom"]
                self.presetName = tk.StringVar(value=choices[0])

                ttk.Label(self.form, text="Material").grid(row=row, column=0, sticky="w", pady=(8, 0), padx=(0, 10))
                presetBox = ttk.Combobox(self.form, textvariable=self.presetName, values=choices,
                                         state="readonly", width=13)
                presetBox.grid(row=row, column=1, sticky="ew", pady=(8, 0))
                presetBox.bind("<<ComboboxSelected>>", lambda event, n=name: self.usePreset(n))
                row += 1

            text = tk.StringVar(value=f"{field['default']:g}")

            ttk.Label(self.form, text=field["label"]).grid(row=row, column=0, sticky="w", pady=(8, 0), padx=(0, 10))
            ttk.Entry(self.form, textvariable=text, width=15).grid(row=row, column=1, sticky="ew", pady=(8, 0))
            ttk.Label(self.form, text=field["unit"], foreground=GREY).grid(row=row, column=2, sticky="w",
                                                                           pady=(8, 0), padx=(6, 0))

            hint = ttk.Label(self.form, text=hintText(field), style="Small.TLabel", foreground=GREY,
                             wraplength=300, justify="left")
            hint.grid(row=row + 1, column=0, columnspan=3, sticky="w")

            self.boxes[name] = (text, hint)

            # re-check the box every time something is typed in it
            text.trace_add("write", lambda *args, n=name: self.checkBox(n))
            row += 2

    def usePreset(self, name):
        material = self.presetName.get()
        presets = self.model.FIELDS[name]["presets"]

        if material in presets:
            self.boxes[name][0].set(f"{presets[material]:g}")

    # ---------------- checking inputs ----------------

    def checkBox(self, name):
        # same checks as the terminal, but the hint under the box changes colour as you type
        # grey is fine, orange is allowed but unrealistic, red won't run
        field = self.model.FIELDS[name]
        text, hint = self.boxes[name]

        value, problem = readNumber(text.get(), field.get("whole", False))
        headsUp = ""

        if problem == "":
            problem, headsUp = checkLimits(value, field)

        if problem != "":
            hint.configure(text=problem, foreground=RED)
        elif headsUp != "":
            hint.configure(text=f"Unusual value ({hintText(field)})", foreground=ORANGE)
        else:
            hint.configure(text=hintText(field), foreground=GREY)

        # typing your own value into the diffusivity box flips the material dropdown to Custom
        if "presets" in field and self.presetName is not None:
            match = "Custom"
            for material in field["presets"]:
                if value == field["presets"][material]:
                    match = material
            self.presetName.set(match)

        return value, problem, headsUp

    # ---------------- solving ----------------

    def solve(self):
        if self.busy:
            return

        values = {}
        problems = []
        headsUps = []

        for name in self.model.FIELDS:
            value, problem, headsUp = self.checkBox(name)

            if problem != "":
                problems.append(f"{self.model.FIELDS[name]['label']}: {problem}")
            elif headsUp != "":
                headsUps.append(headsUp)

            values[name] = value

        # the checks that need two values at once (pluck point vs length, slopes, membrane shape)
        # only make sense once every box on its own is fine
        if problems == []:
            together, warnings = self.model.checkTogether(values)
            problems += together
            headsUps += warnings

        if problems != []:
            messagebox.showerror("Can't solve that yet", "\n".join(problems), parent=self.root)
            return

        if headsUps != []:
            message = "\n\n".join(headsUps) + "\n\nRun it anyway?"
            if not messagebox.askyesno("Heads up", message, icon="warning", parent=self.root):
                return

        self.stopDrawing()
        self.busy = True
        self.solveButton.configure(state="disabled")
        self.replayButton.configure(state="disabled")
        self.setStatus("Adding up the Fourier series...", GREY)

        try:
            # **values passes each input in by name, so values["length"] goes in as length=...
            result = self.model.solve(**values, progress=self.showProgress)
        except tk.TclError:
            # the window got closed halfway through, nothing left to draw on
            return

        self.busy = False
        self.result = result
        self.solveButton.configure(state="normal")
        self.replayButton.configure(state="normal")
        self.setStatus(result["info"], DARK)

        self.draw()

    def showProgress(self, fraction):
        # update() lets the window redraw while the sums run, otherwise it freezes and says Not Responding
        self.progress.configure(value=fraction)
        self.root.update()

    def setStatus(self, text, colour):
        self.status.configure(text=text, foreground=colour)

    # ---------------- drawing ----------------

    def showPlaceholder(self):
        self.figure.clear()
        ax = self.figure.add_subplot()
        ax.axis("off")
        ax.text(0.5, 0.5, "Pick an equation, check the inputs and hit Solve",
                ha="center", va="center", fontsize=13, color=GREY)
        self.canvas.draw_idle()

    def stopDrawing(self):
        if self.job is not None:
            self.root.after_cancel(self.job)
            self.job = None

    def draw(self):
        if self.result is None or self.busy:
            return

        self.stopDrawing()
        self.figure.clear()
        view = self.viewName.get()

        if view == "3D surface":
            makeRoom(self.figure, legend=False)
            ax = self.figure.add_subplot(projection="3d")
            drawSurface(ax, self.result)
            self.canvas.draw_idle()
            return

        ax = self.figure.add_subplot()

        if view == "Animate":
            makeRoom(self.figure, legend=False)
            styleAxes(ax, self.result)

            frames = self.result["lineData"].shape[1]
            self.colours = lineColours(self.result, frames)
            self.line, = ax.plot(self.result["lineX"], self.result["lineData"][:, 0], color=self.colours[0], linewidth=2.5)
            self.clock = ax.text(0.02, 0.95, "", transform=ax.transAxes, fontsize=12, va="top",
                                 bbox=dict(boxstyle="round", facecolor="white", edgecolor="#cccccc", alpha=0.9))
            self.animate(0)
        else:
            # step through (or slices for the membrane), lines pop on one at a time like the original
            makeRoom(self.figure, legend=True)
            styleAxes(ax, self.result)
            self.colours = lineColours(self.result, len(self.result["kept"]))
            self.stepThrough(ax, 0)

    def stepThrough(self, ax, k):
        kept = self.result["kept"]

        if k >= len(kept):
            self.job = None
            return

        column = kept[k]
        ax.plot(self.result["lineX"], self.result["lineData"][:, column], label=self.result["labels"][column],
                color=self.colours[k], linewidth=2)
        addLegend(ax)
        self.canvas.draw_idle()

        # instead of plt.pause, ask tkinter to call this again in a bit with the next line
        self.job = self.root.after(STEP_DELAY, self.stepThrough, ax, k + 1)

    def animate(self, step):
        # one line, moved to the next time every frame, keeps looping until something else gets drawn
        frames = self.result["lineData"].shape[1]

        if self.result["loop"] == "bounce":
            # goes 0 up to the last frame then back down to 0 and so on
            i = step % (2 * (frames - 1))
            if i > frames - 1:
                i = 2 * (frames - 1) - i

            # the clock keeps counting up even when the frames go backwards, because time doesn't
            t = step * self.result["timeStep"]
            self.clock.set_text(f"t = {t * self.result['scale']:.3g} {self.result['unit']}")
        else:
            # hang on the last frame for a bit before starting again
            i = step % (frames + 25)
            if i > frames - 1:
                i = frames - 1

            self.clock.set_text(self.result["labels"][i])
            # changes colour as it goes, so the rod goes from orange to purple as it cools
            self.line.set_color(self.colours[i])

        self.line.set_ydata(self.result["lineData"][:, i])
        self.canvas.draw_idle()

        self.job = self.root.after(FRAME_DELAY, self.animate, step + 1)

    def close(self):
        self.stopDrawing()
        self.root.destroy()


def main():
    # stops the window looking blurry on Windows laptops with display scaling turned up
    try:
        from ctypes import windll
        windll.shcore.SetProcessDpiAwareness(1)
    except (ImportError, AttributeError, OSError):
        pass

    root = tk.Tk()
    App(root)
    root.mainloop()


if __name__ == "__main__":
    main()
