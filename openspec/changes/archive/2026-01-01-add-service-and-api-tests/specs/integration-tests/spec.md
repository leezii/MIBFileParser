# Capability: 集成测试

## ADDED Requirements

### Requirement: 服务层集成测试

服务层 MUST 与真实组件进行集成测试。

#### Scenario: MibService 与解析器集成

**Given** 临时存储目录已创建，真实 MIB 文件已准备
**When** 初始化 MibService 并加载 MIB 文件
**Then** MUST 验证与解析器的集成正常
**And** MUST 验证 MIB 文件成功解析
**And** MUST 验证数据存储到正确位置
**And** MUST 标记为 `@pytest.mark.integration`

#### Scenario: MibService 与文件系统集成

**Given** 临时目录已创建（tmp_path）
**When** MibService 读写 MIB 数据
**Then** MUST 验证文件读写操作正确
**And** MUST 验证文件存储到正确路径
**And** MUST 验证缓存文件创建

#### Scenario: DeviceService 与 MibService 集成

**Given** 临时存储已创建，服务已初始化
**When** DeviceService 创建设备，MibService 为设备加载 MIB
**Then** MUST 验证设备注册表更新
**And** MUST 验证 MIB 数据与设备关联
**And** MUST 验证多服务协作正确

#### Scenario: 服务与设备注册表集成

**Given** 临时存储已创建
**When** DeviceService 操作设备
**Then** MUST 验证设备注册表 JSON 读写
**And** MUST 验证注册表数据一致性
**And** MUST 验证注册表版本管理

---

### Requirement: API 端到端测试

API MUST 有端到端的集成测试，覆盖完整用户流程。

#### Scenario: 完整上传流程

**Given** Flask app 已启动，临时存储已创建
**When** 用户上传 MIB 文件 → 解析 → 查询
**Then** MUST 验证 `POST /api/upload` 上传成功
**And** MUST 验证文件保存到存储
**And** MUST 验证 `GET /api/mibs` MIB 在列表中
**And** MUST 验证 `GET /api/mibs/<name>` MIB 详情正确
**And** MUST 验证 `GET /api/mibs/<name>/tree` 树结构正确
**And** MUST 标记为 `@pytest.mark.integration`

#### Scenario: MIB 查询流程

**Given** Flask app 已启动，MIB 数据已加载
**When** 用户查询 MIB 列表 → 详情 → 树形结构
**Then** MUST 验证 API 端点返回正确数据
**And** MUST 验证数据格式一致
**And** MUST 验证关联查询正确

#### Scenario: 搜索流程

**Given** Flask app 已启动，MIB 数据已加载
**When** 用户搜索节点 → 获取详情
**Then** MUST 验证 `GET /api/search?q=` 搜索结果正确
**And** MUST 验证 `GET /api/node/<oid>` 节点详情正确
**And** MUST 验证搜索参数处理

#### Scenario: 注释管理流程

**Given** Flask app 已启动，节点数据已加载
**When** 用户添加 → 查询 → 更新 → 删除注释
**Then** MUST 验证 `POST /api/annotations` 添加成功
**And** MUST 验证 `GET /api/annotations/<oid>` 查询正确
**And** MUST 验证 `PUT /api/annotations/<oid>` 更新成功
**And** MUST 验证 `DELETE /api/annotations/<oid>` 删除成功

#### Scenario: 错误流程和恢复

**Given** Flask app 已启动
**When** 用户执行失败操作（上传失败 → 错误响应 → 恢复）
**Then** MUST 验证错误响应正确（400, 404, 500）
**And** MUST 验证错误消息清晰
**And** MUST 验证系统状态一致

---

### Requirement: 集成测试隔离要求

集成测试 MUST 保持测试间的隔离。

#### Scenario: 独立临时目录

**Given** 集成测试开始前
**When** 初始化测试环境
**Then** MUST 为每个测试创建独立的临时目录
**And** MUST 使用 `tmp_path` fixture
**And** MUST 在测试完成后清理所有临时文件

#### Scenario: 测试状态清理

**Given** 测试执行中
**When** 测试完成
**Then** MUST 清理所有创建的文件和目录
**And** MUST 重置服务状态
**And** MUST 不影响其他测试

#### Scenario: 独立运行能力

**Given** 任何集成测试
**When** 单独运行该测试
**Then** MUST 不依赖其他测试的状态
**And** MUST 可以独立运行
**And** MUST 结果稳定可重复

---

### Requirement: 集成测试性能要求

集成测试 MUST 在合理时间内完成。

#### Scenario: 测试执行时间

**Given** 集成测试套件
**When** 运行测试
**Then** MUST 每个测试在 10 秒内完成
**And** MUST 整个套件在 3 分钟内完成

#### Scenario: 慢速测试标记

**Given** 可能慢速的集成测试
**When** 编写测试
**Then** MUST 标记为 `@pytest.mark.slow`
**And** MUST 可以通过 `pytest -m "not slow"` 排除

---

### Requirement: 测试数据和 Fixtures 要求

集成测试 MUST 使用真实的测试数据。

#### Scenario: 使用真实 MIB 文件

**Given** 测试 fixtures 目录
**When** 运行集成测试
**Then** MUST 使用 `tests/fixtures/mibs/` 中的真实 MIB 文件
**And** MUST 包含各种 MIB 类型（简单、表格、嵌套）

#### Scenario: 测试环境初始化

**Given** 集成测试开始
**When** 初始化测试环境
**Then** MUST 使用 fixtures 初始化测试环境
**And** MUST 提供辅助函数设置测试场景
**And** MUST 验证环境初始化成功

---

### Requirement: 测试标记和组织要求

集成测试 MUST 使用 pytest 标记进行组织。

#### Scenario: 使用 integration 标记

**Given** 集成测试文件
**When** 编写集成测试
**Then** MUST 使用 `@pytest.mark.integration` 标记
**And** MUST 可以通过 `pytest -m integration` 运行

#### Scenario: 测试文件组织

**Given** 测试目录结构
**When** 组织集成测试
**Then** MUST 位于 `tests/integration/` 目录
**And** MUST 包含 `test_service_integration.py`
**And** MUST 包含 `test_api_e2e.py`

---

## Notes

### 测试类型

- **服务集成测试**: 测试服务与解析器、存储的真实交互
- **API E2E 测试**: 测试完整的用户请求流程
- **错误流程测试**: 测试错误恢复和边界情况

### 测试环境

- 使用 `tmp_path` fixture 创建临时存储目录
- 使用真实的 MIB 文件进行解析
- 使用真实的 Flask app（非 mock）
- 每个测试独立初始化和清理

### 测试场景示例

**服务集成场景**:
1. MIB 加载流程: DeviceService 创建设备 → MibService 加载 MIB → 验证数据
2. 多服务协作: 多个服务协作完成复杂操作

**API E2E 场景**:
1. 完整上传流程: 上传 → 验证 → 查询 → 查看树结构
2. 搜索和查询流程: 搜索 → 获取详情 → 添加注释 → 验证

---

**规格版本**: 1.0
**创建日期**: 2026-01-01
**状态**: 📝 待审批
