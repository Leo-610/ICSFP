#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
ICSFP集成应用 - 结合训练、预测和可视化
将原有的训练/预测功能与新的实时数据和可视化模块集成
"""

import sys
import os
import argparse
import webbrowser
import time
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from ConfigLoader import logger


def start_web_interface():
    """启动Web界面（API服务器 + 可视化）"""
    logger.info("=" * 70)
    logger.info("启动ICSFP Web界面")
    logger.info("=" * 70)
    
    try:
        # 导入Flask应用
        from api.app import create_app
        
        app = create_app()
        
        # 打印访问信息
        logger.info("\n✅ Web服务器启动成功！")
        logger.info("\n可访问的页面:")
        logger.info("  • 基础可视化: http://127.0.0.1:5000/static/visualization.html")
        logger.info("  • 高级可视化: http://127.0.0.1:5000/static/advanced_visualization.html")
        logger.info("  • 实时监控:   http://127.0.0.1:5000/static/realtime.html")
        logger.info("  • API文档:    http://127.0.0.1:5000/api/v1/")
        
        logger.info("\nAPI端点:")
        logger.info("  • 健康检查:   http://127.0.0.1:5000/api/v1/health")
        logger.info("  • 实时报价:   http://127.0.0.1:5000/api/v1/realtime/quote/<symbol>")
        logger.info("  • 实时预测:   http://127.0.0.1:5000/api/v1/realtime/predict/<symbol>")
        
        logger.info("\n按 Ctrl+C 停止服务器")
        logger.info("=" * 70)
        
        # 启动服务器
        app.run(
            host='0.0.0.0',
            port=5000,
            debug=True,
            use_reloader=True
        )
        
    except ImportError as e:
        logger.error(f"无法导入Flask应用: {e}")
        logger.error("请确保已安装所有依赖: pip install -r requirements.txt")
        sys.exit(1)
    except Exception as e:
        logger.error(f"启动Web服务器失败: {e}")
        sys.exit(1)


def train_model():
    """训练模型"""
    logger.info("=" * 70)
    logger.info("开始模型训练")
    logger.info("=" * 70)
    
    try:
        from Main import main as train_main
        train_main()
    except Exception as e:
        logger.error(f"训练失败: {e}")
        sys.exit(1)


def view_predictions(stock_symbol='AAPL'):
    """查看预测结果"""
    logger.info("=" * 70)
    logger.info(f"查看 {stock_symbol} 的预测结果")
    logger.info("=" * 70)
    
    try:
        from StockPredictionViewer import StockPredictionViewer
        
        viewer = StockPredictionViewer()
        predictions = viewer.predict_single_stock(stock_symbol)
        
        if predictions:
            logger.info(f"\n✅ 成功获取 {len(predictions)} 条预测结果")
            # 显示前几条
            for i, pred in enumerate(predictions[:5]):
                logger.info(f"  {i+1}. {pred}")
        else:
            logger.warning("未获取到预测结果")
            
    except Exception as e:
        logger.error(f"查看预测失败: {e}")
        sys.exit(1)


def realtime_predict(symbols=['AAPL', 'GOOG', 'MSFT']):
    """实时预测"""
    logger.info("=" * 70)
    logger.info(f"实时预测: {', '.join(symbols)}")
    logger.info("=" * 70)
    
    try:
        from api.realtime_predictor import RealtimePredictor
        
        predictor = RealtimePredictor()
        
        for symbol in symbols:
            logger.info(f"\n预测 {symbol}...")
            result = predictor.predict_realtime(symbol, use_causal=True)
            
            if result['status'] == 'success':
                pred = result['prediction']
                logger.info(f"  方向: {pred['direction']}")
                logger.info(f"  置信度: {pred['confidence']*100:.1f}%")
                logger.info(f"  上涨概率: {pred['probabilities']['UP']*100:.1f}%")
                logger.info(f"  下跌概率: {pred['probabilities']['DOWN']*100:.1f}%")
            else:
                logger.error(f"  预测失败: {result.get('message', '未知错误')}")
                
    except Exception as e:
        logger.error(f"实时预测失败: {e}")
        sys.exit(1)


def open_browser(url='http://127.0.0.1:5000/static/advanced_visualization.html'):
    """打开浏览器"""
    try:
        time.sleep(2)  # 等待服务器启动
        webbrowser.open(url)
        logger.info(f"已在浏览器中打开: {url}")
    except Exception as e:
        logger.warning(f"无法自动打开浏览器: {e}")


def show_menu():
    """显示菜单"""
    print("\n" + "=" * 70)
    print("ICSFP 股票预测系统 - 集成应用")
    print("=" * 70)
    print("\n请选择功能:")
    print("  1. 启动Web界面 (推荐)")
    print("  2. 训练模型")
    print("  3. 查看预测结果")
    print("  4. 实时预测")
    print("  5. 打开可视化页面")
    print("  0. 退出")
    print("\n" + "=" * 70)


def interactive_mode():
    """交互模式"""
    while True:
        show_menu()
        
        try:
            choice = input("\n请输入选项 (0-5): ").strip()
            
            if choice == '0':
                logger.info("退出程序")
                break
            elif choice == '1':
                start_web_interface()
            elif choice == '2':
                train_model()
            elif choice == '3':
                symbol = input("请输入股票代码 (默认: AAPL): ").strip() or 'AAPL'
                view_predictions(symbol)
            elif choice == '4':
                symbols_input = input("请输入股票代码 (多个用逗号分隔，默认: AAPL,GOOG,MSFT): ").strip()
                symbols = symbols_input.split(',') if symbols_input else ['AAPL', 'GOOG', 'MSFT']
                symbols = [s.strip().upper() for s in symbols]
                realtime_predict(symbols)
            elif choice == '5':
                url = input("请输入URL (默认: 高级可视化页面): ").strip()
                if not url:
                    url = 'http://127.0.0.1:5000/static/advanced_visualization.html'
                open_browser(url)
            else:
                print("无效选项，请重新输入")
                
        except KeyboardInterrupt:
            print("\n\n用户中断")
            break
        except Exception as e:
            logger.error(f"操作失败: {e}")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='ICSFP 股票预测系统 - 集成应用',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 启动Web界面
  python app_integrated.py --web
  
  # 训练模型
  python app_integrated.py --train
  
  # 查看预测
  python app_integrated.py --predict AAPL
  
  # 实时预测
  python app_integrated.py --realtime AAPL,GOOG,MSFT
  
  # 交互模式
  python app_integrated.py --interactive
  
  # 启动Web界面并自动打开浏览器
  python app_integrated.py --web --browser
        """
    )
    
    parser.add_argument('--web', action='store_true', 
                        help='启动Web界面')
    parser.add_argument('--train', action='store_true',
                        help='训练模型')
    parser.add_argument('--predict', type=str, metavar='SYMBOL',
                        help='查看指定股票的预测结果')
    parser.add_argument('--realtime', type=str, metavar='SYMBOLS',
                        help='实时预测（多个股票用逗号分隔）')
    parser.add_argument('--browser', action='store_true',
                        help='自动打开浏览器（配合--web使用）')
    parser.add_argument('--interactive', '-i', action='store_true',
                        help='启动交互模式')
    
    args = parser.parse_args()
    
    # 如果没有参数，显示帮助信息
    if len(sys.argv) == 1:
        parser.print_help()
        print("\n提示: 使用 --interactive 进入交互模式")
        sys.exit(0)
    
    # 执行对应功能
    if args.interactive:
        interactive_mode()
    elif args.web:
        if args.browser:
            import threading
            # 在后台线程中打开浏览器
            browser_thread = threading.Thread(target=open_browser)
            browser_thread.daemon = True
            browser_thread.start()
        start_web_interface()
    elif args.train:
        train_model()
    elif args.predict:
        view_predictions(args.predict)
    elif args.realtime:
        symbols = [s.strip().upper() for s in args.realtime.split(',')]
        realtime_predict(symbols)
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
