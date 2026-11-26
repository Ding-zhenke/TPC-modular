---
name: domain-wall-editor
description: Use when opening the interactive TPC domain-wall editor to click lattice points, draw branches, edit a saved path, or export the edited layout.
---

# 交互式域壁路径编辑器

用户要在三角晶格上点选域壁、画分支或继续编辑已保存的设计时，按[运行环境](../runtime.md)选择带 `geometry` 的 Python。按[编辑器指南](../../docs/PATH_EDITOR.md)启动本地服务，将 `--workspace` 指向本次设计目录，并向用户给出实际 URL 和停止方式。复用端口或停止服务前核对会话身份。

先在编辑器中确认晶胞参数及域壁可选点，再绘制路径、检查相区。保存 JSON 供下次编辑；有待处理的相区冲突时保存草稿，通过检查后按需导出毫米 DXF。用 Python 批量生成路径见[晶格与路径](../lattice-paths/SKILL.md)。
