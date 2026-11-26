from math import pi, sin, cos
import numpy as np
from pde_modelling.helpers import FOURIER_FIELD, askField, pickTimeUnit, printBanner, printTypical, warnAndConfirm
from pde_modelling.plotting import showInTerminal


# 1D wave equation on a string: d2u/dt2 = c^2 * d2u/dx2
# both ends tied down, u(0,t) = u(L,t) = 0
# the string gets pulled up at one point into a triangle and let go from rest, so g(x) = 0
# same setup as the asymmetric plucked string example in PDE 7


NAME = "1D Wave Equation - Plucked String"
EQUATION = "∂²u/∂t² = c² ∂²u/∂x²"
SETUP = [
    "String of length L, plucked into a triangle at x = p",
    "Let go from rest, both ends tied down",
    "Solved with a Fourier sine series",
]
VIEWS = ["Step through", "Animate"]

FIELDS = {
    "length": {
        "label": "String length",
        "unit": "m",
        "default": 0.65,
        "low": 0,
        "typical": (0.1, 5),
        "warning": "The maths still works, it just isn't much like a real string anymore.",
    },
    # c = sqrt(T / rho) so it comes from tension and mass per length,
    # anything way outside this would need a string that snaps or weighs nothing
    "c": {
        "label": "Wave speed c",
        "unit": "m/s",
        "default": 300,
        "low": 0,
        "typical": (10, 1000),
        "warning": "Real strings sit in this range. Way outside it the string would either "
                   "snap from the tension or be floppy enough to just sag.",
    },
    "height": {
        "label": "Pluck height",
        "unit": "m",
        "default": 0.003,
        "notZero": True,
        "hint": "keep it small, a few mm on a guitar",
    },
    # the top limit is the string length, that gets passed in separately since it isn't fixed
    "pluckPos": {
        "label": "Pluck point",
        "unit": "m",
        "default": 0.2,
        "low": 0,
        "hint": "somewhere between 0 and the length",
    },
    "upper": FOURIER_FIELD,
}


def fourierConstant(n, length, pluckPos, height):
    # An for the triangle shape. you get it the same way as the PDE 7 example,
    # integrate each straight bit of the triangle by parts and add the two together
    # the Bn (velocity) ones are all 0 because it starts at rest
    An = (2 * height * length ** 2) / (n ** 2 * pi ** 2 * pluckPos * (length - pluckPos)) * sin((n * pi * pluckPos) / length)

    return An


def slopeWarning(length, height, pluckPos):
    # the wave equation from PDE 5 assumes small displacement and small slope (sin(theta) ~ theta)
    # the steepest part of the triangle is whichever side is shorter, so check that slope
    # if it's too steep the real string wouldn't move like this graph shows
    slope = max(abs(height) / pluckPos, abs(height) / (length - pluckPos))

    if slope <= 0.1:
        return ""

    return (f"The steepest bit of the string has a slope of {slope:.2f}. "
            "The wave equation assumes small slopes (sin(theta) ~ theta, under about 0.1), "
            "past that a real string wouldn't move like the graph shows. "
            "Pulling it up less or plucking nearer the middle fixes it.")


def checkTogether(values):
    # checks that need more than one value at once
    # gives back (problems, warnings)
    if values["pluckPos"] >= values["length"]:
        # pluck point has to be strictly inside the string or An divides by 0
        return [f"Pluck point has to be less than the string length ({values['length']:g} m)"], []

    warning = slopeWarning(values["length"], values["height"], values["pluckPos"])
    if warning != "":
        return [], [warning]

    return [], []


def solve(length, c, height, pluckPos, upper, progress=None):
    # does all the maths and hands back a result dict for plotting.py to draw
    # progress gets called with how far through it is (0 to 1) so the GUI can move its bar
    points = 101
    frames = 101
    Xaxis = np.linspace(0, length, points)

    # nothing dies off here like the heat one, it just keeps going forever
    # after L/c (half a period) the string has flipped to the mirror image of how it started,
    # then it does the exact same thing back, so half a period is all that needs working out
    tMax = length / c
    unit, scale = pickTimeUnit(tMax)

    value = 0
    # abs so pulling the string down instead of up still works
    deltaThresh = abs(height) / 10
    kept = []  # which times get their own line in the step through view
    labels = []

    u = np.zeros((points, frames))

    for i in range(0, frames):
        t = (tMax / (frames - 1)) * i
        labels.append(f"t = {t * scale:.3g} {unit}")

        for j in range(0, points):  # keep t the same, go along the string
            x = Xaxis[j]

            for n in range(1, upper + 1):  # sum of sines per x, even n can matter here
                value += fourierConstant(n, length, pluckPos, height) * sin((n * pi * x) / length) * cos((n * pi * c * t) / length)

            u[j, i] = value
            value = 0

        # same filter as the heat one, only keep it if the string has moved enough
        if i == 0:
            kept.append(i)
        else:
            change = []
            for j in range(0, points):
                change.append(abs(u[j, kept[-1]] - u[j, i]))

            if sum(change) / len(change) >= deltaThresh:
                kept.append(i)

        if progress is not None:
            progress((i + 1) / frames)

    # a full vibration is there and back, so 2L/c, and the note it plays is 1 over that
    return {
        "lineX": Xaxis,
        "lineData": u,
        "labels": labels,
        "kept": kept,
        "xlabel": "Position x (m)",
        "ylabel": "Displacement u(x,t) (m)",
        "title": "Wave Equation Solution",
        "ylim": (-1.2 * abs(height), 1.2 * abs(height)),
        "colours": "viridis",
        "zeroLine": True,
        # the second half of a vibration is the first half played backwards, so the animation
        # just bounces back and forth through the half it already has and it's still exactly right
        "loop": "bounce",
        "timeStep": tMax / (frames - 1),
        "unit": unit,
        "scale": scale,
        "info": f"One full vibration takes {2 * tMax * scale:.3g} {unit}, so it plays a note at about {c / (2 * length):.3g} Hz",
    }


def run():
    # terminal version
    printBanner(NAME, SETUP)
    printTypical(FIELDS)

    # everything gets checked as it's typed in, see helpers.py
    length = askField(FIELDS["length"])
    c = askField(FIELDS["c"])

    while True:
        height = askField(FIELDS["height"])
        pluckPos = askField(FIELDS["pluckPos"], high=length)

        warning = slopeWarning(length, height, pluckPos)
        if warning == "" or warnAndConfirm(warning):
            break

    upper = askField(FIELDS["upper"])

    print()
    print("  Computing solution...")
    print()

    result = solve(length, c, height, pluckPos, upper)

    print("  " + result["info"])
    print("  Done! Displaying graph...")
    print()

    showInTerminal(result)


if __name__ == "__main__":
    run()
