# 🗂️ ICSFP 项目文件结构整理

> **整理日期**: 2025-11-05  
> **项目状态**: Phase 2 - Day 1 完成 (70%)  
> **目的**: 文件分类归档,避免重复工作,方便历史追溯

---

## 📁 文件分类体系

### 1. 📚 核心文档 (docs/)

#### 1.1 项目指南类
- ✅ `README.md` - 项目主文档
- ✅ `README_ICAST.md` - ICAST相关说明
- ✅ `QUICKSTART.md` - 快速开始指南
- ✅ `FILE_MANIFEST.md` - 文件清单

#### 1.2 Phase 1 文档 (已完成)
- ✅ `PHASE1_SUMMARY.md` - Phase 1总结
- ✅ `CIKM18_DATASET_SETUP_SUCCESS.md` - 数据集准备成功报告
- ✅ `INNOVATION_ALGORITHMS_REPORT.md` - 创新算法验证报告
- ✅ `MULTI_DATASET_FEASIBILITY.md` - 多数据集可行性分析

#### 1.3 Phase 2 文档 (进行中)
- ✅ `PHASE2_MULTI_DATASET_SYSTEM.md` - Phase 2详细实现报告
- ✅ `MULTI_DATASET_QUICK_REFERENCE.md` - 多数据集系统快速参考
- ✅ `IMPLEMENTATION_SUMMARY.md` - 实现总结

#### 1.4 快速参考类
- ✅ `QUICK_REFERENCE.md` - 旧版快速参考(实时预测API)
- ✅ `MULTI_DATASET_QUICK_REFERENCE.md` - 新版快速参考(多数据集系统)

#### 1.5 问题修复记录
- ✅ `MODEL_STATUS_VERIFICATION.md` - 模型状态验证
- ✅ `MODEL_USAGE_FIX_COMPLETE.md` - 模型使用修复
- ✅ `MODEL_LOADED_SUCCESS.md` - 模型加载成功
- ✅ `MODEL_STATUS_FIX.md` - 模型状态修复
- ✅ `CRITICAL_MODEL_USAGE_ISSUE.md` - 关键问题记录
- ✅ `PREDICTION_MECHANISM.md` - 预测机制说明

#### 1.6 UI相关文档
- ✅ `UI_OPTIMIZATION_REPORT.md` - UI优化报告
- ✅ `UI_QUICK_GUIDE.md` - UI快速指南
- ✅ `UI_TECH_ENHANCEMENT_REPORT.md` - UI技术增强报告
- ✅ `GLASSMORPHISM_UPGRADE.md` - 玻璃态升级
- ✅ `MOUSE_EFFECTS_REPORT.md` - 鼠标效果报告
- ✅ `STYLE_UNIFICATION_COMPLETE.md` - 样式统一完成
- ✅ `BUGS_FIXED_UI_IMPROVEMENTS.md` - Bug修复和UI改进

#### 1.7 交易平台文档
- ✅ `TRADING_PLATFORM_GUIDE.md` - 交易平台指南
- ✅ `TRADING_QUICKSTART.md` - 交易快速开始
- ✅ `TRADING_SUMMARY.md` - 交易总结
- ✅ `TRADING_DEMO_SCRIPT.md` - 交易演示脚本
- ✅ `README_TRADING.md` - 交易平台README

#### 1.8 集成文档
- ✅ `INTEGRATION_GUIDE.md` - 集成指南
- ✅ `INTEGRATION_SUMMARY.md` - 集成总结
- ✅ `FINAL_STATUS_REPORT.md` - 最终状态报告

#### 1.9 其他文档
- ✅ `VERIFY_FIXES.md` - 修复验证
- ✅ `中期答辩报告_修正版.md` - 中期答辩报告
- ✅ `中期答辩PPT文字脚本.md` - PPT脚本

---

### 2. 💻 核心代码 (根目录)

#### 2.1 主程序
- ✅ `Main.py` - **主训练脚本 (Phase 2增强版)** ⭐
- ✅ `pipeline.py` - 训练流程
- ✅ `Executor.py` - 执行器
- ✅ `quickstart.py` - 快速开始脚本
- ✅ `quick_train.py` - 快速训练
- ✅ `train_full.py` - 完整训练

#### 2.2 模型相关
- ✅ `Model.py` - 模型定义 (含因果图集成)
- ✅ `metrics.py` - 评估指标
- ✅ `ConfigLoader.py` - 配置加载器

#### 2.3 数据处理
- ✅ `DataPipe.py` - 数据管道
- ✅ `data_loader.py` - 数据加载器
- ✅ `dataset_manager.py` - **数据集管理器 (Phase 2新增)** ⭐

#### 2.4 因果发现
- ✅ `granger_causality.py` - Granger因果检验 (318行)
- ✅ `cuts_plus.py` - CUTS+方法 (448行)
- ✅ `compute_cuts_graph.py` - CUTS+因果图生成

#### 2.5 数据准备工具
- ✅ `download_cmin_dataset.py` - 数据集下载工具
- ✅ `prepare_cmin_dataset.py` - 数据集准备
- ✅ `check_cmin_data.py` - 数据检查
- ✅ `create_test_data.py` - 创建测试数据
- ✅ `generate_mock_data.py` - 生成Mock数据

#### 2.6 可视化和工具
- ✅ `StockPredictionViewer.py` - 预测查看器
- ✅ `app_integrated.py` - 集成应用
- ✅ `quickstart_web.py` - Web快速启动
- ✅ `stat_logger.py` - 统计日志
- ✅ `directory_explorer.py` - 目录浏览器

#### 2.7 检查和修复脚本
- ✅ `check_model_status.py` - 检查模型状态
- ✅ `check_pretrained_models.py` - 检查预训练模型
- ✅ `rebuild.py` - 重建脚本
- ✅ `force_retrain_cmin.py` - 强制重训练
- ✅ `run_cmin_experiments.py` - 运行实验
- ✅ `run_eval_acc_mcc.py` - 评估准确率

#### 2.8 更新脚本
- ✅ `update_from_github.py` - 从GitHub更新
- ✅ `git_update.bat` - Git更新(Windows批处理)
- ✅ `git_update.sh` - Git更新(Shell脚本)
- ✅ `git_upload.ps1` - Git上传(PowerShell)

---

### 3. 🧪 测试文件 (tests/ 和根目录)

#### 3.1 Phase 2测试
- ✅ `test_datapipe_cikm18.py` - DataPipe测试
- ✅ `test_model_usage.py` - 模型使用测试
- ✅ `verify_innovation_algorithms.py` - 算法验证

#### 3.2 API测试
- ✅ `test_api_debug.py` - API调试
- ✅ `test_api_fix.py` - API修复测试
- ✅ `test_api_prediction.py` - API预测测试

#### 3.3 实时功能测试
- ✅ `test_realtime.py` - 实时功能测试
- ✅ `test_realtime_prediction.py` - 实时预测测试

#### 3.4 UI测试
- ✅ `test_frontend_fix.py` - 前端修复测试
- ✅ `test_visualization.py` - 可视化测试

#### 3.5 基础测试
- ✅ `test.py` - 基础测试
- ✅ `test_quick.py` - 快速测试
- ✅ `test_simple.py` - 简单测试

---

### 4. 🔌 API模块 (api/)

#### 4.1 核心API
- ✅ `api/app.py` - Flask应用主文件
- ✅ `api/routes.py` - 路由定义
- ✅ `api/schemas.py` - 数据模式
- ✅ `api/middleware.py` - 中间件

#### 4.2 预测器
- ✅ `api/predictor.py` - 基础预测器
- ✅ `api/predictor_enhanced.py` - **增强预测器 (使用因果图)** ⭐

---

### 5. 🎨 前端资源 (static/)

#### 5.1 HTML页面
- ✅ `static/index.html` - 主页
- ✅ `static/visualization.html` - 基础可视化
- ✅ `static/advanced_visualization.html` - 高级可视化
- ✅ `static/realtime.html` - 实时监控
- ✅ `static/trading.html` - 交易平台

#### 5.2 CSS样式
- ✅ `static/css/main.css` - 主样式
- ✅ `static/css/trading.css` - 交易样式

#### 5.3 JavaScript
- ✅ `static/js/main.js` - 主脚本
- ✅ `static/js/trading.js` - 交易脚本

---

### 6. ⚙️ 配置文件

#### 6.1 项目配置
- ✅ `config.yml` - 主配置文件
- ✅ `config_acl18.yml` - **ACL18数据集配置 (Phase 2新增)** ⭐
- ✅ `requirements.txt` - Python依赖

#### 6.2 Docker配置
- ✅ `Dockerfile` - Docker构建文件
- ✅ `docker-compose.yml` - Docker编排

#### 6.3 安装脚本
- ✅ `setup.ps1` - 安装脚本(PowerShell)
- ✅ `setup_simple.ps1` - 简化安装
- ✅ `INSTALL_REALTIME.py` - 实时功能安装

#### 6.4 Git配置
- ✅ `.gitignore` - Git忽略文件
- ✅ `UPLOAD_STEPS.md` - 上传步骤
- ✅ `GITHUB_UPLOAD_GUIDE.md` - GitHub上传指南
- ✅ `github_update_guide.md` - GitHub更新指南

---

### 7. 📊 数据和模型

#### 7.1 因果图
- ✅ `causal_graph.npy` - 因果图矩阵 (31×31)
- ✅ `stock_matrix.npy` - 股票矩阵

#### 7.2 数据目录
- 📁 `data/` - 数据存储
  - 📁 `data/cikm18/` - CIKM18数据集
    - 📁 `data/cikm18/price/preprocessed/` - 价格数据 (88文件)
    - 📁 `data/cikm18/tweet/preprocessed/` - 推文数据 (88目录)
  - 📁 `data/StockTable/` - 股票表

#### 7.3 模型目录
- 📁 `checkpoints/` - 检查点存储
- 📁 `model/` - 模型文件
- 📁 `opt/` - 优化器状态

#### 7.4 结果目录
- 📁 `results/` - 训练结果
- 📁 `log/` - 日志文件
- 📁 `cache/` - 缓存文件

---

### 8. 🧩 模块和子项目

#### 8.1 因果模块
- 📁 `causal/` - 因果发现模块
  - ✅ `causal/__init__.py`
  - ✅ `causal/optimized_compute.py`

#### 8.2 模型模块
- 📁 `modules/` - 模型组件
  - ✅ `modules/base.py`
  - ✅ `modules/causal_module.py`
  - ✅ `modules/msgnet_module.py`
  - ✅ `modules/stocknet_module.py`
  - ✅ `modules/registry.py`

#### 8.3 CUTS+子项目
- 📁 `CUTS_Plus/` - CUTS+完整实现
  - 📁 `CUTS_Plus/data/`
  - 📁 `CUTS_Plus/model/`
  - 📁 `CUTS_Plus/utils/`
  - 📁 `CUTS_Plus/opt/`

#### 8.4 MSGNet子项目
- 📁 `MSGNet/` - MSGNet实现
  - ✅ `MSGNet/__init__.py`
  - ✅ `MSGNet/README.md`
  - 📁 `MSGNet/models/`
  - 📁 `MSGNet/layers/`
  - 📁 `MSGNet/utils/`

---

### 9. 📖 资源文件

#### 9.1 词向量
- 📁 `res/` - 资源文件
  - ✅ `res/glove.twitter.27B.100d.txt` - GloVe词向量

#### 9.2 演示文档
- ✅ `run_example.ipynb` - Jupyter示例
- ✅ `中期答辩_ICSFP.pptx` - 答辩PPT

---

## 📋 文件状态标注

### ✅ 状态说明

| 符号 | 含义 | 说明 |
|------|------|------|
| ⭐ | 核心文件 | Phase 2新增或重点更新的文件 |
| ✅ | 已完成 | 文件存在且功能完整 |
| ⚠️ | 待更新 | 存在但需要更新 |
| 🔄 | 进行中 | 正在开发或修改 |
| ❌ | 缺失 | 计划中但未创建 |
| 📁 | 目录 | 文件夹 |

---

## 🎯 Phase 2 核心文件清单

### Phase 2 - Day 1 (已完成) ✅

| 文件 | 类型 | 状态 | 行数 | 说明 |
|------|------|------|------|------|
| `dataset_manager.py` | 代码 | ✅ 完成 | 350+ | 数据集管理器 |
| `Main.py` | 代码 | ✅ 增强 | 200+ | 主训练脚本(CLI支持) |
| `config_acl18.yml` | 配置 | ✅ 自动生成 | 30+ | ACL18配置文件 |
| `PHASE2_MULTI_DATASET_SYSTEM.md` | 文档 | ✅ 完成 | 800+ | 详细实现报告 |
| `MULTI_DATASET_QUICK_REFERENCE.md` | 文档 | ✅ 完成 | 400+ | 快速参考手册 |
| `IMPLEMENTATION_SUMMARY.md` | 文档 | ✅ 完成 | 600+ | 实现总结 |

### Phase 2 - Day 2-3 (计划中) 🔄

| 文件 | 类型 | 状态 | 预计行数 | 说明 |
|------|------|------|----------|------|
| `unified_data_loader.py` | 代码 | ❌ 未创建 | 300+ | 统一数据加载器 |
| `causal_discovery_manager.py` | 代码 | ❌ 未创建 | 250+ | 因果发现管理器 |
| `transfer_entropy.py` | 代码 | ❌ 未创建 | 200+ | 传递熵实现 |

---

## 🗃️ 建议的文件整理方案

### 方案A: 按功能分类 (推荐) ⭐

```
HCSF/
├── 📚 docs/                      # 所有文档
│   ├── phase1/                  # Phase 1文档
│   ├── phase2/                  # Phase 2文档
│   ├── ui/                      # UI相关文档
│   ├── trading/                 # 交易平台文档
│   └── fixes/                   # 问题修复记录
│
├── 💻 src/                       # 核心代码
│   ├── core/                    # 核心模块
│   │   ├── Main.py
│   │   ├── Model.py
│   │   ├── Executor.py
│   │   └── DataPipe.py
│   │
│   ├── data/                    # 数据处理
│   │   ├── dataset_manager.py
│   │   ├── data_loader.py
│   │   └── download_cmin_dataset.py
│   │
│   ├── causal/                  # 因果发现
│   │   ├── granger_causality.py
│   │   ├── cuts_plus.py
│   │   └── compute_cuts_graph.py
│   │
│   └── utils/                   # 工具函数
│
├── 🧪 tests/                     # 所有测试
│   ├── unit/                    # 单元测试
│   ├── integration/             # 集成测试
│   └── api/                     # API测试
│
├── 🔌 api/                       # API模块
│   ├── app.py
│   ├── routes.py
│   ├── predictor_enhanced.py
│   └── schemas.py
│
├── 🎨 static/                    # 前端资源
│   ├── html/
│   ├── css/
│   └── js/
│
├── ⚙️ config/                    # 配置文件
│   ├── config.yml
│   ├── config_acl18.yml
│   └── config_cmin-cn.yml
│
├── 📊 data/                      # 数据目录
├── 💾 checkpoints/               # 模型检查点
├── 📈 results/                   # 结果输出
└── 📝 logs/                      # 日志文件
```

### 方案B: 保持现状 (最小改动)

仅创建文档分类:
```
docs/
├── phase1/                      # 移动Phase 1文档
├── phase2/                      # 移动Phase 2文档
├── ui/                          # 移动UI文档
├── trading/                     # 移动交易文档
└── archive/                     # 归档旧文档
```

---

## 📊 文件统计

### 按类型统计

| 类型 | 数量 | 说明 |
|------|------|------|
| Python代码 | 60+ | 包括测试文件 |
| Markdown文档 | 35+ | 包括所有MD文件 |
| 配置文件 | 8+ | YAML, JSON等 |
| HTML页面 | 5+ | 前端页面 |
| JavaScript | 5+ | 前端脚本 |
| CSS样式 | 3+ | 样式文件 |
| Shell脚本 | 4+ | 自动化脚本 |

### 按阶段统计

| 阶段 | 文件数 | 完成度 |
|------|--------|--------|
| Phase 1 | 15+ | 100% ✅ |
| Phase 2 Day 1 | 6 | 100% ✅ |
| Phase 2 Day 2-3 | 3 | 0% ⏳ |
| UI功能 | 20+ | 100% ✅ |
| 交易平台 | 10+ | 100% ✅ |

---

## 🔍 重要文件快速定位

### 需要频繁访问的文件

```bash
# 主程序
Main.py                          # 训练入口 ⭐

# 数据管理
dataset_manager.py               # 数据集管理 ⭐
DataPipe.py                      # 数据管道

# 模型
Model.py                         # 模型定义
Executor.py                      # 执行器

# 因果发现
granger_causality.py             # Granger因果
cuts_plus.py                     # CUTS+方法

# API
api/app.py                       # Flask应用
api/predictor_enhanced.py        # 增强预测器 ⭐

# 配置
config.yml                       # 主配置
config_acl18.yml                 # ACL18配置 ⭐

# 文档
PHASE2_MULTI_DATASET_SYSTEM.md   # Phase 2文档 ⭐
MULTI_DATASET_QUICK_REFERENCE.md # 快速参考 ⭐
IMPLEMENTATION_SUMMARY.md        # 实现总结 ⭐
```

### 历史参考文件

```bash
# 问题修复记录
INNOVATION_ALGORITHMS_REPORT.md  # 算法验证
MODEL_USAGE_FIX_COMPLETE.md      # 模型使用修复
CIKM18_DATASET_SETUP_SUCCESS.md  # 数据准备

# 可行性分析
MULTI_DATASET_FEASIBILITY.md     # 多数据集可行性

# Phase 1总结
PHASE1_SUMMARY.md                # Phase 1总结
```

---

## ✅ 下一步建议

### 立即执行 (推荐)

1. **创建docs目录结构**
   ```bash
   mkdir -p docs/{phase1,phase2,ui,trading,fixes,archive}
   ```

2. **移动文档文件**
   - Phase 1文档 → `docs/phase1/`
   - Phase 2文档 → `docs/phase2/`
   - UI文档 → `docs/ui/`
   - 交易文档 → `docs/trading/`
   - 修复记录 → `docs/fixes/`

3. **保持代码结构**
   - 核心代码保持在根目录
   - 避免影响现有导入路径

4. **更新README.md**
   - 添加新的目录结构说明
   - 更新文档索引

### 可选执行

1. **创建src目录** (需要更新导入)
2. **重构测试目录** (统一测试结构)
3. **清理备份文件** (归档旧备份)

---

## 📝 整理检查清单

- [x] ✅ 列出所有文件
- [x] ✅ 按类型分类
- [x] ✅ 标注文件状态
- [x] ✅ 统计文件数量
- [x] ✅ 识别核心文件
- [x] ✅ 提出整理方案
- [ ] ⏳ 执行文件移动
- [ ] ⏳ 更新文档索引
- [ ] ⏳ 验证链接正确性

---

**创建日期**: 2025-11-05  
**版本**: v1.0  
**状态**: ✅ 分析完成,待执行整理
