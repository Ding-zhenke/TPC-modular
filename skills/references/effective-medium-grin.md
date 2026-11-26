# 等效介质与 GRIN 透镜孔阵列

## 从孔面积估算有效折射率

考虑等厚、每个晶胞一个贯穿空气孔的模型。取晶胞面积 `S_cell`、孔面积 `S_air`，空气填充率为 `S_air / S_cell`。所有面积使用相同单位，并检查 `0 ≤ S_air ≤ S_cell`、`S_cell > 0`。正六边形孔的外接圆半径等于边长；晶胞的中心间距和孔的边长分别传给下表对应函数。

| 计算 | 输入及返回值 |
|---|---|
| 晶胞与孔的面积 | `hex_area_from_lattice(L)` 用相邻晶胞中心距；`hex_area_from_side(r)` 用正六边形孔边长。 |
| 两相面积加权 | `effective_permittivity(1, S_air, eps_host, S_cell - S_air)`，末项为剩余基质面积。 |
| 空气孔的 Maxwell–Garnett 型估算 | `ep_cal_air(1, S_air, eps_host, S_cell)`，末项为整个晶胞面积。 |
| 折射率 | 对非磁性、实数正介电常数，`permittivity_to_refractive_index(eps_eff)` 返回其平方根。 |
| 焦点光程差对应的相位 | `cal_phi(r, fp, lambda1)` 的径向距离、焦距与工作波长同单位，结果为取模后的角度，范围为 [0°, 360°)。 |

优化时记录所选混合公式、材料介电常数和填充率，使同一目标折射率下的候选孔尺寸可复算。[等效介质函数实现](../../tpc_toolkit/effective_medium.py)

## 从 GRIN 模板计算孔尺寸与折射率分布

以下离线例子使用 `GRINLensAntenna` 的示例默认几何和假设基质介电常数 12。换成实际设计时，将目标配置传给模板，并填入相应频率的材料参数。按[运行环境](../runtime.md)选带 `geometry` 的 Python。

```python
from topo_templates.grin_lens_antenna import GRINLensAntenna
from topo_modeler.builders.lens import build_grin_lens_holes
from tpc_toolkit.effective_medium import (
    ep_cal_air, hex_area_from_lattice, hex_area_from_side,
    permittivity_to_refractive_index,
)

lens = GRINLensAntenna(lens_method="generate")
spec = lens.make_lens_spec()
holes = build_grin_lens_holes(spec)
cell_area = hex_area_from_lattice(spec.a2)
air_area = hex_area_from_side(holes.radius)
assert ((0 < air_area) & (air_area < cell_area)).all()
index = permittivity_to_refractive_index(ep_cal_air(1, air_area, 12, cell_area))
# 每行依次为孔心 x、y、孔外接圆半径（mm）及局部有效折射率估计
rows = list(zip(holes.x, holes.y, holes.radius, index))
print(len(rows), rows[0])
```

- **椭圆渐变孔阵列**使用 `generate`。实际孔心间距为 `spec.a2 = a / ratio`，内外孔半径为 `r1_0 / ratio` 和 `r2_0 / ratio`。孔半径沿椭圆等距线分段线性变化。示例直接读取计算后的半径，保留每个孔的位置；几何自查可调用 `holes.run_self_checks()`。
- **六边形分层环透镜**使用 `insitu`。离线调用 `lens.make_lens_ring()` 得到默认第一象限的孔心、距离及 `radius_expr`。内区采用固定半径，外区按距离渐变；选取层数时需满足 `n_layers * a2 > d0`。引用该路线的孔数时注明象限范围。
- **已有孔阵列 DXF**使用 `dxf` 并提供 `lens_dxf`。若需估算这份版图的填充率，应使用文件中的实际孔形和相应晶胞面积。

上述折射率为局部均匀化估计。评价离散透镜的聚焦性能时，使用目标频率的场分布提取焦点和焦斑。[透镜几何实现](../../topo_modeler/builders/lens.py) · [GRIN 天线模板](../../topo_templates/grin_lens_antenna.py)
