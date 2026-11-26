from math import pi, sin, e
import numpy as np
from pde_modelling.helpers import FOURIER_FIELD, askField, printBanner, printTypical, warnAndConfirm
from pde_modelling.plotting import showInTerminal


# Laplace equation on a rectangular membrane: d2u/dx2 + d2u/dy2 = 0
# membrane stretched over a frame, a wide (x) and b tall (y)
# left, bottom and top edges are flat at 0
# the right edge x = a gets pushed up into a triangle with its peak halfway up at y = b/2
# same setup as the membrane example in PDE 8 and 9
# no time in this one, it's just the shape the membrane settles into


NAME = "Laplace Equation - Rectangular Membrane"
EQUATION = "∂²u/∂x² + ∂²u/∂y² = 0"
SETUP = [
    "Membrane a wide (x) by b tall (y) on a frame",
    "Edges x = 0, y = 0 and y = b flat at 0",
    "Edge x = a raised into a triangle, peak at y = b/2",
]
VIEWS = ["Slices", "3D surface"]

FIELDS = {
    "a": {
        "label": "Width a",
        "unit": "m",
        "default": 1,
        "low": 0,
        "typical": (0.1, 10),
        "warning": "The maths is fine, it's just a strange size for a membrane.",
    },
    "b": {
        "label": "Height b",
        "unit": "m",
        "default": 1,
        "low": 0,
        "typical": (0.1, 10),
        "warning": "The maths is fine, it's just a strange size for a membrane.",
    },
    "height": {
        "label": "Peak height",
        "unit": "m",
        "default": 0.04,
        "notZero": True,
        "hint": "keep it small, under about b/20",
    },
    "upper": FOURIER_FIELD,
}


def fourierConstant(n, height):
    # Cn for the triangle edge, from the PDE 9 example but with a peak of any height
    # sin(n pi / 2) is 0 for every even n so those drop out
    Cn = (8 * height) / (n ** 2 * pi ** 2) * sin((n * pi) / 2)

    return Cn


def sinhRatio(k, x, a):
    # this is sinh(kx) / sinh(ka) written out with exponentials
    # doing the two sinh's straight up breaks once n gets past about 200
    # because sinh(710) is too big to fit in a float
    # taking e^(k(x-a)) out the front keeps everything between 0 and 1 so it never blows up
    return e ** (k * (x - a)) * (1 - e ** (-2 * k * x)) / (1 - e ** (-2 * k * a))


def shapeWarning(a, b):
    # the bump from the raised edge dies off over a distance of about b,
    # so if a is way bigger than b almost the whole membrane is flat and the graph shows nothing
    if a / b <= 10 and b / a <= 10:
        return ""

    return (f"The membrane is {max(a / b, b / a):.3g} times longer one way than the other. "
            "The raised edge only lifts the membrane for about a distance b in from the edge, "
            "so if a is much bigger than b nearly all of it is flat, and if b is much bigger the "
            "51 points across won't pick up the shape properly.")


def slopeWarning(height, b):
    # same small slope idea as the wave one, the membrane equation in PDE 8 uses sin(theta) ~ theta
    # the raised edge climbs from 0 to the peak over b/2, so its slope is about 2h/b
    slope = 2 * abs(height) / b

    if slope <= 0.1:
        return ""

    return (f"The raised edge has a slope of {slope:.2f}. "
            "The Laplace equation for a membrane assumes small slopes (under about 0.1), "
            "past that a real membrane wouldn't sit in this shape. A smaller peak fixes it.")


def checkTogether(values):
    # checks that need more than one value at once
    # gives back (problems, warnings)
    warnings = []

    for warning in (shapeWarning(values["a"], values["b"]), slopeWarning(values["height"], values["b"])):
        if warning != "":
            warnings.append(warning)

    return [], warnings


def solve(a, b, height, upper, progress=None):
    # does all the maths and hands back a result dict for plotting.py to draw
    # progress gets called with how far through it is (0 to 1) so the GUI can move its bar
    points = 51
    Xaxis = np.linspace(0, a, points)
    Yaxis = np.linspace(0, b, points)

    value = 0

    # rows are y, columns are x, that's the way round plot_surface wants it later
    # it also means each column is a slice going up the membrane at one x, which is what the line graph draws
    u = np.zeros((points, points))

    for i in range(0, points):
        y = Yaxis[i]
        for j in range(0, points):
            x = Xaxis[j]

            for n in range(1, upper + 1, 2):  # sum of sines per point, odd n only
                k = (n * pi) / b
                value += fourierConstant(n, height) * sin(k * y) * sinhRatio(k, x, a)

            u[i, j] = value
            value = 0

        if progress is not None:
            progress((i + 1) / points)

    labels = []
    for x in Xaxis:
        labels.append(f"x = {x:.3g} m")

    # works out the limits either way round so a peak pushed down instead of up still fits
    pad = 0.1 * abs(height)
    X, Y = np.meshgrid(Xaxis, Yaxis)

    # the line graph works like the heat and wave ones, except instead of stepping through time
    # it steps across the membrane in x. each line is a slice going up the membrane in y
    # and they grow from flat at x = 0 to the full triangle at x = a
    return {
        "lineX": Yaxis,
        "lineData": u,
        "labels": labels,
        "kept": list(np.linspace(0, points - 1, 8).astype(int)),
        "xlabel": "Position y (m)",
        "ylabel": "Displacement u(x,y) (m)",
        "title": "Laplace Equation Solution - Slices Across x",
        "ylim": (min(0, height) - pad, max(0, height) + pad),
        "colours": "viridis",
        "zeroLine": False,
        "surface": (X, Y, u),
        "info": f"The middle of the membrane sits at {u[points // 2, points // 2]:.3g} m, "
                f"compared to {height:g} m at the peak of the raised edge",
    }


def run():
    # terminal version
    printBanner(NAME, SETUP)
    printTypical(FIELDS)

    # everything gets checked as it's typed in, see helpers.py
    while True:
        a = askField(FIELDS["a"])
        b = askField(FIELDS["b"])

        warning = shapeWarning(a, b)
        if warning == "" or warnAndConfirm(warning):
            break

    while True:
        height = askField(FIELDS["height"])

        warning = slopeWarning(height, b)
        if warning == "" or warnAndConfirm(warning):
            break

    upper = askField(FIELDS["upper"])

    print()
    print("  Computing solution...")
    print()

    result = solve(a, b, height, upper)

    print("  " + result["info"])
    print("  Done! Displaying graphs...")
    print()

    showInTerminal(result)


if __name__ == "__main__":
    run()
