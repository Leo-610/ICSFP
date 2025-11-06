"""
生成Mock测试数据 - 简化版
"""

import os
import io
from datetime import datetime, timedelta
import random

def create_price_data():
    """创建价格数据"""
    
    data_dir = './data/price/preprocessed'
    os.makedirs(data_dir, exist_ok=True)
    
    print(f"Creating directory: {data_dir}")
    
    # 完整股票列表
    stocks = [
        'XOM', 'RDS-B', 'PTR', 'CVX', 'TOT', 'BP', 'BHP', 'SNP', 'SLB', 'BBL',
        'AAPL', 'PG', 'BUD', 'KO', 'PM', 'TM', 'PEP', 'UN', 'UL', 'MO',
        'JNJ', 'PFE', 'NVS', 'UNH', 'MRK', 'AMGN', 'MDT', 'ABBV', 'SNY', 'CELG',
        'AMZN', 'BABA', 'WMT', 'CMCSA', 'HD', 'DIS', 'MCD', 'CHTR', 'UPS', 'PCLN',
        'NEE', 'DUK', 'D', 'SO', 'NGG', 'AEP', 'PCG', 'EXC', 'SRE', 'PPL',
        'IEP', 'HRG', 'CODI', 'REX', 'SPLP', 'PICO', 'AGFS', 'GMRE',
        'BCH', 'BSAC', 'BRK-A', 'JPM', 'WFC', 'BAC', 'V', 'C', 'HSBC', 'MA',
        'GE', 'MMM', 'BA', 'HON', 'UTX', 'LMT', 'CAT', 'GD', 'DHR', 'ABB',
        'GOOG', 'MSFT', 'FB', 'T', 'CHL', 'ORCL', 'TSM', 'VZ', 'INTC', 'CSCO'
    ]
    
    # 生成交易日
    start_date = datetime(2014, 1, 2)
    end_date = datetime(2016, 1, 2)
    
    trading_days = []
    current = start_date
    while current <= end_date:
        if current.weekday() < 5:
            trading_days.append(current)
        current += timedelta(days=1)
    
    print(f"Generating {len(trading_days)} trading days for {len(stocks)} stocks")
    
    for stock in stocks:
        file_path = os.path.join(data_dir, f'{stock}.txt')
        base_price = random.uniform(20, 300)
        
        with io.open(file_path, 'w', encoding='utf8') as f:
            for day in reversed(trading_days):
                daily_change = random.gauss(0, 0.02)
                base_price *= (1 + daily_change)
                
                close_price = base_price
                high_price = close_price * (1 + abs(random.gauss(0, 0.01)))
                low_price = close_price * (1 - abs(random.gauss(0, 0.01)))
                open_price = close_price * (1 + random.gauss(0, 0.005))
                volume = random.randint(1000000, 100000000)
                
                line = f"{day.strftime('%Y-%m-%d')}\t{daily_change:.6f}\t{close_price:.2f}\t{high_price:.2f}\t{low_price:.2f}\t{open_price:.2f}\t{volume}\n"
                f.write(line)
    
    print(f"[OK] Created {len(stocks)} stock data files")
    return len(stocks)

def test_data():
    """测试数据"""
    try:
        from DataPipe import DataPipe
        print("\nTesting DataPipe...")
        pipe = DataPipe()
        
        batch_gen = pipe.batch_gen_by_stocks('test')
        count = 0
        for batch_dict in batch_gen:
            count += 1
            print(f"  Batch {count}: {batch_dict['s']} - size: {batch_dict['batch_size']}")
            if count >= 5:
                break
        
        print(f"[OK] DataPipe test successful! Generated {count}+ batches")
        return True
    except Exception as e:
        print(f"[ERROR] DataPipe test failed: {e}")
        return False

if __name__ == '__main__':
    print("="*70)
    print("Mock Data Generator")
    print("="*70)
    
    count = create_price_data()
    print(f"\nCreated data for {count} stocks")
    
    print("\n" + "="*70)
    test_data()
    
    print("\n" + "="*70)
    print("[OK] Done! You can now run: python test_model_usage.py")
    print("="*70)
