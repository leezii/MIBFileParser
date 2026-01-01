# 任务清单: 添加服务层和 API 测试

## 任务顺序

### 阶段 1: 核心服务测试

- [ ] **T1: 测试 MibService 初始化和配置**
  - 创建 `tests/unit/test_services/test_mib_service_init.py`
  - 测试服务初始化
  - 测试 MIB 源配置
  - 测试缓存配置
  - 测试设备类型配置
  - **验证**: 初始化测试通过，覆盖率 > 70%
  - **依赖**: T0（无）

- [ ] **T2: 测试 MibService MIB 加载方法**
  - 创建 `tests/unit/test_services/test_mib_service_load.py`
  - 测试 `load_mib()` 方法
  - 测试 `load_mib_from_file()` 方法
  - 测试 MIB 缓存功能
  - 使用 mock parser 和文件系统
  - **验证**: 加载方法测试通过，覆盖率 > 70%
  - **依赖**: T1

- [ ] **T3: 测试 MibService 查询方法**
  - 创建 `tests/unit/test_services/test_mib_service_query.py`
  - 测试 `get_mib_data()` 方法
  - 测试 `get_loaded_mibs()` 方法
  - 测试 `is_mib_loaded()` 方法
  - 测试边界情况（空数据、不存在的 MIB）
  - **验证**: 查询方法测试通过，覆盖率 > 80%
  - **依赖**: T2

- [ ] **T4: 测试 DeviceService**
  - 创建 `tests/unit/test_services/test_device_service.py`
  - 测试设备列表获取
  - 测试设备添加和删除
  - 测试设备注册表更新
  - 测试文件操作（使用 mock）
  - **验证**: DeviceService 测试通过，覆盖率 > 75%
  - **依赖**: T0（可并行）

### 阶段 2: 其他服务测试

- [ ] **T5: 测试 TreeService**
  - 创建 `tests/unit/test_services/test_tree_service.py`
  - 测试树构建方法
  - 测试树节点格式化
  - 测试树搜索功能
  - 测试深度/路径计算
  - **验证**: TreeService 测试通过，覆盖率 > 75%
  - **依赖**: T0（可并行）

- [ ] **T6: 测试 AnnotationService**
  - 创建 `tests/unit/test_services/test_annotation_service.py`
  - 测试注释添加
  - 测试注释查询
  - 测试注释更新和删除
  - 测试注释存储操作
  - **验证**: AnnotationService 测试通过，覆盖率 > 75%
  - **依赖**: T0（可并行）

- [ ] **T7: 测试 MibTableService**
  - 创建 `tests/unit/test_services/test_mib_table_service.py`
  - 测试表格数据查询
  - 测试行数据获取
  - 测试索引字段处理
  - 测试表格遍历
  - **验证**: MibTableService 测试通过，覆盖率 > 70%
  - **依赖**: T2

### 阶段 3: Flask API 测试

- [ ] **T8: 测试核心 API 端点**
  - 创建 `tests/api/test_core_api.py`
  - 测试 `GET /api/mibs` 获取 MIB 列表
  - 测试 `GET /api/mibs/<name>` 获取单个 MIB
  - 测试 `POST /api/mibs/upload` 上传 MIB
  - 测试 `DELETE /api/mibs/<name>` 删除 MIB
  - 使用 pytest-flask client
  - **验证**: 核心 API 测试通过，覆盖率 > 80%
  - **依赖**: T1-T3

- [ ] **T9: 测试搜索和查询 API**
  - 创建 `tests/api/test_search_api.py`
  - 测试 `GET /api/search?q=` 搜索节点
  - 测试 `GET /api/oid/<oid>` OID 查询
  - 测试搜索边界情况（空查询、特殊字符）
  - 测试分页功能
  - **验证**: 搜索 API 测试通过，覆盖率 > 75%
  - **依赖**: T3

- [ ] **T10: 测试上传 API**
  - 创建 `tests/api/test_upload_api.py`
  - 测试文件上传处理
  - 测试多文件上传
  - 测试上传错误处理
  - 测试文件类型验证
  - **验证**: 上传 API 测试通过，覆盖率 > 75%
  - **依赖**: T2

- [ ] **T11: 测试注释 API**
  - 创建 `tests/api/test_annotation_api.py`
  - 测试 `GET /api/annotations` 获取注释
  - 测试 `POST /api/annotations` 添加注释
  - 测试 `PUT /api/annotations/<oid>` 更新注释
  - 测试 `DELETE /api/annotations/<oid>` 删除注释
  - **验证**: 注释 API 测试通过，覆盖率 > 80%
  - **依赖**: T6

- [ ] **T12: 测试主页和辅助路由**
  - 创建 `tests/api/test_main_routes.py`
  - 测试仪表板页面
  - 测试 MIB 查看页面
  - 测试 OID 查看页面
  - **验证**: 主页路由测试通过，覆盖率 > 70%
  - **依赖**: T8

### 阶段 4: 集成和验证

- [ ] **T13: 服务层集成测试**
  - 创建 `tests/integration/test_service_integration.py`
  - 测试服务与解析器集成
  - 测试服务与存储集成
  - 测试多服务协作
  - 使用真实组件（非 mock）
  - **验证**: 集成测试通过，关键流程覆盖
  - **依赖**: T1-T7

- [ ] **T14: API 端到端测试**
  - 创建 `tests/integration/test_api_e2e.py`
  - 测试完整的用户流程（上传→解析→查询）
  - 测试错误流程
  - 标记为 `@pytest.mark.integration`
  - **验证**: E2E 测试通过，关键流程验证
  - **依赖**: T8-T12

- [ ] **T15: 运行完整测试套件并生成报告**
  - 运行所有测试（单元+集成）
  - 生成覆盖率报告
  - 检查服务层覆盖率目标
  - 检查 API 覆盖率目标
  - **验证**: 所有测试通过，覆盖率达标
  - **依赖**: T1-T14

- [ ] **T16: 更新测试文档**
  - 更新 `tests/README.md`
  - 添加服务层测试说明
  - 添加 API 测试说明
  - 添加集成测试说明
  - 更新覆盖率目标
  - **验证**: 文档完整准确
  - **依赖**: T15

- [ ] **T17: 代码质量检查和优化**
  - 运行 black 格式化
  - 运行 flake8 检查
  - 优化测试代码
  - 提取公共测试辅助函数
  - **验证**: 所有检查通过
  - **依赖**: T16

## 可并行化任务组

### 组 1: 服务层并行（无依赖）
- T4 (DeviceService) || T5 (TreeService) || T6 (AnnotationService)

### 组 2: API 测试并行（依赖各自服务）
- T9 (搜索API) || T10 (上传API) || T11 (注释API) （在 T3/T2/T6 完成后可并行）

### 组 3: 集成测试并行
- T13 (服务集成) || T14 (API E2E) （在各自依赖完成后可并行）

## 里程碑

### 里程碑 1: 核心服务测试完成
- **完成条件**: T1-T4 全部完成
- **交付物**: MibService 和 DeviceService 测试套件

### 里程碑 2: 服务层测试完成
- **完成条件**: T1-T7 全部完成
- **交付物**: 所有服务类测试套件

### 里程碑 3: API 测试完成
- **完成条件**: T1-T12 全部完成
- **交付物**: Flask API 完整测试套件

### 里程碑 4: 第三阶段完成
- **完成条件**: T1-T17 全部完成
- **交付物**: 服务层和 API 完整测试，文档更新

## 验收标准

### 功能验收
- ✅ 服务层核心方法测试覆盖 > 70%
- ✅ Flask API 端点测试覆盖 > 80%
- ✅ 关键用户流程有集成测试
- ✅ 错误处理有测试覆盖

### 质量验收
- ✅ 测试代码通过 black, flake8 检查
- ✅ 测试命名清晰，易于理解
- ✅ Mock 使用得当，测试隔离性好
- ✅ API 测试覆盖正常和异常流程

### 工程验收
- ✅ 测试运行时间合理（< 3 分钟）
- ✅ 集成测试标记清晰
- ✅ 测试文档完整
- ✅ 复用已有测试基础设施

## 风险和应对

| 风险 | 应对措施 |
|------|----------|
| Flask 上下文设置复杂 | 使用 pytest-flask 和共享 fixtures |
| 文件系统操作难以测试 | 大量使用 mock 和临时文件 |
| 服务有全局状态 | 每个测试独立初始化，清理状态 |
| API 测试数据准备繁琐 | 创建 API 测试辅助函数和 fixture |
| 集成测试运行慢 | 使用 pytest 标记，CI 中分离运行 |
| 服务间依赖复杂 | 集成测试使用真实组件，单元测试用 mock |

## 后续任务（第四阶段）

- [ ] E2E 测试（Selenium/Playwright）
- [ ] 性能测试
- [ ] 负载测试（Locust）
- [ ] CI/CD 集成优化

---

**任务清单版本**: 1.0
**创建日期**: 2026-01-01
**预计总工时**: 20-29 小时（3-5 个工作日）
