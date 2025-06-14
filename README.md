# Diet optimization

This repository contains the code for some diet optimization projects. The goal is to create a tool for me to automatically generate a diet plan that meets set nutritional needs, while minimizing the cost, the environmental impact and the complexity of the diet.

## Prerequisites

General utilities and for running the backend:

- `make` for running the commands in the `Makefile`.
- `wget` for downloading the data.
- `unzip` for extracting the data.
- `uv` for running python scripts.
- `duckdb` for the duckdb CLI.

To run the frontend:

- `esbuild` for building the frontend.
- `pnpm` for managing the frontend dependencies.

On Ubuntu, you can install some of these with:

```bash
sudo apt install make wget unzip
curl -fsSL https://install.duckdb.org | sh
curl -fsSL https://astral.sh/uv/install.sh | sh
curl -fsSL https://esbuild.github.io/dl/latest | sh
curl -fsSL https://get.pnpm.io/install.sh | sh
```

On MacOS they can be installed with `brew`:

```bash
brew install make wget unzip duckdb uv esbuild pnpm
```

## Usage

To run different parts of the project, check out the `Makefile` for the available commands.
