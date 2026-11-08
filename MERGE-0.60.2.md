# FrozenGEE pokeldn 0.60.2 合并说明

- 模板：`FrozenGEE/pokeldn` `main`（HEAD `ad2e98ed5b505cda3d70496878dc91b1ae6bf289`，
  `List 0.60.2 in the AltStore source`）
- 本地基线：`FrozenGEE-pokeldn` 0.58.0 + GEE 改动（固件源码 1.10.0）
- 本目录是 **0.60.2 + 本地 GEE 改动**。

## 已移植的本地改动

- `pokeldn/app/screen_render_gee.py`：GEE 320×240 Session 镜像（新增）
- `pokeldn/app/screen_render.py`：保留 GEE 的 console/cable/clear 视觉调整
- `gui/views/board_screen.py`：Session 面板按 320×240 渲染、300×225 等比显示
- `gui/views/boards.py`：ESP32-S3「无线」已安装时仍显示重新安装入口；v0.9.5 起该按钮文案为 **Reinstall** / **重新安装**（英文默认 + 简繁中文语言包）
- `gui/board.py`：刷机只使用官方发布镜像（GEE 镜像优先选择已移除）
- `docs/gui.md`：固件选择说明改为官方镜像
- `firmware/esp32/main/{scene.c,scene.h,radio.c,display.h,CMakeLists.txt}`：GEE 固件源码改动（准备上游 PR，不打包进程序）
- `tests/test_esp32_screen.py`：GEE 场景测试
- `scripts/build_gee_app.py`：GEE Windows 构建脚本（含 `firmware/esp32/version.txt` 打包）
- 待机/搜索页精灵球摇晃动画保留在源码中；Session 镜像是同一套动画
- 内置固件：不再打包 GEE 镜像；刷机与固件下载均使用官方 `Decryptu/pokeldn` 发布（固件 1.10.0）

## GEE build 0.9.8（2026-11-08）

本版改动（2026-11-08）。程序关于页不再显示 GEE 构建号，版本与更新检查均按官方
pokeldn 0.60.2 / 官方 GitHub 仓库；刷机使用官方固件镜像（固件 1.10.0），不再打包 GEE 开发板镜像。

- **备份与还原**：设置 → 存储新增卡片，可选「本地」或「WebDAV」。本地只保留一份
  `pokeldn-backup.zip`，再次备份覆盖；WebDAV 需要地址、账号、密码，点「保存并测试」后圆点
  显示连接结果（绿=正常，黄=地址不存在，红=账号错误/无权限/不通）。
- **打包内容**：`config/`（settings.json）、`plugins/`、`plugin-data/`、`pokemon/`（程序创建的
  宝可梦和收藏）、`bank/`、`received/`、`saves/`、`gts/`、`macros/`，外加 `manifest.json`
  （版本、时间、文件数、大小、分类计数）。
- **敏感内容**：`prod.keys` 默认不包含，可在卡片里打开「包含 prod.keys」放进 `keys/`。备份包
  里的 `settings.json` 会去掉 WebDAV 密码，密码只保留在本机设置中。
- **同步与还原**：WebDAV 只保留一份 `pokeldn-backup.zip`。「本地同步到云端」打包本机并覆盖
  云端那一份；「云端同步到本地」下载它并替换本机。本机也可从任意 pokeldn zip 还原。备份、
  同步和还原都会弹窗确认，勾选「我已知晓，确认覆盖」后才能继续；设置暂存为
  `settings.restore.json`，下次启动生效；
  `prod.keys` 写入本机密钥路径。设备相关设置（路径、串口、板子、WebDAV 账号等）保留本机值。
- 新增模块 `pokeldn/app/backup.py`、`pokeldn/app/restore.py`，测试 `tests/test_backup.py`、
  `tests/test_restore.py`，文案同步英文模板与简中包。

## GEE build 0.9.7（2026-11-08）

GEE 程序构建升级到 **0.9.7**；开发板镜像仍是 **0.9.6**（上游固件 1.10.0）。

- **交换记录**：银行页新增「交换记录」盒子，列出程序创建过的宝可梦；新记录带 `.json`
  （物种、异色、合法性、摘要、来源、时间），旧记录从文件名解析。导入/银行转出记录不进入。
- **收藏**：银行和交换记录的详情里可收藏；格子显示星标；侧栏新增「收藏」盒子；状态保存在
  `%APPDATA%\pokeldn\pokemon\.favorites.json`。
- **清理记录**：交换记录工具栏的「清理记录」在确认后删除记录文件和 `.json`；仍在交换队列里的
  记录需要重新添加。
- **GitHub 加速**：设置新增加速卡片，可选直连或 `gh-proxy.com`；选中即生效并测速，绿/黄/红
  圆点表示延迟或不通。通过 `pokeldn/app/github_mirror.py` 与 `update._open` 作用于更新检查、
  下载、插件源和精灵图。
- **手机界面**：窄屏下设备/插件卡片按钮移到文字下方；关于页改用 `标签: 值`，不再截断。
- **Android**：应用名 `pokeldn`，包名使用官方的 `org.pokeldn.usbprobe`，版本名 `0.60.2`。
- **汉化包**：不再内置简繁中文包；可在「插件 → 来源」添加 `ZsyzLahz/pokeldn-zh-hans`
  安装简体或繁体包。手机端 Android 引导等中文修复保留（走语言包机制，缺词条回退英文）。
  程序内新增文案的英文默认值已改回英文，默认语言为英文、不启用任何插件。
- 详细版本记录：[docs/gee_changes.md](docs/gee_changes.md)。

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
