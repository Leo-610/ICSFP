"""
简化测试 - 直接测试API预测功能
"""

import requests
import json

def test_api_prediction():
    """测试API预测端点"""
    
    print("="*80)
    print("测试API预测功能")
    print("="*80)
    
    base_url = "http://localhost:5000"
    
    # 1. 检查模型状态
    print("\n1. 检查模型状态...")
    try:
        response = requests.get(f"{base_url}/api/v1/model/info")
        if response.status_code == 200:
            data = response.json()
            if data['status'] == 'success':
                info = data['data']
                print(f"   - 模型已加载: {info.get('model_loaded', False)}")
                print(f"   - 设备: {info.get('device', 'unknown')}")
                print(f"   - 总参数: {info.get('total_parameters', 0):,}")
                print(f"   - 因果图: {info.get('causal_graph_shape', 'N/A')}")
        else:
            print(f"   ❌ 请求失败: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ 错误: {e}")
        return False
    
    # 2. 测试单只股票预测
    print("\n2. 测试单只股票预测...")
    try:
        payload = {
            "stock_symbol": "AAPL",
            "use_causal": True
        }
        
        response = requests.post(
            f"{base_url}/api/v1/predict/single",
            json=payload,
            headers={'Content-Type': 'application/json'}
        )
        
        if response.status_code == 200:
            data = response.json()
            if data['status'] == 'success':
                result = data['data']
                print(f"   ✅ 预测成功!")
                print(f"   - 股票: {result['stock_symbol']}")
                print(f"   - 模型状态: {result.get('model_status', 'unknown')}")
                print(f"   - 预测方法: {result.get('prediction_method', 'unknown')}")
                print(f"   - 预测数量: {len(result['predictions'])}")
                
                # 显示前3个预测
                print(f"\n   前3个预测:")
                for i, pred in enumerate(result['predictions'][:3]):
                    method = pred.get('method', 'unknown')
                    print(f"   [{i+1}] {pred['predicted_direction']} "
                          f"(置信度: {pred['confidence']:.4f}, 方法: {method})")
                
                # 判断使用的方法
                prediction_method = result.get('prediction_method', 'unknown')
                if prediction_method == 'deep_learning':
                    print(f"\n   ✅ 成功！使用了深度学习模型")
                    return True
                elif prediction_method == 'rule_based':
                    print(f"\n   ⚠️  使用了规则预测（模型未被真正调用）")
                    return False
                else:
                    print(f"\n   ❓ 未知方法: {prediction_method}")
                    return False
            else:
                print(f"   ❌ API返回错误: {data.get('message', 'unknown')}")
                return False
        else:
            print(f"   ❌ HTTP错误: {response.status_code}")
            print(f"      响应: {response.text}")
            return False
            
    except Exception as e:
        print(f"   ❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print("\n" + "="*80)

if __name__ == '__main__':
    print("\n启动API预测测试...")
    print("请确保服务器正在运行: http://localhost:5000\n")
    
    import time
    time.sleep(1)
    
    success = test_api_prediction()
    
    if success:
        print("\n✅ 测试通过！模型正在被真正使用！\n")
    else:
        print("\n⚠️  测试未通过，模型可能未被使用\n")
