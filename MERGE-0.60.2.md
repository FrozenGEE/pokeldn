# FrozenGEE pokeldn 0.60.2 合并说明

- 模板：`FrozenGEE/pokeldn` `main`（HEAD `ad2e98ed5b505cda3d70496878dc91b1ae6bf289`，
  `List 0.60.2 in the AltStore source`）
- 本地基线：`FrozenGEE-pokeldn` 0.58.0 + GEE 改动（v0.9.3 内部版）
- 本目录是 **0.60.2 + 本地 GEE 改动**。

## 已移植的本地改动

- `pokeldn/app/screen_render_gee.py`：GEE 320×240 Session 镜像（新增）
- `pokeldn/app/screen_render.py`：保留 GEE 的 console/cable/clear 视觉调整
- `gui/views/board_screen.py`：Session 面板按 320×240 渲染、300×225 等比显示
- `gui/views/boards.py`：ESP32-S3「无线」已安装时仍显示重新安装入口；v0.9.5 起该按钮文案为 **Reinstall** / **重新安装**（英文默认 + 简繁中文语言包）
- `gui/board.py`：`FIRMWARE_GEE_S3` / `gee_firmware()`；S3 无线使用 GEE 镜像
- `docs/gui.md`：GEE 固件选择说明
- `firmware/esp32/main/{scene.c,scene.h,radio.c,display.h,CMakeLists.txt}`：GEE 固件 overrides
- `tests/test_esp32_screen.py`：GEE 场景测试
- `scripts/build_gee_app.py`：GEE Windows 构建脚本（含 `firmware/esp32/version.txt` 打包）
- v0.9.6：待机/搜索页增加精灵球摇晃动画；Session 镜像是同一套动画
- 内置固件：`D:\vs-code\gee\backup\gee-v0.9.6-full-20261108.bin`（v0.9.6，默认音量 75%）

## 构建

```bat
python -m venv .gee-build-venv
.gee-build-venv\Scripts\python.exe -m pip install -r gui\requirements.txt
set POKELDN_OFFICIAL=D:\vs-code\FrozenGEE-pokeldn-0.60.2\.official\extracted\pokeldn\_internal
.gee-build-venv\Scripts\python.exe scripts\build_gee_app.py
```

官方 0.60.2 资源包：`pokeldn-windows-x64.zip`，SHA256
`6155fdce28ccf012639a16c8c8f77ba337eea427c2a653134c8da93494fe1a25`。
产物：`pokeldn-gee\pokeldn-gee.exe`，自检 `pokeldn 0.60.2` 通过。
