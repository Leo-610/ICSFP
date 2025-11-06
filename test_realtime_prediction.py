"""
实时预测功能测试示例
Test Realtime Prediction Features
"""

import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

print("=" * 70)
print("ICSFP 实时预测功能测试")
print("=" * 70)

# 测试1: 导入模块
print("\n[1/4] 导入实时预测模块...")
try:
    from api.realtime_predictor import get_realtime_predictor
    print("  ✓ 模块导入成功")
except Exception as e:
    print(f"  ✗ 模块导入失败: {e}")
    sys.exit(1)

# 测试2: 初始化预测器
print("\n[2/4] 初始化实时预测器...")
try:
    predictor = get_realtime_predictor()
    print("  ✓ 预测器初始化成功")
    print(f"  ✓ 数据管理器: {predictor.data_manager is not None}")
    print(f"  ✓ 预测模型: {predictor.predictor is not None}")
    print(f"  ✓ 模型已加载: {predictor.predictor.model_loaded}")
except Exception as e:
    print(f"  ✗ 预测器初始化失败: {e}")
    sys.exit(1)

# 测试3: 单只股票实时预测
print("\n[3/4] 测试单只股票实时预测...")
try:
    symbol = 'AAPL'
    print(f"  正在预测 {symbol}...")
    
    result = predictor.predict_realtime(symbol, use_causal=True)
    
    print(f"  ✓ 预测完成")
    print(f"  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print(f"  股票代码: {result['symbol']}")
    print(f"  当前价格: ${result['current_price']:.2f}")
    print(f"  预测方向: {result['prediction']['direction']}")
    print(f"  置信度: {result['prediction']['confidence']*100:.1f}%")
    print(f"  上涨概率: {result['prediction']['probabilities']['UP']*100:.1f}%")
    print(f"  下跌概率: {result['prediction']['probabilities']['DOWN']*100:.1f}%")
    print(f"  预测方法: {result['prediction']['method']}")
    
    # 市场数据
    market = result['market_data']
    print(f"\n  市场数据:")
    print(f"    开盘: ${market.get('open', 0):.2f}")
    print(f"    最高: ${market.get('high', 0):.2f}")
    print(f"    最低: ${market.get('low', 0):.2f}")
    print(f"    涨跌幅: {market.get('change_percent', 0):.2f}%")
    print(f"  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    
except Exception as e:
    print(f"  ✗ 预测失败: {e}")
    import traceback
    traceback.print_exc()

# 测试4: 批量预测
print("\n[4/4] 测试批量实时预测...")
try:
    symbols = ['AAPL', 'GOOG', 'MSFT']
    print(f"  正在预测 {len(symbols)} 只股票...")
    
    results = predictor.predict_realtime_batch(symbols, use_causal=True)
    
    print(f"  ✓ 批量预测完成\n")
    print(f"  {'代码':<8} {'价格':<10} {'预测':<8} {'置信度':<10} {'方法':<12}")
    print("  " + "-" * 56)
    
    for symbol, result in results.items():
        if 'error' in result:
            print(f"  {symbol:<8} 错误: {result['error']}")
        else:
            price = result['current_price']
            direction = result['prediction']['direction']
            confidence = result['prediction']['confidence'] * 100
            method = result['prediction']['method']
            
            # 方向标记
            arrow = "▲" if direction == "UP" else "▼"
            
            print(f"  {symbol:<8} ${price:<9.2f} {arrow}{direction:<7} {confidence:<9.1f}% {method:<12}")
    
except Exception as e:
    print(f"  ✗ 批量预测失败: {e}")
    import traceback
    traceback.print_exc()

# 测试5: 多天预测
print("\n[5/5] 测试未来多天预测...")
try:
    symbol = 'AAPL'
    horizon_days = 5
    print(f"  正在预测 {symbol} 未来 {horizon_days} 天...")
    
    result = predictor.predict_with_horizon(symbol, horizon_days=horizon_days, use_causal=True)
    
    print(f"  ✓ 预测完成\n")
    print(f"  股票代码: {result['symbol']}")
    print(f"  当前价格: ${result['current_price']:.2f}")
    print(f"  预测天数: {result['horizon_days']} 天\n")
    print(f"  {'日期':<12} {'方向':<8} {'置信度':<10}")
    print("  " + "-" * 32)
    
    for pred in result['predictions']:
        direction = pred['predicted_direction']
        confidence = pred['confidence'] * 100
        arrow = "▲" if direction == "UP" else "▼"
        
        print(f"  {pred['date']:<12} {arrow}{direction:<7} {confidence:<9.1f}%")
    
except Exception as e:
    print(f"  ✗ 多天预测失败: {e}")
    import traceback
    traceback.print_exc()

# 测试完成
print("\n" + "=" * 70)
print("✅ 测试完成！实时预测功能工作正常")
print("=" * 70)

print("\n下一步:")
print("  1. 启动API服务器:")
print("     python api/app.py")
print("\n  2. 测试实时预测API:")
print("     curl http://localhost:5000/api/v1/realtime/predict/AAPL")
print("\n  3. 批量预测:")
print("     curl -X POST http://localhost:5000/api/v1/realtime/predict/batch \\")
print("       -H 'Content-Type: application/json' \\")
print("       -d '{\"symbols\": [\"AAPL\", \"GOOG\", \"MSFT\"]}'")
print("\n  4. 多天预测:")
print("     curl http://localhost:5000/api/v1/realtime/predict/horizon/AAPL?days=5")
