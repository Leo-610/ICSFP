"""
API调试测试脚本
"""
import requests
import json

API_BASE = 'http://localhost:5000/api/v1'

print("=" * 50)
print("ICSFP API 调试测试")
print("=" * 50)

# 测试1: 健康检查
print("\n[1] 测试健康检查...")
try:
    response = requests.get(f'{API_BASE}/../health')
    print(f"状态码: {response.status_code}")
    print(f"响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
except Exception as e:
    print(f"错误: {e}")

# 测试2: 模型信息
print("\n[2] 测试模型信息...")
try:
    response = requests.get(f'{API_BASE}/model/info')
    print(f"状态码: {response.status_code}")
    data = response.json()
    print(f"响应: {json.dumps(data, indent=2, ensure_ascii=False)}")
except Exception as e:
    print(f"错误: {e}")

# 测试3: 单股票预测
print("\n[3] 测试单股票预测...")
try:
    payload = {
        'stock_symbol': 'AAPL',
        'start_date': '2024-10-20',
        'end_date': '2024-10-27',
        'use_causal': True
    }
    print(f"请求数据: {json.dumps(payload, indent=2, ensure_ascii=False)}")
    
    response = requests.post(
        f'{API_BASE}/predict/single',
        json=payload,
        headers={'Content-Type': 'application/json'}
    )
    
    print(f"状态码: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"响应键: {list(data.keys())}")
        print(f"完整响应: {json.dumps(data, indent=2, ensure_ascii=False)}")
        
        # 检查predictions字段
        if 'predictions' in data:
            print(f"\n✅ predictions字段存在")
            print(f"类型: {type(data['predictions'])}")
            print(f"长度: {len(data['predictions']) if isinstance(data['predictions'], list) else 'N/A'}")
            if isinstance(data['predictions'], list) and len(data['predictions']) > 0:
                print(f"第一条预测: {json.dumps(data['predictions'][0], indent=2, ensure_ascii=False)}")
        else:
            print(f"\n❌ predictions字段不存在!")
    else:
        print(f"错误响应: {response.text}")
        
except Exception as e:
    print(f"错误: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 50)
print("测试完成")
print("=" * 50)
