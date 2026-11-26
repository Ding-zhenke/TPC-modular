# 已有曲线读取

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

内存数据源使用 `reader.export_csv(path, in_db=False)` 导出复数，每条曲线有 `_re`、`_im` 两列。合写一个 CSV 时，各曲线的频率序列需一致。
