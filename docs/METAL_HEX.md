# 金属六边晶格直波导模块

## 10a 开槽叉形探针

```python
from pathlib import Path
from mesh_grid.metal_hex.fork_waveguide import ForkWaveguideSpec
from mesh_grid.metal_hex.fork_probe import ForkProbeSpec
from topo_templates.fork_waveguide import ForkWaveguide

probe = ForkProbeSpec(gap=.060, stub_length=.190, stub_width=.080, stub_distance=.192)
spec = ForkWaveguideSpec(x_periods=10, upper_rows=5, lower_rows=2, probe=probe)
device = ForkWaveguide(spec)
files = device.preview(Path('outputs/fork_waveguide').resolve())
```

dy=√3a/2，y=0 中心行只算一次；upper_rows=5/lower_rows=2 是裁剪边界的位置，不是完整行数量。默认上下边界分别通过原第 5/第 2 行中心，对应保留 4.5/1.5 行；a=.606 mm 时为 y=[−1.0496227894,2.6240569735] mm。调用 `spec.to_dict()` / `ForkWaveguideSpec.from_dict()` 保存和恢复。

探针默认尺寸（mm）：wide_width=.213938021932、neck_length=.270、taper_length=.780、fork_length=.320、arm_length=.312、arm_width=.050、gap=.060、stub_length=.190、stub_width=.080、stub_distance=.192、insertion=.012。gap 同时定义槽宽和叉口宽；两支臂和开路枝节上下对称，右探针是左探针关于 x=0 的镜像。W0 是基于 h=.1 mm、εr=3.78、t=0、底部连续参考地的准静态估计，实际材料、地面、频散与匹配尚需验证。

`device.build(app)` 只在调用者提供的干净 CST 工程提交参数化几何；不开启求解、不建立地或端口。离线几何前检包括支臂搭接与基板支撑；自动化测试使用平面几何解释器核对 CST 命令，不等于真实 CST 零厚度布尔读回。

当前默认采用用户于 2026-11-04 确认的居中晶格、左右镜像渐变铜面探针和 A—空气侧石英缩短方案。t=0；本次实现不运行真实 CST 或电磁求解。

## 快速使用

安装 `tpc-topology[geometry]` 后，无 CST 即可运行：

```python
from pathlib import Path
from mesh_grid.metal_hex import MetalHexSpec
from topo_templates.metal_hex import MetalHexStraight

spec = MetalHexSpec(layout='AB')  # 'AB'、'BA'、'A_air'
device = MetalHexStraight(spec)
geometry = device.geometry()
files = device.preview(Path('outputs/metal_waveguide').resolve())
print(geometry.summary())
```

PNG/SVG/JSON 按布局分别命名为 `metal_hex_ab.*`、`metal_hex_ba.*`、`metal_hex_a_air.*`。插件运行时选择用户工作区，不写入插件缓存。图使用实际多边形、等比例坐标；探针参数是已批准的可调初值，不表示阻抗匹配完成。

## 默认几何

| layout | y>0 | y<0 晶格 | 石英 Y 范围 / mm | 探针接触宽 Wt / mm | 探针中心 yf / mm |
|---|---|---|---|---|---|
| AB | A | B | [-3.636, 3.636] | 0.303 | 0 |
| BA | B | A | [-3.636, 3.636] | 0.100 | 0 |
| A_air | A | 无 | [-0.606, 3.636] | 0.100 | 0.050 |

默认晶格 X 范围 [-1.818,1.818]，两探针外端 X 坐标 ±3.210，基板 X 范围 [-3.513,3.513]。晶格、两端探针和基板沿 X 严格镜像。BA 只交换 A/B 图案半区；A_air 删除下半晶格，保留可调宽度的无晶格石英支撑。探针在晶格外侧的直颈可能跨越 y=0，不属于下半晶格；A_air 接触尖端从 y=0 接入上半 A 铜面。

铜面 z=0、石英 -h≤z≤0。地参考沿用调用者模板的设计；本模块不添加实体地板、电壁、端口或激励。P01/P02 是晶格界面节点，不是 CST 端口。

## 可调参数（长度均为 mm）

| Python 字段 | 默认 / 规则 | 含义 / CST 名 |
|---|---|---|
| lattice_constant | 0.606 | 晶格格距 a / a |
| substrate_thickness | 0.1 | 石英厚度 / h |
| metal_thickness | 0，仅支持铜面 | t |
| ring_inset | 0.04 | 内外六边形半径差 / d1 |
| pad_ratio | 0.5，范围 (0,1] | 原图案长度/外环半径 / k1 |
| x_periods | 6，正整数 | 晶格裁剪长度/a，非单元数 / nx |
| y_half_periods | 6，正整数 | 原晶格半区高度/a / ny |
| layout | AB | AB、BA、A_air，上下分区 |
| centered | True | 晶格及基板沿 x=0 居中 |
| probes_enabled | True | 双端镜像渐变探针，需要 centered=True |
| taper_length | None→2a=1.212 | 整段线性渐变长，含搭接段 / lt |
| neck_length | 0.200 | 输入端直颈长度 / ln |
| port_width | 0.200 | 直颈宽度；名字不表示已建立端口 / wp |
| tip_width | None→AB:a/2；其它:0.100 | 晶格接触端宽度 / wt |
| probe_insertion | 0.020 | 尖端进入晶格裁剪区的搭接长度 / li |
| probe_y | None→A_air:0.050；其它:0 | 两端探针共同 Y 中心 / yf |
| substrate_margin | None→a/2=0.303 | 探针外端以外的左右基板边距 / mg |
| air_substrate_width | None→A_air:a；其它:ny*a | A_air 界面到下侧石英边界距离 / wa |

None 的初值在创建 spec 时解析为具体数值，并写入 JSON；之后各长度独立可调。CST 派生量 r1=a/√3、p1=k1*r1。源阵列先在旧坐标系生成，再整体平移 sx=−(nx−1)*a/2，保持原晶格内部结构。左探针尖端 xt=−nx*a/2+li，渐变起点 xb=xt−lt，直颈外端 xe=xb−ln；右探针严格按 x→−x 镜像；基板半长 bx=−xe+mg。关闭探针时 bx=nx*a/2+mg。

`ring_inset` 是半径差，单环法向线宽是它乘 cos(30°)，共边铜带可更宽。原 notebook 的 l1→ring_radius、l2→ring_inset、l3/l1→pad_ratio、x1→x_periods、y1→y_half_periods；未用的 e1/e2/l4/x2 等不保留。l4 原注释不能当作新探针净间隙。

例：

```python
spec = MetalHexSpec(layout='A_air', taper_length=1.5, neck_length=.3,
                    port_width=.18, tip_width=.12, probe_y=.06,
                    probe_insertion=.015, substrate_margin=.2,
                    air_substrate_width=.35)
```

构造/几何生成拒绝非有限尺寸、非法内环/周期、非零 t、断开铜面或缺少基板支撑的探针。CST adapter 在任何建模写入前也执行接触和支撑预检。

## 几何与 JSON

`MetalHexGeometry` 包含局部单元 `unit_ring/unit_a/unit_b`，全局 `rings/phase_a/phase_b/core_metal`，`probe_left/probe_right`，全部铜面并集 `metal`，以及 `substrate/metal_extent`。metal_extent 是晶格裁剪包络，不含外侧探针。A_air 的 phase_b 为空，关闭探针时 probe_left/right 为空。

`summary()` 同时记录 core_metal_area_mm2 和含探针的 metal_area_mm2。默认 AB 两者约 9.319165634 和 9.996715627 mm²。bottom_blank 是基板下边界到全部铜面下边界的跨度；right_blank 是晶格右边界到基板右边界的距离，包含探针空间，不能当作外边距 mg。

```python
import json
saved = json.loads(files['json'].read_text(encoding='utf-8'))
restored = MetalHexSpec.from_dict(saved['spec'])
assert restored == spec
```

0.2 版只含旧字段的 JSON 由 from_dict 自动恢复为旧 notebook 放置方式、无探针、完整石英，避免悄悄改变历史设计。显式旧模型：`MetalHexSpec.legacy_notebook(layout='AB')`。新任务使用构造器；若用旧字段集合的字典表达新设计，应显式加 `centered=True`。原 notebook/模板只读，不纳入发行包。

## CST 接口与证据

```python
# app 由 cst-automation 会话流程提供；干净工程、长度 mm、地参考已审阅。
result = device.build(app, prefix='mh', component='metal_hex')
print(result['shapes'])
print(result['evidence'])
```

也可调用 `topo_modeler.builders.metal_hex.build_metal_hex(app,spec)`。仅提交参数化几何，使用当前公开 material=、subtract() 等接口；不创建会话、保存工程、配置边界/频率/求解器或运行求解。曲线、旋转和阵列保留表达式依赖，左右馈源采用参数化镜像轮廓。shapes 包含活动角色，A_air 无 phase_b，启用探针时包含 probe_left/right。返回证据是命令提交，CST 零厚度布尔、接触/合并和材料读回仍未实机验证。

工程参数是全局短名，prefix/component 不隔离它们；不同规格使用干净工程。改变 layout、centered、probes_enabled、或跨越 ny=1 时，用新 spec 在干净工程重生成；仅改旧历史参数不足以改变分支结构。

实际仿真模板仍遵循 [topological-modeling](../skills/topological-modeling/SKILL.md)：干净参数、fmin/fmax、时域频段裕量和读回。旧模板频段与 notebook 请求不同，旧 Zmin 电壁也不会自动生效。图形或 mock 不证明拓扑带隙、单向传输或阻抗匹配。

## 馈源设计来源

借鉴仓库硅基 feed.py 的“直颈+渐变”组织，重新实现 t=0 金属轮廓。平面微带馈电及 AB/BA 分别匹配参考 [Shi 等的公开预印本，图 3/4](https://arxiv.org/abs/2210.06995)，正式版本 DOI [10.1109/JLT.2023.3288342](https://doi.org/10.1109/JLT.2023.3288342)。本模块的探针尺寸取自用户批准草图，不是复制论文尺寸；论文 PDF 不打包。
