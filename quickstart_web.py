#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
ICSFP 快速启动脚本
提供一键启动Web界面和可视化功能
"""

import sys
import os
import time
import webbrowser
import threading
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def print_banner():
    """打印欢迎横幅"""
    print("\n" + "=" * 80)
    print("""
    ██╗ ██████╗███████╗███████╗██████╗ 
    ██║██╔════╝██╔════╝██╔════╝██╔══██╗
    ██║██║     ███████╗█████╗  ██████╔╝
    ██║██║     ╚════██║██╔══╝  ██╔═══╝ 
    ██║╚██████╗███████║██║     ██║     
    ╚═╝ ╚═════╝╚══════╝╚═╝     ╚═╝     
    
    智能股票预测系统 - Intelligent Causal Stock Forecasting Platform
    """)
    print("=" * 80)


def check_environment():
    """检查环境"""
    print("\n🔍 检查运行环境...")
    
    # 检查Python版本
    python_version = sys.version_info
    print(f"  ✓ Python {python_version.major}.{python_version.minor}.{python_version.micro}")
    
    # 检查关键依赖
    dependencies = {
        'torch': 'PyTorch',
        'flask': 'Flask',
        'flask_socketio': 'Flask-SocketIO',
        'yfinance': 'yfinance',
        'numpy': 'NumPy',
    }
    
    missing = []
    for module, name in dependencies.items():
        try:
            __import__(module)
            print(f"  ✓ {name}")
        except ImportError:
            print(f"  ✗ {name} 未安装")
            missing.append(name)
    
    if missing:
        print(f"\n⚠️  缺少依赖: {', '.join(missing)}")
        print("请运行: pip install -r requirements.txt")
        return False
    
    return True


def check_model():
    """检查模型文件"""
    print("\n📦 检查模型文件...")
    
    # 检查因果图
    if Path('causal_graph.npy').exists():
        print("  ✓ 因果图文件")
    else:
        print("  ⚠️  因果图文件不存在（将自动生成）")
    
    # 检查模型checkpoint
    checkpoint_dirs = list(Path('checkpoints').glob('*'))
    if checkpoint_dirs:
        print(f"  ✓ 找到 {len(checkpoint_dirs)} 个模型检查点")
    else:
        print("  ⚠️  未找到训练好的模型（需要先训练）")
    
    return True


def open_browser_delayed(url, delay=3):
    """延迟打开浏览器"""
    time.sleep(delay)
    try:
        webbrowser.open(url)
        print(f"\n✅ 已在浏览器中打开: {url}")
    except Exception as e:
        print(f"\n⚠️  无法自动打开浏览器: {e}")
        print(f"   请手动访问: {url}")


def start_server():
    """启动服务器"""
    print("\n🚀 启动Web服务器...")
    print("-" * 80)
    
    try:
        from api.app import create_app
        
        app = create_app()
        
        # 打印访问信息
        print("\n" + "=" * 80)
        print("✅ ICSFP Web服务器已启动！")
        print("=" * 80)
        
        print("\n📊 可视化页面:")
        print("  1. 高级可视化 (推荐)")
        print("     → http://127.0.0.1:5000/static/advanced_visualization.html")
        print("  2. 基础可视化")
        print("     → http://127.0.0.1:5000/static/visualization.html")
        print("  3. 实时监控")
        print("     → http://127.0.0.1:5000/static/realtime.html")
        
        print("\n🔌 API端点:")
        print("  • 健康检查:  GET /api/v1/health")
        print("  • 实时报价:  GET /api/v1/realtime/quote/<symbol>")
        print("  • 历史数据:  GET /api/v1/realtime/historical/<symbol>")
        print("  • 实时预测:  GET /api/v1/realtime/predict/<symbol>")
        print("  • 多天预测:  GET /api/v1/realtime/predict/horizon/<symbol>")
        
        print("\n💡 使用提示:")
        print("  • 在页面中输入股票代码（如: AAPL, GOOG, MSFT）")
        print("  • 点击'刷新全部'加载数据和图表")
        print("  • 点击'多天预测'查看未来趋势")
        print("  • 点击'连接WebSocket'启用实时推送")
        
        print("\n⚠️  按 Ctrl+C 停止服务器")
        print("=" * 80 + "\n")
        
        # 在后台线程中打开浏览器
        browser_url = 'http://127.0.0.1:5000/static/advanced_visualization.html'
        browser_thread = threading.Thread(
            target=open_browser_delayed,
            args=(browser_url, 3)
        )
        browser_thread.daemon = True
        browser_thread.start()
        
        # 启动服务器
        app.run(
            host='0.0.0.0',
            port=5000,
            debug=False,  # 生产环境建议关闭debug
            use_reloader=False  # 避免重复打开浏览器
        )
        
    except ImportError as e:
        print(f"\n❌ 无法导入Flask应用: {e}")
        print("请确保已安装所有依赖: pip install -r requirements.txt")
        return False
    except OSError as e:
        if 'Address already in use' in str(e):
            print(f"\n❌ 端口5000已被占用")
            print("请停止其他服务或使用不同端口")
        else:
            print(f"\n❌ 启动服务器失败: {e}")
        return False
    except KeyboardInterrupt:
        print("\n\n👋 服务器已停止")
        return True
    except Exception as e:
        print(f"\n❌ 启动失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主函数"""
    print_banner()
    
    # 检查环境
    if not check_environment():
        print("\n❌ 环境检查失败，请先安装依赖")
        sys.exit(1)
    
    # 检查模型
    check_model()
    
    # 启动服务器
    print("\n" + "=" * 80)
    print("准备启动...")
    print("=" * 80)
    
    try:
        start_server()
    except KeyboardInterrupt:
        print("\n\n👋 程序已退出")
    except Exception as e:
        print(f"\n❌ 发生错误: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
