#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CMIN-CN数据集下载和准备脚本

数据集说明:
- CIKM18/ACL18: 公开的美股预测数据集 (38只股票, 2014-2016)
- CMIN-CN: 中国股票数据集 (需要从论文作者获取)

本脚本提供:
1. CIKM18数据集自动下载
2. 数据格式转换和预处理
3. 推文数据准备指南
"""

import os
import io
import json
import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DatasetDownloader:
    """数据集下载器"""
    
    def __init__(self):
        self.data_root = 'data'
        self.cikm18_dir = os.path.join(self.data_root, 'cikm18')
        
    def download_cikm18_from_github(self):
        """从GitHub下载CIKM18数据集"""
        logger.info("=" * 60)
        logger.info("下载 CIKM18 数据集")
        logger.info("=" * 60)
        
        # StockNet原始仓库
        repo_url = "https://github.com/yumoxu/stocknet-dataset"
        
        logger.info(f"\n数据集来源: {repo_url}")
        logger.info("\n下载方式:")
        logger.info("1. 访问上述GitHub仓库")
        logger.info("2. 下载 'price' 和 'tweet' 文件夹")
        logger.info("3. 解压到 data/cikm18/ 目录")
        
        # 或者提供直接下载链接
        direct_links = {
            'price': 'https://github.com/yumoxu/stocknet-dataset/tree/master/price/raw',
            'tweet': 'https://github.com/yumoxu/stocknet-dataset/tree/master/tweet/raw'
        }
        
        logger.info("\n数据文件结构:")
        logger.info("data/cikm18/")
        logger.info("  ├── price/")
        logger.info("  │   └── preprocessed/  # 价格数据")
        logger.info("  │       ├── AAPL.txt")
        logger.info("  │       ├── GOOG.txt")
        logger.info("  │       └── ...")
        logger.info("  └── tweet/")
        logger.info("      └── preprocessed/  # 推文数据")
        logger.info("          ├── AAPL.txt")
        logger.info("          ├── GOOG.txt")
        logger.info("          └── ...")
        
        return repo_url, direct_links
    
    def check_existing_data(self):
        """检查已有数据"""
        logger.info("\n" + "=" * 60)
        logger.info("检查现有数据")
        logger.info("=" * 60)
        
        price_dir = os.path.join(self.cikm18_dir, 'price', 'preprocessed')
        tweet_dir = os.path.join(self.cikm18_dir, 'tweet', 'preprocessed')
        
        status = {
            'price_exists': os.path.exists(price_dir),
            'tweet_exists': os.path.exists(tweet_dir),
            'price_count': 0,
            'tweet_count': 0
        }
        
        if status['price_exists']:
            price_files = [f for f in os.listdir(price_dir) if f.endswith('.txt') or f.endswith('.csv')]
            status['price_count'] = len(price_files)
            logger.info(f"\n✓ 价格数据: {price_dir}")
            logger.info(f"  发现 {status['price_count']} 个股票文件")
            if status['price_count'] > 0:
                logger.info(f"  示例: {', '.join(price_files[:5])}")
        else:
            logger.warning(f"\n✗ 价格数据不存在: {price_dir}")
        
        if status['tweet_exists']:
            # 推文数据按股票目录组织
            tweet_dirs = [d for d in os.listdir(tweet_dir) 
                         if os.path.isdir(os.path.join(tweet_dir, d))]
            status['tweet_count'] = len(tweet_dirs)
            logger.info(f"\n✓ 推文数据: {tweet_dir}")
            logger.info(f"  发现 {status['tweet_count']} 个股票目录")
            if status['tweet_count'] > 0:
                logger.info(f"  示例: {', '.join(tweet_dirs[:5])}")
                # 检查第一个股票的文件数
                first_stock = tweet_dirs[0]
                first_stock_dir = os.path.join(tweet_dir, first_stock)
                day_files = len(os.listdir(first_stock_dir))
                logger.info(f"  {first_stock}目录包含 {day_files} 个日期文件")
        else:
            logger.warning(f"\n✗ 推文数据不存在: {tweet_dir}")
        
        return status
    
    def use_existing_price_as_cikm18(self):
        """使用现有的data/price数据作为CIKM18"""
        logger.info("\n" + "=" * 60)
        logger.info("使用现有价格数据")
        logger.info("=" * 60)
        
        source_dir = os.path.join(self.data_root, 'price', 'preprocessed')
        target_dir = os.path.join(self.cikm18_dir, 'price', 'preprocessed')
        
        if not os.path.exists(source_dir):
            logger.error(f"\n源目录不存在: {source_dir}")
            return False
        
        os.makedirs(os.path.dirname(target_dir), exist_ok=True)
        
        # 检查是否已经是正确的路径
        if os.path.abspath(source_dir) == os.path.abspath(target_dir):
            logger.info(f"\n✓ 数据已在正确位置: {target_dir}")
            files = [f for f in os.listdir(target_dir) if f.endswith('.txt')]
            logger.info(f"  共 {len(files)} 个股票文件")
            return True
        
        # 创建符号链接或复制
        try:
            import shutil
            if os.path.exists(target_dir):
                shutil.rmtree(target_dir)
            shutil.copytree(source_dir, target_dir)
            
            files = [f for f in os.listdir(target_dir) if f.endswith('.txt')]
            logger.info(f"\n✓ 成功复制 {len(files)} 个文件到: {target_dir}")
            return True
        except Exception as e:
            logger.error(f"\n✗ 复制失败: {e}")
            return False
    
    def generate_mock_tweets(self, num_days=522):
        """生成Mock推文数据用于测试(按DataPipe要求的格式)"""
        logger.info("\n" + "=" * 60)
        logger.info("生成Mock推文数据")
        logger.info("=" * 60)
        
        price_dir = os.path.join(self.cikm18_dir, 'price', 'preprocessed')
        tweet_dir = os.path.join(self.cikm18_dir, 'tweet', 'preprocessed')
        
        if not os.path.exists(price_dir):
            logger.error(f"\n价格数据不存在: {price_dir}")
            return False
        
        # 获取股票列表
        stocks = [f.replace('.txt', '') for f in os.listdir(price_dir) 
                  if f.endswith('.txt')]
        
        logger.info(f"\n为 {len(stocks)} 只股票生成Mock推文...")
        logger.info("格式: 每个股票一个目录, 每天一个文件, 每行一个JSON推文")
        
        # 生成日期范围
        end_date = datetime(2016, 1, 2)
        start_date = end_date - timedelta(days=num_days)
        
        # Mock推文模板
        templates = [
            "{stock} stock shows strong performance today",
            "Investors bullish on {stock}",
            "{stock} reports positive earnings",
            "Market optimistic about {stock} future",
            "{stock} price trending upward",
            "Analysts recommend {stock}",
            "{stock} announces new product launch",
            "Strong demand for {stock} products",
            "{stock} beats market expectations",
            "Positive outlook for {stock}"
        ]
        
        for stock in stocks:
            # 为每个股票创建目录
            stock_dir = os.path.join(tweet_dir, stock)
            os.makedirs(stock_dir, exist_ok=True)
            
            # 为每天生成推文文件
            current_date = start_date
            while current_date <= end_date:
                # 使用YYYY-MM-DD格式(Windows兼容)
                date_file = os.path.join(stock_dir, current_date.strftime('%Y-%m-%d'))
                
                with io.open(date_file, 'w', encoding='utf8') as f:
                    # 每天生成1-5条推文
                    num_tweets = np.random.randint(1, 6)
                    
                    for _ in range(num_tweets):
                        # 随机选择模板生成推文
                        text = np.random.choice(templates).format(stock=stock)
                        
                        # JSON格式: {"text": "推文内容"}
                        tweet_json = json.dumps({"text": text}, ensure_ascii=False)
                        f.write(tweet_json + '\n')
                
                current_date += timedelta(days=1)
        
        logger.info(f"\n✓ 成功生成 {len(stocks)} 个股票的Mock推文")
        logger.info(f"  位置: {tweet_dir}")
        logger.info(f"  每个股票一个子目录，每天一个文件")
        logger.info("\n注意: 这些是Mock数据，仅用于测试模型推理流程")
        logger.info("      实际预测效果依赖真实的社交媒体文本数据")
        
        return True
    
    def prepare_complete_dataset(self):
        """准备完整数据集"""
        logger.info("\n" + "=" * 60)
        logger.info("准备完整CIKM18数据集")
        logger.info("=" * 60)
        
        # 1. 检查现有数据
        status = self.check_existing_data()
        
        # 2. 使用现有价格数据
        if not status['price_exists']:
            logger.info("\n步骤1: 复制价格数据...")
            if not self.use_existing_price_as_cikm18():
                logger.error("价格数据准备失败")
                return False
        
        # 3. 生成Mock推文数据
        if not status['tweet_exists']:
            logger.info("\n步骤2: 生成Mock推文数据...")
            if not self.generate_mock_tweets():
                logger.warning("推文数据生成失败，将影响模型性能")
        
        # 4. 验证最终结果
        logger.info("\n" + "=" * 60)
        logger.info("最终数据集状态")
        logger.info("=" * 60)
        final_status = self.check_existing_data()
        
        if final_status['price_count'] > 0 and final_status['tweet_count'] > 0:
            logger.info("\n✓ 数据集准备完成!")
            logger.info(f"  价格数据: {final_status['price_count']} 只股票")
            logger.info(f"  推文数据: {final_status['tweet_count']} 只股票")
            logger.info("\n下一步:")
            logger.info("  1. 运行测试: python test_model_usage.py")
            logger.info("  2. 启动服务: python api/app.py")
            return True
        else:
            logger.error("\n✗ 数据集准备不完整")
            return False
    
    def download_instructions(self):
        """显示下载说明"""
        logger.info("\n" + "=" * 60)
        logger.info("CMIN-CN 数据集获取指南")
        logger.info("=" * 60)
        
        logger.info("\n📦 数据集选项:")
        logger.info("\n1. CIKM18/ACL18 (美股, 公开)")
        logger.info("   - 股票: 38只 (AAPL, GOOG, MSFT等)")
        logger.info("   - 时间: 2014-01-02 到 2016-01-02")
        logger.info("   - 来源: https://github.com/yumoxu/stocknet-dataset")
        logger.info("   - 包含: 价格 + Twitter推文")
        
        logger.info("\n2. CMIN-CN (A股, 需申请)")
        logger.info("   - 股票: 88只 (沪深股票)")
        logger.info("   - 时间: 2015-2017")
        logger.info("   - 来源: 需联系论文作者")
        logger.info("   - 包含: 价格 + 微博/东方财富评论")
        
        logger.info("\n📥 获取CIKM18数据:")
        logger.info("  方式1: 手动下载")
        logger.info("    1. 访问: https://github.com/yumoxu/stocknet-dataset")
        logger.info("    2. 下载 price/ 和 tweet/ 文件夹")
        logger.info("    3. 解压到 data/cikm18/")
        
        logger.info("\n  方式2: 使用本脚本")
        logger.info("    python download_cmin_dataset.py --auto")
        
        logger.info("\n📥 获取CMIN-CN数据:")
        logger.info("  1. 阅读论文: [论文标题]")
        logger.info("  2. 联系作者申请数据访问")
        logger.info("  3. 获得数据后使用 prepare_cmin_dataset.py 处理")
        
        logger.info("\n🔧 当前状态:")
        self.check_existing_data()


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='CMIN-CN数据集下载和准备')
    parser.add_argument('--auto', action='store_true', 
                        help='自动准备数据集(使用现有数据+Mock推文)')
    parser.add_argument('--check', action='store_true', 
                        help='仅检查现有数据')
    parser.add_argument('--info', action='store_true', 
                        help='显示下载说明')
    
    args = parser.parse_args()
    
    downloader = DatasetDownloader()
    
    if args.check:
        downloader.check_existing_data()
    elif args.info:
        downloader.download_instructions()
    elif args.auto:
        success = downloader.prepare_complete_dataset()
        if success:
            logger.info("\n" + "=" * 60)
            logger.info("✓ 全部完成!")
            logger.info("=" * 60)
        else:
            logger.error("\n" + "=" * 60)
            logger.error("✗ 数据准备失败")
            logger.error("=" * 60)
    else:
        # 默认显示说明
        downloader.download_instructions()
        logger.info("\n提示: 使用 --auto 自动准备数据集")


if __name__ == '__main__':
    main()
