# leaf-extractor-tests Specification

## Purpose
TBD - created by archiving change add-parser-and-tools-tests. Update Purpose after archive.
## Requirements
### Requirement: 叶节点识别测试

`LeafNodeExtractor` MUST 能正确识别各种类型的叶节点。

#### Scenario: 识别标量节点

**Given** 节点是标量对象（非表格列）
**When** 检查是否为叶节点
**Then** 返回 True
**And** 节点被识别为叶节点

#### Scenario: 识别表格列节点

**Given** 节点是表格的列对象
**When** 检查是否为叶节点
**Then** 返回 True
**And** 节点被识别为叶节点

#### Scenario: 过滤非叶节点

**Given** 节点是表格对象
**Or** 节点包含子节点
**When** 检查是否为叶节点
**Then** 返回 False
**And** 节点不被识别为叶节点

#### Scenario: 处理边界情况

**Given** 节点缺少必要属性
**Or** 节点结构异常
**When** 检查是否为叶节点
**Then** 返回合理的默认值
**And** 不抛出异常

---

### Requirement: 叶节点提取测试

LeafNodeExtractor 的提取方法 MUST 能正确从 MIB 数据或树中提取叶节点。

#### Scenario: 从 MibData 提取叶节点

**Given** MibData 包含多个节点
**When** 调用 `extract_leaf_nodes(mib_data)`
**Then** 返回所有叶节点列表
**And** 列表不包含表格或内部节点
**And** 保留节点的完整信息

#### Scenario: 从树结构提取叶节点

**Given** 存在构建好的 MibTree
**When** 从树中提取叶节点
**Then** 遍历整个树
**And** 收集所有叶节点
**And** 保持树的层次信息

#### Scenario: 保留父节点信息

**Given** 提取叶节点
**When** 返回结果
**Then** 每个叶节点包含父节点信息
**And** 可以追溯叶节点的路径

---

### Requirement: 表格索引处理测试

LeafNodeExtractor MUST 能正确处理表格的 INDEX 子句和索引字段。

#### Scenario: 识别表格索引字段

**Given** 表格条目包含 INDEX 子句
**When** 解析索引字段
**Then** 正确识别索引字段名称
**And** 正确识别索引字段类型
**And** 保存索引信息到节点

#### Scenario: 处理多字段索引

**Given** 表格索引包含多个字段
**When** 解析 INDEX 子句
**Then** 解析所有索引字段
**And** 保持索引字段的顺序
**And** 正确构建 IndexField 对象

#### Scenario: 处理 AUGMENTS 子句

**Given** 表格使用 AUGMENTS 引用其他表格
**When** 解析表格索引
**Then** 识别 AUGMENTS 关系
**And** 包含被增强表格的索引字段
**And** 正确合并索引信息

#### Scenario: 处理复杂索引表达式

**Given** INDEX 包含复杂表达式
**When** 解析索引
**Then** 正确处理嵌套索引
**And** 正确处理索引长度限制
**And** 保持索引的语义

---

