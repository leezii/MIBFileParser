# 任务清单: 添加解析器和工具模块测试

## 任务顺序

### 阶段 1: parser.py 测试（核心解析器）

- [x] **T1: 测试 MibParser 初始化**
  - 创建 `tests/unit/test_parser/test_mib_parser_init.py`
  - 测试默认参数初始化
  - 测试自定义 MIB sources 初始化
  - 测试 debug_mode 参数
  - 测试 resolve_dependencies 参数
  - 测试 device_type 参数
  - **验证**: 初始化测试通过，覆盖率 > 80%
  - **依赖**: T0（无）

- [x] **T2: 测试 MIB 文件解析**
  - 创建 `tests/unit/test_parser/test_mib_parser_parse.py`
  - 测试 `parse()` 方法解析单个 MIB 文件
  - 测试解析包含依赖的 MIB 文件
  - 测试解析失败时的错误处理
  - 测试解析缓存功能
  - 使用 mock 模拟 pysmi 编译器
  - **验证**: 解析测试通过，覆盖率 > 70%
  - **依赖**: T1

- [x] **T3: 测试 MIB 查询方法**
  - 创建 `tests/unit/test_parser/test_mib_parser_query.py`
  - 测试 `get_mib_data()` 方法
  - 测试 `get_all_mib_names()` 方法
  - 测试 `is_mib_loaded()` 方法
  - 测试查询不存在 MIB 的处理
  - **验证**: 查询方法测试通过，覆盖率 > 80%
  - **依赖**: T2

- [x] **T4: 测试 MIB 依赖解析集成**
  - 创建 `tests/unit/test_parser/test_mib_parser_dependencies.py`
  - 测试解析器与 MibDependencyResolver 的集成
  - 测试自动依赖解析功能
  - 测试依赖缓存
  - 测试循环依赖处理
  - **验证**: 集成测试通过，覆盖率 > 70%
  - **依赖**: T2

### 阶段 2: dependency_resolver.py 测试

- [x] **T5: 测试 MibFile 类**
  - 创建 `tests/unit/test_dependency_resolver/test_mib_file.py`
  - 测试 MibFile 初始化
  - 测试 MIB 文件路径解析
  - 测试 MIB 名称提取
  - 测试导入语句解析
  - 测试边界情况（空文件、格式错误）
  - **验证**: MibFile 测试通过，覆盖率 > 80%
  - **依赖**: T0（可并行）

- [x] **T6: 测试 MibDependencyResolver**
  - 创建 `tests/unit/test_dependency_resolver/test_resolver.py`
  - 测试依赖关系图构建
  - 测试依赖顺序计算（拓扑排序）
  - 测试循环依赖检测
  - 测试缺失依赖处理
  - 测试多文件依赖解析
  - **验证**: 依赖解析测试通过，覆盖率 > 75%
  - **依赖**: T5

### 阶段 3: tree.py 测试

- [x] **T7: 测试 MibTree 树构建**
  - 创建 `tests/unit/test_tree/test_tree_build.py`
  - 测试从节点列表构建树
  - 测试父子关系建立
  - 测试根节点识别
  - 测试空列表处理
  - 测试重复节点处理
  - **验证**: 树构建测试通过，覆盖率 > 80%
  - **依赖**: T0（可并行）

- [x] **T8: 测试 MibTree 树遍历**
  - 创建 `tests/unit/test_tree/test_tree_traversal.py`
  - 测试深度优先遍历
  - 测试广度优先遍历
  - 测试子树遍历
  - 测试特定节点查找
  - **验证**: 遍历测试通过，覆盖率 > 80%
  - **依赖**: T7

- [x] **T9: 测试 MibTree 树操作**
  - 创建 `tests/unit/test_tree/test_tree_operations.py`
  - 测试添加节点
  - 测试获取子节点
  - 测试获取父节点
  - 测试获取节点深度
  - 测试获取节点路径
  - **验证**: 树操作测试通过，覆盖率 > 75%
  - **依赖**: T7

### 阶段 4: leaf_extractor.py 测试

- [x] **T10: 测试叶节点识别**
  - 创建 `tests/unit/test_leaf_extractor/test_identification.py`
  - 测试标量节点识别
  - 测试表格节点识别
  - 测试非叶节点过滤
  - 测试边界情况
  - **验证**: 叶节点识别测试通过，覆盖率 > 80%
  - **依赖**: T0（可并行）

- [x] **T11: 测试 LeafNodeExtractor 提取方法**
  - 创建 `tests/unit/test_leaf_extractor/test_extraction.py`
  - 测试 `extract_leaf_nodes()` 方法
  - 测试从 MibData 提取
  - 测试从树结构提取
  - 测试保留父节点信息
  - **验证**: 提取测试通过，覆盖率 > 75%
  - **依赖**: T10

- [x] **T12: 测试表格索引处理**
  - 创建 `tests/unit/test_leaf_extractor/test_table_indexes.py`
  - 测试表格索引字段识别
  - 测试 INDEX 子句解析
  - 测试 AUGMENTS 子句处理
  - 测试复杂索引情况
  - **验证**: 表格处理测试通过，覆盖率 > 70%
  - **依赖**: T10

### 阶段 5: 验证和文档

- [x] **T13: 运行完整测试套件**
  - 运行所有新增测试
  - 运行覆盖率报告
  - 检查覆盖率是否达到目标
  - 修复任何测试失败
  - **验证**: 所有测试通过，覆盖率达标
  - **依赖**: T1-T12

- [x] **T14: 更新测试文档**
  - 更新 `tests/README.md`
  - 添加新模块测试说明
  - 更新覆盖率目标
  - 添加测试运行示例
  - **验证**: 文档完整准确
  - **依赖**: T13

- [x] **T15: 代码质量检查**
  - 运行 black 格式化
  - 运行 flake8 检查
  - 修复代码质量问题
  - 确保测试命名清晰
  - **验证**: 所有检查通过
  - **依赖**: T14

## 可并行化任务组

### 组 1: 完全可并行（无依赖）
- T5 (MibFile 测试) || T7 (树构建测试) || T10 (叶节点识别)

### 组 2: 阶段内并行
- T8, T9 (依赖 T7) 可并行
- T11, T12 (依赖 T10) 可并行

### 组 3: 阶段间并行（阶段1完成后）
- T6 (依赖 T5) 可与 T7-T9 并行

## 里程碑

### 里程碑 1: Parser 测试完成
- **完成条件**: T1-T4 全部完成
- **交付物**: parser.py 测试套件，覆盖率 > 70%

### 里程碑 2: 工具模块测试完成
- **完成条件**: T5-T12 全部完成
- **交付物**: dependency_resolver, tree, leaf_extractor 测试套件

### 里程碑 3: 第二阶段完成
- **完成条件**: T1-T15 全部完成
- **交付物**: 完整的解析器和工具测试，文档更新

## 验收标准

### 功能验收
- ✅ 所有新测试稳定通过
- ✅ parser.py 覆盖率 > 70%
- ✅ tree.py 覆盖率 > 75%
- ✅ leaf_extractor.py 覆盖率 > 75%
- ✅ dependency_resolver.py 覆盖率 > 70%

### 质量验收
- ✅ 测试代码通过 black, flake8 检查
- ✅ 测试命名清晰，易于理解
- ✅ Mock 使用得当，测试隔离性好
- ✅ 边界情况和错误处理有测试覆盖

### 工程验收
- ✅ 测试运行时间合理（< 2 分钟）
- ✅ 测试与实现代码分离
- ✅ 测试文档完整
- ✅ 复用第一阶段的基础设施

## 风险和应对

| 风险 | 应对措施 |
|------|----------|
| parser.py 测试复杂，mock 难度高 | 先测试简单方法，逐步增加复杂度 |
| pysmi 行为难以完全模拟 | 聚焦测试解析器自己的逻辑，不测试 pysmi |
| 树操作测试数据准备繁琐 | 创建测试辅助函数和数据生成器 |
| 依赖解析涉及文件系统 | 使用 tempfile 和 mock 文件操作 |
| 测试运行时间过长 | 使用 pytest 标记分离慢速测试 |

## 后续任务（第三阶段）

- [x] 服务层测试（device_service, mib_service 等）
- [x] Flask API 路由测试
- [x] 集成测试
- [x] CI/CD 集成

---

**任务清单版本**: 1.0
**创建日期**: 2026-01-01
**预计总工时**: 11-17 小时（2-3 个工作日）
