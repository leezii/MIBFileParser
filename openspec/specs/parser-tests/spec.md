# parser-tests Specification

## Purpose
TBD - created by archiving change add-unit-tests. Update Purpose after archive.
## Requirements
### Requirement: MibNode 模型测试

`MibNode` 类 MUST 有完整的单元测试，MUST 确保其序列化和反序列化功能正确。

#### Scenario: 创建基本的 MIB 节点

**Given** 测试导入 `MibNode` 类
**When** 创建包含基本属性的 MIB 节点
```
node = MibNode(
    oid="1.3.6.1.2.1.1.1",
    name="sysDescr",
    description="System description"
)
```
**Then** 节点对象成功创建
**And** 所有属性可以正确访问

#### Scenario: 序列化 MIB 节点到字典

**Given** 存在一个 MIB 节点对象
**When** 调用 `node.to_dict()` 方法
**Then** 返回包含所有节点属性的字典
**And** 字典包含 `oid`, `name`, `description` 等字段
**And** 字典值与节点对象属性一致

#### Scenario: 从字典反序列化 MIB 节点

**Given** 存在一个包含 MIB 节点数据的字典
**When** 调用 `MibNode.from_dict(data)` 方法
**Then** 返回一个 MIB 节点对象
**And** 对象属性与字典数据一致
**And** 对象类型正确

#### Scenario: 处理特殊 OID 格式

**Given** 需要创建包含特殊 OID 的节点
**When** 使用长 OID、带前导零或嵌套 OID
**Then** 节点正确存储 OID 字符串
**And** 序列化和反序列化保持 OID 不变

#### Scenario: 处理空值和可选属性

**Given** 创建 MIB 节点时部分属性未提供
**When** 访问这些可选属性
**Then** 返回合理的默认值（None 或空列表）
**And** 不抛出异常

---

### Requirement: IndexField 模型测试

`IndexField` 类 MUST 有完整的单元测试，MUST 确保表格索引字段功能正确。

#### Scenario: 创建索引字段对象

**Given** 测试导入 `IndexField` 类
**When** 创建索引字段
```
field = IndexField(
    name="ifIndex",
    type="Integer32",
    description="Interface index"
)
```
**Then** 索引字段对象成功创建
**And** 所有属性可以正确访问

#### Scenario: 序列化索引字段到字典

**Given** 存在一个索引字段对象
**When** 调用 `field.to_dict()` 方法
**Then** 返回包含所有字段属性的字典
**And** 字典包含 `name`, `type`, `description` 等字段

#### Scenario: 从字典反序列化索引字段

**Given** 存在索引字段数据字典
**When** 调用 `IndexField.from_dict(data)` 方法
**Then** 返回索引字段对象
**And** 对象属性与字典数据一致

---

### Requirement: MibData 模型测试

`MibData` 类 MUST 有完整的单元测试，MUST 确保节点管理功能正确。

#### Scenario: 创建空的 MIB 数据容器

**Given** 测试导入 `MibData` 类
**When** 创建空的 MibData 对象
```
mib_data = MibData(name="TEST-MIB", module_name="TEST")
```
**Then** 对象成功创建
**And** `get_root_nodes()` 返回空列表

#### Scenario: 添加节点到 MIB 数据

**Given** 存在一个 MibData 对象
**And** 存在一个 MibNode 对象
**When** 调用 `mib_data.add_node(node)`
**Then** 节点被添加到 MIB 数据中
**And** `get_node_by_oid()` 可以找到该节点

#### Scenario: 通过 OID 查找节点

**Given** MibData 中包含多个节点
**When** 调用 `get_node_by_oid("1.3.6.1.2.1.1.1")`
**Then** 返回对应的 MIB 节点对象
**And** 节点的 OID 匹配查询条件

#### Scenario: 查找不存在的 OID

**Given** MibData 中包含节点
**When** 调用 `get_node_by_oid()` 查找不存在的 OID
**Then** 返回 `None`
**And** 不抛出异常

#### Scenario: 通过名称查找节点

**Given** MibData 中包含多个节点
**When** 调用 `get_node_by_name("sysDescr")`
**Then** 返回对应的 MIB 节点对象
**And** 节点的 name 匹配查询条件

#### Scenario: 获取根节点列表

**Given** MibData 中包含多层嵌套节点
**When** 调用 `get_root_nodes()`
**Then** 返回所有根节点（没有父节点的节点）
**And** 不包含子节点

#### Scenario: 获取子节点列表

**Given** MibData 中包含节点树结构
**When** 调用 `get_children(parent_node_name)`
**Then** 返回父节点的直接子节点列表
**And** 不包含孙节点或更深层的节点

#### Scenario: 获取所有后代节点

**Given** MibData 中包含多层节点树
**When** 调用 `get_descendants(ancestor_name)`
**Then** 返回所有后代节点（子节点、孙节点等）
**And** 包含整个子树

#### Scenario: 处理重复节点

**Given** MibData 中已存在某个 OID 的节点
**When** 添加相同 OID 的新节点
**Then** 行为符合设计（替换或忽略）
**And** 不会导致数据不一致

#### Scenario: 序列化 MibData 对象

**Given** 存在包含多个节点的 MibData 对象
**When** 调用 `mib_data.to_dict()` 方法
**Then** 返回包含 MIB 信息的字典
**And** 字典包含所有节点的序列化数据
**And** 可以从字典反序列化恢复对象

---

### Requirement: 测试覆盖率要求

MIB 解析器相关模块 MUST 达到指定的测试覆盖率。

#### Scenario: models.py 模块覆盖率检查

**Given** `src/mib_parser/models.py` 包含 IndexField, MibNode, MibData 类
**When** 运行测试并生成覆盖率报告
**Then** `models.py` 模块覆盖率至少达到 80%
**And** 所有公共方法都有测试覆盖
**And** 关键边界情况有测试覆盖

#### Scenario: 测试覆盖所有代码路径

**Given** MibData 类包含多个方法
**When** 运行完整测试套件
**Then** 每个方法至少有一个正常场景测试
**And** 每个方法至少有一个边界情况测试
**And** 错误处理路径有测试覆盖（如适用）

---

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

