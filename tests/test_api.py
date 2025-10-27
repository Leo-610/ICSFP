"""
API测试脚本
测试所有API端点的功能
"""

import requests
import json
import sys

BASE_URL = "http://localhost:5000"


def test_health_check():
    """测试健康检查"""
    print("Testing health check...")
    response = requests.get(f"{BASE_URL}/health")
    assert response.status_code == 200
    data = response.json()
    assert data['status'] == 'healthy'
    print("✓ Health check passed")
    return True


def test_single_prediction():
    """测试单股票预测"""
    print("\nTesting single prediction...")
    url = f"{BASE_URL}/api/v1/predict/single"
    data = {
        "stock_symbol": "AAPL",
        "start_date": "2015-10-01",
        "end_date": "2015-10-05",
        "use_causal": True
    }
    
    response = requests.post(url, json=data)
    assert response.status_code == 200
    result = response.json()
    assert result['status'] == 'success'
    assert 'predictions' in result['data']
    print(f"✓ Single prediction passed: {result['data']['stock_symbol']}")
    return True


def test_batch_prediction():
    """测试批量预测"""
    print("\nTesting batch prediction...")
    url = f"{BASE_URL}/api/v1/predict/batch"
    data = {
        "stock_symbols": ["AAPL", "GOOG", "MSFT"],
        "start_date": "2015-10-01",
        "end_date": "2015-10-05",
        "use_causal": True
    }
    
    response = requests.post(url, json=data)
    assert response.status_code == 200
    result = response.json()
    assert result['status'] == 'success'
    assert 'summary' in result['data']
    print(f"✓ Batch prediction passed: {result['data']['summary']['total_stocks']} stocks")
    return True


def test_causal_graph():
    """测试因果图"""
    print("\nTesting causal graph...")
    url = f"{BASE_URL}/api/v1/causal/graph"
    params = {
        "threshold": 0.3
    }
    
    response = requests.get(url, params=params)
    assert response.status_code == 200
    result = response.json()
    assert result['status'] == 'success'
    assert 'graph' in result['data']
    print(f"✓ Causal graph passed: {len(result['data']['stocks'])} stocks")
    return True


def test_causal_influence():
    """测试因果影响力"""
    print("\nTesting causal influence...")
    url = f"{BASE_URL}/api/v1/causal/influence"
    params = {
        "stock": "AAPL",
        "top_k": 5
    }
    
    response = requests.get(url, params=params)
    assert response.status_code == 200
    result = response.json()
    assert result['status'] == 'success'
    assert 'influenced_by' in result['data']
    print(f"✓ Causal influence passed for {result['data']['stock']}")
    return True


def test_get_stocks():
    """测试获取股票列表"""
    print("\nTesting get stocks...")
    url = f"{BASE_URL}/api/v1/stocks"
    
    response = requests.get(url)
    assert response.status_code == 200
    result = response.json()
    assert result['status'] == 'success'
    assert 'stocks' in result['data']
    print(f"✓ Get stocks passed: {len(result['data']['stocks'])} stocks available")
    return True


def test_model_info():
    """测试获取模型信息"""
    print("\nTesting model info...")
    url = f"{BASE_URL}/api/v1/model/info"
    
    response = requests.get(url)
    assert response.status_code == 200
    result = response.json()
    assert result['status'] == 'success'
    assert 'model_name' in result['data']
    print(f"✓ Model info passed: {result['data']['model_name']}")
    return True


def test_error_handling():
    """测试错误处理"""
    print("\nTesting error handling...")
    url = f"{BASE_URL}/api/v1/predict/single"
    
    # 发送无效请求（缺少必需字段）
    response = requests.post(url, json={})
    assert response.status_code == 400
    result = response.json()
    assert result['status'] == 'error'
    print("✓ Error handling passed")
    return True


def run_all_tests():
    """运行所有测试"""
    print("="*50)
    print("iCast API Test Suite")
    print("="*50)
    
    tests = [
        test_health_check,
        test_single_prediction,
        test_batch_prediction,
        test_causal_graph,
        test_causal_influence,
        test_get_stocks,
        test_model_info,
        test_error_handling
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"✗ {test.__name__} failed: {e}")
            failed += 1
    
    print("\n" + "="*50)
    print(f"Test Results: {passed} passed, {failed} failed")
    print("="*50)
    
    return failed == 0


if __name__ == "__main__":
    try:
        # 首先检查服务是否运行
        try:
            requests.get(f"{BASE_URL}/health", timeout=2)
        except requests.exceptions.ConnectionError:
            print("Error: API server is not running!")
            print("Please start the server with: python api/app.py")
            sys.exit(1)
        
        # 运行测试
        success = run_all_tests()
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        print("\n\nTests interrupted by user")
        sys.exit(1)
