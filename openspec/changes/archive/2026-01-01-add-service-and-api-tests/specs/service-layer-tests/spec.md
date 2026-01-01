# Capability: 服务层测试

## ADDED Requirements

### Requirement: MibService 核心方法测试覆盖

`MibService` 类 MUST 有完整的单元测试，覆盖所有核心方法，测试覆盖率 MUST 达到 70% 以上。

#### Scenario: 测试 MibService 初始化和配置

**Given** 测试环境已配置
**When** 测试 `__init__()` 方法和配置初始化
**Then** MUST 验证服务初始化成功
**And** MUST 验证 MIB 源配置正确
**And** MUST 验证缓存配置正确
**And** MUST 验证设备类型配置正确

#### Scenario: 测试 MibService MIB 加载方法

**Given** 测试环境已配置，mock parser 已设置
**When** 测试 `load_mib()` 和 `load_mib_from_file()` 方法
**Then** MUST 验证 MIB 加载成功
**And** MUST 验证 MIB 缓存功能正常
**And** MUST 使用 mock parser 隔离文件系统依赖

#### Scenario: 测试 MibService 查询方法

**Given** 测试环境已配置，MIB 数据已加载
**When** 测试 `get_mib_data()`, `get_loaded_mibs()`, `is_mib_loaded()` 方法
**Then** MUST 验证查询方法返回正确数据
**And** MUST 验证边界情况（空数据、不存在的 MIB）
**And** MUST 覆盖率 > 80%

---

### Requirement: DeviceService 测试覆盖

`DeviceService` 类 MUST 有完整的单元测试，覆盖设备管理功能，测试覆盖率 MUST 达到 75% 以上。

#### Scenario: 测试设备管理方法

**Given** 测试环境已配置，mock 文件系统已设置
**When** 测试 `list_devices()`, `create_device()`, `delete_device()` 方法
**Then** MUST 验证设备列表获取正确
**And** MUST 验证设备添加和删除功能
**And** MUST 验证设备注册表更新
**And** MUST 使用 mock 文件操作

#### Scenario: 测试设备查询和元数据

**Given** 测试环境已配置，设备数据已创建
**When** 测试 `get_current_device()`, `set_current_device()`, `update_device_metadata()` 方法
**Then** MUST 验证当前设备查询和设置
**And** MUST 验证元数据更新功能
**And** MUST 验证设备注册表 JSON 序列化

---

### Requirement: TreeService 测试覆盖

`TreeService` 类 MUST 有完整的单元测试，覆盖树结构操作，测试覆盖率 MUST 达到 75% 以上。

#### Scenario: 测试树构建和格式化

**Given** 测试环境已配置，MIB 数据已准备
**When** 测试树构建方法（`build_tree_structure()`, `build_breadth_first_tree()`）
**Then** MUST 验证树结构构建正确
**And** MUST 验证树节点格式化
**And** MUST 验证深度和路径计算

#### Scenario: 测试树搜索功能

**Given** 测试环境已配置，树结构已构建
**When** 测试树搜索功能
**Then** MUST 验证搜索结果正确
**And** MUST 处理边界情况（空树、单节点、深度嵌套）

---

### Requirement: AnnotationService 测试覆盖

`AnnotationService` 类 MUST 有完整的单元测试，覆盖注释管理功能，测试覆盖率 MUST 达到 75% 以上。

#### Scenario: 测试注释 CRUD 操作

**Given** 测试环境已配置，mock 存储已设置
**When** 测试注释添加、查询、更新、删除
**Then** MUST 验证 `add_annotation()` 添加注释
**And** MUST 验证 `get_annotation()`, `get_all_annotations()` 查询注释
**And** MUST 验证 `update_annotation()` 更新注释
**And** MUST 验证 `delete_annotation()` 删除注释
**And** MUST 验证注释 JSON 序列化

---

### Requirement: MibTableService 测试覆盖

`MibTableService` 类 MUST 有完整的单元测试，覆盖表格数据查询，测试覆盖率 MUST 达到 70% 以上。

#### Scenario: 测试表格数据查询

**Given** 测试环境已配置，表格数据已准备
**When** 测试表格查询和行数据获取
**Then** MUST 验证表格数据查询正确
**And** MUST 验证 `get_table_row()` 获取行数据
**And** MUST 验证索引字段处理
**And** MUST 验证表格遍历功能

#### Scenario: 测试表格边界情况

**Given** 测试环境已配置
**When** 测试边界情况（空表、不存在的表、无效索引）
**Then** MUST 正确处理空表
**And** MUST 正确处理不存在的表
**And** MUST 正确处理无效索引

---

### Requirement: 测试隔离和 Mock 要求

所有服务层测试 MUST 使用适当的 mock 技术隔离依赖。

#### Scenario: 使用 Mock 隔离文件系统

**Given** 测试文件系统操作的服务
**When** 编写测试
**Then** MUST 使用 `unittest.mock` mock 文件系统操作
**And** MUST 使用 `tmp_path` fixture 创建临时文件
**And** MUST mock Flask 上下文（如果需要）
**And** MUST 在每次测试后清理状态

#### Scenario: 使用 Mock 隔离 Parser

**Given** 测试依赖 parser 的服务
**When** 编写测试
**Then** MUST mock parser 依赖
**And** MUST 避免解析真实 MIB 文件
**And** MUST 不依赖全局状态

---

## Notes

### 测试策略

- **单元测试**: 使用 mock 隔离每个服务类
- **边界测试**: 测试空数据、None 值、空字符串等边界情况
- **错误处理测试**: 测试异常处理和错误返回

### Mock 策略

- 使用 `unittest.mock.patch` mock 文件操作
- 使用 `tmp_path` fixture 创建临时文件和目录
- 使用 `MagicMock` mock parser 和其他服务依赖
- 使用 pytest fixtures 复用 mock 对象

### 覆盖率目标

- MibService: > 70%
- DeviceService: > 75%
- TreeService: > 75%
- AnnotationService: > 75%
- MibTableService: > 70%

---

**规格版本**: 1.0
**创建日期**: 2026-01-01
**状态**: 📝 待审批
