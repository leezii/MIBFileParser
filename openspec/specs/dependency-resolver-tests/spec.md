# dependency-resolver-tests Specification

## Purpose
TBD - created by archiving change add-parser-and-tools-tests. Update Purpose after archive.
## Requirements
### Requirement: MibFile 类测试

`MibFile` 类 MUST 有完整的测试，MUST 确保能正确解析 MIB 文件的基本信息。

#### Scenario: 从文件路径创建 MibFile

**Given** 存在有效的 MIB 文件路径
**When** 创建 MibFile 对象
**Then** 正确提取文件名
**And** 正确提取模块名
**And** 正确提取文件路径

#### Scenario: 解析 MIB 导入语句

**Given** MIB 文件包含 IMPORTS 语句
**When** 解析文件内容
**Then** 提取所有导入的模块名
**And** 保存导入列表
**And** 返回完整的导入信息

#### Scenario: 处理不存在的文件

**Given** MIB 文件路径不存在
**When** 尝试创建 MibFile
**Then** 抛出 FileNotFoundError
**Or** 返回空对象（根据设计）

#### Scenario: 处理格式错误的 MIB 文件

**Given** MIB 文件内容格式错误
**When** 尝试解析
**Then** 返回部分结果或抛出异常
**And** 错误处理不影响其他文件

---

### Requirement: MibDependencyResolver 测试

`MibDependencyResolver` MUST 有完整的测试，MUST 确保能正确解析和处理 MIB 依赖关系。

#### Scenario: 构建依赖关系图

**Given** 多个 MIB 文件存在依赖关系
**When** 调用依赖解析器
**Then** 构建完整的依赖图
**And** 每个节点表示一个 MIB
**And** 边表示依赖关系

#### Scenario: 计算依赖顺序（拓扑排序）

**Given** MIB 依赖关系图
**When** 计算加载顺序
**Then** 返回拓扑排序的 MIB 列表
**And** 被依赖的 MIB 在依赖它的 MIB 之前
**And** 所有依赖关系满足

#### Scenario: 检测循环依赖

**Given** MIB A 依赖 B
**And** MIB B 依赖 A（循环）
**When** 尝试解析依赖
**Then** 检测到循环依赖
**And** 抛出异常或标记循环
**And** 提供循环路径信息

#### Scenario: 处理缺失依赖

**Given** MIB 导入不存在的模块
**When** 解析依赖
**Then** 标记缺失的依赖
**And** 继续处理其他依赖
**And** 返回部分结果或警告

#### Scenario: 解析多个文件的依赖

**Given** 提供多个 MIB 文件列表
**When** 批量解析依赖
**Then** 正确处理所有文件
**And** 合并依赖关系
**And** 返回完整的依赖图

---

