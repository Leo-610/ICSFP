"""
ICSFP API 简单测试脚本
Intelligent Causal Stock Forecasting Platform
"""
import requests
import json

BASE_URL = "http://localhost:5000"

print("=" * 60)
print("ICSFP API 测试")
print("=" * 60)

# 测试1: 健康检查
print("\n1. 测试健康检查...")
try:
    response = requests.get(f"{BASE_URL}/health", timeout=5)
    print(f"   状态码: {response.status_code}")
    print(f"   响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
except Exception as e:
    print(f"   错误: {e}")

# 测试2: 获取可用股票
print("\n2. 测试获取可用股票...")
try:
    response = requests.get(f"{BASE_URL}/api/v1/stocks", timeout=5)
    print(f"   状态码: {response.status_code}")
    result = response.json()
    print(f"   可用股票数: {len(result['data']['stocks'])}")
    print(f"   部分股票: {result['data']['stocks'][:5]}")
except Exception as e:
    print(f"   错误: {e}")

# 测试3: 获取模型信息
print("\n3. 测试获取模型信息...")
try:
    response = requests.get(f"{BASE_URL}/api/v1/model/info", timeout=5)
    print(f"   状态码: {response.status_code}")
    result = response.json()
    if result['status'] == 'success':
        print(f"   模型: {result['data'].get('model_name', 'Unknown')}")
        print(f"   设备: {result['data'].get('device', 'Unknown')}")
    else:
        print(f"   响应: {json.dumps(result, indent=2, ensure_ascii=False)}")
except Exception as e:
    print(f"   错误: {e}")

print("\n" + "=" * 60)
print("测试完成！")
print("=" * 60)
print("\n访问以下URL查看更多：")
print(f"  - 健康检查: {BASE_URL}/health")
print(f"  - 股票列表: {BASE_URL}/api/v1/stocks")
print(f"  - 模型信息: {BASE_URL}/api/v1/model/info")
