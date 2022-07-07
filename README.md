# Pilus 🦠

## Load, analyze, plot, filter, classify, ...

Pilus is your one-stop toolbox for SBT data files (IQS, BDR, etc.).

## Use cases

### Convert BDR to CSV

You can use the CLI:

```shell
pilus convert measure-bb2221028-A02.bdr measure-bb2221028-A02.csv
```

If you're not within a Poetry shell, prefix `poetry run` to the command:

```shell
poetry run pilus convert measure-bb2221028-A02.bdr measure-bb2221028-A02.csv
```

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
