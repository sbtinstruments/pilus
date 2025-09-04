# Pilus 🦠

## Load, analyze, plot, filter, classify, ...

Pilus is your one-stop toolbox for SBT data files (IQS, BDR, etc.).

## Use cases

### Convert BDR to CSV

You can use the CLI:

```shell
uv run pilus convert measure-bb2221028-A02.bdr measure-bb2221028-A02.csv
```

## Install

We use [`uv`](https://docs.astral.sh/uv/) to manage dependencies. Install `uv` with:

```shell
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Follow `uv`'s installation instructions.
Make sure that `uv` is available on the current path.
E.g., with `export PATH=$PATH:$HOME/.local/bin`.

With `uv` installed, we install all of Pilus' dependencies:

```shell
uv sync --all-extras
```

That's it.

## Test

The tests use assets from a separate repository. Get the assets:

```shell
git submodule update --init
```

Run all tests:

```shell
uv run pytest
```
