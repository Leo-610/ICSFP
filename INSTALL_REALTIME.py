"""
实时数据模块安装和快速启动指南
Installation and Quick Start Guide
"""

print("""
╔═══════════════════════════════════════════════════════════════════╗
║                                                                   ║
║           ICSFP 实时数据接入模块 - 安装指南                        ║
║                                                                   ║
╚═══════════════════════════════════════════════════════════════════╝

📦 第一步: 安装依赖包
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

在项目根目录执行:

    cd D:\\ICSFP\\HCSF
    pip install -r requirements.txt

或者只安装实时数据相关的依赖:

    pip install yfinance>=0.2.28
    pip install flask-socketio>=5.3.0
    pip install python-socketio>=5.9.0

可选依赖(根据需要):

    # Alpha Vantage 数据源
    pip install alpha-vantage>=2.3.1
    
    # Tushare 中国A股数据
    pip install tushare>=1.2.89


🔧 第二步: 配置数据源
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

编辑配置文件: config/realtime_config.yml

1. Yahoo Finance (默认，免费，推荐)
   - 无需配置，开箱即用
   - 不需要API密钥

2. Alpha Vantage (可选)
   - 访问: https://www.alphavantage.co/support/#api-key
   - 注册获取免费API密钥
   - 在配置文件中填入api_key

3. Tushare (可选，中国A股)
   - 访问: https://tushare.pro
   - 注册获取token
   - 在配置文件中填入token


🧪 第三步: 运行测试
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

运行快速测试脚本:

    python test_realtime.py

测试项目:
  ✓ 检查依赖包
  ✓ 导入模块
  ✓ 初始化管理器
  ✓ 获取实时数据
  ✓ 测试缓存功能

如果所有测试通过，表示模块安装成功！


🎯 第四步: 运行示例
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

运行交互式示例程序:

    python examples/realtime_data_example.py

示例包括:
  1. 获取单只股票实时报价
  2. 批量获取多只股票报价
  3. 获取历史数据
  4. 获取市场摘要
  5. 缓存使用演示
  6. 自动更新功能


🚀 第五步: 启动服务
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

启动API服务器:

    python api/app.py

服务将在 http://localhost:5000 启动


🌐 第六步: 访问Web界面
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

在浏览器中访问:

    http://localhost:5000/realtime

功能:
  ✓ 实时股票报价显示
  ✓ WebSocket实时推送
  ✓ 订阅/取消订阅
  ✓ 市场统计信息
  ✓ 自动刷新


📚 第七步: 查看文档
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

完整文档:

    docs/REALTIME_DATA_MODULE.md

内容包括:
  - 详细的功能说明
  - API参考文档
  - 配置选项说明
  - 使用示例代码
  - 故障排查指南
  - 最佳实践


💡 快速使用示例
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Python脚本:
    
    from api.realtime_data import get_realtime_manager
    
    # 初始化
    manager = get_realtime_manager()
    
    # 获取报价
    quote = manager.get_realtime_quote('AAPL')
    print(f"AAPL: ${quote['price']}")


HTTP API:

    # 获取单只股票
    GET http://localhost:5000/api/v1/realtime/quote/AAPL
    
    # 批量获取
    POST http://localhost:5000/api/v1/realtime/quotes
    Body: {"symbols": ["AAPL", "GOOG", "MSFT"]}


WebSocket:

    const socket = io('/realtime');
    socket.emit('subscribe', {symbols: ['AAPL']});
    socket.on('market_update', (data) => console.log(data));


🔥 核心特性
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ 多数据源支持 (Yahoo Finance, Alpha Vantage, Tushare)
✅ 智能缓存系统 (内存+文件双层缓存)
✅ WebSocket实时推送
✅ 批量数据获取
✅ 自动更新调度
✅ 历史数据查询
✅ 市场摘要统计
✅ 错误重试机制


⚠️  常见问题
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Q1: ImportError: No module named 'yfinance'
A1: 运行 pip install yfinance

Q2: 数据获取失败
A2: 检查网络连接，确保可以访问数据源

Q3: WebSocket连接失败
A3: 确保flask-socketio已安装，检查防火墙设置

Q4: API限流错误
A4: 启用缓存，增加TTL时间，或使用多个数据源


📞 获取帮助
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

- 查看文档: docs/REALTIME_DATA_MODULE.md
- 运行测试: python test_realtime.py
- 查看示例: python examples/realtime_data_example.py


╔═══════════════════════════════════════════════════════════════════╗
║                                                                   ║
║                       安装完成！祝使用愉快！                        ║
║                                                                   ║
╚═══════════════════════════════════════════════════════════════════╝
""")
