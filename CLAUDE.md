# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Educational visualization using an urban traffic metaphor to teach concurrency and synchronization concepts. Threads are cars, resources are intersections/bridges, synchronization primitives are traffic controls.

## Tech Stack

- **Processing** with **Python Mode** (Jycessing/Jython — Python 2.7 syntax)
- Single-file application: `GestiondeHilos/GestiondeHilos.pyde` (~970 lines)
- No external dependencies beyond Processing + Python Mode

## Running the Project

1. Install [Processing](https://processing.org/download)
2. In Processing, install **Python Mode for Processing** (dropdown → Manage Modes)
3. Open `GestiondeHilos/GestiondeHilos.pyde`
4. Press Play (or Cmd+R on macOS)

There is no build step, linter, or test suite.

## Architecture

**Mode-based dispatch**: 7 interactive modes (keys 1-7), each demonstrating a concurrency concept:

| Mode | Concept | Key Visual |
|------|---------|------------|
| 1 | Semaphore | Cars at intersection, counter controls how many pass |
| 2 | Mutex | Single-lane bridge, lock/unlock barrier |
| 3 | Monitor | Toll booth with automatic internal management |
| 4 | Critical Section | Hazard zone, toggle protected/unprotected (ENTER) |
| 5 | Race Condition | Two cars merge without control → collision |
| 6 | Deadlock | Perpendicular bridges, cars stuck at center |
| 7 | Concurrency | 6 cars in parallel lanes, independent speeds |

**Each mode follows the pattern:**
- `init_<mode>()` — creates cars and resets state
- `update_<mode>()` — runs every frame: state machine logic + overlay drawing + car rendering
- Global state variables prefixed per mode (`sem_`, `mut_`, `mon_`, `sec_`, `race_`, `dead_`, `conc_`)
- `init_mode(m)` dispatches to the correct init function

**Car class** (core entity): Represents a thread as a vehicle with state machine (`drive → wait → cross → exit`), smooth position interpolation, directional rotation, and detailed top-down car rendering.

## Key Constraints (Jython/Processing Python Mode)

- **No f-strings** — use `.format()` or `%` formatting
- **No Python 3 features** — no `nonlocal`, no `super()` without args, no type hints
- **Integer division**: `int/int` returns int; cast to `float()` when needed
- **All Processing functions are global** (`fill()`, `rect()`, `text()`, `ellipse()`, etc.)
- **`global` keyword required** to reassign module-level variables inside functions
- `setup()` and `draw()` are Processing entry points (called by the framework)
- `keyPressed()` and `mousePressed()` are Processing event hooks
- Images must be in `GestiondeHilos/data/` for `loadImage()` to find them

## Layout Constants

- Window: 1200×700
- Scene area: `(5, 45, 840, 550)` — background image + car animations
- Panel: `(855, 0, 340, 700)` — mode info, controls, analogies
- Helper functions `sx(pct)` / `sy(pct)` convert 0.0–1.0 proportions to scene pixel coordinates

## Adding a New Mode

1. Add mode name, image filename, description, and controls to the arrays at the top
2. Add global state variables with a unique prefix
3. Create `init_newmode()` and `update_newmode()` functions following existing patterns
4. Add dispatch cases in `init_mode()`, `draw()`, and `keyPressed()`
5. Place the background PNG in `GestiondeHilos/data/`
