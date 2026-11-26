from math import pi, sin, e, log
import numpy as np
from pde_modelling.helpers import FOURIER_FIELD, askField, pickTimeUnit, printBanner, printTypical
from pde_modelling.plotting import showInTerminal


# 1D heat equation on a rod: du/dt = alpha^2 * d2u/dx2
# both ends held at 0 the whole time, u(0,t) = u(L,t) = 0
# the rod starts at one uniform temperature everywhere
# solved with the Fourier sine series from MA2102


NAME = "1D Heat Equation - Finite Rod"
EQUATION = "∂u/∂t = α² ∂²u/∂x²"
SETUP = [
    "Rod of length L, starts at one uniform temperature",
    "Both ends held at 0 °C, u(0,t) = u(L,t) = 0",
    "Solved with a Fourier sine series",
]
VIEWS = ["Step through", "Animate"]

# alpha² for some common stuff in m²/s, the GUI has a dropdown of these and the terminal lists them
MATERIALS = {
    "Copper": 1.11e-4,
    "Aluminium": 9.7e-5,
    "Steel": 1.2e-5,
    "Glass": 3.4e-7,
    "Water": 1.4e-7,
    "Wood": 1e-7,
}

FIELDS = {
    "length": {
        "label": "Rod length",
        "unit": "m",
        "default": 0.5,
        "low": 0,
        "typical": (0.01, 10),
        "warning": "Fine for the maths, but a really long rod can take days or years to cool, "
                   "and a really short one cools in a blink.",
    },
    # the ends are held at 0 °C so u is the actual temperature, and that can't go under absolute zero
    "initial": {
        "label": "Starting temperature",
        "unit": "°C",
        "default": 100,
        "low": -273.15,
        "notZero": True,
        "typical": (-50, 1500),
        "warning": "Most metals have melted by about 1500 °C, and the model assumes alpha² "
                   "stays the same at every temperature which stops being true at the extremes.",
    },
    # people tend to type 1 or 111 here forgetting the e-4, which makes it cool insanely fast
    "alphaSqr": {
        "label": "Diffusivity α²",
        "unit": "m²/s",
        "default": MATERIALS["Copper"],
        "low": 0,
        "typical": (1e-8, 2e-3),
        "warning": "Nothing real is outside this (even diamond is about 1e-3). "
                   "If you meant copper it's 0.000111, not 111 or 1.",
        "presets": MATERIALS,
    },
    "upper": FOURIER_FIELD,
}


def fourierConstant(n, initial):
    # Bn for a uniform starting temperature
    # the even ones all come out as 0, so the sum below only goes through odd n
    Bn = (4 * initial) / (n * pi)

    return Bn


def time_to_near_zero(length, alphaSqr, epsilon=0.01):
    # n = 1 is the slowest term to die off, so once e^(-alpha^2 pi^2 t / L^2) gets down
    # to epsilon the rod is basically cold. this is that rearranged for t
    return (length ** 2 / (alphaSqr * pi ** 2)) * log(1 / epsilon)


def checkTogether(values):
    # checks that need more than one value at once, nothing like that for the rod
    # gives back (problems, warnings)
    return [], []


def solve(length, initial, alphaSqr, upper, progress=None):
    # does all the maths and hands back a result dict for plotting.py to draw
    # progress gets called with how far through it is (0 to 1) so the GUI can move its bar

    # x used to be range(0, length + 1) which only works for whole number lengths
    # and gives you about 4 points on a short rod, so now it's always 101 points along it
    points = 101
    frames = 101
    Xaxis = np.linspace(0, length, points)

    tMax = time_to_near_zero(length, alphaSqr)
    unit, scale = pickTimeUnit(tMax)

    value = 0
    # abs so a rod starting below 0 doesn't make the threshold negative and keep every single time
    deltaThresh = abs(initial) / 10
    kept = []  # which times get their own line in the step through view
    labels = []

    # every time gets stored now (the animation uses all of them),
    # kept just remembers which ones are different enough to be worth their own line
    u = np.zeros((points, frames))

    for i in range(0, frames):
        t = (tMax / (frames - 1)) * i
        labels.append(f"t = {t * scale:.3g} {unit}")

        for j in range(0, points):  # keep t the same, go along the rod
            x = Xaxis[j]

            for n in range(1, upper + 1, 2):  # sum of sines per x
                value += fourierConstant(n, initial) * sin((n * pi * x) / length) * e ** (-alphaSqr * ((n ** 2 * pi ** 2) / length ** 2) * t)

            u[j, i] = value
            value = 0

        # only keep this time if the rod has changed enough since the last one we kept,
        # otherwise the end of the graph is just a load of lines stacked on top of each other
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

    # room above and below for the little overshoot the Fourier sum has at t = 0 near the ends
    pad = 0.12 * abs(initial)

    return {
        "lineX": Xaxis,
        "lineData": u,
        "labels": labels,
        "kept": kept,
        "xlabel": "Position x (m)",
        "ylabel": "Temperature u(x,t) (°C)",
        "title": "Heat Equation Solution",
        "ylim": (min(0, initial) - pad, max(0, initial) + pad),
        "colours": "plasma_r",  # orange when hot going to purple when cold
        "zeroLine": False,
        "loop": "restart",
        "info": f"The rod is basically cold after about {tMax * scale:.3g} {unit}",
    }


def run():
    # terminal version
    printBanner(NAME, SETUP)
    printTypical(FIELDS)

    print("  alpha² for some materials (m²/s):")
    for material in MATERIALS:
        print(f"  - {material:<10} {MATERIALS[material]:g}")
    print()

    # everything gets checked as it's typed in, see helpers.py
    length = askField(FIELDS["length"])
    initial = askField(FIELDS["initial"])
    alphaSqr = askField(FIELDS["alphaSqr"])
    upper = askField(FIELDS["upper"])

    print()
    print("  Computing solution...")
    print()

    result = solve(length, initial, alphaSqr, upper)

    print("  " + result["info"])
    print("  Done! Displaying graph...")
    print()

    showInTerminal(result)


if __name__ == "__main__":
    run()
