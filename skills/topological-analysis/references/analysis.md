# 离线数据与扫描

[ResultReader](../../../topo_modeler/result_reader.py) 接受 `.cst` 路径或提供 `read_all_s_parameters(run_id=0)` 的对象。已有内存数据可用轻量适配器；每条曲线采用 `(频率 GHz, 复数幅度)` 点列，不能混入 dB 幅度：

```python
from topo_modeler.result_reader import ResultReader

class CurveSource:
    def __init__(self, data):
        self.data = data

    def read_all_s_parameters(self, run_id=0):
        return self.data

    def read_s_parameter(self, name, run_id=0):
        return self.data[name]

reader = ResultReader(CurveSource({
    'S2,1': [(110.0, complex(0.5)), (120.0, complex(0.25))],
}))
print(reader.value_at('S2,1', 110.0))  # 20*log10(0.5) = -6.0206 dB
```

频率单位由数据源确认再统一为 GHz；已有 dB 数据先按 `10**(dB/20)` 转成幅度。端口方向取自目标工程，不由文件名或偏置极性推断。`.cst` 路径读取需要外部 CST 结果 API；`resonances()` / `resonance_shift()` 和 `tpc_toolkit.curves/s2p` 需要 `cst-automation` 离线解析模块。

扫描的两种 runner 返回值不能混淆：

| 返回值 | 含义 |
|---|---|
| `ResultReader` 或兼容 reader | 对曲线执行 `metric_specs` 指标函数 |
| 字典，如 `{'S21@110': -6.02}` | 已提取完成的标量指标，不再执行 `metric_specs` |
| `.cst` 路径字符串 | 通过外部 CST 结果接口读取已有文件 |

下面只用合成曲线，输出目录 `out` 应由任务脚本给出工作区绝对路径：

```python
from pathlib import Path
from topo_modeler.config import example_config
from topo_modeler.scanner import ParameterScan, value_metric

out = Path.cwd() / 'tpc-analysis'
out.mkdir(parents=True, exist_ok=True)
scan = ParameterScan(
    example_config('straight_waveguide'), {'length': [8, 10]},
    runner=lambda point: reader, workdir=str(out),
    metric_specs={'S21@110': value_metric('S2,1', 110.0)},
)
print([(p.name, p.params) for p in scan.plan()])
scan.run()
assert len(scan.succeeded) == 2
scan.export_csv(str(out / 'scan.csv'))
scan.report(str(out / 'scan.html'))
```

这里两个扫描点复用同一合成曲线，验证汇总接口而非参数对性能的影响。真实 runner 必须把各点参数映射到各自结果；保留 `failed`、错误详情、运行身份和指标缺项。批处理接口见 [batch.py](../../../topo_modeler/batch.py)，结构化审计见 [audit.py](../../../topo_modeler/audit.py)。
