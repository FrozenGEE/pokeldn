#!/usr/bin/env python3
"""Build pokeldn-gee: this fork's Flet app (GEE 320x240 Session mirror) as a Windows one-folder app.

    .gee-build-venv\\Scripts\\python.exe scripts\\build_gee_app.py

The official package's resources (PKHeX helper, firmware, the Flet client with file drops, Unicorn)
are reused; the Python code is this working tree's. The result is pokeldn-gee/pokeldn-gee.exe.
Flet's packer deletes its --distpath, so the build goes to the isolated .dist-gee directory and is
copied to pokeldn-gee only after it succeeds.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
VENV = ROOT / ".gee-build-venv"
PY = VENV / "Scripts" / "python.exe"
DIST_PARENT = ROOT / ".dist-gee"
NAME = "pokeldn-gee"
OUT = DIST_PARENT / NAME
FINAL = ROOT / NAME
OFFICIAL = Path(os.environ.get("POKELDN_OFFICIAL", r"D:\Users\GEE\Desktop\pokeldn\_internal"))


def need(path: Path) -> Path:
    if not path.exists():
        raise SystemExit(f"missing: {path}")
    return path


def run(args: list[str], **kw) -> None:
    print("+", " ".join(str(a) for a in args))
    env = dict(os.environ)
    env["VIRTUAL_ENV"] = str(VENV)
    env["PATH"] = str(VENV / "Scripts") + os.pathsep + env.get("PATH", "")
    env.pop("PYTHONHOME", None)
    env.pop("PYTHONPATH", None)
    kw.setdefault("env", env)
    subprocess.run([str(a) for a in args], check=True, **kw)


def main() -> int:
    need(PY)
    flet_cmd = [PY, "-c", "from flet_cli.cli import main; main()"]
    need(OFFICIAL / "services/pkhex/dist/pokeldn-pkhex.exe")
    need(OFFICIAL / "gui/firmware")
    need(OFFICIAL / "flet_desktop/app/flet-windows.zip")
    fw = sorted((OFFICIAL / "gui/firmware").glob("pokeldn-*.bin"))
    if len(fw) < 8:
        raise SystemExit(f"only {len(fw)} firmware images found under {OFFICIAL / 'gui/firmware'}")

    # Give Flet's packer the official custom client up front, so it neither downloads the stock one nor
    # bundles a viewer without the FileDrop extension.
    try:
        import flet_desktop
        appdir = Path(flet_desktop.__file__).resolve().parent / "app"
        appdir.mkdir(parents=True, exist_ok=True)
        for name in ("flet-windows.zip", "flet-windows.zip.sha256", "pokeldn-drop"):
            src = OFFICIAL / "flet_desktop" / "app" / name
            if src.exists():
                shutil.copy2(src, appdir / name)
    except Exception as exc:   # the packer reports a missing client itself
        print(f"warning: could not stage the Flet client: {exc}")

    work = ROOT / ".build-gee"
    for path in (work, DIST_PARENT, FINAL):
        if path.exists():
            shutil.rmtree(path)
    work.mkdir()
    DIST_PARENT.mkdir()

    add: list[tuple[Path, str]] = [
        (ROOT / "bin", "bin"),
        (ROOT / "config", "config"),
        (ROOT / "docs", "docs"),
        # screen_render.Scene reads firmware/esp32/version.txt for the Session mirror's v line.
        (ROOT / "firmware" / "esp32" / "version.txt", "firmware/esp32"),
        (ROOT / "gui" / "assets", "gui/assets"),
        (ROOT / "gui" / "guide.md", "gui"),
        (ROOT / "pokeldn", "pokeldn"),
        (ROOT / "src", "src"),
        (ROOT / "vendor/LDN/ldn", "vendor/LDN/ldn"),
        (ROOT / "vendor/LDN/LICENSE", "vendor/LDN"),
        (ROOT / "LICENSE", "."),
        (OFFICIAL / "services/pkhex/dist", "services/pkhex/dist"),
        (OFFICIAL / "gui/firmware", "gui/firmware"),
        (OFFICIAL / "unicorn/lib", "unicorn/lib"),
        (OFFICIAL / "flet_desktop/app/flet-windows.zip", "flet_desktop/app"),
        (OFFICIAL / "flet_desktop/app/flet-windows.zip.sha256", "flet_desktop/app"),
        (OFFICIAL / "flet_desktop/app/pokeldn-drop", "flet_desktop/app"),
    ]
    add = [(src, dest) for src, dest in add if src.exists()]
    for src, dest in add:
        need(src)

    from pokeldn import __version__

    args: list[str] = [
        *flet_cmd, "pack", ROOT / "gui" / "main.py",
        "--name", NAME, "-y",
        "--distpath", DIST_PARENT,
        "--product-name", NAME,
        "--product-version", __version__,
        "--file-version", f"{__version__}.0",
        "--bundle-id", "io.github.decryptu.pokeldn",
        "--icon", ROOT / "gui" / "assets" / "icon.ico",
    ]
    for src, dest in add:
        args += ["--add-data", f"{src}{os.pathsep}{dest}"]

    bin_scripts = sorted(p.stem for p in (ROOT / "bin").glob("*.py"))
    pyi = [
        "--onedir", "--console", "--hide-console=hide-early",
        f"--paths={ROOT}", f"--paths={ROOT / 'bin'}", f"--paths={ROOT / 'vendor' / 'LDN'}",
        f"--workpath={work / 'build'}", f"--specpath={work}",
        *[f"--hidden-import={s}" for s in bin_scripts],
        "--collect-submodules=pokeldn", "--collect-submodules=ldn",
        "--collect-submodules=bleak", "--collect-submodules=unicorn",
        "--collect-all=esptool", "--collect-all=esp_pylib",
        "--collect-all=trio", "--collect-all=Crypto", "--collect-all=zstandard",
        "--collect-all=serial", "--collect-all=websockets", "--collect-all=certifi",
    ]
    for option in pyi:
        args.append(f"--pyinstaller-build-args={option}")

    run(args, cwd=work)

    need(OUT)
    shutil.copytree(OUT, FINAL)

    # The official packer clears PyInstaller's Control Flow Guard: Unicorn faults under it
    # (0xC0000409). The frozen self-check exercises it.
    from scripts.pack_app import clear_cfg
    clear_cfg(FINAL / f"{NAME}.exe")

    # The stock Flet client has no file drops; the official package carries the custom one.
    built = FINAL / "_internal" / "flet_desktop"
    for rel in ("app/flet-windows.zip", "app/flet-windows.zip.sha256", "app/pokeldn-drop"):
        src = OFFICIAL / "flet_desktop" / rel
        if src.exists():
            dst = built / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)

    readme = FINAL / "README.txt"
    readme.write_text(
        "pokeldn-gee\n"
        "===========\n"
        "Windows build of pokeldn 0.60.2 with the GEE 320x240 Session screen mirror.\n"
        "The board's status, exchange and opening pages are rendered at 320x240 and\n"
        "scaled proportionally to 300x225 in the Session panel.\n"
        "Based on the official pokeldn source; the GEE Session-screen changes are merged in.\n"
        "Official firmware 1.10.0 · pokeldn 0.60.2\n\n"
        "v0.9.1: the Session mirror reads firmware/esp32/version.txt, so it shows\n"
        "v1.10.0 instead of vunknown.\n\n"
        "v0.9.5: the installed-state Wireless button says Reinstall / 重新安装.\n\n"
        "GEE app build 0.9.8: Settings, Storage backs up the settings, plugins and\n"
        "every Pokemon file into one zip, sorted into folders, either to a folder\n"
        "on this computer or to WebDAV (address, account, password and a\n"
        "connection dot). prod.keys is off by default; its switch adds it.\n"
        "WebDAV keeps one pokeldn-backup.zip: local-to-cloud replaces it, and\n"
        "cloud-to-local replaces this computer. A local pokeldn zip can also be\n"
        "restored; every backup, sync and restore needs a ticked confirmation.\n\n"
        "GEE app build 0.9.7: Exchange history and favorites on the Bank page, a\n"
        "one-press Clear records, the GitHub accelerator in Settings, the phone\n"
        "card/About layout, and the Chinese pack updated to 1.0.6.\n\n"
        "The Board page flashes the official firmware images for every chip,\n"
        "including the ESP32-S3 Wireless image (firmware 1.10.0). The GEE board\n"
        "image is not bundled; the Board page downloads from the official\n"
        "pokeldn releases when an image is missing.\n\n"
        "Run pokeldn-gee.exe. The first launch may take a few seconds while Flet\n"
        "unpacks its viewer. Keep the _internal folder beside the exe.\n",
        encoding="utf-8", newline="\r\n")

    print(f"built {FINAL}")
    return 0


if __name__ == "__main__":
    if "--help" in sys.argv or "-h" in sys.argv:
        print(__doc__)
        raise SystemExit(0)
    raise SystemExit(main())
