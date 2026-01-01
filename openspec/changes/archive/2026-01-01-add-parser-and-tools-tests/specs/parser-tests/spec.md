# Capability: Parser Tests

## ADDED Requirements

### Requirement: MibParser 初始化测试

`MibParser` 类的初始化方法 MUST 有完整的单元测试，MUST 确保各种配置选项正确处理。

#### Scenario: 使用默认参数初始化解析器

**Given** 测试创建 MibParser 实例
**When** 不传任何参数
**Then** 解析器使用默认配置成功创建
**And** mib_sources 设置为默认路径
**And** resolve_defaults 设置为 True

#### Scenario: 使用自定义 MIB 源初始化

**Given** 提供自定义 MIB 源路径列表
**When** 使用这些路径创建 MibParser
**Then** mib_sources 设置为提供的路径
**And** 解析器可以从这些路径加载 MIB

#### Scenario: 禁用依赖解析初始化

**Given** 设置 resolve_dependencies=False
**When** 创建 MibParser
**Then** dependency_resolver 为 None
**And** 解析器不会自动解析依赖

---

### Requirement: MIB 文件解析测试

MibParser 的核心解析方法 MUST 有完整的测试覆盖，MUST 确保能正确解析各种 MIB 文件。

#### Scenario: 解析单个 MIB 文件成功

**Given** 存在有效的 MIB 文件
**And** 文件可以成功编译
**When** 调用 `parse()` 方法
**Then** 返回 MibData 对象
**And** MibData 包含解析的节点
**And** 节点数据正确

#### Scenario: 解析包含依赖的 MIB 文件

**Given** MIB 文件导入其他 MIB
**And** 依赖的 MIB 存在于源路径中
**When** 调用 `parse()` 方法
**Then** 自动解析依赖的 MIB
**And** 返回完整的 MibData 对象
**And** 包含所有依赖的节点

#### Scenario: 解析失败时抛出异常

**Given** MIB 文件格式错误
**Or** MIB 文件不存在
**When** 调用 `parse()` 方法
**Then** 抛出适当的异常
**And** 异常信息清晰说明错误原因

#### Scenario: 已解析的 MIB 使用缓存

**Given** MIB 文件已被解析过
**When** 再次调用 `parse()` 方法解析相同文件
**Then** 从缓存返回结果
**And** 不重复解析文件

---

### Requirement: MIB 查询方法测试

MibParser 的查询方法 MUST 有完整的测试，MUST 确保能正确查询已加载的 MIB 数据。

#### Scenario: 查询已加载的 MIB

**Given** MIB 已成功加载
**When** 调用 `get_mib_data(mib_name)`
**Then** 返回对应的 MibData 对象
**And** 对象包含完整的数据

#### Scenario: 查询不存在的 MIB

**Given** MIB 未加载
**When** 调用 `get_mib_data(mib_name)`
**Then** 返回 None
**Or** 抛出 KeyError（根据实现）

#### Scenario: 获取所有已加载 MIB 名称

**Given** 已加载多个 MIB
**When** 调用 `get_all_mib_names()`
**Then** 返回所有 MIB 名称列表
**And** 列表包含所有已加载的 MIB

#### Scenario: 检查 MIB 是否已加载

**Given** MIB 已加载
**When** 调用 `is_mib_loaded(mib_name)`
**Then** 返回 True

**Given** MIB 未加载
**When** 调用 `is_mib_loaded(mib_name)`
**Then** 返回 False

---

### Requirement: 依赖解析集成测试

MibParser 与 MibDependencyResolver 的集成 MUST 有测试，MUST 确保依赖解析正确工作。

#### Scenario: 解析器使用依赖解析器

**Given** MibParser 配置了 resolve_dependencies=True
**When** 解析包含导入的 MIB 文件
**Then** 调用 MibDependencyResolver 解析依赖
**And** 按正确顺序加载依赖

#### Scenario: 处理循环依赖

**Given** MIB 文件存在循环依赖
**When** 尝试解析
**Then** 检测到循环依赖
**And** 抛出适当异常或处理循环

---

## Notes

### 测试策略

- **使用 mock**: pysmi 编译器、文件系统使用 mock
- **测试数据**: 使用第一阶段的测试 MIB 文件
- **隔离性**: 每个测试独立，不依赖文件系统状态

### 覆盖率目标

- MibParser 类: > 70%
- 公共方法: 100%
- 私有方法: > 60%

---

**规格版本**: 1.0
**创建日期**: 2026-01-01
**状态**: 📝 待审批
