<p align="center">
  <img src=".github/assets/banner.png" alt="pokeldn：为 Nintendo Switch 上的宝可梦游戏提供 ESP32 本地无线工具" width="100%">
</p>

<p align="center">
  <a href="https://pokeldn.app"><img alt="Website" src="https://img.shields.io/badge/website-pokeldn.app-fd474d?style=flat-square"></a>
  <a href="https://discord.gg/PyvaVYnpXC"><img alt="Discord" src="https://img.shields.io/badge/discord-join-5865F2?style=flat-square&logo=discord&logoColor=white"></a>
  <a href="https://decryptu.github.io/pokeldn/"><img alt="Documentation" src="https://img.shields.io/badge/docs-decryptu.github.io%2Fpokeldn-3fa9f5?style=flat-square&logo=readthedocs&logoColor=white"></a>
  <img alt="Python 3.13" src="https://img.shields.io/badge/python-3.13-3fa9f5?style=flat-square&logo=python&logoColor=white">
</p>

# pokeldn

[English](README.md) | 简体中文

pokeldn 通过一块 USB 连接到电脑的 ESP32 开发板，与 Switch 和 Switch 2 上的零售版宝可梦游戏进行交换。
主机上不需要安装任何东西。

桌面应用支持 macOS（Apple 芯片和 Intel）、Windows 和 Linux。同一个应用也可以运行在 Android 上
（开发板插在手机的 USB 口），以及 iPhone 和 iPad 上（通过蓝牙连接开发板）。命令行工具从源码运行，
文档中描述了各游戏的本地无线协议。AI 工具帮助逆向分析了这些协议，并编写了部分代码。

## 支持的游戏

| | [FRLG](docs/frlg.md) | [LGPE](docs/lgpe.md) | [SwSh](docs/swsh.md) | [BDSP](docs/bdsp.md) | [PLA](docs/pla.md) | [SV](docs/sv.md) | [PLZA](docs/za.md) |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| 交换 | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| 在线交换 | ✓ | ○ | ○ | ○ | ○ | ✓ | ○ |
| 神秘礼物 | ✓ | ∅ | ✓ | ∅ | ∅ | ∅ | ∅ |
| 活动宝可梦 | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| 连接对战 | ✓ | ✗ | ✗ | ✗ | ∅ | ✗ | ✗ |
| 主机代码与存档读写 | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |

✓ 已在实机验证 · ○ 仅离线测试 · ✗ 未实现 · ∅ 本地无线不可用

FRLG：火红/叶绿 · LGPE：Let's Go 皮卡丘/伊布 · SwSh：剑/盾 ·
BDSP：晶灿钻石/明亮珍珠 · PLA：传说 阿尔宙斯 · SV：朱/紫 · PLZA：传说 Z-A

朱/紫还支持以访客身份参加[本地太晶团体战](docs/sv_raid.md)和
[联盟集友圈](docs/sv_union_circle.md)；剑/盾支持
[极巨团体战和极巨大冒险](docs/swsh_raid.md)，可以由电脑选择首领或传说的宝可梦来主持，也可以作为
主机方的搭档加入。剑/盾还可以通过电脑自己的网络，在其隐藏的[局域网模式](docs/swsh_session.md#lan-mode)
下进行交换、团体战和极巨大冒险，无需开发板即可加入或主持。活动宝可梦在 FRLG 和 SwSh 上通过神秘礼物
获得，在其他作品中则作为主机方交换的官方礼物送达
（[模拟神秘礼物](docs/gift_simulated.md)）。

## 开始使用

<img src=".github/assets/desktop-app.webp" alt="pokeldn 桌面应用正在为火红交换提供一只异色吉利蛋" width="100%">

你需要一块[受支持的 ESP32 开发板](docs/hardware_esp32.md#supported-boards)、一根 USB 数据线、
Switch 的 `prod.keys`，以及一台装有受支持游戏的 Switch 或 Switch 2。

1. 从 [Releases](https://github.com/Decryptu/pokeldn/releases) 或 [pokeldn.app](https://pokeldn.app) 下载应用。
2. 在「设置」中选择 `prod.keys`。
3. 连接开发板，在「设备」页面安装「无线」固件。
4. 选择游戏和工具，然后按照应用中的主机操作说明进行。

在手机上：

- **Android**：从 Releases 安装 `pokeldn-android-arm64.apk`，用 USB 数据线把 ESP32-S3、C3 或 C6，
  或带 CP210x USB 芯片的经典 ESP32 插到手机上
  （[Android 设置](docs/gui.md#android-setup-requirements)）。
- **iPhone 和 iPad**：用 AltStore 或 SideStore 安装 `pokeldn-ios.ipa`（应用的
  [AltStore 源](https://raw.githubusercontent.com/Decryptu/pokeldn/main/.github/altstore/source.json)）。
  先通过桌面应用的「设备」页面给开发板刷入一次**蓝牙无线**固件；之后开发板只需要 USB 供电
  （[iOS 设置](docs/gui.md#ios-setup)）。

平台说明：[首次启动](docs/gui.md#first-launch)、[Windows USB 驱动](docs/gui.md#windows-usb-drivers)、
[Linux 串口](docs/gui.md#linux-serial-ports)。

## 文档

| 主题 | 指南 |
|---|---|
| 命令行设置和游戏命令 | [使用说明](docs/usage.md) |
| 银行、宝可梦导入与转换 | [银行](docs/gui.md#the-bank) |
| 在线交换和 GTS | [在线交换](docs/online.md)、[GTS](docs/online.md#the-gts) |
| 制作和分享神秘礼物 | [礼物文件](docs/gifts.md) |
| 火红/叶绿存档备份与恢复 | [存档备份与恢复](docs/frlg_gift.md#save-backup-and-restore) |
| 控制器和宏 | [控制器](docs/gui.md#the-controller) |
| 安装或编写插件 | [插件](docs/plugins.md) |
| Windows USB Wi-Fi 适配器 | [ldnrs 设置](docs/hardware_adapters.md#windows-usb-wi-fi-through-ldnrs) |
| 开发板、固件和可选屏幕 | [ESP32 无线电](docs/hardware_esp32.md) |
| 从源码运行和构建桌面应用 | [桌面版构建](docs/gui.md#run-from-source) |
| 构建 Android 应用 | [Android 应用](examples/android/README.md) |
| 构建 iOS 应用（蓝牙无线电、AltStore） | [iOS 应用](examples/ios/README.md) |
| 代码结构、宝可梦合法性与测试 | [代码组织](docs/architecture.md) |
| 无线协议与逆向分析 | [文档索引](docs/index.md) |

文档也发布在 [decryptu.github.io/pokeldn](https://decryptu.github.io/pokeldn/)。

## 鸣谢

pokeldn 是 [MercuryEnigma/frlg-ldn-trade](https://github.com/MercuryEnigma/frlg-ldn-trade) 的 fork，
原作者是 [MercuryEnigma](https://github.com/MercuryEnigma)；后者又是
[tornadus/frlg-ldn-trade](https://github.com/tornadus/frlg-ldn-trade) 的 fork，原作者是
[tornadus](https://github.com/tornadus)，并有
[trowgundam](https://github.com/trowgundam) 的贡献。

本仓库的贡献者（GitHub 不会在 fork 上列出贡献者）：

- [Gr3nSkyDragon](https://github.com/Gr3nSkyDragon)：ESP32-S3 固件
- [ismailhasannnnnn](https://github.com/ismailhasannnnnn)：朱/紫太晶团体战的主持和加入，RaidPoint
  结构的逆向分析与重建，包括奖励编码和团体战启动压缩，以及主持团体战的奖励模板，含薄荷、对战道具、
  树果和进化道具的组合
- [easyworld](https://github.com/easyworld)：高波特率会话后的 ESP32 串口重连；语言包，用于翻译
  游戏名称、模块消息、工具帮助、文档及其页面标题、游戏选项和团体战搭档名称；语言包检查器；CJK
  工具提示；以及按显示语言显示游戏名称、礼物摘要、遭遇地点和初训家备注
- [capito27](https://github.com/capito27)：朱/紫活动太晶团体战；团体战查找器的奖励筛选、完整种子
  搜索、按奖励排序和尺寸标记筛选；太晶团体战 NPC 搭档（从 RaidPoint 抽取以及主持方的选择）；
  为接收存档制作的模拟神秘礼物；程序的弹窗；剑/盾官方活动中的 Pokémon HOME 礼物；太晶团体战首领的
  脚本化行动；传说 阿尔宙斯的训练家性别；仍在写入帧时对 ESP32 的鸣谢；USB 上传速度接近翻倍；
  以及朱/紫联盟集友圈访客：蓝之圆盘任务完成、Snacksworth 的传说宝可梦和自制的野外遭遇
- [DedHapp3n](https://github.com/DedHapp3n)：Android 应用中使用 CP210x USB 芯片的经典 ESP32 开发板
- [elsardine6k7](https://github.com/elsardine6k7)：宝可梦构建器中的亲密度、Showdown 配置和
  模拟神秘礼物队列
- [junkmailkeep](https://github.com/junkmailkeep)：礼物和交换编辑器中的神秘礼物精灵图与形态预览
- [MarcJa420](https://github.com/MarcJa420)：E32R40T 4 英寸屏幕构建、待机屏幕上的固件版本、
  开发板屏幕上的团体战和极巨大冒险大厅，以及超极巨化精灵图
- [axechaso](https://github.com/axechaso)：火红/叶绿异色超梦提升背后的精确 RNG 帧一击 A 键，
  以及插件 API 中的火红/叶绿 RNG
- [unlimitedcoder2](https://github.com/unlimitedcoder2)：[ldnrs](https://github.com/unlimitedcoder2/ldnrs)，
  可选无线电后端所支持的 Windows USB Wi-Fi 外部守护进程
- [kinnay](https://github.com/kinnay)：本项目所基于的 [LDN 库](https://github.com/kinnay/LDN)，
  以及 [NintendoClients wiki](https://github.com/kinnay/NintendoClients/wiki)
- [pokefirered](https://github.com/pret/pokefirered)：火红/叶绿的逆向工程，包括 Switch 移植版
- [GB-Link Team](https://github.com/GB-Link/GB-Link-Switch-LDN)：`vendor/gblink-cards/` 中的
  自制火红/叶绿神秘卡片（GPL-3.0）
- [xCyrusBR](https://github.com/xCyrusBR)：[TeraLoop-Bridge](https://github.com/xCyrusBR/TeraLoop-Bridge)、
  [SV-Past-Tera-Raid](https://github.com/xCyrusBR/SV-Past-Tera-Raid) 和
  [pokeldn-TeraLoop-](https://github.com/xCyrusBR/pokeldn-TeraLoop-)，朱/紫太晶团体战相关工作，
  包括团体战主持方等待主机的 Ready
- [Project Pokemon](https://github.com/projectpokemon)：应用下载的朱/紫团体战活动配送
  [EventsGallery](https://github.com/projectpokemon/EventsGallery)，以及每个活动的 pkNX 文本
- [Matcore962](https://github.com/Matcore962)：把宝可梦文件和游戏存档导入银行

## 代码签名政策

免费代码签名由 [SignPath.io](https://about.signpath.io) 提供，证书由
[SignPath Foundation](https://signpath.org) 提供。签名范围、团队角色和隐私政策见
[代码签名政策](https://decryptu.github.io/pokeldn/code_signing.html)页面。

## 许可证

代码以 AGPLv3 许可。该许可仅覆盖本仓库的代码，不覆盖其他内容。

pokeldn 是非官方粉丝项目，与 Nintendo、The Pokémon Company、Game Freak 或 Creatures 没有关联，
也未获得其认可或赞助。Pokémon、Nintendo Switch 及相关名称和角色是其所有者的商标。根据 AGPL
第 7(e) 条，本项目不授予使用这些商标或任何其他宝可梦知识产权的权利。

作者不赞成将 pokeldn 用于商业、推广或品牌活动，包括神秘礼物配送。这样做的人需自行负责取得所需权利。
