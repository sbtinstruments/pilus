# Pilus🦠

## Load, analyze, plot, filter, classify, ...

Pilus is the one-stop toolbox to work with SBT data files (IQS, BDR, etc.).

## Install

We use [`poetry`](https://python-poetry.org) to manage dependencies. [Install `poetry`](https://python-poetry.org/docs/master/#installation):

```shell
curl -sSL https://install.python-poetry.org | python3 -
```

Follow `poetry`'s installation instructions.
Make sure that `poetry` is available on the current path.
E.g., with `export PATH=$PATH:$HOME/.local/bin`.

With `poetry` installed, we can install all of Pilus' dependencies:

```shell
poetry install
```

That's it.

## Test

The tests use assets from a separate repository. Get the assets:

```shell
git submodule update --init
```

Run all tests:

```shell
poetry run pytest
```
