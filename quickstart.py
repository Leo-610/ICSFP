#!/usr/bin/env python3
"""
ICSFP Quick Start Script
Intelligent Causal Stock Forecasting Platform - 快速启动脚本
一键启动API服务或运行测试
"""

import sys
import os
import subprocess
import argparse


def check_dependencies():
    """检查依赖是否安装"""
    print("Checking dependencies...")
    try:
        import flask
        import torch
        import numpy
        print("✓ All core dependencies installed")
        return True
    except ImportError as e:
        print(f"✗ Missing dependency: {e}")
        print("\nPlease install dependencies first:")
        print("  pip install -r requirements.txt")
        return False


def start_api_server(port=5000, workers=4):
    """启动API服务器"""
    print(f"\nStarting ICSFP API server on port {port}...")
    print(f"Workers: {workers}")
    print(f"Access API at: http://localhost:{port}")
    print(f"Health check: http://localhost:{port}/health")
    print(f"API docs: http://localhost:{port}/api/v1")
    print("\nPress Ctrl+C to stop\n")
    
    try:
        if workers == 1:
            # 开发模式
            subprocess.run([
                sys.executable, "api/app.py"
            ])
        else:
            # 生产模式
            subprocess.run([
                "gunicorn",
                "-w", str(workers),
                "-b", f"0.0.0.0:{port}",
                "--timeout", "120",
                "api.app:create_app()"
            ])
    except KeyboardInterrupt:
        print("\n\nServer stopped by user")
    except FileNotFoundError:
        print("\n✗ gunicorn not found. Installing...")
        subprocess.run([sys.executable, "-m", "pip", "install", "gunicorn"])
        print("Please run the command again")


def run_tests():
    """运行测试"""
    print("\nRunning API tests...")
    print("Make sure the API server is running first!\n")
    
    try:
        subprocess.run([
            sys.executable, "tests/test_api.py"
        ])
    except Exception as e:
        print(f"✗ Test failed: {e}")


def train_model():
    """训练模型"""
    print("\nTraining model...")
    try:
        subprocess.run([
            sys.executable, "Main.py"
        ])
    except Exception as e:
        print(f"✗ Training failed: {e}")


def compute_causal_graph():
    """计算因果图"""
    print("\nComputing causal graph...")
    try:
        subprocess.run([
            sys.executable, "compute_cuts_graph.py"
        ])
    except Exception as e:
        print(f"✗ Causal graph computation failed: {e}")


def show_info():
    """显示项目信息"""
    print("\n" + "="*60)
    print("ICSFP - Intelligent Causal Stock Forecasting Platform")
    print("="*60)
    print("\nVersion: 1.0.0")
    print("Platform: Stock Prediction with Causal Analysis")
    print("\nFeatures:")
    print("  • Multi-modal data fusion (price + text)")
    print("  • Dynamic causal discovery (Granger, CUTS+)")
    print("  • Deep learning prediction (VAE, GNN)")
    print("  • RESTful API for easy integration")
    print("  • GPU acceleration support")
    print("\nProject Structure:")
    print("  api/          - Web API module")
    print("  causal/       - Causal discovery module")
    print("  modules/      - Model modules")
    print("  data/         - Data directory")
    print("  checkpoints/  - Model checkpoints")
    print("\nDocumentation:")
    print("  README_ICAST.md      - Project overview")
    print("  docs/API_GUIDE.md    - API documentation")
    print("  PHASE1_SUMMARY.md    - Phase 1 summary")
    print("\nQuick Commands:")
    print("  python quickstart.py --serve     # Start API server")
    print("  python quickstart.py --test      # Run tests")
    print("  python quickstart.py --train     # Train model")
    print("  python quickstart.py --causal    # Compute causal graph")
    print("="*60 + "\n")


def main():
    parser = argparse.ArgumentParser(
        description="ICSFP Quick Start Script",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        '--serve', '-s',
        action='store_true',
        help='Start API server'
    )
    
    parser.add_argument(
        '--test', '-t',
        action='store_true',
        help='Run API tests'
    )
    
    parser.add_argument(
        '--train',
        action='store_true',
        help='Train model'
    )
    
    parser.add_argument(
        '--causal', '-c',
        action='store_true',
        help='Compute causal graph'
    )
    
    parser.add_argument(
        '--port', '-p',
        type=int,
        default=5000,
        help='API server port (default: 5000)'
    )
    
    parser.add_argument(
        '--workers', '-w',
        type=int,
        default=1,
        help='Number of workers (default: 1 for dev, 4 for prod)'
    )
    
    parser.add_argument(
        '--info', '-i',
        action='store_true',
        help='Show project information'
    )
    
    args = parser.parse_args()
    
    # 如果没有参数，显示帮助
    if len(sys.argv) == 1:
        show_info()
        parser.print_help()
        return
    
    # 检查依赖
    if not check_dependencies():
        return
    
    # 执行操作
    if args.info:
        show_info()
    elif args.serve:
        start_api_server(args.port, args.workers)
    elif args.test:
        run_tests()
    elif args.train:
        train_model()
    elif args.causal:
        compute_causal_graph()


if __name__ == "__main__":
    main()
