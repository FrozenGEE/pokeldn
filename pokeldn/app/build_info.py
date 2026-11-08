"""Version labels shown under Settings, About."""
from pathlib import Path

from pokeldn.app.paths import ROOT

# This build's date. The app reports the official pokeldn version and the upstream firmware
# version (firmware/esp32/version.txt).
BUILD_DATE = "2026-11-08"


def firmware_version() -> str:
    """The upstream firmware version bundled with this app, e.g. 1.10.0."""
    try:
        return (Path(ROOT) / "firmware" / "esp32" / "version.txt").read_text(encoding="ascii").strip()
    except OSError:
        return "1.10.0"
