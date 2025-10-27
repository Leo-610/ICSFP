# iCast - Intelligent Causal Stock Forecasting Platform

![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)
![Python](https://img.shields.io/badge/python-3.8+-green.svg)
![License](https://img.shields.io/badge/license-MIT-orange.svg)

**iCast** (Intelligent Causal Stock Forecasting Platform) 是一个基于多源异构数据融合与因果推理的智能股票预测分析平台，集成了深度学习、因果发现和时间序列分析技术。

---

## 🎯 核心特性

- **多模态数据融合**：整合价格、社交媒体文本、技术指标等多源数据
- **动态因果发现**：自动识别股票间的因果关系（Granger、CUTS+等方法）
- **深度学习预测**：基于VAE、GNN的股票涨跌预测
- **可解释性分析**：预测归因和因果链路追踪
- **RESTful API**：便捷的Web服务接口
- **GPU加速**：支持CUDA加速的因果图计算

---

## 📦 安装

### 环境要求

- Python 3.8+
- CUDA 11.7+ (可选，用于GPU加速)
- 4GB+ RAM
- 10GB+ 磁盘空间

### 快速安装

```bash
# 克隆仓库
git clone https://github.com/wenrui-jiang/HCSF.git
cd HCSF

# 创建虚拟环境
conda create -n icast python=3.8
conda activate icast

# 安装依赖
pip install -r requirements.txt

# 验证安装
python -c "import torch; print('CUDA available:', torch.cuda.is_available())"
```

---

## 🚀 快速开始

### 1. 基础预测

```python
from Model import Model
from Executor import Executor
import numpy as np

# 加载因果图
graph = np.load('causal_graph.npy')

# 创建模型
model = Model(graph=graph)

# 训练
executor = Executor(model, device='cuda')
executor.train_and_dev()

# 测试
executor.restore_and_test()
```

### 2. 使用API服务

启动API服务器：

```bash
python api/app.py
```

调用API：

```python
import requests

# 单股票预测
response = requests.post('http://localhost:5000/api/v1/predict/single', json={
    'stock_symbol': 'AAPL',
    'start_date': '2015-10-01',
    'end_date': '2015-10-05',
    'use_causal': True
})

print(response.json())
```

### 3. 因果图计算

```python
from causal import OptimizedCausalGraphComputer
import numpy as np

# 准备数据
data = np.random.randn(100, 10)  # (时间步, 股票数)
stock_names = [f'Stock_{i}' for i in range(10)]

# 计算因果图
computer = OptimizedCausalGraphComputer(method='granger', device='cuda')
graph, info = computer.compute_graph(data, stock_names)

print(f"Causal graph shape: {graph.shape}")
print(f"Sparsity: {info['sparsity']:.2%}")
```

---

## 📚 API文档

### 预测接口

#### POST `/api/v1/predict/single`

单只股票预测

**请求体：**
```json
{
  "stock_symbol": "AAPL",
  "start_date": "2015-10-01",
  "end_date": "2015-10-05",
  "use_causal": true
}
```

**响应：**
```json
{
  "status": "success",
  "data": {
    "stock_symbol": "AAPL",
    "predictions": [
      {
        "date": "2015-10-01",
        "predicted_direction": "UP",
        "confidence": 0.85,
        "probabilities": {"UP": 0.85, "DOWN": 0.15}
      }
    ]
  }
}
```

#### POST `/api/v1/predict/batch`

批量股票预测

**请求体：**
```json
{
  "stock_symbols": ["AAPL", "GOOG", "MSFT"],
  "start_date": "2015-10-01",
  "end_date": "2015-10-05",
  "use_causal": true
}
```

### 因果图接口

#### GET `/api/v1/causal/graph`

获取因果图

**查询参数：**
- `stocks`: 逗号分隔的股票代码（可选）
- `threshold`: 因果关系阈值（默认0.3）

**响应：**
```json
{
  "status": "success",
  "data": {
    "graph": [[0.0, 0.5, ...], ...],
    "stocks": ["AAPL", "GOOG", ...],
    "edges": [
      {"from": "AAPL", "to": "GOOG", "weight": 0.5}
    ]
  }
}
```

#### GET `/api/v1/causal/influence`

获取股票因果影响力分析

**查询参数：**
- `stock`: 股票代码（必需）
- `top_k`: 返回前k个影响最大的股票（默认10）

---

## 🏗️ 项目结构

```
HCSF/
├── api/                    # Web API模块
│   ├── app.py             # Flask应用
│   ├── routes.py          # API路由
│   ├── predictor.py       # 预测器封装
│   ├── schemas.py         # 数据模式
│   └── middleware.py      # 中间件
├── causal/                # 因果发现模块
│   ├── optimized_compute.py  # 优化的因果图计算
│   └── __init__.py
├── modules/               # 模型模块
│   ├── base.py
│   ├── causal_module.py
│   ├── msgnet_module.py
│   └── stocknet_module.py
├── MSGNet/                # MSGNet时序预测模型
├── data/                  # 数据目录
├── checkpoints/           # 模型检查点
├── config.yml             # 配置文件
├── Model.py               # 主模型
├── Executor.py            # 训练执行器
├── DataPipe.py            # 数据管道
├── Main.py                # 主入口
└── requirements.txt       # 依赖包
```

---

## ⚙️ 配置

编辑 `config.yml` 来自定义模型和训练参数：

```yaml
model:
  variant_type: 'hedge'     # hedge, tech, fund
  alpha: 0.5                # 因果权重 (0-1)
  dropout_vmd_in: 0.3
  max_n_days: 5
  max_n_msgs: 30
  max_n_words: 40

causal_discovery:
  method: 'granger'         # granger, cuts_plus
  significance_level: 0.05

training:
  device: 'cuda'            # cuda or cpu
  learning_rate: 0.001
  num_epochs: 15
  batch_size: 32
```

---

## 🧪 运行测试

```bash
# 单元测试
python -m pytest tests/

# 集成测试
python test.py

# API测试
python tests/test_api.py
```

---

## 📊 性能基准

| 数据集 | 准确率 | MCC | 计算时间 |
|--------|-------|-----|---------|
| ACL18  | 58.2% | 0.165 | 15min |
| CMIN-CN | 61.5% | 0.230 | 20min |

*测试环境: NVIDIA RTX 3090, Intel i9-10900K*

---

## 🛠️ 开发指南

### 添加新的因果发现方法

1. 在 `causal/optimized_compute.py` 中添加方法：

```python
def _compute_my_method(self, data, **kwargs):
    # 实现你的因果发现算法
    graph = ...
    return graph, {'info': 'value'}
```

2. 在 `compute_graph` 中注册：

```python
elif self.method == 'my_method':
    graph, info = self._compute_my_method(data, **kwargs)
```

### 添加新的预测模型

1. 在 `modules/` 下创建新模块
2. 继承 `BackboneModuleBase`
3. 实现 `forward` 方法
4. 在 `modules/registry.py` 中注册

---

## 📝 待办事项

- [ ] 实时数据流接入
- [ ] Web前端界面
- [ ] Docker容器化
- [ ] 模型自动调参
- [ ] 多语言支持

---

## 🤝 贡献

欢迎贡献！请查看 [CONTRIBUTING.md](CONTRIBUTING.md) 了解详情。

1. Fork 项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

---

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

---

## 📮 联系方式

- **项目主页**: https://github.com/wenrui-jiang/HCSF
- **问题反馈**: https://github.com/wenrui-jiang/HCSF/issues
- **邮箱**: your.email@example.com

---

## 🙏 致谢

- StockNet (ACL 2018)
- MSGNet
- CUTS+ Causal Discovery
- PyTorch Team

---

## 📖 引用

如果你使用了本项目，请引用：

```bibtex
@misc{icast2024,
  title={iCast: Intelligent Causal Stock Forecasting Platform},
  author={Your Name},
  year={2024},
  publisher={GitHub},
  url={https://github.com/wenrui-jiang/HCSF}
}
```

---

**Happy Forecasting! 🚀📈**
