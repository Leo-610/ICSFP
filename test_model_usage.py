"""
测试真实模型预测 vs 规则预测
验证模型确实被使用
"""

import sys
import logging
from api.predictor_enhanced import EnhancedStockPredictor

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_model_prediction():
    """测试模型预测功能"""
    
    print("="*80)
    print("测试真实模型预测功能")
    print("="*80)
    
    # 1. 初始化预测器
    print("\n1. 初始化预测器...")
    predictor = EnhancedStockPredictor()
    
    print(f"   - 模型已加载: {predictor.model_loaded}")
    print(f"   - 设备: {predictor.device}")
    print(f"   - 模型对象: {predictor.model is not None}")
    print(f"   - DataPipe: {predictor.pipe is not None}")
    
    # 2. 测试单只股票预测
    print("\n2. 测试单只股票预测...")
    test_symbol = "AAPL"
    
    try:
        result = predictor.predict_single(
            stock_symbol=test_symbol,
            start_date=None,
            end_date=None,
            use_causal=True
        )
        
        print(f"\n   预测结果:")
        print(f"   - 股票: {result['stock_symbol']}")
        print(f"   - 模型状态: {result['model_status']}")
        print(f"   - 预测方法: {result.get('prediction_method', 'unknown')}")
        print(f"   - 使用因果图: {result['use_causal']}")
        print(f"   - 预测数量: {len(result['predictions'])}")
        
        # 显示前3个预测
        print(f"\n   前3个预测详情:")
        for i, pred in enumerate(result['predictions'][:3]):
            print(f"   [{i+1}]")
            print(f"      日期: {pred.get('date', 'N/A')}")
            print(f"      方向: {pred['predicted_direction']}")
            print(f"      置信度: {pred['confidence']:.4f}")
            print(f"      UP概率: {pred['probabilities']['UP']:.4f}")
            print(f"      DOWN概率: {pred['probabilities']['DOWN']:.4f}")
            print(f"      方法: {pred.get('method', 'unknown')}")
        
        # 3. 判断是否使用了真实模型
        print("\n3. 验证预测方法...")
        prediction_method = result.get('prediction_method', 'unknown')
        if prediction_method == 'deep_learning':
            print("   ✅ 成功！使用了深度学习模型进行预测")
        elif prediction_method == 'rule_based':
            print("   ⚠️  使用了规则预测（模型未被使用）")
            if not predictor.model_loaded:
                print("      原因: 模型未加载")
            elif predictor.pipe is None:
                print("      原因: DataPipe未初始化")
            else:
                print("      原因: 未知错误")
        else:
            print(f"   ❓ 未知预测方法: {prediction_method}")
        
        # 4. 检查预测结果的一致性
        print("\n4. 检查预测结果一致性...")
        methods_used = set()
        for pred in result['predictions']:
            if 'method' in pred:
                methods_used.add(pred['method'])
        
        print(f"   使用的方法: {', '.join(methods_used)}")
        
        if len(methods_used) == 1:
            method = list(methods_used)[0]
            if method == 'deep_learning':
                print("   ✅ 所有预测都使用深度学习模型")
            elif method == 'rule_based':
                print("   ⚠️  所有预测都使用规则方法")
            else:
                print(f"   ℹ️  所有预测都使用: {method}")
        else:
            print(f"   ⚠️  混合使用多种方法")
        
    except Exception as e:
        print(f"\n   ❌ 预测失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print("\n" + "="*80)
    print("测试完成")
    print("="*80)
    
    return True

def compare_predictions():
    """对比模型预测和规则预测的差异"""
    
    print("\n" + "="*80)
    print("对比模型预测 vs 规则预测")
    print("="*80)
    
    predictor = EnhancedStockPredictor()
    
    # 如果模型加载成功
    if predictor.model_loaded and predictor.pipe is not None:
        print("\n模型可用，进行对比测试...")
        
        test_symbol = "AAPL"
        
        # 强制使用模型预测
        try:
            result_model = predictor._predict_with_model(test_symbol, None, None, True)
            print(f"\n深度学习模型预测 (前3个):")
            for i, pred in enumerate(result_model[:3]):
                print(f"  [{i+1}] {pred['predicted_direction']} - 置信度: {pred['confidence']:.4f}")
        except Exception as e:
            print(f"\n模型预测失败: {e}")
            result_model = []
        
        # 强制使用规则预测
        result_rule = predictor._rule_based_prediction(test_symbol, None, None, True)
        print(f"\n规则预测 (前3个):")
        for i, pred in enumerate(result_rule[:3]):
            print(f"  [{i+1}] {pred['predicted_direction']} - 置信度: {pred['confidence']:.4f}")
        
        if result_model and result_rule:
            print("\n差异分析:")
            if len(result_model) != len(result_rule):
                print(f"  - 预测数量不同: 模型={len(result_model)}, 规则={len(result_rule)}")
            
            # 比较前几个预测
            for i in range(min(3, len(result_model), len(result_rule))):
                if result_model[i]['predicted_direction'] != result_rule[i]['predicted_direction']:
                    print(f"  - 预测[{i+1}]方向不同: 模型={result_model[i]['predicted_direction']}, 规则={result_rule[i]['predicted_direction']}")
    else:
        print("\n模型不可用，跳过对比测试")
        if not predictor.model_loaded:
            print("  原因: 模型未加载")
        if predictor.pipe is None:
            print("  原因: DataPipe未初始化")

if __name__ == '__main__':
    print("\n" + "="*80)
    print("模型使用验证测试")
    print("="*80)
    
    # 运行测试
    success = test_model_prediction()
    
    # 对比测试
    if success:
        compare_predictions()
    
    print("\n测试结束\n")
