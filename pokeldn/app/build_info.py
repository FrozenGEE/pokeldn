"""Version labels shown under Settings, About."""
from pathlib import Path

from pokeldn.app.paths import ROOT

# This fork's own build label and the day it was built. The firmware version itself follows upstream
# (firmware/esp32/version.txt); bump GEE_BUILD for each GEE release.
GEE_BUILD = "0.9.6"
BUILD_DATE = "2026-11-08"


def firmware_version() -> str:
    """The upstream firmware version bundled with this app, e.g. 1.10.0."""
    try:
        return (Path(ROOT) / "firmware" / "esp32" / "version.txt").read_text(encoding="ascii").strip()
    except OSError:
        return "1.10.0"
