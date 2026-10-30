# 模板入口

| 配置 `model.type` | 模板类 |
|---|---|
| `straight_waveguide` | `StraightWaveguide` |
| `unit_antenna` | `UnitAntenna` |
| `grin_lens_antenna` | `GRINLensAntenna` |
| `multiport_antenna` | `MultiPortAntenna` |
| `mzi_switch` | `MZISwitch` |
| `power_divider` | `PowerDivider` |

源代码见 [config.py](../../../topo_modeler/config.py) 和 [topo_templates](../../../topo_templates)。`accepted_fields(type)`、`field_help(type)` 查看配置字段，`example_config(type)` 获取当前实现的例子；保留用户参数与默认值来源。

在任务脚本中按[运行环境](../../runtime.md)设置导入路径后，可直接运行这个离线例子：

```python
from topo_modeler.config import example_config, template_from_config
from topo_modeler.preflight import validate_model_spec

cfg = example_config('power_divider')
check = validate_model_spec(cfg, check_paths=False, diagnose_cst=False)
assert check['ok'], check['errors']
kwargs = template_from_config(cfg, validate_only=True)
print(kwargs['_class'], check['effective'], check['field_sources'])
```

`check_paths=False` 只用于不检查本机工程路径的离线检查。准备实建时改为 `True` 并给真实模板和输出路径；`validate_only=True` 返回构造参数，不建实体。不在离线预检中读取模板 `app`。

审批完成、CST 环境就绪后，`template_from_config(cfg)` 创建模板对象，显式 `template.build_all()` 才执行建模；保存、求解按用户范围分别调用。不能仅凭 `buildable=True` 宣称 CST 已建成。功分器当前支持分路数为 2/3/4/6；单馈源结构的端口数不等于输出臂数，具体以[功分器实现](../../../topo_templates/power_divider.py)为准。
