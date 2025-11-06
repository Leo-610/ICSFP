#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试可视化页面功能
测试visualization.html和advanced_visualization.html页面的功能
"""

import sys
import os
import time
import webbrowser
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_visualization_pages():
    """测试可视化页面"""
    print("=" * 70)
    print("可视化页面测试")
    print("=" * 70)
    
    # 检查文件是否存在
    static_dir = project_root / "static"
    
    files = {
        "基础可视化": static_dir / "visualization.html",
        "高级可视化": static_dir / "advanced_visualization.html",
        "实时监控": static_dir / "realtime.html"
    }
    
    print("\n📁 检查文件...")
    for name, file_path in files.items():
        if file_path.exists():
            size = file_path.stat().st_size / 1024
            print(f"✓ {name}: {file_path.name} ({size:.1f} KB)")
        else:
            print(f"✗ {name}: {file_path.name} 不存在")
            return False
    
    # 检查服务器是否运行
    print("\n🔌 检查服务器状态...")
    try:
        import requests
        response = requests.get("http://127.0.0.1:5000/api/v1/health", timeout=2)
        if response.status_code == 200:
            print("✓ 服务器运行中")
            server_running = True
        else:
            print("✗ 服务器未响应")
            server_running = False
    except Exception as e:
        print(f"✗ 无法连接到服务器: {e}")
        server_running = False
    
    if not server_running:
        print("\n⚠️  请先启动服务器:")
        print("   conda activate ic_sfp_gpu")
        print("   python api/app.py")
        return False
    
    # 页面功能说明
    print("\n📊 可视化页面功能:")
    print("\n1. visualization.html (基础版)")
    print("   - 实时价格走势图")
    print("   - 单只股票预测")
    print("   - 置信度可视化")
    print("   - 市场数据展示")
    print("   - 自动刷新功能")
    
    print("\n2. advanced_visualization.html (高级版)")
    print("   - 多图表展示 (价格/成交量/波动率)")
    print("   - 多天预测可视化")
    print("   - WebSocket实时推送")
    print("   - 历史数据表格")
    print("   - 响应式设计")
    
    print("\n3. realtime.html (实时监控)")
    print("   - WebSocket连接")
    print("   - 多股票订阅")
    print("   - 实时报价更新")
    print("   - 市场统计")
    
    # 访问页面
    print("\n🌐 打开浏览器访问页面...")
    urls = [
        ("基础可视化", "http://127.0.0.1:5000/static/visualization.html"),
        ("高级可视化", "http://127.0.0.1:5000/static/advanced_visualization.html"),
        ("实时监控", "http://127.0.0.1:5000/static/realtime.html")
    ]
    
    print("\n可用页面:")
    for i, (name, url) in enumerate(urls, 1):
        print(f"{i}. {name}: {url}")
    
    print("\n请选择要打开的页面 (1-3), 或按回车跳过:")
    try:
        choice = input("选择: ").strip()
        if choice and choice.isdigit():
            choice = int(choice)
            if 1 <= choice <= 3:
                name, url = urls[choice - 1]
                print(f"\n正在打开 {name}...")
                webbrowser.open(url)
                time.sleep(1)
                print(f"✓ 已在浏览器中打开: {url}")
    except Exception as e:
        print(f"✗ 打开浏览器失败: {e}")
    
    # 测试API端点
    print("\n🔍 测试API端点...")
    test_symbol = "AAPL"
    
    endpoints = [
        ("实时报价", f"/api/v1/realtime/quote/{test_symbol}"),
        ("历史数据", f"/api/v1/realtime/historical/{test_symbol}"),
        ("实时预测", f"/api/v1/realtime/predict/{test_symbol}"),
    ]
    
    try:
        import requests
        for name, endpoint in endpoints:
            url = f"http://127.0.0.1:5000{endpoint}"
            try:
                response = requests.get(url, timeout=5)
                if response.status_code == 200:
                    data = response.json()
                    if data.get('status') == 'success':
                        print(f"✓ {name}: OK")
                    else:
                        print(f"✗ {name}: {data.get('message', '未知错误')}")
                else:
                    print(f"✗ {name}: HTTP {response.status_code}")
            except Exception as e:
                print(f"✗ {name}: {e}")
    except ImportError:
        print("⚠️  需要安装requests库来测试API")
    
    # 使用说明
    print("\n📖 使用说明:")
    print("\n基础可视化页面:")
    print("1. 输入股票代码 (如: AAPL, GOOG, MSFT)")
    print("2. 选择历史天数 (7/30/90天)")
    print("3. 点击'加载数据'查看走势图")
    print("4. 点击'预测'获取预测结果")
    print("5. 点击'自动刷新'每60秒更新一次")
    
    print("\n高级可视化页面:")
    print("1. 输入股票代码并选择时间范围")
    print("2. 选择预测范围 (1-7天)")
    print("3. 点击'刷新全部'加载所有图表")
    print("4. 点击'多天预测'查看未来趋势")
    print("5. 点击'连接WebSocket'启用实时推送")
    
    print("\n✅ 测试完成!")
    return True


def check_dependencies():
    """检查依赖"""
    print("\n📦 检查依赖...")
    
    required = {
        'flask': 'Flask',
        'flask_socketio': 'Flask-SocketIO',
        'yfinance': 'yfinance',
    }
    
    missing = []
    for module, name in required.items():
        try:
            __import__(module)
            print(f"✓ {name}")
        except ImportError:
            print(f"✗ {name} 未安装")
            missing.append(name)
    
    if missing:
        print(f"\n⚠️  缺少依赖: {', '.join(missing)}")
        print("请运行: pip install -r requirements.txt")
        return False
    
    return True


def main():
    """主函数"""
    print("\n" + "=" * 70)
    print("实时可视化模块测试")
    print("=" * 70)
    
    try:
        # 检查依赖
        if not check_dependencies():
            return
        
        # 测试可视化页面
        test_visualization_pages()
        
        print("\n" + "=" * 70)
        print("测试完成!")
        print("=" * 70)
        
    except KeyboardInterrupt:
        print("\n\n测试被用户中断")
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
