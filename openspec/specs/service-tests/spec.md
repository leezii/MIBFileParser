# service-tests Specification

## Purpose
TBD - created by archiving change add-unit-tests. Update Purpose after archive.
## Requirements
### Requirement: API 测试框架配置

项目 MUST 配置 Flask API 测试框架，MUST 支持 HTTP 端点测试。

#### Scenario: 配置 pytest-flask 测试客户端

**Given** 项目使用 Flask Web 框架
**When** 在 `conftest.py` 中配置 pytest-flask
**Then** 提供 `client` fixture 用于发送 HTTP 请求
**And** 测试可以使用 `client.get()`, `client.post()` 等方法

#### Scenario: 测试前设置应用上下文

**Given** Flask 测试需要应用上下文
**When** 测试函数运行
**Then** pytest-flask 自动设置应用上下文
**And** 测试可以访问应用配置和资源

---

### Requirement: Flask API 端点测试（占位）

项目 MUST 为 Flask API 端点提供测试框架，MUST 支持端点测试。

*注意: 本提案第一阶段不包含 API 测试实现，仅预留规格。*

#### Scenario: 测试健康检查端点

**Given** 应用运行且存在 `/api/health` 端点
**When** 发送 GET 请求到 `/api/health`
**Then** 返回 200 状态码
**And** 响应包含健康状态信息

#### Scenario: 测试 MIB 列表 API

**Given** 应用运行且存在 `/api/mibs` 端点
**When** 发送 GET 请求到 `/api/mibs`
**Then** 返回 200 状态码
**And** 响应包含已加载的 MIB 列表

#### Scenario: 测试 MIB 查询 API

**Given** 应用运行且存在 `/api/mibs/<name>` 端点
**When** 发送 GET 请求到 `/api/mibs/SNMPv2-MIB`
**Then** 返回 200 状态码（如果 MIB 存在）
**And** 响应包含 MIB 树结构数据

#### Scenario: 测试节点搜索 API

**Given** 应用运行且存在 `/api/search` 端点
**When** 发送 GET 请求到 `/api/search?q=sysDescr`
**Then** 返回 200 状态码
**And** 响应包含匹配的节点列表

#### Scenario: 测试文件上传 API

**Given** 应用运行且存在 `/api/upload` 端点
**When** 上传有效的 MIB 文件
**Then** 返回 200 状态码
**And** 响应包含上传成功信息

#### Scenario: 测试 API 错误处理

**Given** API 端点存在输入验证
**When** 发送无效的请求数据
**Then** 返回 4xx 状态码
**And** 响应包含错误信息

---

### Requirement: 服务层测试（占位）

项目 MUST 为服务层提供单元测试框架，MUST 支持服务层测试。

*注意: 本提案第一阶段不包含服务层测试实现，仅预留规格。*

#### Scenario: 测试 DeviceService 设备管理

**Given** DeviceService 负责设备注册表管理
**When** 调用服务方法（如 `get_devices()`, `add_device()`）
**Then** 返回预期的设备数据
**And** 设备注册表文件正确更新

#### Scenario: 测试 MibService MIB 缓存

**Given** MibService 负责 MIB 解析和缓存
**When** 调用 `load_mib()` 方法加载 MIB
**Then** MIB 被正确解析
**And** MIB 被缓存以供后续使用
**And** 再次加载相同 MIB 时使用缓存

#### Scenario: 测试 TreeService 树操作

**Given** TreeService 负责树结构可视化
**When** 调用 `build_tree()` 方法
**Then** 返回正确的树结构数据
**And** 树结构适合前端渲染

---

