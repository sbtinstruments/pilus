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

Follow `poetry`'s installation instructions.
Make sure that `poetry` is available on the current path.
E.g., with `export PATH=$PATH:$HOME/.local/bin`.

With `poetry` installed, we can install all of Pilus' dependencies:

```shell
poetry install --with analysis,cli
```

That's it.
Note that we use `--with analysis,cli`.
The `analysis` group of tools allows you to, e.g., convert SBT data types to numpy arrays.
The `cli` group of tools gives you the `pilus` command in your shell.

## Test

The tests use assets from a separate repository. Get the assets:

```shell
git submodule update --init
```

Run all tests:

```shell
poetry run pytest
```
