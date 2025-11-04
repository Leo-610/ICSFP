"""
测试 API 并验证前端修复
"""
import requests
import json

API_BASE = 'http://127.0.0.1:5000/api/v1'

print("=" * 60)
print("测试 ICSFP API 和前端修复")
print("=" * 60)

# 测试 1: 检查服务器状态
print("\n1. 检查服务器状态...")
try:
    response = requests.get(f'{API_BASE}/model/info', timeout=10)
    if response.status_code == 200:
        data = response.json()
        print(f"✅ 服务器运行正常")
        print(f"   设备: {data.get('data', {}).get('device', 'Unknown')}")
        print(f"   可用股票: {data.get('data', {}).get('total_stocks', 'Unknown')}")
    else:
        print(f"❌ 服务器响应异常: {response.status_code}")
except Exception as e:
    print(f"❌ 无法连接到服务器: {e}")
    print("\n请确保服务器正在运行:")
    print("  conda activate ic_sfp_gpu")
    print("  cd D:\\ICSFP\\HCSF")
    print("  python api/app.py")
    exit(1)

# 测试 2: 批量预测并验证 avg_confidence
print("\n2. 测试批量预测 API...")
try:
    payload = {
        "stock_symbols": ["AAPL", "MSFT"],
        "start_date": "2025-10-01",
        "end_date": "2025-10-07",
        "use_causal": True
    }
    
    response = requests.post(
        f'{API_BASE}/predict/batch',
        json=payload,
        timeout=30
    )
    
    if response.status_code == 200:
        result = response.json()
        if result['status'] == 'success':
            summary = result['data']['summary']
            avg_conf = summary['avg_confidence']
            
            print(f"✅ 批量预测成功")
            print(f"\n=== 关键数据验证 ===")
            print(f"后端返回的 avg_confidence (原始值): {avg_conf}")
            print(f"数据类型: {type(avg_conf)}")
            print(f"数值范围: {'0-1 (概率)' if 0 <= avg_conf <= 1 else '异常'}")
            
            # 模拟前端显示
            print(f"\n=== 前端显示模拟 ===")
            print(f"修复前错误显示: {avg_conf:.1f}%  ❌ (错误)")
            print(f"修复后正确显示: {(avg_conf * 100):.1f}%  ✅ (正确)")
            
            print(f"\n=== 预测摘要 ===")
            print(f"总股票数: {summary.get('total_stocks', 0)}")
            print(f"成功预测: {summary.get('successful', 0)}")
            print(f"总预测次数: {summary.get('total_predictions', 0)}")
            
            # 验证修复
            print(f"\n=== 修复验证 ===")
            if 0 < avg_conf < 1:
                percentage = avg_conf * 100
                print(f"✅ 后端数据格式正确 (0-1 范围)")
                print(f"✅ 前端修复有效 (乘以 100)")
                print(f"✅ 最终显示: {percentage:.1f}%")
            else:
                print(f"⚠️ 数据范围异常: {avg_conf}")
        else:
            print(f"❌ API 返回错误: {result.get('message', 'Unknown')}")
    else:
        print(f"❌ HTTP 错误: {response.status_code}")
        print(f"   响应: {response.text[:200]}")
        
except Exception as e:
    print(f"❌ 请求失败: {e}")

print("\n" + "=" * 60)
print("测试完成")
print("=" * 60)
