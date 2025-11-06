# ICSFP 页面集成方案

## 现有页面分析

### 已有页面
1. **index.html** - 主预测页面
   - 股票预测表单
   - 预测结果展示  
   - 系统状态信息

2. **trading.html** - 模拟交易页面
   - 交易界面
   - 持仓管理

### 新增页面
3. **visualization.html** - 基础可视化（独立）
4. **advanced_visualization.html** - 高级可视化（独立）
5. **realtime.html** - 实时监控（独立）

## 集成方案

### 方案1: 导航集成（已完成）
在现有页面的导航栏中添加链接到新页面：
```html
<a href="/visualization" class="nav-link">📊 可视化</a>
<a href="/realtime" class="nav-link">⚡ 实时监控</a>
```

### 方案2: index.html增强

#### 2.1 添加实时数据面板
在主页面添加一个实时报价小部件：
- 显示当前选中股票的实时价格
- 显示涨跌幅
- 实时更新（可选WebSocket）

#### 2.2 增强预测功能
- 集成实时数据获取
- 添加实时预测按钮
- 显示实时置信度

#### 2.3 添加快速链接
在预测结果中添加：
- "查看详细图表" → 跳转到可视化页面
- "实时监控" → 跳转到监控页面

### 方案3: 创建统一的仪表板页面

创建 `dashboard.html` 作为中央控制面板：
- 整合所有功能的入口
- 显示关键指标
- 快速导航到各个功能

### 方案4: API路由配置

在 `api/app.py` 中添加路由：
```python
@app.route('/visualization')
def visualization():
    return send_from_directory('static', 'advanced_visualization.html')

@app.route('/realtime')
def realtime():
    return send_from_directory('static', 'realtime.html')
```

## 推荐实施步骤

### 第1步：更新导航栏（已完成）
✅ 在 index.html 和 trading.html 的导航中添加新页面链接

### 第2步：添加API路由
在 Flask 应用中添加路由映射

### 第3步：在 index.html 添加实时数据组件
- 添加实时报价显示
- 添加"查看可视化"按钮
- 集成实时预测API

### 第4步：在 trading.html 添加实时价格
- 显示当前交易股票的实时价格
- 使用WebSocket实时更新

### 第5步：统一样式
确保所有页面使用相同的设计风格

## 具体实现

### index.html 增强代码

```html
<!-- 在预测表单下方添加实时数据面板 -->
<div class="card" id="realtimePanel" style="display: none;">
    <div class="card-header">
        <h2 class="card-title">
            <span>⚡</span>
            <span>实时数据</span>
        </h2>
    </div>
    <div class="card-body">
        <div class="realtime-quote">
            <div class="quote-price">$<span id="realtimePrice">--</span></div>
            <div class="quote-change" id="realtimeChange">--</div>
            <div class="quote-updated">更新于 <span id="realtimeUpdated">--</span></div>
        </div>
        <button class="btn btn-primary" onclick="openVisualization()">
            查看详细图表
        </button>
    </div>
</div>
```

### JavaScript 增强

```javascript
// 获取实时报价
async function loadRealtimeQuote(symbol) {
    try {
        const response = await fetch(`${API_BASE}/realtime/quote/${symbol}`);
        const result = await response.json();
        
        if (result.status === 'success') {
            const quote = result.data;
            document.getElementById('realtimePrice').textContent = quote.price.toFixed(2);
            document.getElementById('realtimeChange').textContent = 
                `${quote.change_percent > 0 ? '+' : ''}${quote.change_percent.toFixed(2)}%`;
            document.getElementById('realtimeUpdated').textContent = 
                new Date(quote.timestamp * 1000).toLocaleTimeString();
            document.getElementById('realtimePanel').style.display = 'block';
        }
    } catch (error) {
        console.error('获取实时数据失败:', error);
    }
}

// 打开可视化页面
function openVisualization() {
    const symbol = document.getElementById('stockSymbol').value;
    window.open(`/visualization?symbol=${symbol}`, '_blank');
}
```

## 文件清单

### 需要修改的文件
- [x] static/index.html - 添加导航链接 ✅
- [ ] static/trading.html - 添加导航链接和实时价格
- [ ] api/app.py - 添加路由映射
- [ ] api/routes.py - 添加实时数据端点集成

### 新增的文件（已完成）
- [x] static/visualization.html - 基础可视化
- [x] static/advanced_visualization.html - 高级可视化
- [x] static/realtime.html - 实时监控
- [x] api/realtime_data.py - 实时数据模块
- [x] api/realtime_predictor.py - 实时预测器
- [x] api/realtime_routes.py - 实时路由
- [x] app_integrated.py - 集成应用
- [x] quickstart_web.py - 快速启动

## 下一步行动

1. **立即执行**：
   - 在 trading.html 中添加导航链接
   - 在 api/app.py 中添加路由
   - 测试页面跳转

2. **增强功能**：
   - 在 index.html 添加实时数据面板
   - 在预测结果中添加"查看图表"按钮
   - 统一所有页面的样式

3. **优化体验**：
   - 添加页面间数据传递（URL参数）
   - 添加面包屑导航
   - 添加返回按钮

## 集成完成标准

- [x] 导航栏中有所有页面链接
- [x] 可以从任何页面跳转到其他页面
- [ ] index.html 集成实时数据显示
- [ ] trading.html 集成实时价格更新
- [ ] 所有API端点正常工作
- [ ] 页面样式统一
- [ ] 用户体验流畅

## 用户使用流程

1. **预测流程**：
   首页 → 选择股票 → 查看预测 → [查看详细图表] → 可视化页面

2. **交易流程**：
   交易页 → 查看持仓 → [查看实时数据] → 监控页面

3. **分析流程**：
   可视化页 → 多图表分析 → [开始交易] → 交易页面

4. **监控流程**：
   监控页 → 实时订阅 → [深度分析] → 可视化页面
