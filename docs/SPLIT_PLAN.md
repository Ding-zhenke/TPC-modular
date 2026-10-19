# TPC 拆分实施计划

> 状态：已按用户授权执行。方案依据 Codex 聊天“规划 TPC 模块拆分”（`01a152f0-7441-7272-bcbb-9842c9f3246f`）和当前拆分总任务；计划与实现一并维护。

## 目标

把拓扑光子晶体的离线晶格/路径/相区/示意图、拓扑器件模板、拓扑专用建模与后处理独立成可安装的 TPC 项目。纯离线入口不加载 CST；CST 建模只在用户实际调用时连接 `cst-automation`。通用服务、曲线解析和 MCP 不在 TPC 发行包重复实现。

## 全局约束

- 原 TPC 迁移源只读；源 commit 为 `51e4a63d302f0deea58d2a2df349892087dbfe7`，其当前差异快照在忽略目录 `work/source-snapshot/`。
- `mesh_grid` 是晶格/离散几何，不是 CST 电磁求解网格。
- 发布名 `tpc-topology`；Python 导入名继续为 `mesh_grid`、`topo_modeler`、`topo_templates`、`templates`、`tpc_toolkit`。
- 基础安装只含离线必要依赖；CST、DXF/几何、科学与开发依赖分设 extras。发行元数据不得硬编码 E:/D: 或个人目录。
- 不新增 `cst_solver`、通用 `tpc_service`、`cst_mcp` 或 `em_enclosure` 包。
- `tpc_toolkit.curves/s2p` 只延迟委托 `cst_automation.curves/s2p`；导入 `tpc_toolkit` 不加载 GA 优化、绘图库或 CST。
- 离线测试、mock/预检、真实 CST readback、实际 solver 分开记录；不启动昂贵电磁求解。
- `templates` 兼容 shim 暂保留一个次版本周期；后续以弃用说明和迁移说明引导到 `topo_templates`。
- 不知来源的标准件资源不纳入本次 TPC 发布；不宣称取得制造或再分发许可。

## 文件与接口设计

| 路径/模块 | 职责与接口 |
|---|---|
| `mesh_grid/**` | 三角/六边晶格、坐标、相区、域壁、路径、阵列裁剪、几何辅助与示意图/DXF；公开导入保持原样。 |
| `topo_modeler/**` | 领域配置、预检、拓扑实体构造器、透镜/等效介质、扫描、拓扑结果读取与审计；包导入和 `TopoModeler()` 构造不能探测/初始化 CST。显式 CST 动作才解析通用后端。 |
| `topo_templates/**`、`templates/__init__.py` | 拓扑器件模板与一个发行周期兼容入口。 |
| `tpc_toolkit/**` | 保留拓扑 GA 和 effective-medium；顶层使用惰性 `__getattr__`/导入机制；`curves`/`s2p` 对应符号经 `cst_automation` 转发。 |
| `topo_service/**` | 领域 handler、schema/配置扫描和后处理适配。公共协议以 `cst-automation/docs/PUBLIC_API.md` 为准；文件尚未发布时，只完成协议无关实现并记录精确缺口，不构造虚假的注册成功。 |
| `pyproject.toml` | setuptools 独立构建；项目名 `tpc-topology`；`cst` extra 指定已确认的 `cst-automation` 发行版兼容范围；不依赖开发机路径。 |
| `skills/` | 每项技能有可发现的 `SKILL.md` 简短入口与按需 references；保留拓扑示意图规范、权威参数源和证据限制。 |

## 实施步骤与验收

### 1. 源状态、归属与接口冻结

- [x] 读取原拆分方案、源 `AGENTS.md`、源 `pyproject.toml`、包/skill/支持矩阵目录。
- [x] 记录 source HEAD、tracked diff、staged diff、工作树状态和未跟踪路径到忽略的 `work/source-snapshot/`；测试临时产物不迁移。
- [x] 建立逐文件/目录迁移表 `docs/MIGRATION_MAP.md`，保留有效拓扑实现，隔离通用 CST/服务。
- [x] 读取 `cst-automation/docs/PUBLIC_API.md` 并冻结真实 handler 接口；根据实际 `RunService.register_handler` 实现完成适配。

验收：源仓库 HEAD 与差异可审计；源目录未被写入；迁移表涵盖保留、排除、改写的代码/测试/docs/skills。

### 2. 独立包与离线拓扑层

- [x] 迁入 `mesh_grid`、`topo_modeler`、`topo_templates`、受限 `templates` shim、`tpc_toolkit` 与对应测试。
- [x] 让 `TopoModeler` 的构造/配置/预检和离线方法不触发 CST。CST 连接采用延迟依赖入口，并在缺失时给安装指引。
- [x] 将拓扑域壁/扫描/结果后处理从旧 `CstBackend` 中分离为 `topo_service`，不复制通用任务状态/队列/MCP。
- [x] 修正 `tpc_toolkit` 导入副作用；实现 `curves`、`s2p` 的兼容转发，不复制解析算法。
- [x] 添加可移植路径解析，删除指向开发机或用户目录的发行时代码依赖。

验收：隔离环境无 CST 与无 cst-automation 时，离线 imports、路径/相区、配置校验、绘图 API 可运行；CST 动作只在显式调用时给清楚错误或成功连接。导入跟踪证明通用/拓扑依赖边界成立。

### 3. 包装、资源和技能

- [x] 创建独立 `pyproject.toml`：离线基础依赖与 `geometry`、`science`、`yaml`、`cst`、`dev` extras 分离。
- [x] 确认 MIT 许可证并保留随源包提供的许可证文件。
- [x] 建立 `topological-modeling`、`topological-schematic`、`lattice-paths` 技能，统一保存在根目录 `skills/`，由 `AGENTS.md` 指引读取。
- [x] 增加 README、迁移指南、API/支持矩阵、验证记录、CONTRIBUTING 和离线 CI。

验收：wheel/sdist 清单不含通用服务、CST 驱动、MCP、pycache、原实验资源或 `.venv`；干净环境安装只靠发行包运行，不依赖源目录或 `PYTHONPATH`。

### 4. 协议集成、审阅、提交与发布

- [x] 根据公共 API 实现拓扑 handler 注册；在隔离 venv 安装 TPC 与 cst-automation 实际 wheel，使用 FakeBackend 验证 RunService 注册与 solve handler 分派。
- [x] 跑迁入相关离线测试、隔离 wheel 安装、发行清单审查和本地构建；真实 CST readback/求解仍独立标为未验证。
- [x] 审阅 diff、归属/许可、未跟踪内容、git status 后本地提交。
- [x] 确认提交仅留在本地；GitHub 创建/推送由主会话统一负责。
- [x] 记录 origin 为 `TPC-modular`；提交 SHA 以实际 Git commit 输出为准。

验收：可复现命令和准确结果均在 `docs/VALIDATION.md`；包元数据/文件清单独立；跨包状态真实；本地提交可读；远程状态未验证前不写“已发布”。

## 风险与复核点

- 旧 `TopoModeler` 会在构造或方法调用中隐式触发 CST；需区分几何规则/预检 API 与实体构造 API，避免把只改导入延迟误当离线可用。
- 模板模块导入 `TopoModeler`，但对象构造才需要 CST；验证 import 与 instance/create 两个层级。
- 旧 `tpc_toolkit.__init__` 会导入 `curves`、`effective_medium`、GA 和 `s2p`；兼容属性懒加载须覆盖 `from tpc_toolkit import ...` 用法。
- 插件技能 frontmatter 与源技能正文可能含跨仓库通用 CST 指引；保留拓扑流程、去除 CST 通用手册副本。
- `cst-automation` 公共协议已读取；handler 注册与公开参数查询 API 已按实际代码联调。CST 实机操作仍待目标机器验证。
- 旧模板的 CST/SAT 外部资源路径可能依赖本机；没有来源/许可证清晰度的二进制资源不打包。

## 当前状态

计划已由本次用户明确授权直接执行。代码、离线验证、制品检查和跨包 fake-backend 分派完成；本地提交由本次执行创建。GitHub 创建/推送由主会话统一执行。真实 CST readback、几何 rebuild 和 solver 不属于已验证能力。
