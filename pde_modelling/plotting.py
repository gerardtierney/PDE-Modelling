import matplotlib
import matplotlib.pyplot as plt
import numpy as np


# graph drawing shared by the GUI and the terminal
#
# every solver hands back a "result" dict with the same keys, so one set of drawing code works for all three:
#   lineX     what goes along the bottom of the line graph
#   lineData  2D array, each column is one line you could draw
#   labels    a label for each column
#   kept      which columns get drawn in the step through view
#   xlabel, ylabel, title, ylim, colours (a colormap name), zeroLine (draw y = 0 or not)
#   surface   optional (X, Y, Z) for the 3D view
#   loop      optional, "bounce" or "restart", how the animation repeats


def lineColours(result, count):
    # the lines go in order (hot to cold, or across the membrane) so they get colours from a gradient
    # before it used the default colours which only has 10, so line 11 came out the same as line 1
    # 0.1 to 0.85 skips the very ends of the colormap, the light end is hard to see on white
    cmap = matplotlib.colormaps[result["colours"]]

    return cmap(np.linspace(0.1, 0.85, max(count, 1)))


def makeRoom(fig, legend):
    # fixed margins so the graph doesn't jump about as the legend grows line by line
    if legend:
        fig.subplots_adjust(left=0.11, right=0.83, top=0.9, bottom=0.11)
    else:
        fig.subplots_adjust(left=0.11, right=0.96, top=0.9, bottom=0.11)


def styleAxes(ax, result):
    ax.set_xlabel(result["xlabel"], fontsize=12)
    ax.set_ylabel(result["ylabel"], fontsize=12)
    ax.set_title(result["title"], fontsize=14, fontweight="bold", pad=15)
    ax.grid(True, linestyle="--", alpha=0.3)

    # lock both axes so nothing rescales while lines are being added
    ax.set_xlim(result["lineX"][0], result["lineX"][-1])
    ax.set_ylim(result["ylim"][0], result["ylim"][1])

    if result["zeroLine"]:
        ax.axhline(0, color="black", linewidth=0.8)


def addLegend(ax):
    # sits just outside the right of the graph so it never covers a line
    ax.legend(fontsize=9, framealpha=0.8, loc="upper left", bbox_to_anchor=(1.01, 1))


def drawSurface(ax, result):
    X, Y, Z = result["surface"]

    surface = ax.plot_surface(X, Y, Z, cmap="viridis", edgecolor="none")
    ax.figure.colorbar(surface, ax=ax, shrink=0.6, pad=0.1, label=result["ylabel"])

    ax.set_xlabel("x (m)", fontsize=11)
    ax.set_ylabel("y (m)", fontsize=11)
    ax.set_zlabel(result["ylabel"], fontsize=11)
    ax.set_title("Membrane Shape", fontsize=14, fontweight="bold", pad=15)


def showInTerminal(result):
    # what the terminal version uses, same as the old way where each line pops on one at a time
    fig = plt.figure(figsize=(12, 6))
    makeRoom(fig, legend=True)
    ax = fig.add_subplot()
    styleAxes(ax, result)

    colours = lineColours(result, len(result["kept"]))

    for k in range(len(result["kept"])):
        column = result["kept"][k]
        ax.plot(result["lineX"], result["lineData"][:, column], label=result["labels"][column],
                color=colours[k], linewidth=2)
        addLegend(ax)
        plt.pause(0.6)

    if "surface" in result:
        fig3d = plt.figure(figsize=(11, 7))
        ax3d = fig3d.add_subplot(projection="3d")
        drawSurface(ax3d, result)

    plt.show()
