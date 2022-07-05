# Pilus 🦠

## Load, analyze, plot, filter, classify, ...

Pilus is your one-stop toolbox for SBT data files (IQS, BDR, etc.).

## Install

We use [`poetry`](https://python-poetry.org) to manage dependencies.
Moreover, we use `poetry` version 1.2.x for it's dependency group feature.
As of this writing, `poetry` offers version 1.2.x through it's "preview" channel.
[Install "preview" version of `poetry`](https://python-poetry.org/docs/master/#installation):

```shell
curl -sSL https://install.python-poetry.org | python3 - --preview
```

Follow `poetry`'s installation instructions.
Make sure that `poetry` is available on the current path.
E.g., with `export PATH=$PATH:$HOME/.local/bin`.

With `poetry` installed, we can install all of Pilus' dependencies:

```shell
poetry install --with analysis
```

That's it.
Note that we use `--with analysis`.
The `analysis` group of tools allows you to, e.g., convert SBT data types to numpy arrays.
Without `analysis`, Pilus only includes the basic tools to, e.g., load/save data files.

## Test

The tests use assets from a separate repository. Get the assets:

```shell
git submodule update --init
```

Run all tests:

```shell
poetry run pytest
```
