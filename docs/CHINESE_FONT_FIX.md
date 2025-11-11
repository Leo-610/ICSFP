# 中文字体支持 - 快速修复指南

## 🐛 问题：图表中中文显示为方框

如果您在生成的图表中看到中文字符显示为小方框 `□□□`，这是matplotlib的中文字体问题。

## ✅ 解决方案

### 方法1：使用可视化工具（推荐）

**步骤1**: 导入并配置
```python
from utils.visualization import setup_chinese_font

# 在脚本开头调用
setup_chinese_font()
```

**步骤2**: 使用可视化函数
```python
from utils.visualization import plot_causal_graph

plot_causal_graph(
    causal_graph=your_graph,
    stock_names=['股票A', '股票B', '股票C'],  # 支持中文！
    title='因果关系图',  # 支持中文！
    save_path='graph.png'
)
```

### 方法2：手动配置matplotlib

在任何绘图代码之前添加：

```python
import matplotlib.pyplot as plt

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'SimSun']
plt.rcParams['axes.unicode_minus'] = False  # 解决负号显示问题
```

## 📦 可用的可视化函数

### 1. 因果图热图
```python
from utils.visualization import plot_causal_graph

plot_causal_graph(
    causal_graph=graph,        # numpy数组
    stock_names=['股票1', '股票2'],
    title='因果关系图',
    save_path='causal_graph.png',
    cmap='hot'                 # 颜色映射
)
```

### 2. 方法对比
```python
from utils.visualization import plot_method_comparison

results = {
    'Granger': (graph1, info1),
    '传递熵': (graph2, info2),
    'CUTS+': (graph3, info3)
}

plot_method_comparison(
    results=results,
    stock_names=['股票A', 'B', 'C'],
    save_path='comparison.png'
)
```

### 3. 敏感性分析
```python
from utils.visualization import plot_sensitivity_analysis

plot_sensitivity_analysis(
    param_values=[0.1, 0.2, 0.3],
    metrics={
        '边数': [44, 25, 13],
        '稀疏度': [0.31, 0.61, 0.80]
    },
    param_name='阈值',
    save_path='sensitivity.png'
)
```

## 🔍 检查可用字体

如果仍然有问题，检查系统字体：

```python
import matplotlib.font_manager as fm

# 列出所有中文字体
fonts = [f.name for f in fm.fontManager.ttflist]
chinese_fonts = [f for f in fonts if any(x in f for x in ['Hei', 'Song', 'Kai', 'YaHei'])]
print("可用中文字体:", chinese_fonts)
```

## 📖 完整示例

```python
# 完整的工作示例
import numpy as np
from causal_discovery_manager import CausalDiscoveryManager
from utils.visualization import setup_chinese_font, plot_causal_graph

# 1. 配置中文字体
setup_chinese_font()

# 2. 生成数据
data = np.random.randn(200, 5)
stock_names = ['工商银行', '中国平安', '贵州茅台', '招商银行', '五粮液']

# 3. 计算因果图
manager = CausalDiscoveryManager()
causal_graph, info = manager.compute_causal_graph(
    data=data,
    stock_names=stock_names,
    method='cuts_plus'
)

# 4. 绘制图表（中文正常显示！）
plot_causal_graph(
    causal_graph=causal_graph,
    stock_names=stock_names,
    title='股票因果关系分析',
    save_path='我的因果图.png',
    figsize=(10, 8)
)

print("✅ 图表已保存，中文显示正常！")
```

## 🎨 支持的字体列表

默认自动检测以下字体（按优先级）：

1. **Microsoft YaHei** (微软雅黑) - Windows 推荐
2. **SimHei** (黑体)
3. **SimSun** (宋体)
4. **KaiTi** (楷体)
5. **FangSong** (仿宋)
6. **STSong** (华文宋体)
7. **STKaiti** (华文楷体)

## 💡 提示

- 所有新项目请使用 `utils/visualization.py`
- 一次配置，所有图表生效
- 支持保存为 PNG、PDF、SVG 等格式
- 自动处理高DPI显示

## 📚 更多信息

- 详细文档: `docs/VISUALIZATION_GUIDE.md` (API文档)
- 示例代码: `examples/example_cuts_plus.py`
- 源代码: `utils/visualization.py`

---

**更新日期**: 2025-11-11  
**解决问题**: 图表中文显示为方框  
**状态**: ✅ 已修复
