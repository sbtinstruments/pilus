from typer import Typer

from ._commands import convert, show

CLI_APP = Typer(no_args_is_help=True)
CLI_APP.command()(convert)
CLI_APP.command()(show)
# TODO: Remove this dummy command. We only need as long as there only is
# a single command.
CLI_APP.command()(lambda: 42)


def run() -> None:
    """Run the CLI application."""
    CLI_APP()
    # # Set `standalone_mode=False` to avoid a `SystemExit` exception
    # result = CLI_APP(standalone_mode=False)
    # if isinstance(result, int):
    #     raise SystemExit(result)
