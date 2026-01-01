# flask-api-tests Specification

## Purpose
TBD - created by archiving change add-service-and-api-tests. Update Purpose after archive.
## Requirements
### Requirement: 核心 API 端点测试覆盖

Flask API 核心端点 MUST 有完整的测试覆盖，测试覆盖率 MUST 达到 80% 以上。

#### Scenario: 测试 MIB 列表和详情端点

**Given** Flask app context 已设置，MIB 数据已准备
**When** 测试 `GET /api/mibs` 和 `GET /api/mibs/<name>`
**Then** MUST 验证成功的响应（200 OK）
**And** MUST 验证响应 JSON 格式和字段
**And** MUST 验证错误响应（404 Not Found）
**And** MUST 验证查询参数 `include_data` 处理

#### Scenario: 测试 MIB 树结构端点

**Given** Flask app context 已设置，MIB 数据已准备
**When** 测试 `GET /api/mibs/<name>/tree`
**Then** MUST 验证树结构返回正确
**And** MUST 验证 `format` 参数处理（d3, flat）
**And** MUST 验证 `include_stats` 参数处理
**And** MUST 验证 404 错误处理

#### Scenario: 测试缓存管理端点

**Given** Flask app context 已设置，MIB 数据已缓存
**When** 测试 `POST /api/mibs/<name>/refresh` 和 `POST /api/cache/clear`
**Then** MUST 验证缓存刷新成功
**And** MUST 验证缓存清除成功
**And** MUST 验证 404 和 500 错误处理

---

### Requirement: 搜索和查询 API 测试覆盖

搜索和查询 API MUST 有完整的测试覆盖，测试覆盖率 MUST 达到 75% 以上。

#### Scenario: 测试节点搜索端点

**Given** Flask app context 已设置，MIB 数据已准备
**When** 测试 `GET /api/search?q=`
**Then** MUST 验证搜索结果正确
**And** MUST 验证查询参数 `q`, `mib`, `limit`, `match_type` 处理
**And** MUST 验证空查询和特殊字符处理
**And** MUST 验证 400 错误（缺少查询参数）

#### Scenario: 测试 OID 查询端点

**Given** Flask app context 已设置，节点数据已准备
**When** 测试 `GET /api/node/<oid>`
**Then** MUST 验证节点查询正确
**And** MUST 验证跨 MIB 查询功能
**And** MUST 验证 404 错误（不存在的 OID）

#### Scenario: 测试统计信息端点

**Given** Flask app context 已设置
**When** 测试 `GET /api/statistics`
**Then** MUST 验证统计信息返回
**And** MUST 验证统计数据准确性

---

### Requirement: 上传 API 测试覆盖

文件上传 API MUST 有完整的测试覆盖，测试覆盖率 MUST 达到 75% 以上。

#### Scenario: 测试单文件上传

**Given** Flask app context 已设置，临时文件已准备
**When** 测试 `POST /api/upload` 上传单个文件
**Then** MUST 验证文件上传成功
**And** MUST 验证文件存储到正确路径
**And** MUST 验证解析成功
**And** MUST 验证 200 响应

#### Scenario: 测试多文件上传和错误处理

**Given** Flask app context 已设置
**When** 测试多文件上传和错误情况
**Then** MUST 验证多文件上传处理
**And** MUST 验证文件类型验证
**And** MUST 验证文件大小限制
**And** MUST 验证上传错误处理（400, 500）

---

### Requirement: 注释 API 测试覆盖

注释管理 API MUST 有完整的测试覆盖，测试覆盖率 MUST 达到 80% 以上。

#### Scenario: 测试注释 CRUD 端点

**Given** Flask app context 已设置，注释数据已准备
**When** 测试注释 API 端点
**Then** MUST 验证 `GET /api/annotations` 获取所有注释
**And** MUST 验证 `GET /api/annotations/<oid>` 获取单个注释
**And** MUST 验证 `POST /api/annotations` 添加注释（201）
**And** MUST 验证 `PUT /api/annotations/<oid>` 更新注释
**And** MUST 验证 `DELETE /api/annotations/<oid>` 删除注释

#### Scenario: 测试注释请求验证

**Given** Flask app context 已设置
**When** 测试注释 API 请求验证
**Then** MUST 验证请求体 JSON 格式验证
**And** MUST 验证必填字段验证
**And** MUST 验证 400 错误响应

---

### Requirement: 主页和辅助路由测试覆盖

主页和辅助路由 MUST 有测试覆盖，测试覆盖率 MUST 达到 70% 以上。

#### Scenario: 测试页面渲染

**Given** Flask app context 已设置
**When** 测试主页和辅助路由
**Then** MUST 验证 `GET /` 仪表板页面渲染（200）
**And** MUST 验证 `GET /mib/<name>` MIB 查看页面渲染
**And** MUST 验证 `GET /oid/<oid>` OID 查看页面渲染
**And** MUST 验证模板上下文数据

---

### Requirement: pytest-flask 使用要求

所有 API 测试 MUST 使用 pytest-flask 的 client fixture。

#### Scenario: 使用 pytest-flask client

**Given** Flask app 和 client fixtures 已配置
**When** 编写 API 测试
**Then** MUST 使用 `client` fixture 发送 HTTP 请求
**And** MUST 使用 `client.get()`, `client.post()` 等方法
**And** MUST 验证 `response.status_code`
**And** MUST 验证 `response.get_json()`
**And** MUST 使用 `@pytest.mark.api` 标记

---

