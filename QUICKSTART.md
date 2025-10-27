# iCast 快速开始指南

## 🚀 5分钟快速上手

### 步骤1：安装依赖

```powershell
# 使用自动安装脚本（推荐）
.\setup.ps1

# 或手动安装
pip install -r requirements.txt
```

### 步骤2：验证安装

```powershell
python quickstart.py --info
```

### 步骤3：启动API服务

```powershell
# 开发模式（单worker）
python quickstart.py --serve

# 生产模式（4 workers）
python quickstart.py --serve --workers 4
```

### 步骤4：测试API

打开新的终端窗口：

```powershell
python quickstart.py --test
```

或使用浏览器访问：
- 健康检查: http://localhost:5000/health
- API文档: http://localhost:5000/api/v1

---

## 📝 常用命令

```powershell
# 显示项目信息
python quickstart.py --info

# 启动API服务器
python quickstart.py --serve

# 运行测试
python quickstart.py --test

# 训练模型
python quickstart.py --train

# 计算因果图
python quickstart.py --causal
```

---

## 🔧 配置

编辑 `config.yml` 自定义配置：

```yaml
model:
  alpha: 0.5              # 因果权重 (0-1)
  max_n_days: 5          # 最大天数
  batch_size: 32         # 批大小

causal_discovery:
  method: 'granger'      # 因果方法

training:
  device: 'cuda'         # 计算设备
  learning_rate: 0.001   # 学习率
```

---

## 📖 更多文档

- **项目概览**: [README_ICAST.md](README_ICAST.md)
- **API文档**: [docs/API_GUIDE.md](docs/API_GUIDE.md)
- **第一阶段总结**: [PHASE1_SUMMARY.md](PHASE1_SUMMARY.md)

---

## 🐛 故障排查

### 问题1: 导入错误

```powershell
# 重新安装依赖
pip install -r requirements.txt --force-reinstall
```

### 问题2: CUDA不可用

检查CUDA安装：
```powershell
python -c "import torch; print(torch.cuda.is_available())"
```

如果显示False，安装CPU版本：
```powershell
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
```

### 问题3: API服务无法启动

确保端口5000未被占用：
```powershell
netstat -ano | findstr :5000
```

使用其他端口：
```powershell
python quickstart.py --serve --port 8000
```

---

## 💡 使用示例

### Python调用API

```python
import requests

# 预测单只股票
response = requests.post('http://localhost:5000/api/v1/predict/single', 
    json={
        'stock_symbol': 'AAPL',
        'use_causal': True
    })
print(response.json())

# 获取因果图
response = requests.get('http://localhost:5000/api/v1/causal/graph',
    params={'threshold': 0.3})
print(response.json())
```

### PowerShell调用API

```powershell
# 使用Invoke-RestMethod
$body = @{
    stock_symbol = "AAPL"
    use_causal = $true
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:5000/api/v1/predict/single" `
    -Method Post `
    -ContentType "application/json" `
    -Body $body
```

---

## 🎯 下一步

1. 查看完整文档: `README_ICAST.md`
2. 阅读API指南: `docs/API_GUIDE.md`
3. 运行示例代码
4. 自定义配置和模型

---

**需要帮助？** 查看 [GitHub Issues](https://github.com/wenrui-jiang/HCSF/issues)
