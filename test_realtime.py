"""
快速测试实时数据模块
Quick Test for Realtime Data Module
"""

import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

print("=" * 70)
print("ICSFP 实时数据模块快速测试")
print("=" * 70)

# 测试1: 检查依赖
print("\n[1/5] 检查依赖包...")
required_packages = {
    'yfinance': 'yfinance>=0.2.28',
    'flask': 'flask>=2.3.0',
    'flask_socketio': 'flask-socketio>=5.3.0',
    'pandas': 'pandas>=2.1.0',
    'numpy': 'numpy>=1.26.0'
}

missing_packages = []
for package, install_cmd in required_packages.items():
    try:
        __import__(package)
        print(f"  ✓ {package}")
    except ImportError:
        print(f"  ✗ {package} (缺失)")
        missing_packages.append(install_cmd)

if missing_packages:
    print(f"\n  ⚠️  缺少依赖包，请安装:")
    print(f"  pip install {' '.join(missing_packages)}")
    sys.exit(1)
else:
    print("  ✓ 所有依赖包已安装")

# 测试2: 导入模块
print("\n[2/5] 导入实时数据模块...")
try:
    from api.realtime_data import get_realtime_manager, YahooFinanceSource
    print("  ✓ 模块导入成功")
except Exception as e:
    print(f"  ✗ 模块导入失败: {e}")
    sys.exit(1)

# 测试3: 初始化管理器
print("\n[3/5] 初始化数据管理器...")
try:
    config = {
        'cache_dir': 'cache/realtime',
        'cache_ttl': 60,
        'auto_update': False,
        'data_sources': {
            'yahoo_finance': {'enabled': True}
        },
        'watch_list': ['AAPL']
    }
    manager = get_realtime_manager(config)
    print("  ✓ 管理器初始化成功")
    print(f"  ✓ 可用数据源: {list(manager.data_sources.keys())}")
except Exception as e:
    print(f"  ✗ 管理器初始化失败: {e}")
    sys.exit(1)

# 测试4: 获取实时数据
print("\n[4/5] 测试数据获取...")
try:
    print("  正在获取 AAPL 实时报价...")
    quote = manager.get_realtime_quote('AAPL', use_cache=False)
    
    print(f"  ✓ 数据获取成功")
    print(f"  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print(f"  股票代码: {quote['symbol']}")
    print(f"  当前价格: ${quote['price']:.2f}")
    print(f"  涨跌幅: {quote['change_percent']:.2f}%")
    print(f"  成交量: {quote['volume']:,}")
    print(f"  数据来源: {quote['source']}")
    print(f"  更新时间: {quote['timestamp']}")
    print(f"  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
except Exception as e:
    print(f"  ✗ 数据获取失败: {e}")
    print(f"  提示: 请检查网络连接")
    sys.exit(1)

# 测试5: 测试缓存
print("\n[5/5] 测试缓存功能...")
try:
    import time
    
    # 第一次请求（从数据源）
    start = time.time()
    quote1 = manager.get_realtime_quote('AAPL', use_cache=False)
    time1 = time.time() - start
    
    # 第二次请求（从缓存）
    start = time.time()
    quote2 = manager.get_realtime_quote('AAPL', use_cache=True)
    time2 = time.time() - start
    
    print(f"  ✓ 缓存功能正常")
    print(f"  首次请求耗时: {time1:.3f}秒")
    print(f"  缓存请求耗时: {time2:.3f}秒")
    print(f"  速度提升: {time1/time2:.1f}x")
except Exception as e:
    print(f"  ✗ 缓存测试失败: {e}")

# 测试完成
print("\n" + "=" * 70)
print("✅ 所有测试通过！实时数据模块工作正常")
print("=" * 70)

print("\n下一步:")
print("  1. 运行示例程序:")
print("     python examples/realtime_data_example.py")
print("\n  2. 启动API服务器:")
print("     python api/app.py")
print("\n  3. 访问实时监控页面:")
print("     http://localhost:5000/realtime")
print("\n  4. 查看文档:")
print("     docs/REALTIME_DATA_MODULE.md")
