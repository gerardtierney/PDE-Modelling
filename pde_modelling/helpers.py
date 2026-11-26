from math import isfinite
import textwrap


# shared bits used by all three solvers, by the GUI and by the terminal menu
#
# every input is described by a "field", a dict like this:
#   label    what it's called
#   unit     shown next to it
#   default  what the GUI box starts with
#   low/high hard limits, the maths breaks or it makes no sense past them, so it won't let you
#   notZero  0 isn't allowed
#   whole    has to be a whole number (then low and high are allowed values themselves)
#   typical  the range real stuff sits in. outside it you get a warning saying what goes
#            wrong, but you can still say yes and use it if you want to see what happens
#   warning  what to tell them when they go outside typical
#   hint     optional, replaces the "usual x to y" text under the box in the GUI
#
# keeping it all in one dict means the GUI and the terminal can't end up with different limits


# same question in all three, so it lives here
# too few terms and the graph has ripples that aren't really there,
# too many and you're just waiting for no visible difference
FOURIER_FIELD = {
    "label": "Fourier terms",
    "unit": "",
    "default": 500,
    "whole": True,
    "low": 1,
    "high": 5000,
    "typical": (100, 2000),
    "warning": "Under 100 the series hasn't settled so you'll see wobbles near any sharp corner. "
               "Over 2000 it gets slow (could be a minute or more) and looks the same anyway.",
}


def readNumber(text, whole=False):
    # turns what was typed into a number
    # gives back (number, problem), problem is "" if it went fine
    text = text.strip()

    if text == "":
        return None, "Can't be left empty"

    if whole:
        try:
            return int(text), ""
        except ValueError:
            return None, "Has to be a whole number"

    try:
        value = float(text)
    except ValueError:
        return None, "That's not a number"

    # float() will happily take 'inf' or 'nan', neither of those are any use here
    if not isfinite(value):
        return None, "Needs to be an actual number"

    return value, ""


def checkLimits(value, field, high=None):
    # gives back (problem, headsUp)
    # problem means it's not allowed at all, headsUp means it's allowed but unrealistic
    # high can be passed in for limits that depend on another value, like the pluck point
    low = field.get("low")
    if high is None:
        high = field.get("high")

    if field.get("whole"):
        if value < low or value > high:
            return f"Has to be between {low} and {high}", ""
    else:
        # strict for decimals, so low=0 means it has to be bigger than 0, not 0 itself
        if low is not None and value <= low:
            return f"Has to be bigger than {low:g}", ""
        if high is not None and value >= high:
            return f"Has to be less than {high:g}", ""

    if field.get("notZero") and value == 0:
        return "Can't be 0", ""

    typical = field.get("typical")
    if typical is not None and (value < typical[0] or value > typical[1]):
        headsUp = f"{field['label']} of {value:g} {field['unit']} is outside the usual range of {typical[0]:g} to {typical[1]:g}."
        if field.get("warning", "") != "":
            headsUp += " " + field["warning"]

        return "", headsUp

    return "", ""


def hintText(field):
    # the little grey line under each box in the GUI, and the typical values list in the terminal
    if "hint" in field:
        return field["hint"]

    typical = field.get("typical")
    if typical is None:
        return ""

    return f"usual {typical[0]:g} to {typical[1]:g} {field['unit']}".strip()


# ---------------- terminal only ----------------


def printBanner(name, setup):
    print("=" * 55)
    print("   " + name)
    print("=" * 55)
    print()
    print("  Problem Setup:")
    for line in setup:
        print("  - " + line)
    print()
    print("=" * 55)
    print()


def printTypical(fields):
    print("  Typical values:")
    for field in fields.values():
        if hintText(field) != "":
            print(f"  - {field['label']:<22}: {hintText(field)}")
    print()


def askYesNo(prompt):
    while True:
        answer = input(prompt).strip().lower()

        if answer in ("y", "yes"):
            return True
        if answer in ("n", "no"):
            return False

        print("  Just y or n")


def warnAndConfirm(message):
    # prints a warning and asks if they want to keep going anyway
    # True means use it, False means go back and type something else
    print()
    print(textwrap.fill("Heads up: " + message, 90, initial_indent="  ", subsequent_indent="  "))
    ok = askYesNo("  Use it anyway? (y/n): ")
    print()

    return ok


def askField(field, high=None):
    # keeps asking until it gets something valid, so a typo can't crash anything
    if field["unit"] != "":
        prompt = f"  {field['label']} ({field['unit']}): "
    else:
        prompt = f"  {field['label']}: "

    while True:
        value, problem = readNumber(input(prompt), field.get("whole", False))

        if problem == "":
            problem, headsUp = checkLimits(value, field, high)

        if problem != "":
            print("  " + problem + ", try again")
            continue

        if headsUp != "" and not warnAndConfirm(headsUp):
            continue

        return value


def pickTimeUnit(tMax):
    # tMax comes in as seconds. this picks whatever unit makes the times on the graph
    # sensible numbers, so a guitar string shows ms and a big lump of steel shows hours
    # gives back the unit name and what to multiply the seconds by
    if tMax < 1e-3:
        return "µs", 1e6
    if tMax < 1:
        return "ms", 1e3
    if tMax < 120:
        return "s", 1
    if tMax < 2 * 3600:
        return "min", 1 / 60
    if tMax < 2 * 86400:
        return "h", 1 / 3600
    if tMax < 2 * 365 * 86400:
        return "days", 1 / 86400

    return "years", 1 / (365 * 86400)
