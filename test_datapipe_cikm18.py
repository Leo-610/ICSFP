#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""测试DataPipe是否能正确读取CIKM18数据"""

import logging
from DataPipe import DataPipe

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    print("=" * 70)
    print("测试 DataPipe 读取 CIKM18 数据集")
    print("=" * 70)
    
    # 初始化DataPipe
    print("\n1. 初始化 DataPipe...")
    pipe = DataPipe()
    
    print(f"   价格目录: {pipe.movement_path}")
    print(f"   推文目录: {pipe.tweet_path}")
    
    # 检查数据加载
    from ConfigLoader import stock_symbols
    print(f"\n2. 数据加载状态:")
    print(f"   股票数量: {len(stock_symbols)}")
    print(f"   前10只股票: {stock_symbols[:10]}")
    
    # 尝试生成测试批次
    print(f"\n3. 生成测试批次...")
    gen = pipe.batch_gen_by_stocks('test')
    
    batch_count = 0
    for i, batch in enumerate(gen):
        print(f"   批次 {i+1}:")
        print(f"     键: {list(batch.keys())}")
        
        if 's' in batch:
            print(f"     股票: {batch['s']}")
        if 'y_T' in batch:
            print(f"     标签形状: {batch['y_T'].shape}")
        if 'price' in batch:
            print(f"     价格形状: {batch['price'].shape}")
        if 'word' in batch:
            print(f"     词汇形状: {batch['word'].shape}")
        
        batch_count += 1
        if batch_count >= 5:
            break
    
    print(f"\n4. 结果:")
    if batch_count > 0:
        print(f"   ✓ 成功生成 {batch_count} 个批次")
        print(f"   ✓ DataPipe 工作正常，可以用于模型推理!")
    else:
        print(f"   ✗ 未生成任何批次")
        print(f"   可能原因:")
        print(f"     1. 数据格式不匹配")
        print(f"     2. 推文数据缺失或格式错误")
        print(f"     3. 日期范围不匹配")
    
    print("\n" + "=" * 70)


if __name__ == '__main__':
    main()
