# PDE-Modelling-

Solves and graphs three of the PDEs from MA2102 using Fourier series.

- **Heat equation** - a rod starting at one uniform temperature, both ends held at 0. Shows it cooling over time.
- **Wave equation** - a string plucked at one point and let go from rest, both ends tied down. Shows it vibrating and the note it plays.
- **Laplace equation** - a membrane stretched over a rectangular frame with one edge pushed up into a triangle. Shows slices across it and the full 3D shape.

## Running it

```
pip install -r requirements.txt
python -m pde_modelling
```

Or just run `main.py`. A window opens with the inputs on the left and the graph on the right:

- Pick Heat, Wave or Laplace along the top
- The hint under each box turns orange for unrealistic values and red for ones that won't work
- Hit Solve (or Enter), then pick how to view it: lines stepping through time, an animation, or a 3D surface for the membrane
- The toolbar under the graph can zoom, pan and save it as an image

The old typing version is still there:

```
python -m pde_modelling --terminal
```

## Layout

```
pde_modelling/
    __main__.py   starts the window, or the terminal menu with --terminal
    gui.py        the window
    heat.py       heat equation
    wave.py       wave equation
    laplace.py    laplace / membrane
    helpers.py    input checking shared by the window and the terminal
    plotting.py   graph drawing shared by the window and the terminal
main.py           runs it
```
