---
title: GEE version history
nav_order: 20
---
# GEE version history

This fork adds the GEE board port and the desktop/phone changes below to pokeldn 0.60.2.
The app reports the official pokeldn version, checks the official GitHub releases for updates,
and flashes the official firmware images; no fork-specific build number or board image is
presented.

| Item | Version |
|---|---|
| Firmware images | official 1.10.0 |
| pokeldn | 0.60.2 |

## 0.9.8 (2026-11-08)

### Official build identity and firmware

- Settings, About no longer shows a separate GEE build row. The app reports the official
  pokeldn version (0.60.2) and the official firmware version.
- The Board page flashes the official firmware images for every chip, including the ESP32-S3
  Wireless image; the GEE-specific board image is no longer bundled. Flashing, firmware downloads
  and the update check all use the official `Decryptu/pokeldn` releases.
- The Android package name is the official `org.pokeldn.usbprobe`, and the desktop bundle id is
  `io.github.decryptu.pokeldn`. A build therefore replaces an installed official app of the same
  version instead of installing beside it.

### Backup and restore

Settings, Storage has a new **Backup and restore** card with two destinations:

- **This computer** writes one `pokeldn-backup.zip` to a folder chosen in the card; the folder
  button opens it. A new backup replaces that one file (no timestamped pile).
- **WebDAV** keeps one `pokeldn-backup.zip` in a server folder. The card asks for the address,
  account and password. **Save and test** probes the folder and lights the dot green (reachable),
  amber (the folder is missing) or red (wrong password, no write permission or no answer). The
  account and password are kept in `settings.json` only; the password is removed from the
  `settings.json` inside the archive, so a backup stored on that server does not carry its own
  credentials.

The archive is sorted into folders, so a restore (or a look inside) is readable:

| folder | contents |
|---|---|
| `config/` | `settings.json` without the WebDAV password |
| `plugins/`, `plugin-data/` | installed language packs and plugins, and their saved data |
| `pokemon/` | records created by the program (builder, Mystery Gift), with sidecars and favorites |
| `bank/` | `Documents/pokeldn/Bank` |
| `received/` | `Documents/pokeldn/Received` |
| `saves/` | `Documents/pokeldn/Saves` |
| `gts/`, `macros/` | GTS listings/offers and controller macros |
| `keys/` | `prod.keys`, only when **Include prod.keys** is on |
| `manifest.json` | app and build versions, time, file count, size and per-folder counts |

`prod.keys` is off by default; turning **Include prod.keys** on adds it under `keys/` when the
chosen file exists, and a missing one is skipped rather than stopping the backup. Session
captures, logs and the sprite cache are always left out. The card is in Settings, so it
is on every platform, including the phone build.

### Phone layout (0.9.8)

- The Bank's sort and filter dropdowns each take a full row below 760 points, with Select or
  Clear records below them; the clipping to "最新优…" and "所有宝可…" is gone.
- List panes are named 盒子列表 / 设备列表 / 宏列表, so a switcher no longer shows
  the same label as its selected item.
- The Android board guidance (the English body under 未插入设备) now goes through the language
  pack instead of the native `Setup.java` text; the WebView warning screen is Chinese on a
  Chinese phone too.

### Language pack 1.0.6.1

- No language pack is bundled. The community Simplified (`community-zh-hans`) and Traditional
  (`community-zh-hant`) Chinese packs are installed from the plugin source
  `ZsyzLahz/pokeldn-zh-hans`; keys added by this fork fall back to English until translated.
- The phone's Android board guidance still goes through the language pack
  (`app.android_connect_board` and friends, with English inline defaults), so the fix remains
  available to an installed pack instead of coming from `Setup.java`.
- The GEE-added strings have English inline defaults, so a player who enables no language pack
  sees English rather than Chinese.
- `plugins.seed_bundled` installs any pack placed in `src/plugins` and refreshes a same-version
  copy when its files changed (a SHA-256 marker in `plugins/.bundled.json`), while a newer pack
  the player installed is kept.
- The phone's WebView warning screen is Chinese when the system language is Chinese.

### Sync and restore

- **From file restore** reads any pokeldn zip, including the older
  `pokeldn-backup-YYYYMMDD-HHMMSS.zip` files.
- **WebDAV** has two sync buttons around the single cloud file:
  - **Local to cloud**: packs this computer and overwrites `pokeldn-backup.zip` on the server;
    the local side is the source of truth.
  - **Cloud to local**: downloads that file and replaces this computer with it; the cloud side
    is the source of truth. If the fixed file is absent but an older timestamped backup exists,
    the newest older one is used.
- A local restore and cloud-to-local both replace: every category present in the archive is
  cleared and written back, `settings.json` is restored (device-local fields below stay), and
  `prod.keys` is written to the key path this computer already uses.
- Every local backup, WebDAV sync and restore opens a confirmation that says it overwrites the
  other side. The confirm button stays disabled until **我已知晓，确认覆盖** is ticked. There is
  no automatic safety copy.
- `settings.json` is staged as `settings.restore.json` and applied by the next launch, so the
  running app cannot overwrite it. After a restore the card offers **Restart now** on desktop.
- Kept from the current computer (not taken from the archive): key and received paths, the board
  port and radio settings, serial speed and transmit power, the GitHub accelerator, update and
  UI preferences, board names, and the WebDAV/backup choices. Trainer, games, tool values and
  Pokemon data come from the archive.
- Zip members with an absolute path, `..`, or a path outside their category are refused; a
  member outside the archive's top folder is ignored.

## 0.9.7 (2026-11-08)

### Exchange history

The Bank page has a new **Exchange history** box. It lists the records the program created:
Pokemon built on the Games page, Mystery Gift copies, and anything else written through
`pokeldn.pokemon.Service.keep` under `%APPDATA%\pokeldn\pokemon\<game>`.

- New records get a `.json` sidecar with species, species ID, shiny, summary, legality, time
  and source (`built` or `gift`), so the list opens without asking PKHeX to read each file.
- Older records without a sidecar are read from their file name and resolved against the
  English species list. Imports and bank-to-game moves are tagged `imported` / `trade` and stay
  out of the history; an untagged older record cannot be told apart and may appear.
- The box supports the same search, sort, shiny and legality filters as the bank.
- **Clear records** in the box's toolbar deletes every listed record and its sidecar after a
  confirmation. If a record is still queued for a trade, add it again after clearing.

### Favorites

- A Pokemon's details have **Favorite / Remove from favorites**; bank and exchange-history
  Pokemon can both be starred.
- A starred tile shows a star, and the new **Favorites** box in the Bank sidebar lists every
  starred Pokemon.
- Favorites persist in `%APPDATA%\pokeldn\pokemon\.favorites.json`.

### GitHub accelerator

Settings has a **GitHub accelerator** card:

- Pick **Direct** or one of nine mirrors: gh-proxy.com, ghfile.geekertao.top, gitproxy.click,
  gh-proxy.org, ghproxy.imciel.com, ghfast.top, ghproxy.cfd, ghproxy.cn and gh-proxy.net. Each
  answered a probe on 2026-11-08. Selecting an entry applies it at once and tests it against a
  small GitHub file; no confirmation button.
- The dot beside the label is green below 1000 ms, amber above, and red when the probe fails
  or times out. The latency in milliseconds is shown next to it.
- The pick is stored as `github_mirror` in `settings.json`. `pokeldn.app.github_mirror`
  prefixes the mirror to GitHub hosts only; every other address is unchanged.
- `pokeldn.app.update._open` applies it, so update checks, release and plugin downloads, plugin
  source listings and sprite downloads use the same accelerator. Checksums still verify the
  files; the accelerator is only a transport.
- Add another mirror by adding `(prefix, name)` to `MIRRORS` in
  `pokeldn/app/github_mirror.py`.

### Phone layout

- Below 760 points wide, the firmware and plugin cards put their buttons below the text
  instead of pinning them to the right, so summaries keep the full width instead of wrapping
  one character per line.
- Settings, About uses `label: value`, so long version rows and repository links are not
  clipped.
- The Android app label is **pokeldn**. 0.9.7 used the GEE package `org.pokeldn.gee` so it
  installed beside the official app; 0.9.8 uses the official package name, `org.pokeldn.usbprobe`.

### Language pack

- The bundled Simplified Chinese pack is updated to upstream **1.0.6**; the in-app source stays
  `ZsyzLahz/pokeldn-zh-hans`.
- The bundled copy adds the strings for the About labels, **Reinstall**, the GitHub accelerator
  and the exchange history/favorites UI. The English template carries the same keys.

## 0.9.6

ESP32-S3 Wireless firmware image (upstream firmware 1.10.0): the Poké Ball wobble animation on
the idle/search pages. The Session mirror shows the same animation.

## 0.9.5

The installed-state Wireless button says **Reinstall / 重新安装**.

## 0.9.3

First GEE board port: ST7789 320x240 screen, ES8311 speaker, ES7210 microphone, GC0308 camera,
the exchange sound effects and the 320x240 Session mirror.
