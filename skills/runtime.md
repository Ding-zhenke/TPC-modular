# 插件代码与 Python 环境

从当前 `SKILL.md` 向上两级得到插件根目录 `PLUGIN_ROOT`（含 `plugin.json`、`mesh_grid/`、`scripts/`）。安装后使用当前加载技能的位置，不能假定原仓库路径或当前工作目录。源码与技能随同一个插件分发。

先选已有 Python 3.9+ 环境，执行只读检查；把下面的绝对路径替换成当前插件真实位置：

```powershell
python -B "<PLUGIN_ROOT>/scripts/plugin_runtime.py" --check --extras geometry,science,yaml
```

按任务选 extra：DXF/裁剪为 `geometry`，科学计算为 `science`，YAML 文件为 `yaml`；不用则省略。检查在独立进程实际导入依赖并核对最低版本；JSON 的 `ready` 表示是否就绪，失败时 `errors` 给出原因且命令返回非零。若环境不足，按当前任务授权准备独立环境，位置选在用户工作区的运行目录或用户环境目录，必须在插件目录之外：

```powershell
python -B "<PLUGIN_ROOT>/scripts/plugin_runtime.py" --prepare --venv "<RUNTIME_DIR>/tpc-venv" --extras geometry,science,yaml
```

这一步只安装公开 Python 依赖，不安装或连接 CST。返回 JSON 中的 `python` 是后续使用的解释器。插件安装本身不会自动安装 Python 依赖。网络不可用时保留现有环境并报告缺失包，可用本地 wheel 安装相同依赖。

任务脚本存放在用户工作区；在脚本开头以当前实际插件路径加入导入搜索路径：

```python
import sys
from pathlib import Path

PLUGIN_ROOT = Path(r"<当前加载的插件根目录>")
sys.path.insert(0, str(PLUGIN_ROOT))
```

然后用选定解释器的 `-B` 运行脚本，工作目录保持用户工作区；所有输出给工作区绝对路径。这样不会把任务结果或字节码写进插件缓存，也不要求全局安装本库。

完整离线冒烟入口：`python -B "<PLUGIN_ROOT>/scripts/verify_plugin.py" --output "<WORKSPACE>/tpc-check"`。例子中的参数和合成数据只验证接口，不是器件设计依据或真实仿真结果。

实际 CST 操作需要单独可用的 `cst-automation` 和本机 CST Python API。`tpc_toolkit.curves/s2p`、`ResultReader.resonances/resonance_shift` 也依赖通用包的离线解析模块。不要在插件内复制通用 CST 服务或把解析依赖误报成需要启动求解器。
