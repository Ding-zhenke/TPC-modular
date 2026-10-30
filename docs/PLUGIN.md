# TPC 插件

插件标识 `tpc`，本地市场标识 `tpc-local`，初始版本 `0.1.0`。一次安装可获得[六个 skills](../skills/README.md)：晶格路径、示意图、拓扑建模、器件模板、扫描分析、优化与等效介质。

## 安装

推荐用本仓库附带的市场目录安装。支持插件命令的 Codex 版本可执行：

```powershell
codex plugin marketplace add "<本仓库或解压后的市场根目录>"
codex plugin add tpc@tpc-local
codex plugin list --marketplace tpc-local --json
```

也可在桌面应用的插件目录里，从本地 `TPC Local` 来源安装 `TPC 光子晶体工具箱`。界面入口因版本而异，命令行返回的启用状态与技能缓存清单用于确认实际安装。安装后开新聊天；若界面尚未刷新，重启应用再检查。

插件代码、文档和六个技能一同进入插件缓存，不依赖原始 checkout。Python 依赖与 CST 环境不是插件安装器自动提供的；首次使用按[运行环境说明](../skills/runtime.md)检查或准备 Python。离线功能不需要 CST；实际 CST 建模/结果 API 仍依赖独立的 `cst-automation` 和本机 CST。

## 构建与分享

在仓库根目录执行：

```powershell
python -B scripts/build_plugin.py --output dist
```

输出 `dist/tpc-0.1.0.zip`，内部只有一个 `tpc/` 插件目录，含代码、技能、文档、许可证和验收脚本。解压后以其 `tpc/` 为市场根目录注册，再安装同一插件即可。发布包的市场配置是可移植相对路径，不带开发机路径。

打包器按目录与扩展名白名单选文件，不复制整个工作树；排除 `.git`、`work`、缓存、环境、工程大文件和机器配置。根 `plugin.json` 使用 Agent Plugins 清单，`.codex-plugin/plugin.json` 提供 Codex 兼容入口；技能唯一源位于 `skills/`。本插件没有 MCP 或自动启动钩子。

## 离线验收

先选择具备基础依赖及 `geometry,science,yaml` 的 Python。将 ZIP 解压到独立目录后执行：

```powershell
python -B "<解压目录>/tpc/scripts/plugin_runtime.py" --check --extras geometry,science,yaml
python -B "<解压目录>/tpc/scripts/verify_plugin.py" --output "<工作区>/tpc-plugin-check"
```

验收包含六个技能入口、三角路径、示意 PNG、六边晶格 DXF、功分器配置预检、合成 S 参数指标、两点扫描报告、极小连续优化和等效介质计算。输出 JSON 记录代码来源并确认未导入 CST。所有数值和图形均是接口验证例子。

## 更新与旧技能

修改后重新构建并解压到原市场目录，再用 `codex plugin add tpc@tpc-local` 刷新安装；随后开新聊天。市场目录是本地安装源，应保留。对外分享新版本时同时更新两个清单版本及 Python 包版本，并重新验证。

如果用户目录里已有 `lattice-paths`、`topological-modeling`、`topological-schematic` 独立副本，先比较差异，再备份后停用旧副本。插件内这三个名字保持兼容；用户独有规则不可直接丢弃。插件卸载与旧技能恢复分别处理，不清理用户工程或结果。

## 维护依据

- [OpenAI 插件打包规范](https://developers.openai.com/plugins/build/plugins)
- [桌面执行插件说明](https://developers.openai.com/plugins/deploy/desktop-only)
- [能力与证据记录](VALIDATION.md)
