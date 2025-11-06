# 数据可视化模块文档

## 📊 概述

实时数据可视化模块为ICSFP系统提供了强大的数据展示和分析功能，包括价格走势图、预测结果可视化、实时数据更新等功能。

## 🎯 功能特性

### 三种可视化页面

#### 1. 基础可视化 (visualization.html)
- **价格走势图**: 使用Chart.js展示历史价格数据
- **单只股票预测**: 实时预测结果展示
- **置信度可视化**: 直观的进度条显示
- **市场数据**: 开盘/最高/最低/成交量等数据
- **自动刷新**: 可配置的自动更新功能

#### 2. 高级可视化 (advanced_visualization.html)
- **多图表展示**: 价格、成交量、波动率三合一
- **多天预测**: 支持1-7天的预测展示
- **WebSocket实时推送**: 实时数据更新
- **历史数据表格**: 详细的历史记录
- **响应式设计**: 适配各种屏幕尺寸

#### 3. 实时监控 (realtime.html)
- **WebSocket连接**: 实时双向通信
- **多股票订阅**: 同时监控多只股票
- **实时报价**: 毫秒级数据更新
- **市场统计**: 市场整体数据概览

## 🚀 快速开始

### 1. 启动服务器

```bash
# 激活环境
conda activate ic_sfp_gpu

# 启动服务器
python api/app.py
```

服务器将在 http://127.0.0.1:5000 启动

### 2. 访问页面

在浏览器中打开以下任一页面：

- 基础版: http://127.0.0.1:5000/static/visualization.html
- 高级版: http://127.0.0.1:5000/static/advanced_visualization.html
- 监控版: http://127.0.0.1:5000/static/realtime.html

### 3. 使用测试脚本

```bash
python test_visualization.py
```

测试脚本会：
- ✓ 检查文件完整性
- ✓ 验证服务器状态
- ✓ 测试API端点
- ✓ 自动打开浏览器

## 📖 详细使用指南

### 基础可视化页面

#### 功能说明
```
┌─────────────────────────────────────────┐
│  股票代码: [AAPL]  天数: [30天]        │
│  [✓] 使用因果图增强                     │
│  [🔍 加载数据] [🎯 预测] [🔄 自动刷新]  │
├─────────────────────────────────────────┤
│  当前价格  │  涨跌幅  │  预测方向  │  置信度 │
│  $268.18  │  +1.2%  │    ▲ UP   │  52.9% │
├─────────────────────────────────────────┤
│  📊 价格走势图          │  🎯 预测结果  │
│  [价格折线图]           │  [预测卡片]   │
│                         │  [置信度条]   │
└─────────────────────────────────────────┘
```

#### 操作步骤

1. **加载股票数据**
   ```
   输入股票代码 → 选择天数 → 点击"加载数据"
   ```

2. **查看价格走势**
   - 鼠标悬停查看具体数值
   - 缩放和拖动图表
   - 查看顶部统计数据

3. **获取预测结果**
   ```
   点击"预测" → 查看方向和置信度 → 分析概率分布
   ```

4. **启用自动刷新**
   ```
   点击"自动刷新" → 每60秒自动更新数据和预测
   ```

### 高级可视化页面

#### 功能说明
```
┌────────────────────────────────────────────────────┐
│ 股票: [AAPL]  时间: [30天]  预测: [5天]  [✓] 因果  │
│ [🔄 刷新全部] [🎯 多天预测]  [🔌 WebSocket: 已连接] │
├────────────────────────────────────────────────────┤
│  当前价格  │  预测方向  │  成交量  │  波动率      │
│  $268.18  │   ▲ UP   │  89.5M  │   2.3%       │
├────────────────────────────────────────────────────┤
│  📈 价格走势与预测 (8列)      │  🎯 实时预测 (4列) │
│  [折线图]                     │  [Day 1: UP 52%]  │
│                               │  [Day 2: UP 48%]  │
│                               │  [Day 3: DOWN 51%]│
├───────────────────────────────┼─────────────────────┤
│  📊 成交量分析 (6列)          │  📉 波动率趋势 (6列)│
│  [柱状图]                     │  [折线图]          │
├────────────────────────────────────────────────────┤
│  📋 历史数据 (12列)                                │
│  [数据表格 - 最近10条记录]                         │
└────────────────────────────────────────────────────┘
```

#### 高级功能

1. **多图表分析**
   - **价格图**: 查看历史价格趋势
   - **成交量图**: 分析交易活跃度
   - **波动率图**: 评估风险水平

2. **多天预测**
   ```
   选择预测天数 (1-7) → 点击"多天预测" → 查看未来趋势
   ```
   
   每个预测包含：
   - 方向 (UP/DOWN)
   - 置信度百分比
   - 上涨/下跌概率
   - 预测方法

3. **WebSocket实时推送**
   ```
   点击"连接WebSocket" → 自动接收实时数据 → 图表动态更新
   ```

4. **响应式布局**
   - 桌面端: 多列布局
   - 平板端: 2列布局
   - 移动端: 单列布局

### 实时监控页面

#### 功能说明
```
┌─────────────────────────────────────────┐
│  [WebSocket: 已连接]  [订阅管理]        │
├─────────────────────────────────────────┤
│  AAPL    │  GOOG    │  MSFT    │  TSLA  │
│  $268.18 │  $279.35 │  $514.01 │  $--   │
│  +1.2%   │  -0.5%   │  +0.8%   │  --    │
├─────────────────────────────────────────┤
│  市场统计                               │
│  • 更新次数: 125                        │
│  • 上涨数量: 2                          │
│  • 下跌数量: 1                          │
└─────────────────────────────────────────┘
```

#### 订阅管理

1. **连接WebSocket**
   ```javascript
   点击"连接" → 建立WebSocket连接 → 状态变为"已连接"
   ```

2. **订阅股票**
   ```javascript
   输入股票代码 → 点击"订阅" → 开始接收实时数据
   ```

3. **取消订阅**
   ```javascript
   点击股票卡片上的"取消订阅" → 停止接收该股票数据
   ```

## 🎨 自定义配置

### 修改图表样式

在HTML文件中修改Chart.js配置：

```javascript
// 修改颜色
const primaryColor = '#667eea';  // 主色调
const secondaryColor = '#764ba2'; // 副色调

// 修改图表选项
charts.price = new Chart(ctx, {
    type: 'line',
    options: {
        // 自定义选项
        aspectRatio: 2,  // 宽高比
        tension: 0.4,    // 曲线平滑度
    }
});
```

### 调整更新频率

```javascript
// 自动刷新间隔 (毫秒)
const refreshInterval = 60000;  // 60秒

// WebSocket心跳间隔
const heartbeatInterval = 30000; // 30秒
```

### 修改显示数量

```javascript
// 数据表格显示条数
const maxTableRows = 10;

// 图表数据点数量
const maxDataPoints = 100;
```

## 🔧 API集成

### 使用的API端点

#### 1. 实时报价
```http
GET /api/v1/realtime/quote/{symbol}
```

响应示例：
```json
{
    "status": "success",
    "data": {
        "symbol": "AAPL",
        "price": 268.18,
        "change_percent": 1.2,
        "volume": 89500000
    }
}
```

#### 2. 历史数据
```http
GET /api/v1/realtime/historical/{symbol}?start_date=2024-01-01&end_date=2024-01-31
```

响应示例：
```json
{
    "status": "success",
    "data": {
        "symbol": "AAPL",
        "records": [
            {
                "date": "2024-01-01",
                "open": 265.0,
                "high": 270.0,
                "low": 264.0,
                "close": 268.18,
                "volume": 89500000
            }
        ]
    }
}
```

#### 3. 实时预测
```http
GET /api/v1/realtime/predict/{symbol}?use_causal=true
```

响应示例：
```json
{
    "status": "success",
    "data": {
        "prediction": {
            "direction": "UP",
            "confidence": 0.529,
            "method": "model",
            "probabilities": {
                "UP": 0.529,
                "DOWN": 0.471
            }
        }
    }
}
```

#### 4. 多天预测
```http
GET /api/v1/realtime/predict/horizon/{symbol}?horizon_days=5&use_causal=true
```

响应示例：
```json
{
    "status": "success",
    "data": {
        "predictions": [
            {
                "day": 1,
                "direction": "UP",
                "confidence": 0.529,
                "probabilities": {"UP": 0.529, "DOWN": 0.471}
            }
        ],
        "statistics": {
            "average_confidence": 0.51,
            "consistency_score": 0.8,
            "recommendation": "HOLD"
        }
    }
}
```

### JavaScript集成示例

```javascript
// 封装API调用
class StockAPI {
    constructor(baseURL = 'http://127.0.0.1:5000') {
        this.baseURL = baseURL;
    }
    
    async getQuote(symbol) {
        const response = await fetch(`${this.baseURL}/api/v1/realtime/quote/${symbol}`);
        return await response.json();
    }
    
    async getHistorical(symbol, startDate, endDate) {
        const url = `${this.baseURL}/api/v1/realtime/historical/${symbol}?` +
                    `start_date=${startDate}&end_date=${endDate}`;
        const response = await fetch(url);
        return await response.json();
    }
    
    async predict(symbol, useCausal = true) {
        const url = `${this.baseURL}/api/v1/realtime/predict/${symbol}?use_causal=${useCausal}`;
        const response = await fetch(url);
        return await response.json();
    }
    
    async predictHorizon(symbol, days = 5, useCausal = true) {
        const url = `${this.baseURL}/api/v1/realtime/predict/horizon/${symbol}?` +
                    `horizon_days=${days}&use_causal=${useCausal}`;
        const response = await fetch(url);
        return await response.json();
    }
}

// 使用示例
const api = new StockAPI();

// 获取报价
const quote = await api.getQuote('AAPL');
console.log(quote.data.price);

// 获取预测
const prediction = await api.predict('AAPL');
console.log(prediction.data.prediction.direction);
```

## 📱 响应式设计

### 断点配置

```css
/* 桌面端 (> 1200px) */
.dashboard {
    grid-template-columns: 2fr 1fr;
}

/* 平板端 (768px - 1200px) */
@media (max-width: 1200px) {
    .dashboard {
        grid-template-columns: 1fr;
    }
}

/* 移动端 (< 768px) */
@media (max-width: 768px) {
    .metrics-grid {
        grid-template-columns: 1fr;
    }
}
```

## 🐛 故障排查

### 常见问题

#### 1. 页面无法加载

**问题**: 打开页面显示空白或404错误

**解决方案**:
```bash
# 检查服务器是否运行
curl http://127.0.0.1:5000/api/v1/health

# 检查文件是否存在
ls static/visualization.html

# 确保服务器正确启动
python api/app.py
```

#### 2. 图表不显示

**问题**: 页面加载但图表区域为空

**解决方案**:
```javascript
// 检查控制台错误
// F12 → Console → 查看错误信息

// 常见原因：
// 1. Chart.js未加载
// 2. 数据格式错误
// 3. Canvas元素不存在

// 调试代码
console.log('Chart.js loaded:', typeof Chart !== 'undefined');
console.log('Canvas element:', document.getElementById('priceChart'));
```

#### 3. API请求失败

**问题**: 显示"加载数据失败"错误

**解决方案**:
```javascript
// 检查API端点
fetch('http://127.0.0.1:5000/api/v1/realtime/quote/AAPL')
    .then(r => r.json())
    .then(data => console.log(data))
    .catch(err => console.error('Error:', err));

// 检查CORS设置
// 确保api/app.py中启用了CORS：
from flask_cors import CORS
CORS(app)
```

#### 4. WebSocket连接失败

**问题**: 显示"未连接"状态

**解决方案**:
```javascript
// 检查SocketIO是否加载
console.log('SocketIO loaded:', typeof io !== 'undefined');

// 检查服务器WebSocket支持
// 确保安装了flask-socketio
pip install flask-socketio python-socketio

// 检查连接URL
const socket = io('http://localhost:5000', {
    transports: ['websocket', 'polling']  // 尝试不同传输方式
});
```

#### 5. 数据不更新

**问题**: 自动刷新不工作

**解决方案**:
```javascript
// 检查定时器
console.log('Interval ID:', autoRefreshInterval);

// 手动测试
setInterval(() => {
    loadStockData();
    console.log('Manual refresh');
}, 5000);  // 5秒测试

// 检查是否有JavaScript错误阻止执行
```

### 性能优化

#### 1. 减少API调用

```javascript
// 使用防抖
function debounce(func, wait) {
    let timeout;
    return function(...args) {
        clearTimeout(timeout);
        timeout = setTimeout(() => func.apply(this, args), wait);
    };
}

const debouncedLoad = debounce(loadStockData, 500);
```

#### 2. 优化图表渲染

```javascript
// 使用动画配置
chart.options.animation = {
    duration: 300  // 减少动画时间
};

// 限制数据点数量
if (data.length > 100) {
    data = data.slice(-100);  // 只保留最近100个点
}
```

#### 3. 缓存数据

```javascript
// 简单缓存实现
const cache = new Map();

async function getCachedData(key, fetcher, ttl = 60000) {
    const cached = cache.get(key);
    if (cached && Date.now() - cached.time < ttl) {
        return cached.data;
    }
    
    const data = await fetcher();
    cache.set(key, { data, time: Date.now() });
    return data;
}
```

## 🎯 最佳实践

### 1. 用户体验

- ✅ 显示加载状态
- ✅ 提供错误提示
- ✅ 支持键盘操作
- ✅ 响应式布局
- ✅ 优雅的动画

### 2. 数据展示

- ✅ 使用颜色区分涨跌
- ✅ 格式化数字显示
- ✅ 提供上下文信息
- ✅ 支持数据导出
- ✅ 历史记录保存

### 3. 性能优化

- ✅ 懒加载图表
- ✅ 虚拟滚动长列表
- ✅ 防抖和节流
- ✅ 缓存策略
- ✅ 代码分割

### 4. 安全考虑

- ✅ 输入验证
- ✅ XSS防护
- ✅ CSRF令牌
- ✅ 速率限制
- ✅ 错误处理

## 📚 相关文档

- [实时数据模块文档](REALTIME_DATA_MODULE.md)
- [实时预测指南](REALTIME_PREDICTION_GUIDE.md)
- [API文档](API_GUIDE.md)
- [Chart.js文档](https://www.chartjs.org/docs/)
- [Socket.IO文档](https://socket.io/docs/)

## 🤝 贡献

欢迎提交问题和改进建议！

## 📄 许可证

与ICSFP项目保持一致
