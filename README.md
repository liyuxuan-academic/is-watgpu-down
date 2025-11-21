# Is WatGPU Down?

A simple [status page](http://liyuxuan-academic.github.io/is-watgpu-down/) for the [WATGPU](https://watgpu.cs.uwaterloo.ca/) cluster.
The watgpu is frequently down and it makes me mad. So here we are.
This repository automatically checks the status of the WATGPU cluster (HTTP and SSH) every 15 minutes and updates the status page.

## How it works

1. A GitHub Action runs `monitor.py` every 15 minutes.
2. The script:
   - Pings `https://watgpu.cs.uwaterloo.ca/`
   - Checks SSH connectivity to `watgpu.cs.uwaterloo.ca:22`
   - Updates `history.json`
   - Generates a new `index.html`
3. The results are committed back to the repository.
4. GitHub Pages serves the `index.html`.

## Setup

1. Fork or create this repository.
2. Enable GitHub Pages in `Settings > Pages`.
   - Source: `Deploy from a branch`
   - Branch: `main`
   - Folder: `/` (root)
3. The action will start running automatically.

