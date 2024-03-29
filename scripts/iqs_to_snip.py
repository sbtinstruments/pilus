from pathlib import Path

import typer

from pilus.basic import Wave
from pilus.formats import iqs
from pilus.formats import wave as wave_format
from pilus.snipdb import SnipDb


def _main(source_file: typer.FileBinaryRead) -> None:
    try:
        snip_db = SnipDb.from_iqs_io(source_file)
    except iqs.IqsError as exc:
        typer.echo(f"Could not deserialize IQS file: {exc}")
        return
    finally:
        source_file.close()
    # TODO: Serialize `snip_db` into directory

    wave = snip_db.get(Wave)
    assert wave is not None

    wave_file = Path("data.wav")
    with wave_file.open("wb") as io:
        wave_format.to_io(wave.value.lpcm, io)


if __name__ == "__main__":
    typer.run(_main)
