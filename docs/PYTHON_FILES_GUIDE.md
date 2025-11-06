# 📂 Python代码文件分类说明

> **更新日期**: 2025-11-05  
> **根目录Python文件**: 47个  
> **说明**: 代码文件保留在根目录以保持导入路径正确

---

## 📌 为什么代码文件不移动?

### ✅ 保留在根目录的原因:

1. **导入路径依赖** 
   - Python模块相互导入依赖当前路径
   - 移动会破坏 `from Model import Model` 等导入

2. **运行脚本方便**
   - `python Main.py` 直接运行
   - 无需修改PYTHONPATH

3. **工具链兼容**
   - IDE自动补全依赖文件位置
   - 测试框架依赖目录结构

### ⚠️ 只移动文档文件:
- ✅ MD文档 → `docs/` 子目录
- ✅ PY代码 → 保留根目录

---

## 🗂️ 根目录Python文件分类

### 1️⃣ 核心训练模块 (9个)

| 文件 | 功能 | 状态 |
|------|------|------|
| `Main.py` | **主训练脚本 (CLI版本)** ⭐ | ✅ Phase 2增强 |
| `Model.py` | 模型定义 (VAE+GRU+因果图) | ✅ 核心 |
| `Executor.py` | 训练执行器 | ✅ 核心 |
| `DataPipe.py` | 数据管道 | ✅ 核心 |
| `ConfigLoader.py` | 配置加载器 | ✅ 核心 |
| `metrics.py` | 评估指标 | ✅ 核心 |
| `pipeline.py` | 训练流程 | ✅ 工具 |
| `quick_train.py` | 快速训练 | ✅ 工具 |
| `train_full.py` | 完整训练 | ✅ 工具 |

**用途**: 模型训练的核心组件

---

### 2️⃣ 数据处理模块 (7个)

| 文件 | 功能 | 状态 |
|------|------|------|
| `dataset_manager.py` | **数据集管理器** ⭐ | ✅ Phase 2新增 |
| `data_loader.py` | 数据加载器 | ✅ 核心 |
| `download_cmin_dataset.py` | 数据下载工具 | ✅ 工具 |
| `prepare_cmin_dataset.py` | 数据准备 | ✅ 工具 |
| `check_cmin_data.py` | 数据检查 | ✅ 工具 |
| `create_test_data.py` | 测试数据生成 | ✅ 工具 |
| `generate_mock_data.py` | Mock数据生成 | ✅ 工具 |

**用途**: 数据集管理和预处理

---

### 3️⃣ 因果发现模块 (3个)

| 文件 | 功能 | 状态 |
|------|------|------|
| `granger_causality.py` | Granger因果检验 (318行) | ✅ 完整实现 |
| `cuts_plus.py` | CUTS+神经网络方法 (448行) | ✅ 完整实现 |
| `compute_cuts_graph.py` | CUTS+因果图生成 | ✅ 完整实现 |

**用途**: 因果关系发现

**命令**:
```bash
python granger_causality.py      # 生成 causal_graph.npy
python compute_cuts_graph.py     # 生成 causal_graph_cuts_plus.npy
```

---

### 4️⃣ 测试文件 (15个)

#### 验证测试 (3个)
| 文件 | 功能 |
|------|------|
| `test_datapipe_cikm18.py` | DataPipe测试 |
| `test_model_usage.py` | 模型使用测试 |
| `verify_innovation_algorithms.py` | **算法验证** ⭐ |

#### API测试 (3个)
| 文件 | 功能 |
|------|------|
| `test_api_debug.py` | API调试 |
| `test_api_fix.py` | API修复测试 |
| `test_api_prediction.py` | API预测测试 |

#### 实时功能测试 (2个)
| 文件 | 功能 |
|------|------|
| `test_realtime.py` | 实时功能测试 |
| `test_realtime_prediction.py` | 实时预测测试 |

#### UI测试 (2个)
| 文件 | 功能 |
|------|------|
| `test_frontend_fix.py` | 前端修复测试 |
| `test_visualization.py` | 可视化测试 |

#### 基础测试 (3个)
| 文件 | 功能 |
|------|------|
| `test.py` | 基础测试 |
| `test_quick.py` | 快速测试 |
| `test_simple.py` | 简单测试 |

#### 实验脚本 (2个)
| 文件 | 功能 |
|------|------|
| `run_cmin_experiments.py` | CMIN实验 |
| `run_eval_acc_mcc.py` | 准确率评估 |

**用途**: 功能测试和验证

---

### 5️⃣ 应用和界面 (5个)

| 文件 | 功能 | 状态 |
|------|------|------|
| `app_integrated.py` | 集成应用 | ✅ 完整 |
| `quickstart_web.py` | Web快速启动 | ✅ 完整 |
| `quickstart.py` | 命令行快速启动 | ✅ 完整 |
| `StockPredictionViewer.py` | 预测查看器 | ✅ 完整 |
| `generate_ppt.py` | PPT生成工具 | ✅ 工具 |

**用途**: 用户界面和快速启动

---

### 6️⃣ 检查和诊断工具 (4个)

| 文件 | 功能 | 状态 |
|------|------|------|
| `check_model_status.py` | 模型状态检查 | ✅ 诊断 |
| `check_pretrained_models.py` | 预训练模型检查 | ✅ 诊断 |
| `gpu_check.py` | GPU检查 | ✅ 工具 |
| `directory_explorer.py` | 目录浏览器 | ✅ 工具 |

**用途**: 系统诊断和检查

---

### 7️⃣ 维护和更新工具 (4个)

| 文件 | 功能 | 状态 |
|------|------|------|
| `rebuild.py` | 重建脚本 | ✅ 维护 |
| `force_retrain_cmin.py` | 强制重训练 | ✅ 维护 |
| `update_from_github.py` | GitHub更新 | ✅ 维护 |
| `stat_logger.py` | 统计日志 | ✅ 工具 |

**用途**: 项目维护和更新

---

### 8️⃣ 安装脚本 (1个)

| 文件 | 功能 | 状态 |
|------|------|------|
| `INSTALL_REALTIME.py` | 实时功能安装 | ✅ 安装 |

**用途**: 依赖安装

---

## 📊 统计总结

| 类别 | 文件数 | 用途 |
|------|--------|------|
| 核心训练模块 | 9 | 模型训练核心 |
| 数据处理模块 | 7 | 数据管理 |
| 因果发现模块 | 3 | 因果关系发现 ⭐ |
| 测试文件 | 15 | 功能测试验证 |
| 应用界面 | 5 | 用户交互 |
| 检查工具 | 4 | 系统诊断 |
| 维护工具 | 4 | 项目维护 |
| 安装脚本 | 1 | 环境配置 |
| **总计** | **48** | |

---

## 🎯 常用文件快速定位

### 启动训练
```bash
# Phase 2增强版 (推荐)
python Main.py --dataset ACL18 --mode train

# 快速训练
python quick_train.py

# 完整训练
python train_full.py
```

### 数据管理
```bash
# 管理数据集 (Phase 2新增)
python dataset_manager.py

# 下载数据
python download_cmin_dataset.py

# 检查数据
python check_cmin_data.py
```

### 因果发现
```bash
# Granger方法
python granger_causality.py

# CUTS+方法
python compute_cuts_graph.py
```

### 测试验证
```bash
# 验证算法
python verify_innovation_algorithms.py

# 测试DataPipe
python test_datapipe_cikm18.py

# 测试模型使用
python test_model_usage.py
```

### 启动应用
```bash
# Web应用
python quickstart_web.py

# 集成应用
python app_integrated.py
```

---

## 🔍 文件查找技巧

### 按功能查找
```bash
# 查找所有测试文件
Get-ChildItem -Filter "test*.py"

# 查找因果相关
Get-ChildItem -Filter "*causal*.py"

# 查找数据相关
Get-ChildItem -Filter "*data*.py"
```

### 按大小查找
```bash
# 查找大文件 (>100KB)
Get-ChildItem *.py | Where-Object {$_.Length -gt 100KB} | Sort-Object Length -Descending
```

---

## 📝 文件命名规范

### 已有规范:
- `test_*.py` - 测试文件
- `check_*.py` - 检查工具
- `run_*.py` - 运行脚本
- `*_cmin*.py` - CMIN数据集相关
- `quick*.py` - 快速工具

### Phase 2新增规范:
- `*_manager.py` - 管理器类
- `unified_*.py` - 统一接口类 (计划)
- `*_discovery.py` - 发现算法 (计划)

---

## ⚠️ 注意事项

### 不要移动Python文件!
❌ **错误做法**:
```bash
# 不要这样做!
mkdir src/
mv *.py src/  # 这会破坏导入
```

✅ **正确做法**:
```bash
# 只移动文档
mv *.md docs/  # 文档可以移动

# 代码保持原位
# Python文件留在根目录
```

### 为什么?
1. **导入依赖**: `from Model import Model` 依赖当前目录
2. **相对路径**: 代码中使用相对路径加载数据
3. **配置文件**: config.yml中的路径是相对根目录

### 如果真要重构目录结构:
1. 创建 `src/` 目录
2. 移动文件
3. 修改所有导入语句
4. 更新配置文件路径
5. 添加 `__init__.py`
6. 修改 PYTHONPATH

**工作量大,风险高,暂不推荐!**

---

## 🎯 目录结构总览

```
HCSF/
├── 📄 README.md                    # 项目主文档
├── 📄 QUICKSTART.md                # 快速开始
├── 📄 README_ICAST.md              # ICAST说明
│
├── 🐍 [48个Python文件]            # 代码保持根目录
│   ├── Main.py ⭐                 # 主训练脚本
│   ├── Model.py                   # 模型定义
│   ├── dataset_manager.py ⭐      # 数据集管理器
│   ├── granger_causality.py       # Granger因果
│   ├── cuts_plus.py               # CUTS+方法
│   └── ...
│
├── 📁 docs/                       # 文档目录
│   ├── 📄 INDEX.md                # 文档索引
│   ├── 📁 phase1/                 # Phase 1文档
│   ├── 📁 phase2/                 # Phase 2文档 ⭐
│   ├── 📁 ui/                     # UI文档
│   ├── 📁 trading/                # 交易文档
│   ├── 📁 fixes/                  # 修复记录
│   └── 📁 archive/                # 归档文档
│
├── 📁 api/                        # API模块
├── 📁 modules/                    # 模型模块
├── 📁 causal/                     # 因果模块
├── 📁 static/                     # 前端资源
├── 📁 data/                       # 数据目录
├── 📁 checkpoints/                # 模型检查点
└── 📁 results/                    # 结果输出
```

---

## 🎉 整理成果

### ✅ 已完成:
- ✅ 文档分类整理 (29个MD文件)
- ✅ 创建docs子目录结构
- ✅ 文档索引创建
- ✅ 代码文件分类说明

### ✅ 目录清晰度:
- **根目录**: 3个核心MD + 48个PY文件
- **docs/**: 29个文档,分类清晰
- **其他**: 模块化子目录

### 💡 带来的好处:
- 🎯 文档易查找
- 🚀 代码易运行
- 📦 结构专业化
- 🔍 分类清晰化

---

**创建日期**: 2025-11-05  
**维护者**: GitHub Copilot  
**版本**: v1.0
