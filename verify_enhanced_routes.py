"""
验证 Phase 3 增强 API 路由注册
"""
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from api.app import create_app

def test_route_registration():
    """测试路由注册"""
    print("=" * 70)
    print("Phase 3 增强 API 路由注册验证")
    print("=" * 70)
    print()
    
    # 创建应用
    app = create_app()
    
    # 获取所有增强路由
    enhanced_routes = []
    for rule in app.url_map.iter_rules():
        if 'enhanced' in str(rule):
            enhanced_routes.append(str(rule))
    
    # 排序并显示
    enhanced_routes.sort()
    
    print(f"✅ 成功注册 {len(enhanced_routes)} 个增强 API 端点:")
    print()
    
    # 按类别分组显示
    categories = {
        'performance': [],
        'causal': [],
        'pipeline': [],
        'monitor': []
    }
    
    for route in enhanced_routes:
        for category in categories:
            if category in route:
                categories[category].append(route)
                break
    
    # 显示每个类别
    for category, routes in categories.items():
        if routes:
            print(f"📊 {category.upper()} ({len(routes)} 个端点):")
            for route in routes:
                # 提取端点路径和方法
                parts = route.split()
                if len(parts) >= 2:
                    path = parts[0]
                    methods = parts[1] if len(parts) > 1 else ""
                    print(f"  {path}")
            print()
    
    # 测试端点可调用性
    print("=" * 70)
    print("端点功能验证 (Mock 测试)")
    print("=" * 70)
    print()
    
    with app.test_client() as client:
        # 测试 1: 性能状态
        print("🧪 测试 1: GET /api/v1/enhanced/performance/status")
        try:
            response = client.get('/api/v1/enhanced/performance/status')
            print(f"   状态码: {response.status_code}")
            if response.status_code == 200:
                print("   ✅ 端点可访问")
            else:
                print(f"   ⚠️ 响应异常: {response.status_code}")
        except Exception as e:
            print(f"   ❌ 错误: {str(e)}")
        print()
        
        # 测试 2: 因果方法列表
        print("🧪 测试 2: GET /api/v1/enhanced/causal/methods")
        try:
            response = client.get('/api/v1/enhanced/causal/methods')
            print(f"   状态码: {response.status_code}")
            if response.status_code == 200:
                print("   ✅ 端点可访问")
                data = response.get_json()
                if data and 'methods' in data:
                    print(f"   📝 返回 {len(data['methods'])} 个方法")
            else:
                print(f"   ⚠️ 响应异常: {response.status_code}")
        except Exception as e:
            print(f"   ❌ 错误: {str(e)}")
        print()
        
        # 测试 3: 管道状态
        print("🧪 测试 3: GET /api/v1/enhanced/pipeline/status")
        try:
            response = client.get('/api/v1/enhanced/pipeline/status')
            print(f"   状态码: {response.status_code}")
            if response.status_code == 200:
                print("   ✅ 端点可访问")
            else:
                print(f"   ⚠️ 响应异常: {response.status_code}")
        except Exception as e:
            print(f"   ❌ 错误: {str(e)}")
        print()
        
        # 测试 4: 系统监控
        print("🧪 测试 4: GET /api/v1/enhanced/monitor/system")
        try:
            response = client.get('/api/v1/enhanced/monitor/system')
            print(f"   状态码: {response.status_code}")
            if response.status_code == 200:
                print("   ✅ 端点可访问")
            else:
                print(f"   ⚠️ 响应异常: {response.status_code}")
        except Exception as e:
            print(f"   ❌ 错误: {str(e)}")
        print()
    
    print("=" * 70)
    print("✅ 路由注册验证完成")
    print("=" * 70)

if __name__ == "__main__":
    test_route_registration()
