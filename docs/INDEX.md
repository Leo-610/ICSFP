# 📚 ICSFP 文档索引

> **更新日期**: 2025-11-05  
> **项目状态**: Phase 2 - Day 1 完成 (70%)  
> **文档总数**: 35+

---

## 🎯 快速导航

### 🚀 新手开始
1. [📖 README.md](../README.md) - 项目主文档
2. [⚡ QUICKSTART.md](../QUICKSTART.md) - 快速开始指南
3. [📋 FILE_MANIFEST.md](../FILE_MANIFEST.md) - 文件清单

### 💡 Phase 2 - 多数据集系统 (最新)
1. [📊 PHASE2_MULTI_DATASET_SYSTEM.md](phase2/PHASE2_MULTI_DATASET_SYSTEM.md) - **详细实现报告** ⭐
2. [⚡ MULTI_DATASET_QUICK_REFERENCE.md](phase2/MULTI_DATASET_QUICK_REFERENCE.md) - **快速参考手册** ⭐
3. [📝 IMPLEMENTATION_SUMMARY.md](phase2/IMPLEMENTATION_SUMMARY.md) - **实现总结** ⭐

---

## 📁 文档分类

### 1️⃣ Phase 1 文档 (已完成 ✅)

**位置**: `docs/phase1/`

| 文档 | 说明 | 状态 |
|------|------|------|
| [PHASE1_SUMMARY.md](phase1/PHASE1_SUMMARY.md) | Phase 1总结报告 | ✅ 完成 |
| [CIKM18_DATASET_SETUP_SUCCESS.md](phase1/CIKM18_DATASET_SETUP_SUCCESS.md) | 数据集准备成功报告 | ✅ 完成 |
| [INNOVATION_ALGORITHMS_REPORT.md](phase1/INNOVATION_ALGORITHMS_REPORT.md) | 创新算法验证报告 | ✅ 完成 |
| [MULTI_DATASET_FEASIBILITY.md](phase1/MULTI_DATASET_FEASIBILITY.md) | 多数据集可行性分析 | ✅ 完成 |

**主要内容**:
- ✅ 算法验证 (Granger, CUTS+, 因果图)
- ✅ 数据准备 (CIKM18数据集)
- ✅ 可行性分析 (多数据集系统)
- ✅ 模型验证 (深度学习预测)

---

### 2️⃣ Phase 2 文档 (进行中 🔄)

**位置**: `docs/phase2/`

| 文档 | 说明 | 状态 | 行数 |
|------|------|------|------|
| [PHASE2_MULTI_DATASET_SYSTEM.md](phase2/PHASE2_MULTI_DATASET_SYSTEM.md) | 详细实现报告 | ✅ Day 1完成 | 800+ |
| [MULTI_DATASET_QUICK_REFERENCE.md](phase2/MULTI_DATASET_QUICK_REFERENCE.md) | 快速参考手册 | ✅ Day 1完成 | 400+ |
| [IMPLEMENTATION_SUMMARY.md](phase2/IMPLEMENTATION_SUMMARY.md) | 实现总结 | ✅ Day 1完成 | 600+ |

**主要内容**:
- ✅ 数据集管理器 (dataset_manager.py)
- ✅ 增强的Main.py (16个CLI参数)
- ✅ 多数据集支持 (ACL18, CIKM18, CMIN-CN)
- ✅ 因果方法选择 (Granger, CUTS+, Transfer Entropy)
- ⏳ 统一数据加载器 (Day 2计划)
- ⏳ 因果发现管理器 (Day 2-3计划)

**使用示例**:
```bash
# 查看所有数据集
python Main.py --list_datasets

# 检查数据集状态
python Main.py --check_dataset ACL18

# 训练模型
python Main.py --dataset ACL18 --causal_method granger --mode train
```

---

### 3️⃣ UI 相关文档

**位置**: `docs/ui/`

| 文档 | 说明 | 状态 |
|------|------|------|
| [UI_OPTIMIZATION_REPORT.md](ui/UI_OPTIMIZATION_REPORT.md) | UI优化报告 | ✅ 完成 |
| [UI_QUICK_GUIDE.md](ui/UI_QUICK_GUIDE.md) | UI快速指南 | ✅ 完成 |
| [UI_TECH_ENHANCEMENT_REPORT.md](ui/UI_TECH_ENHANCEMENT_REPORT.md) | UI技术增强报告 | ✅ 完成 |
| [GLASSMORPHISM_UPGRADE.md](ui/GLASSMORPHISM_UPGRADE.md) | 玻璃态升级报告 | ✅ 完成 |
| [MOUSE_EFFECTS_REPORT.md](ui/MOUSE_EFFECTS_REPORT.md) | 鼠标效果报告 | ✅ 完成 |
| [STYLE_UNIFICATION_COMPLETE.md](ui/STYLE_UNIFICATION_COMPLETE.md) | 样式统一完成报告 | ✅ 完成 |
| [BUGS_FIXED_UI_IMPROVEMENTS.md](ui/BUGS_FIXED_UI_IMPROVEMENTS.md) | Bug修复和UI改进 | ✅ 完成 |

**主要功能**:
- 🎨 玻璃态设计
- 🖱️ 鼠标特效
- 📊 可视化增强
- 🎯 响应式布局

---

### 4️⃣ 交易平台文档

**位置**: `docs/trading/`

| 文档 | 说明 | 状态 |
|------|------|------|
| [TRADING_PLATFORM_GUIDE.md](trading/TRADING_PLATFORM_GUIDE.md) | 交易平台指南 | ✅ 完成 |
| [TRADING_QUICKSTART.md](trading/TRADING_QUICKSTART.md) | 交易快速开始 | ✅ 完成 |
| [TRADING_SUMMARY.md](trading/TRADING_SUMMARY.md) | 交易功能总结 | ✅ 完成 |
| [TRADING_DEMO_SCRIPT.md](trading/TRADING_DEMO_SCRIPT.md) | 交易演示脚本 | ✅ 完成 |
| [README_TRADING.md](trading/README_TRADING.md) | 交易平台README | ✅ 完成 |

**主要功能**:
- 📈 实时行情监控
- 💰 模拟交易
- 📊 持仓管理
- 💹 收益统计

---

### 5️⃣ 问题修复记录

**位置**: `docs/fixes/`

| 文档 | 说明 | 状态 |
|------|------|------|
| [MODEL_STATUS_VERIFICATION.md](fixes/MODEL_STATUS_VERIFICATION.md) | 模型状态验证 | ✅ 完成 |
| [MODEL_USAGE_FIX_COMPLETE.md](fixes/MODEL_USAGE_FIX_COMPLETE.md) | 模型使用修复完成 | ✅ 完成 |
| [MODEL_LOADED_SUCCESS.md](fixes/MODEL_LOADED_SUCCESS.md) | 模型加载成功验证 | ✅ 完成 |
| [MODEL_STATUS_FIX.md](fixes/MODEL_STATUS_FIX.md) | 模型状态修复 | ✅ 完成 |
| [CRITICAL_MODEL_USAGE_ISSUE.md](fixes/CRITICAL_MODEL_USAGE_ISSUE.md) | 关键问题记录 | ✅ 完成 |
| [PREDICTION_MECHANISM.md](fixes/PREDICTION_MECHANISM.md) | 预测机制说明 | ✅ 完成 |
| [VERIFY_FIXES.md](fixes/VERIFY_FIXES.md) | 修复验证 | ✅ 完成 |

**修复历程**:
1. 发现问题: 模型未真实使用
2. 诊断分析: 预测器使用随机方法
3. 修复实施: 重构predictor_enhanced.py
4. 验证成功: 深度学习预测 (confidence ~0.997)

---

### 6️⃣ 集成文档

**位置**: `docs/`

| 文档 | 说明 | 状态 |
|------|------|------|
| [INTEGRATION_GUIDE.md](INTEGRATION_GUIDE.md) | 集成指南 | ✅ 完成 |
| [INTEGRATION_SUMMARY.md](INTEGRATION_SUMMARY.md) | 集成总结 | ✅ 完成 |
| [FINAL_STATUS_REPORT.md](FINAL_STATUS_REPORT.md) | 最终状态报告 | ✅ 完成 |

---

## 🔍 按主题查找

### 数据集相关
- [CIKM18_DATASET_SETUP_SUCCESS.md](phase1/CIKM18_DATASET_SETUP_SUCCESS.md) - 数据集准备
- [MULTI_DATASET_FEASIBILITY.md](phase1/MULTI_DATASET_FEASIBILITY.md) - 多数据集可行性
- [PHASE2_MULTI_DATASET_SYSTEM.md](phase2/PHASE2_MULTI_DATASET_SYSTEM.md) - 多数据集实现

### 算法相关
- [INNOVATION_ALGORITHMS_REPORT.md](phase1/INNOVATION_ALGORITHMS_REPORT.md) - 算法验证
- [PREDICTION_MECHANISM.md](fixes/PREDICTION_MECHANISM.md) - 预测机制

### 模型相关
- [MODEL_USAGE_FIX_COMPLETE.md](fixes/MODEL_USAGE_FIX_COMPLETE.md) - 模型使用修复
- [MODEL_LOADED_SUCCESS.md](fixes/MODEL_LOADED_SUCCESS.md) - 模型加载验证

### UI相关
- [UI_OPTIMIZATION_REPORT.md](ui/UI_OPTIMIZATION_REPORT.md) - UI优化
- [GLASSMORPHISM_UPGRADE.md](ui/GLASSMORPHISM_UPGRADE.md) - 玻璃态设计

### 交易平台
- [TRADING_PLATFORM_GUIDE.md](trading/TRADING_PLATFORM_GUIDE.md) - 完整指南
- [TRADING_QUICKSTART.md](trading/TRADING_QUICKSTART.md) - 快速开始

---

## 📊 文档统计

### 按阶段

| 阶段 | 文档数 | 完成度 |
|------|--------|--------|
| Phase 1 | 4 | 100% ✅ |
| Phase 2 | 3 | Day 1 完成 ✅ |
| UI功能 | 7 | 100% ✅ |
| 交易平台 | 5 | 100% ✅ |
| 问题修复 | 7 | 100% ✅ |
| 集成文档 | 3 | 100% ✅ |

### 按类型

| 类型 | 数量 |
|------|------|
| 实现报告 | 10+ |
| 快速指南 | 5+ |
| 问题修复 | 7+ |
| 技术文档 | 8+ |
| 总结报告 | 5+ |

---

## 🎯 推荐阅读路径

### 路径1: 新手入门
1. [README.md](../README.md)
2. [QUICKSTART.md](../QUICKSTART.md)
3. [MULTI_DATASET_QUICK_REFERENCE.md](phase2/MULTI_DATASET_QUICK_REFERENCE.md)

### 路径2: 算法研究
1. [INNOVATION_ALGORITHMS_REPORT.md](phase1/INNOVATION_ALGORITHMS_REPORT.md)
2. [PREDICTION_MECHANISM.md](fixes/PREDICTION_MECHANISM.md)
3. [PHASE2_MULTI_DATASET_SYSTEM.md](phase2/PHASE2_MULTI_DATASET_SYSTEM.md)

### 路径3: 系统开发
1. [MULTI_DATASET_FEASIBILITY.md](phase1/MULTI_DATASET_FEASIBILITY.md)
2. [IMPLEMENTATION_SUMMARY.md](phase2/IMPLEMENTATION_SUMMARY.md)
3. [INTEGRATION_SUMMARY.md](INTEGRATION_SUMMARY.md)

### 路径4: UI/交易开发
1. [UI_OPTIMIZATION_REPORT.md](ui/UI_OPTIMIZATION_REPORT.md)
2. [TRADING_PLATFORM_GUIDE.md](trading/TRADING_PLATFORM_GUIDE.md)
3. [FINAL_STATUS_REPORT.md](FINAL_STATUS_REPORT.md)

---

## 🔧 维护说明

### 添加新文档

1. 确定文档类别
2. 放入对应目录
3. 更新本索引文件
4. 更新README.md链接

### 文档命名规范

- 使用大写字母和下划线
- 使用描述性名称
- 添加版本后缀 (如需要)
- 示例: `FEATURE_NAME_REPORT.md`

### 目录结构

```
docs/
├── phase1/          # Phase 1文档
├── phase2/          # Phase 2文档
├── ui/              # UI文档
├── trading/         # 交易文档
├── fixes/           # 修复记录
├── archive/         # 归档文档
└── INDEX.md         # 本索引文件
```

---

## 📞 相关资源

### 项目文档
- [PROJECT_STRUCTURE.md](../PROJECT_STRUCTURE.md) - 项目结构说明
- [FILE_MANIFEST.md](../FILE_MANIFEST.md) - 文件清单

### API文档
- [docs/API_GUIDE.md](API_GUIDE.md) - API使用指南

### 其他资源
- GitHub仓库: Leo-610/ICSFP
- 分支: main

---

**维护者**: GitHub Copilot  
**最后更新**: 2025-11-05  
**版本**: v1.0
