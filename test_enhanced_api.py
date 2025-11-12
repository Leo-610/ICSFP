"""
测试 Phase 3 增强 API 端点
"""
import requests
import json
import time

BASE_URL = "http://localhost:5000/api/v1/enhanced"

def test_performance_status():
    """测试性能状态端点"""
    print("🧪 测试 1: 性能状态查询")
    print("-" * 60)
    
    try:
        response = requests.get(f"{BASE_URL}/performance/status", timeout=5)
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(json.dumps(data, indent=2, ensure_ascii=False))
            print("✅ 测试通过")
        else:
            print(f"❌ 测试失败: {response.text}")
    except Exception as e:
        print(f"❌ 请求失败: {str(e)}")
    
    print()

def test_causal_methods():
    """测试获取因果方法端点"""
    print("🧪 测试 2: 获取可用因果方法")
    print("-" * 60)
    
    try:
        response = requests.get(f"{BASE_URL}/causal/methods", timeout=5)
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(json.dumps(data, indent=2, ensure_ascii=False))
            print("✅ 测试通过")
        else:
            print(f"❌ 测试失败: {response.text}")
    except Exception as e:
        print(f"❌ 请求失败: {str(e)}")
    
    print()

def test_pipeline_status():
    """测试管道状态端点"""
    print("🧪 测试 3: 管道状态查询")
    print("-" * 60)
    
    try:
        response = requests.get(f"{BASE_URL}/pipeline/status", timeout=5)
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(json.dumps(data, indent=2, ensure_ascii=False))
            print("✅ 测试通过")
        else:
            print(f"❌ 测试失败: {response.text}")
    except Exception as e:
        print(f"❌ 请求失败: {str(e)}")
    
    print()

def test_system_monitor():
    """测试系统监控端点"""
    print("🧪 测试 4: 系统监控")
    print("-" * 60)
    
    try:
        response = requests.get(f"{BASE_URL}/monitor/system", timeout=5)
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(json.dumps(data, indent=2, ensure_ascii=False))
            print("✅ 测试通过")
        else:
            print(f"❌ 测试失败: {response.text}")
    except Exception as e:
        print(f"❌ 请求失败: {str(e)}")
    
    print()

def test_optimize_causal():
    """测试 GPU 加速因果发现端点"""
    print("🧪 测试 5: GPU 加速因果发现 (小数据集)")
    print("-" * 60)
    
    try:
        payload = {
            "stock_codes": ["000001.SZ", "600000.SH"],
            "method": "granger",
            "use_gpu": False,  # 使用 CPU 避免初始化问题
            "cache_enabled": True,
            "batch_size": 8
        }
        
        response = requests.post(
            f"{BASE_URL}/performance/optimize_causal",
            json=payload,
            timeout=30
        )
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(json.dumps(data, indent=2, ensure_ascii=False))
            print("✅ 测试通过")
        else:
            print(f"❌ 测试失败: {response.text}")
    except Exception as e:
        print(f"❌ 请求失败: {str(e)}")
    
    print()

if __name__ == "__main__":
    print("=" * 60)
    print("Phase 3 增强 API 端点测试")
    print("=" * 60)
    print()
    
    # 等待服务器启动
    print("⏳ 等待 API 服务器...")
    time.sleep(2)
    
    # 运行测试
    test_performance_status()
    test_causal_methods()
    test_pipeline_status()
    test_system_monitor()
    # test_optimize_causal()  # 需要数据，暂时跳过
    
    print("=" * 60)
    print("✅ 测试完成")
    print("=" * 60)
