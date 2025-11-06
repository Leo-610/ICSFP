"""
实时数据模块使用示例
演示如何使用实时数据接入功能
"""

import sys
import os
import yaml
import logging
from datetime import datetime, timedelta

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.realtime_data import get_realtime_manager, RealtimeDataManager

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_config():
    """加载配置文件"""
    config_path = 'config/realtime_config.yml'
    
    if os.path.exists(config_path):
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        logger.info(f"Loaded config from {config_path}")
    else:
        # 使用默认配置
        config = {
            'cache_dir': 'cache/realtime',
            'cache_ttl': 60,
            'auto_update': False,
            'update_interval': 300,
            'data_sources': {
                'yahoo_finance': {'enabled': True}
            },
            'watch_list': ['AAPL', 'GOOG', 'MSFT']
        }
        logger.info("Using default config")
    
    return config


def example_get_single_quote():
    """示例1: 获取单只股票实时报价"""
    print("\n" + "="*60)
    print("示例1: 获取单只股票实时报价")
    print("="*60)
    
    config = load_config()
    manager = get_realtime_manager(config)
    
    symbol = 'AAPL'
    
    try:
        # 获取实时报价
        quote = manager.get_realtime_quote(symbol)
        
        print(f"\n{symbol} 实时报价:")
        print(f"  当前价格: ${quote['price']:.2f}")
        print(f"  开盘价: ${quote['open']:.2f}")
        print(f"  最高价: ${quote['high']:.2f}")
        print(f"  最低价: ${quote['low']:.2f}")
        print(f"  成交量: {quote['volume']:,}")
        print(f"  涨跌额: ${quote['change']:.2f}")
        print(f"  涨跌幅: {quote['change_percent']:.2f}%")
        print(f"  数据来源: {quote['source']}")
        print(f"  更新时间: {quote['timestamp']}")
        
    except Exception as e:
        print(f"错误: {e}")


def example_get_multiple_quotes():
    """示例2: 批量获取多只股票报价"""
    print("\n" + "="*60)
    print("示例2: 批量获取多只股票报价")
    print("="*60)
    
    config = load_config()
    manager = get_realtime_manager(config)
    
    symbols = ['AAPL', 'GOOG', 'MSFT', 'AMZN', 'TSLA']
    
    try:
        # 批量获取报价
        quotes = manager.get_multiple_quotes(symbols)
        
        print(f"\n获取 {len(symbols)} 只股票的实时报价:\n")
        print(f"{'代码':<8} {'价格':<10} {'涨跌幅':<10} {'成交量':<15}")
        print("-" * 50)
        
        for symbol, quote in quotes.items():
            if 'error' in quote:
                print(f"{symbol:<8} 错误: {quote['error']}")
            else:
                price = quote['price']
                change_pct = quote['change_percent']
                volume = quote['volume']
                
                # 根据涨跌添加颜色标记
                trend = "▲" if change_pct > 0 else "▼" if change_pct < 0 else "━"
                
                print(f"{symbol:<8} ${price:<9.2f} {trend}{change_pct:<9.2f}% {volume:>14,}")
        
    except Exception as e:
        print(f"错误: {e}")


def example_get_historical_data():
    """示例3: 获取历史数据"""
    print("\n" + "="*60)
    print("示例3: 获取历史数据")
    print("="*60)
    
    config = load_config()
    manager = get_realtime_manager(config)
    
    symbol = 'AAPL'
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)
    
    try:
        # 获取最近30天的历史数据
        df = manager.get_historical_data(
            symbol,
            start_date.strftime('%Y-%m-%d'),
            end_date.strftime('%Y-%m-%d')
        )
        
        print(f"\n{symbol} 最近30天历史数据:")
        print(f"  数据条数: {len(df)}")
        print(f"  日期范围: {df.index.min()} 到 {df.index.max()}")
        print(f"\n最近5天数据:")
        print(df.tail())
        
        # 计算一些统计指标
        if 'Close' in df.columns:
            close_prices = df['Close']
            print(f"\n统计指标:")
            print(f"  平均收盘价: ${close_prices.mean():.2f}")
            print(f"  最高收盘价: ${close_prices.max():.2f}")
            print(f"  最低收盘价: ${close_prices.min():.2f}")
            print(f"  价格波动率: {close_prices.std():.2f}")
            
            # 计算收益率
            returns = close_prices.pct_change().dropna()
            print(f"  平均日收益率: {returns.mean()*100:.2f}%")
            print(f"  收益率标准差: {returns.std()*100:.2f}%")
        
    except Exception as e:
        print(f"错误: {e}")


def example_market_summary():
    """示例4: 获取市场摘要"""
    print("\n" + "="*60)
    print("示例4: 获取市场摘要")
    print("="*60)
    
    config = load_config()
    manager = get_realtime_manager(config)
    
    try:
        # 获取市场摘要
        summary = manager.get_market_summary()
        
        if 'error' in summary:
            print(f"错误: {summary['error']}")
            return
        
        print(f"\n市场摘要 ({summary['timestamp']}):")
        print(f"  关注股票总数: {summary['total_stocks']}")
        print(f"  有效报价数: {summary['valid_quotes']}")
        print(f"  上涨股票数: {summary['up_count']} ({summary['up_count']/summary['valid_quotes']*100:.1f}%)")
        print(f"  下跌股票数: {summary['down_count']} ({summary['down_count']/summary['valid_quotes']*100:.1f}%)")
        print(f"  平均涨跌幅: {summary['avg_change_percent']:.2f}%")
        
        # 显示涨幅前3和跌幅前3
        quotes = summary['quotes']
        valid_quotes = [(symbol, q) for symbol, q in quotes.items() if 'error' not in q]
        
        # 按涨跌幅排序
        sorted_quotes = sorted(valid_quotes, key=lambda x: x[1]['change_percent'], reverse=True)
        
        print("\n涨幅前3:")
        for symbol, quote in sorted_quotes[:3]:
            print(f"  {symbol}: {quote['change_percent']:.2f}% (${quote['price']:.2f})")
        
        print("\n跌幅前3:")
        for symbol, quote in sorted_quotes[-3:]:
            print(f"  {symbol}: {quote['change_percent']:.2f}% (${quote['price']:.2f})")
        
    except Exception as e:
        print(f"错误: {e}")


def example_cache_usage():
    """示例5: 缓存使用"""
    print("\n" + "="*60)
    print("示例5: 缓存使用演示")
    print("="*60)
    
    config = load_config()
    config['cache_ttl'] = 10  # 设置缓存过期时间为10秒
    manager = get_realtime_manager(config)
    
    symbol = 'AAPL'
    
    try:
        import time
        
        # 第一次请求（从数据源获取）
        print("\n第1次请求（从数据源获取）:")
        start_time = time.time()
        quote1 = manager.get_realtime_quote(symbol, use_cache=True)
        time1 = time.time() - start_time
        print(f"  价格: ${quote1['price']:.2f}")
        print(f"  耗时: {time1:.3f}秒")
        
        # 第二次请求（从缓存获取）
        print("\n第2次请求（从缓存获取）:")
        start_time = time.time()
        quote2 = manager.get_realtime_quote(symbol, use_cache=True)
        time2 = time.time() - start_time
        print(f"  价格: ${quote2['price']:.2f}")
        print(f"  耗时: {time2:.3f}秒")
        print(f"  速度提升: {time1/time2:.1f}倍")
        
        # 清除缓存
        print("\n清除缓存:")
        manager.cache.clear(f"quote_{symbol}")
        print("  缓存已清除")
        
        # 第三次请求（从数据源重新获取）
        print("\n第3次请求（缓存清除后，重新从数据源获取）:")
        start_time = time.time()
        quote3 = manager.get_realtime_quote(symbol, use_cache=True)
        time3 = time.time() - start_time
        print(f"  价格: ${quote3['price']:.2f}")
        print(f"  耗时: {time3:.3f}秒")
        
    except Exception as e:
        print(f"错误: {e}")


def example_auto_update():
    """示例6: 自动更新功能"""
    print("\n" + "="*60)
    print("示例6: 自动更新功能")
    print("="*60)
    
    config = load_config()
    config['auto_update'] = True
    config['update_interval'] = 10  # 10秒更新一次
    config['watch_list'] = ['AAPL', 'GOOG', 'MSFT']
    
    manager = RealtimeDataManager(config)
    
    try:
        import time
        
        print("\n启动自动更新（每10秒更新一次）...")
        print("按 Ctrl+C 停止\n")
        
        # 运行30秒
        for i in range(3):
            time.sleep(10)
            print(f"\n更新 {i+1} - {datetime.now().strftime('%H:%M:%S')}")
            
            # 查看缓存的数据
            for symbol in config['watch_list']:
                cache_key = f"quote_{symbol}"
                cached = manager.cache.get(cache_key)
                if cached:
                    print(f"  {symbol}: ${cached['price']:.2f} ({cached['change_percent']:.2f}%)")
        
        # 停止自动更新
        manager.stop_auto_update()
        print("\n自动更新已停止")
        
    except KeyboardInterrupt:
        manager.stop_auto_update()
        print("\n\n自动更新已停止")
    except Exception as e:
        print(f"错误: {e}")
        manager.stop_auto_update()


def main():
    """主函数"""
    print("="*60)
    print("实时数据模块使用示例")
    print("="*60)
    
    while True:
        print("\n请选择要运行的示例:")
        print("1. 获取单只股票实时报价")
        print("2. 批量获取多只股票报价")
        print("3. 获取历史数据")
        print("4. 获取市场摘要")
        print("5. 缓存使用演示")
        print("6. 自动更新功能")
        print("7. 运行所有示例（除自动更新）")
        print("0. 退出")
        
        choice = input("\n请输入选项 (0-7): ").strip()
        
        if choice == '1':
            example_get_single_quote()
        elif choice == '2':
            example_get_multiple_quotes()
        elif choice == '3':
            example_get_historical_data()
        elif choice == '4':
            example_market_summary()
        elif choice == '5':
            example_cache_usage()
        elif choice == '6':
            example_auto_update()
        elif choice == '7':
            example_get_single_quote()
            example_get_multiple_quotes()
            example_get_historical_data()
            example_market_summary()
            example_cache_usage()
        elif choice == '0':
            print("\n再见!")
            break
        else:
            print("\n无效的选项，请重新输入")
        
        input("\n按回车键继续...")


if __name__ == '__main__':
    main()
