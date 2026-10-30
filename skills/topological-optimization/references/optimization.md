# 优化接口

入口见 [optimizer.py](../../../topo_modeler/optimizer.py)。连续变量可用 `(下限, 上限)` 或 `(下限, 上限, 'int')`；目标函数接收按变量顺序排列的基因列表，返回标量。默认 `maximize=True`；最小化损失需显式 `maximize=False`。

```python
from topo_modeler.optimizer import GeneticOptimizer, continuous_variables

opt = GeneticOptimizer(
    continuous_variables({'length': (10, 30, 'int')}),
    evaluate=lambda genes: (genes[0] - 18) ** 2,
    maximize=False, population_size=4, generations=3, seed=7,
)
result = opt.run()
assert 10 <= result.best_params['length'] <= 30
assert result.improved
assert result.evaluations <= 12
print(result.best_params, result.best_fitness, result.seed, result.history)
```

这是演示接口的数学目标函数，`length` 无器件单位含义。固定 seed 便于复现；该小预算不保证找到 18。`opt.report(result, path=绝对输出路径)` 导出 HTML 优化记录。

| 任务 | 入口与条件 |
|---|---|
| 连续实数/整数参数 | `continuous_variables(spec)`；种群至少 2，代数至少 1 |
| 二值晶格图案 | `binary_variables(n_bits, shape=(rows, cols))`；位数等于行列乘积，种群至少 4，按成对交叉使用偶数种群 |
| 二值原始算子 | [ga_optimizer.py](../../../tpc_toolkit/ga_optimizer.py)，通常通过统一优化器调用 |
| 等效介电常数/折射率 | [effective_medium.py](../../../tpc_toolkit/effective_medium.py) 的 `effective_permittivity(ep1,s1,ep2,s2)`、`permittivity_to_refractive_index(ep)` |
| 透镜参数到几何 | [lens.py](../../../topo_modeler/builders/lens.py) 的规格、环孔计算；实际建模另走 CST |

二值模式共享 NumPy 全局随机状态，seed 要记录；避免在同一进程并发运行相互干扰的二值优化。原始 `selection()` 有固定种群假设，统一优化器没有调用它。目标函数失败、非有限值或无法收敛的真实求解不能作为有效器件最优结果。按[证据边界](../../topological-modeling/references/evidence.md)报告。
