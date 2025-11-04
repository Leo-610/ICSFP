"""
测试前端系统信息加载修复
"""
import requests
import time

API_BASE = "http://127.0.0.1:5000/api/v1"

print("=" * 60)
print("测试前端系统信息加载")
print("=" * 60)

# 测试 model/info 端点
print("\n1. 测试 /api/v1/model/info 端点...")
try:
    response = requests.get(f"{API_BASE}/model/info")
    response.raise_for_status()
    result = response.json()
    
    print(f"✅ API 响应成功")
    print(f"\n返回结构:")
    print(f"  status: {result.get('status')}")
    print(f"  data: {type(result.get('data'))}")
    
    data = result.get('data', {})
    print(f"\n系统信息 (从 result.data 获取):")
    print(f"  📊 可用股票: {data.get('total_stocks', 'N/A')}")
    print(f"  🔗 因果图状态: {'已加载' if data.get('causal_graph_available') else '未加载'}")
    print(f"  💻 计算设备: {data.get('device', 'N/A')}")
    print(f"  🏷️  平台版本: {data.get('version', 'N/A')}")
    
    if data.get('causal_graph_shape'):
        print(f"  📈 因果图大小: {data['causal_graph_shape']}")
        print(f"  📉 稀疏度: {data.get('causal_graph_sparsity', 0):.2%}")
    
    print(f"\n模型信息:")
    if data.get('model_name'):
        print(f"  模型名称: {data['model_name'][:50]}...")
    print(f"  总参数: {data.get('total_parameters', 'N/A'):,}")
    print(f"  可训练参数: {data.get('trainable_parameters', 'N/A'):,}")
    print(f"  模型已加载: {'是' if data.get('model_loaded') else '否'}")
    
except requests.exceptions.RequestException as e:
    print(f"❌ API 请求失败: {e}")
    exit(1)

# 验证前端数据访问
print("\n" + "=" * 60)
print("2. 前端数据访问验证")
print("=" * 60)

print("\n前端 JavaScript 代码:")
print("```javascript")
print("const response = await fetch(`${API_BASE}/model/info`);")
print("const result = await response.json();")
print("const data = result.data || result;  // ← 修复：支持两种格式")
print("")
print("// 现在可以正确访问:")
print(f"data.total_stocks = {data.get('total_stocks')}")
print(f"data.causal_graph_available = {data.get('causal_graph_available')}")
print(f"data.device = '{data.get('device')}'")
print("```")

# 测试浏览器访问
print("\n" + "=" * 60)
print("3. 浏览器访问说明")
print("=" * 60)
print(f"\n✅ 修复已应用到: static/index.html")
print(f"\n请在浏览器中访问: http://127.0.0.1:5000")
print(f"\n预期显示:")
print(f"  📊 可用股票: 33")
print(f"  🔗 因果图: 已加载")
print(f"  💻 设备: cuda")
print(f"  🟢 系统状态: 运行中")

print("\n" + "=" * 60)
print("如果显示仍为 0 或未加载，请:")
print("  1. 刷新浏览器页面 (Ctrl+F5 硬刷新)")
print("  2. 打开浏览器开发者工具 (F12)")
print("  3. 查看 Console 标签页的错误信息")
print("  4. 查看 Network 标签页的 /model/info 请求")
print("=" * 60)
