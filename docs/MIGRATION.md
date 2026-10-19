# 迁移与安装指南

## 包名变化

拆分后的发行包名为 `tpc-topology`，Python 导入名保持 `mesh_grid`、`topo_modeler`、`topo_templates`、`templates` 和 `tpc_toolkit`。不要再安装包含 TPC 全部旧组件的 `tpc-cst` 发行版来获得这里的模块；同一环境同时装新旧发行版可能导致文件覆盖，迁移时应在干净环境重建。

基础离线安装：

```powershell
python -m pip install .
```

DXF/几何、科学计算、YAML 和 CST 按需选择：

```powershell
python -m pip install '.[geometry,science,yaml]'
python -m pip install '.[cst]'
```

CST 使用前需安装匹配版本的 `cst-automation` 并配置本机 CST Studio Suite。`cst` extra 只声明 Python 包依赖，不能安装 CST 软件本身。

## 兼容边界

- `templates` 仍作为一个次版本周期 shim；新代码使用 `topo_templates`。
- `tpc_toolkit.curves` 和 `tpc_toolkit.s2p` 保留旧导入入口，但函数实现位于 `cst-automation`。使用这两个入口需安装其发行包；不使用数据分析时，基础拓扑路径与相区功能不需要通用包。
- 旧 `tpc_service` 与 `cst_mcp` 不再由 TPC 分发；改用 `cst-automation` 的通用服务/MCP，并注册 `topo_service` handler。
- 本地并行开发请在开发说明或私有虚拟环境中配置本地 editable 项目；发行元数据不保存 E:/、D:/ 绝对路径。

## 许可证和资源

迁入的 Python 实现保留原 MIT 许可与版权声明。未能确认来源/再分发资格的 CST/SAT 标准件及原始模型资源不包含在这个发行包中。
