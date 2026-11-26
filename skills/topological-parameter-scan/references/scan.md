# 扫描 runner 与结果汇总

按返回值选择指标处理方式。

| 返回值 | 含义 |
|---|---|
| `ResultReader` 或兼容 reader | 对曲线执行 `metric_specs` 指标函数 |
| 字典，如 `{'S21@110': -6.02}` | 已提取完成的标量指标，不再执行 `metric_specs` |
| `.cst` 路径字符串 | 通过外部 CST 结果接口读取已有文件 |

下面复用[曲线读取示例](../../topological-analysis/references/analysis.md)创建的合成曲线对象 `reader`，输出目录 `out` 应由任务脚本给出工作区绝对路径：

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
    required_metrics=['S21@110'],
)
print([(p.name, p.params) for p in scan.plan()])
scan.run()
assert len(scan.succeeded) == 2
scan.export_csv(str(out / 'scan.csv'))
scan.report(str(out / 'scan.html'))
```

这里两个扫描点复用同一合成曲线，验证汇总接口而非参数对性能的影响。真实 runner 必须把各点参数映射到各自结果；保留 `failed`、错误详情、运行身份和指标缺项。批处理接口见 [batch.py](../../../topo_modeler/batch.py)，结构化审计见 [audit.py](../../../topo_modeler/audit.py)。

`required_metrics` 适用于指标字典和 reader。缺少指定指标或值为 NaN、无穷大时，该点记入 `scan.failed`。默认空序列允许只执行、不提取指标的扫描。再次调用 `run()` 会重新评估各点，汇总只包含本次的指标和错误。
