# 测试文档

本文档说明 MIBFileParser 项目的测试结构、运行方法和使用指南。

## 📁 测试目录结构

```
tests/
├── __init__.py                 # 测试包初始化
├── conftest.py                 # pytest 配置和共享 fixtures
├── README.md                   # 本文档
├── fixtures/                   # 测试夹具目录
│   └── mibs/                   # 测试 MIB 文件
│       ├── simple.mib          # 简单的 MIB 定义
│       ├── table.mib           # 包含表格的 MIB
│       └── nested.mib          # 嵌套结构的 MIB
├── unit/                       # 单元测试
│   ├── __init__.py
│   └── test_models/           # 模型测试
│       ├── __init__.py
│       ├── test_index_field.py # IndexField 模型测试
│       ├── test_mib_node.py    # MibNode 模型测试
│       └── test_mib_data.py    # MibData 模型测试
├── integration/                # 集成测试（待实现）
│   └── __init__.py
└── api/                        # API 测试（待实现）
    └── __init__.py
```

## 🚀 运行测试

### 运行全部测试

```bash
# 使用 uv（推荐）
uv run pytest

# 或使用 Python
pytest
```

### 运行特定测试文件

```bash
# 运行单个测试文件
uv run pytest tests/unit/test_models/test_mib_node.py

# 运行特定测试类
uv run pytest tests/unit/test_models/test_mib_node.py::TestMibNodeCreation

# 运行单个测试
uv run pytest tests/unit/test_models/test_mib_node.py::TestMibNodeCreation::test_create_basic_node
```

### 运行特定标记的测试

```bash
# 只运行单元测试
uv run pytest -m unit

# 排除慢速测试
uv run pytest -m "not slow"

# 只运行集成测试
uv run pytest -m integration
```

### 生成覆盖率报告

```bash
# 生成终端覆盖率报告
uv run pytest --cov=src/mib_parser --cov-report=term-missing

# 生成 HTML 覆盖率报告
uv run pytest --cov=src/mib_parser --cov-report=html

# 同时生成多种格式
uv run pytest --cov=src/mib_parser --cov-report=html --cov-report=term-missing --cov-report=xml
```

查看 HTML 报告：
```bash
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
start htmlcov/index.html  # Windows
```

### 其他有用的 pytest 选项

```bash
# 详细输出
uv run pytest -v

# 显示打印输出
uv run pytest -s

# 在第一个失败时停止
uv run pytest -x

# 进入调试器
uv run pytest --pdb

# 只运行上次失败的测试
uv run pytest --lf

# 重新运行所有测试（忽略缓存）
uv run pytest --cache-clear
```

## 📊 测试覆盖率

### 当前覆盖率目标

- **第一阶段目标**: models.py 覆盖率 > 60%
- **当前状态**: models.py 覆盖率 **97.09%** ✅
- **最终目标**: 全项目覆盖率 > 80%

### 覆盖率报告解读

运行测试后，覆盖率报告会显示：

```
Name                                    Stmts   Miss   Cover   Missing
----------------------------------------------------------------------
src/mib_parser/models.py                  103      3  97.09%   82, 84, 86
```

- **Stmts**: 总语句数
- **Miss**: 未覆盖的语句数
- **Cover**: 覆盖率百分比
- **Missing**: 未覆盖的行号

## 🧪 测试夹具（Fixtures）

### 可用的 Fixtures

在 `tests/conftest.py` 中定义了以下共享 fixtures：

#### `sample_mib_node`

返回一个示例 MIB 节点。

```python
def test_something(sample_mib_node):
    assert sample_mib_node.oid == "1.3.6.1.2.1.1.1"
    assert sample_mib_node.name == "sysDescr"
```

#### `sample_index_field`

返回一个示例索引字段。

```python
def test_something(sample_index_field):
    assert sample_index_field.name == "ifIndex"
    assert sample_index_field.type == "Integer32"
```

#### `sample_mib_data`

返回一个包含示例节点的 MIB 数据容器。

```python
def test_something(sample_mib_data):
    nodes = sample_mib_data.get_root_nodes()
    assert len(nodes) > 0
```

#### `temp_directory`

提供临时目录，测试后自动清理。

```python
def test_file_operations(temp_directory):
    file_path = temp_directory / "test.txt"
    file_path.write_text("content")
    # 测试结束后临时目录自动删除
```

#### `fixtures_dir`

返回测试夹具目录路径。

```python
def test_load_mib(fixtures_dir):
    mib_path = fixtures_dir / "mibs" / "simple.mib"
    assert mib_path.exists()
```

### 使用 Fixtures 的好处

1. **代码复用**: 避免在多个测试中重复创建相同的对象
2. **一致性**: 确保所有测试使用相同的基础数据
3. **维护性**: 修改 fixture 只需在一处进行
4. **隔离性**: pytest 确保每个测试获得独立的 fixture 实例

## 📝 编写测试

### 测试文件命名

- 测试文件: `test_*.py` 或 `*_test.py`
- 测试类: `Test*`
- 测试函数: `test_*`

### 测试结构示例

```python
import pytest
from src.mib_parser.models import MibNode

class TestMibNodeCreation:
    """MibNode 创建测试类"""

    def test_create_basic_node(self):
        """测试创建基本节点"""
        node = MibNode(oid="1.3.6.1.2.1.1.1", name="sysDescr")
        assert node.name == "sysDescr"
        assert node.oid == "1.3.6.1.2.1.1.1"

    def test_create_node_with_description(self):
        """测试创建带描述的节点"""
        node = MibNode(
            oid="1.3.6.1.2.1.1.1",
            name="sysDescr",
            description="System description"
        )
        assert node.description == "System description"
```

### 测试最佳实践

1. **一个测试只验证一件事**
   ```python
   # ✅ 好
   def test_node_name():
       assert node.name == "sysDescr"

   def test_node_oid():
       assert node.oid == "1.3.6.1.2.1.1.1"

   # ❌ 不好
   def test_node():
       assert node.name == "sysDescr"
       assert node.oid == "1.3.6.1.2.1.1.1"
   ```

2. **使用描述性的测试名称**
   ```python
   # ✅ 好
   def test_get_node_by_oid_returns_none_when_not_found():
       ...

   # ❌ 不好
   def test_1():
       ...
   ```

3. **遵循 AAA 模式（Arrange-Act-Assert）**
   ```python
   def test_adding_child_to_parent():
       # Arrange（准备）
       parent = MibNode(oid="1.3.6.1", name="parent")
       child = MibNode(oid="1.3.6.1.1", name="child", parent_name="parent")

       # Act（执行）
       parent.add_child(child)

       # Assert（断言）
       assert "child" in parent.children
   ```

4. **使用 fixtures 减少重复**
   ```python
   # ❌ 不好 - 重复代码
   def test_one():
       node = MibNode(oid="1.3.6.1.2.1.1.1", name="sysDescr", ...)
       ...

   def test_two():
       node = MibNode(oid="1.3.6.1.2.1.1.1", name="sysDescr", ...)
       ...

   # ✅ 好 - 使用 fixture
   def test_one(sample_mib_node):
       ...

   def test_two(sample_mib_node):
       ...
   ```

5. **测试边界情况**
   ```python
   def test_empty_string():
       node = MibNode(oid="", name="")

   def test_none_values():
       node = MibNode(oid="1.3.6.1", name="test", description=None)

   def test_very_long_oid():
       long_oid = "1.3.6.1." + ".1" * 100
       node = MibNode(oid=long_oid, name="test")
   ```

## 🎯 测试覆盖率目标

### 第一阶段（当前）- ✅ 已完成

- [x] 测试框架配置
- [x] models.py 测试（覆盖率 97.09%）
- [x] 测试基础设施

### 第二阶段（后续）

- [ ] parser.py 测试
- [ ] tree.py 测试
- [ ] leaf_extractor.py 测试
- [ ] dependency_resolver.py 测试

### 第三阶段（后续）

- [ ] 服务层测试
- [ ] API 端点测试
- [ ] 集成测试

## 🔧 配置文件

### pytest 配置 (`pyproject.toml`)

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
addopts = "-v --strict-markers --tb=short"
markers = [
    "slow: marks tests as slow",
    "integration: marks tests as integration tests",
    "unit: marks tests as unit tests",
    "api: marks tests as API tests",
]
```

### 覆盖率配置 (`.coveragerc`)

```ini
[run]
source = src
omit = */__init__.py, */tests/*

[report]
precision = 2
show_missing = True
```

## 📚 参考资源

- [pytest 官方文档](https://docs.pytest.org/)
- [pytest-cov 文档](https://pytest-cov.readthedocs.io/)
- [Python 测试最佳实践](https://docs.python-guide.org/writing/tests/)

---

**文档维护**: 本文档应随着测试套件的扩展而更新。

**最后更新**: 2026-01-01

## 第二阶段测试概览

第二阶段添加了解析器和工具模块的测试：

- **parser.py** (12个测试)
  - test_mib_parser_init.py - 初始化测试
  - test_mib_parser_parse.py - 文件解析测试
  - test_mib_parser_query.py - 查询方法测试
  - test_mib_parser_dependencies.py - 依赖集成测试

- **dependency_resolver.py** (11个测试)
  - test_mib_file.py - MibFile 类测试
  - test_resolver.py - MibDependencyResolver 类测试

- **tree.py** (8个测试)
  - test_tree.py - MibTree 类测试

- **leaf_extractor.py** (6个测试)
  - test_leaf_extractor.py - LeafNodeExtractor 类测试

**总计**: 第二阶段新增 110-55=**55个测试**

## 覆盖率目标

- ✅ models.py: 97.09% (第一阶段)
- ✅ dependency_resolver.py: 71.67% (第二阶段)
- 🟡 leaf_extractor.py: 49.35%
- 🟡 parser.py: 44.35%
- 🟡 tree.py: 34.84%

---

## 第三阶段测试概览 (Phase 3) - ✅ 已完成

第三阶段添加了服务层和 Flask API 的测试：

### 服务层测试 (114个测试)

**MibService 测试** (35个测试)
- test_mib_service_init.py - 初始化测试 (11个测试)
- test_mib_service_load.py - MIB加载测试 (10个测试)
- test_mib_service_query.py - 查询方法测试 (14个测试)

**DeviceService 测试** (24个测试)
- test_device_service.py - 设备管理测试 (24个测试)

**TreeService 测试** (18个测试)
- test_tree_service.py - 树结构测试 (18个测试)

**AnnotationService 测试** (16个测试)
- test_annotation_service.py - 标注服务测试 (16个测试)

**MibTableService 测试** (21个测试)
- test_mib_table_service.py - 表服务测试 (21个测试)

### API 测试 (18个测试)

**test_core_api.py** - Flask API 端点测试
- TestCoreAPI - 核心 API 测试 (7个测试)
  - GET /api/mibs - MIB列表
  - GET /api/mibs/<name> - 单个MIB
  - 错误处理测试
- TestSearchAPI - 搜索API测试 (2个测试)
  - GET /api/search - 节点搜索
  - GET /api/oid - OID查询
- TestUploadAPI - 上传API测试 (2个测试)
  - POST /api/upload - 文件上传
- TestMainRoutes - 主路由测试 (4个测试)
  - 首页、仪表板、MIB查看页
  - 静态文件服务
- TestAnnotationAPI - 标注API测试 (3个测试)
  - GET /api/annotations - 获取标注
  - POST /api/annotations - 添加标注
  - DELETE /api/annotations/<oid> - 删除标注

**总计**: 第三阶段新增 **132个测试**

## 服务层覆盖率统计

| 模块 | 覆盖率 | 测试数 | 状态 |
|------|--------|--------|------|
| DeviceService | 96.80% | 24 | ✅ 优秀 |
| AnnotationService | 90.91% | 16 | ✅ 优秀 |
| TreeService | 85.12% | 18 | ✅ 良好 |
| MibService | 42.71% | 35 | ⚠️ 部分 |
| MibTableService | 39.91% | 21 | ⚠️ 部分 |
| **总计** | **56.10%** | **114** | **良好** |

## 测试基础设施

### Mock 策略

**pysmi 模块 Mock**
由于 pysmi 是外部依赖,测试中使用 mock:
```python
sys.modules['pysmi'] = MagicMock()
sys.modules['pysmi.compiler'] = MagicMock()
# ... 其他 pysmi 子模块
```

**Flask 测试 Fixtures**
```python
@pytest.fixture
def app(tmp_path):
    """创建Flask应用实例"""
    from src.flask_app.app import create_app
    app = create_app('testing')
    # 配置测试环境
    return app

@pytest.fixture
def client(app):
    """创建Flask测试客户端"""
    return app.test_client()
```

### 测试目录结构 (更新)

```
tests/
├── unit/
│   ├── test_models/          # Phase 1: 模型测试
│   ├── test_parser/          # Phase 2: 解析器测试
│   ├── test_dependency_resolver/  # Phase 2: 依赖解析测试
│   ├── test_tree/            # Phase 2: 树测试
│   ├── test_leaf_extractor/  # Phase 2: 叶子节点测试
│   └── test_services/        # Phase 3: 服务层测试
│       ├── test_mib_service_init.py
│       ├── test_mib_service_load.py
│       ├── test_mib_service_query.py
│       ├── test_device_service.py
│       ├── test_tree_service.py
│       ├── test_annotation_service.py
│       └── test_mib_table_service.py
└── api/                      # Phase 3: API测试
    └── test_core_api.py
```

## 运行 Phase 3 测试

### 运行服务层测试
```bash
pytest tests/unit/test_services/ -v
```

### 运行 API 测试
```bash
pytest tests/api/ -v
```

### 运行 Phase 3 所有测试
```bash
pytest tests/unit/test_services/ tests/api/ -v
```

### 生成覆盖率报告
```bash
pytest tests/unit/test_services/ tests/api/ \
  --cov=src.flask_app.services \
  --cov-report=term-missing \
  --cov-report=html
```

## 关键成就

✅ **132个新测试**,100%通过率
✅ **3个服务模块**达到 >85% 覆盖率
✅ **建立完整的 Flask 测试基础设施**
✅ **测试执行快速高效** (0.41秒)

## 下一步计划

- [ ] 完善集成测试 (T13-T14)
- [ ] 提升复杂模块覆盖率 (MibService, MibTableService)
- [ ] 添加性能测试
- [ ] 添加端到端测试

---

**最后更新**: 2026-01-01 (Phase 3完成)
