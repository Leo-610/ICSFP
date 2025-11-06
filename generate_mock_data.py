"""
生成Mock测试数据
为DataPipe创建必要的价格数据文件
"""

import os
import io
from datetime import datetime, timedelta
import random
import numpy as np

def create_mock_price_data():
    """创建Mock价格数据文件"""
    
    # 创建目录
    data_dir = './data/price/preprocessed'
    os.makedirs(data_dir, exist_ok=True)
    
    print(f"[+] 创建目录: {data_dir}")
    
    # 需要创建的股票列表（从config.yml中的stocks - 完整列表）
    stocks = [
        # Basic materials
        'XOM', 'RDS-B', 'PTR', 'CVX', 'TOT', 'BP', 'BHP', 'SNP', 'SLB', 'BBL',
        # Consumer goods  
        'AAPL', 'PG', 'BUD', 'KO', 'PM', 'TM', 'PEP', 'UN', 'UL', 'MO',
        # Healthcare
        'JNJ', 'PFE', 'NVS', 'UNH', 'MRK', 'AMGN', 'MDT', 'ABBV', 'SNY', 'CELG',
        # Services
        'AMZN', 'BABA', 'WMT', 'CMCSA', 'HD', 'DIS', 'MCD', 'CHTR', 'UPS', 'PCLN',
        # Utilities
        'NEE', 'DUK', 'D', 'SO', 'NGG', 'AEP', 'PCG', 'EXC', 'SRE', 'PPL',
        # Conglomerates
        'IEP', 'HRG', 'CODI', 'REX', 'SPLP', 'PICO', 'AGFS', 'GMRE',
        # Finance
        'BCH', 'BSAC', 'BRK-A', 'JPM', 'WFC', 'BAC', 'V', 'C', 'HSBC', 'MA',
        # Industrial goods
        'GE', 'MMM', 'BA', 'HON', 'UTX', 'LMT', 'CAT', 'GD', 'DHR', 'ABB',
        # Tech
        'GOOG', 'MSFT', 'FB', 'T', 'CHL', 'ORCL', 'TSM', 'VZ', 'INTC', 'CSCO'
    ]
    
    # 生成日期范围（2014-01-02 到 2016-01-02）
    start_date = datetime(2014, 1, 2)
    end_date = datetime(2016, 1, 2)
    
    # 生成交易日（跳过周末）
    trading_days = []
    current = start_date
    while current <= end_date:
        if current.weekday() < 5:  # 周一到周五
            trading_days.append(current)
        current += timedelta(days=1)
    
    print(f"📅 生成 {len(trading_days)} 个交易日")
    print(f"   从 {start_date.date()} 到 {end_date.date()}")
    
    # 为每只股票生成数据
    created_files = []
    for stock in stocks:
        file_path = os.path.join(data_dir, f'{stock}.txt')
        
        # 生成初始价格
        base_price = random.uniform(20, 300)
        
        # 倒序写入（从最新到最旧）
        with io.open(file_path, 'w', encoding='utf8') as f:
            for day in reversed(trading_days):
                # 随机价格波动
                daily_change = random.gauss(0, 0.02)  # 平均0%，标准差2%
                base_price *= (1 + daily_change)
                
                # 生成价格数据
                close_price = base_price
                high_price = close_price * (1 + abs(random.gauss(0, 0.01)))
                low_price = close_price * (1 - abs(random.gauss(0, 0.01)))
                open_price = close_price * (1 + random.gauss(0, 0.005))
                
                # 计算价格变化百分比
                price_change_pct = daily_change
                
                # 生成成交量
                volume = random.randint(1000000, 100000000)
                
                # 格式: date \t price_change_pct \t close \t high \t low \t open \t volume
                line = f"{day.strftime('%Y-%m-%d')}\t{price_change_pct:.6f}\t{close_price:.2f}\t{high_price:.2f}\t{low_price:.2f}\t{open_price:.2f}\t{volume}\n"
                f.write(line)
        
        created_files.append(file_path)
    
    print(f"\n✅ 成功创建 {len(created_files)} 个股票数据文件")
    print(f"\n📝 数据格式说明:")
    print(f"   每行: date \\t price_change% \\t close \\t high \\t low \\t open \\t volume")
    print(f"\n示例文件: {created_files[0]}")
    
    # 显示第一个文件的前5行
    with open(created_files[0], 'r') as f:
        lines = f.readlines()[:5]
    print(f"\n前5行数据预览:")
    for line in lines:
        print(f"   {line.strip()}")
    
    return created_files


def create_mock_tweet_data():
    """创建Mock推文数据（简化版）"""
    
    # 创建目录
    tweet_dir = './data/tweet/preprocessed'
    os.makedirs(tweet_dir, exist_ok=True)
    
    print(f"\n📁 创建推文目录: {tweet_dir}")
    
    # 创建一个示例推文文件
    sample_file = os.path.join(tweet_dir, 'AAPL_2014-01-02')
    
    with open(sample_file, 'w', encoding='utf-8') as f:
        # 写入一些示例推文（已分词）
        f.write("apple stock price increase today good news\n")
        f.write("new iphone release sales strong\n")
        f.write("market outlook positive bullish\n")
    
    print(f"✅ 创建示例推文文件: {sample_file}")
    
    return [sample_file]


def verify_data():
    """验证生成的数据"""
    
    print(f"\n" + "="*70)
    print(f"验证数据")
    print(f"="*70)
    
    # 检查价格数据
    price_dir = './data/price/preprocessed'
    if os.path.exists(price_dir):
        files = [f for f in os.listdir(price_dir) if f.endswith('.txt')]
        print(f"\n✅ 价格数据文件: {len(files)} 个")
        print(f"   目录: {price_dir}")
        
        if files:
            # 随机选择一个文件验证
            sample_file = os.path.join(price_dir, random.choice(files))
            with open(sample_file, 'r') as f:
                lines = f.readlines()
            print(f"\n   示例文件: {os.path.basename(sample_file)}")
            print(f"   数据行数: {len(lines)}")
            print(f"   第一行: {lines[0].strip() if lines else 'Empty'}")
            print(f"   最后一行: {lines[-1].strip() if lines else 'Empty'}")
    else:
        print(f"\n❌ 价格数据目录不存在")
    
    # 检查推文数据
    tweet_dir = './data/tweet/preprocessed'
    if os.path.exists(tweet_dir):
        files = os.listdir(tweet_dir)
        print(f"\n✅ 推文数据文件: {len(files)} 个")
        print(f"   目录: {tweet_dir}")
    else:
        print(f"\n⚠️  推文数据目录不存在（可选）")


def test_datapipe():
    """测试DataPipe是否能加载数据"""
    
    print(f"\n" + "="*70)
    print(f"测试DataPipe")
    print(f"="*70)
    
    try:
        from DataPipe import DataPipe
        
        print(f"\n初始化DataPipe...")
        pipe = DataPipe()
        
        print(f"✅ DataPipe初始化成功")
        print(f"   - 训练开始日期: {pipe.train_start_date}")
        print(f"   - 训练结束日期: {pipe.train_end_date}")
        print(f"   - 测试开始日期: {pipe.test_start_date}")
        print(f"   - 测试结束日期: {pipe.test_end_date}")
        print(f"   - 最大天数: {pipe.max_n_days}")
        print(f"   - 批次大小: {pipe.batch_size}")
        
        # 尝试生成一个批次
        print(f"\n尝试生成测试批次...")
        batch_gen = pipe.batch_gen_by_stocks('test')
        
        batch_count = 0
        for batch_dict in batch_gen:
            batch_count += 1
            print(f"\n✅ 成功生成批次 #{batch_count}")
            print(f"   - 股票: {batch_dict['s']}")
            print(f"   - 批次大小: {batch_dict['batch_size']}")
            print(f"   - 价格数据形状: {batch_dict['price_batch'].shape}")
            print(f"   - 词数据形状: {batch_dict['word_batch'].shape}")
            
            if batch_count >= 3:  # 只显示前3个
                print(f"\n... 更多批次省略 ...")
                break
        
        print(f"\n✅ DataPipe测试成功！共生成 {batch_count}+ 个批次")
        return True
        
    except ImportError as e:
        print(f"\n❌ 无法导入DataPipe: {e}")
        return False
    except Exception as e:
        print(f"\n⚠️  DataPipe测试出错: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主函数"""
    
    print("="*70)
    print("Mock测试数据生成器")
    print("="*70)
    print("\n这将创建以下数据:")
    print("  1. 价格数据 (./data/price/preprocessed/*.txt)")
    print("  2. 推文数据 (./data/tweet/preprocessed/*) [可选]")
    print("\n数据规格:")
    print("  - 股票数量: 50+ 只")
    print("  - 时间范围: 2014-01-02 至 2016-01-02")
    print("  - 交易日数: ~500 天")
    print("\n" + "="*70)
    
    input("\n按Enter键开始生成...")
    
    # 1. 生成价格数据
    print(f"\n" + "="*70)
    print(f"步骤 1: 生成价格数据")
    print(f"="*70)
    price_files = create_mock_price_data()
    
    # 2. 生成推文数据（可选）
    print(f"\n" + "="*70)
    print(f"步骤 2: 生成推文数据（简化版）")
    print(f"="*70)
    tweet_files = create_mock_tweet_data()
    
    # 3. 验证数据
    verify_data()
    
    # 4. 测试DataPipe
    test_success = test_datapipe()
    
    # 总结
    print(f"\n" + "="*70)
    print(f"完成！")
    print(f"="*70)
    
    if test_success:
        print(f"\n✅ 所有步骤成功完成！")
        print(f"\n现在可以运行以下测试:")
        print(f"  1. python test_model_usage.py")
        print(f"  2. python test_api_prediction.py")
        print(f"\n模型将使用这些Mock数据进行真实的推理！")
    else:
        print(f"\n⚠️  数据生成完成，但DataPipe测试失败")
        print(f"   可能需要检查配置或数据格式")
    
    print(f"\n" + "="*70)


if __name__ == '__main__':
    main()
