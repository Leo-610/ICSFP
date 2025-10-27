#!/usr/bin/env python3
"""
检查CMIN数据质量和格式
"""

import os
import pandas as pd
import numpy as np
import yaml
from collections import Counter

def check_data_format(data_path, config_path):
    """检查数据格式和质量"""
    print("=" * 60)
    print("CMIN数据质量检查")
    print("=" * 60)
    
    # 加载配置
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    stock_list = config['stocks']['cmin']
    print(f"配置文件中定义了 {len(stock_list)} 只股票")
    
    # 检查数据文件
    valid_files = []
    invalid_files = []
    file_stats = []
    
    for i, stock in enumerate(stock_list):
        if i % 50 == 0:
            print(f"检查进度: {i}/{len(stock_list)}")
            
        file_path = os.path.join(data_path, f'{stock}.txt')
        
        if not os.path.exists(file_path):
            invalid_files.append((stock, "文件不存在"))
            continue
            
        try:
            # 尝试读取文件
            df = pd.read_csv(file_path, sep='\t', header=None, 
                           names=['date', 'return', 'volume', 'high', 'low', 'close'])
            
            # 检查数据质量
            issues = []
            
            if len(df) < 100:
                issues.append(f"数据行数不足: {len(df)}")
            
            if df['return'].isna().all():
                issues.append("收益率全为NaN")
            
            if df['return'].isna().sum() > len(df) * 0.5:
                issues.append(f"收益率缺失过多: {df['return'].isna().sum()}/{len(df)}")
            
            if df['date'].isna().any():
                issues.append("日期有缺失值")
            
            # 检查日期格式
            try:
                pd.to_datetime(df['date'].dropna())
            except:
                issues.append("日期格式错误")
            
            if issues:
                invalid_files.append((stock, "; ".join(issues)))
            else:
                valid_files.append(stock)
                file_stats.append({
                    'stock': stock,
                    'rows': len(df),
                    'date_range': f"{df['date'].min()} to {df['date'].max()}",
                    'return_mean': df['return'].mean(),
                    'return_std': df['return'].std(),
                    'missing_returns': df['return'].isna().sum()
                })
                
        except Exception as e:
            invalid_files.append((stock, f"读取错误: {str(e)}"))
    
    # 输出结果
    print(f"\n有效文件: {len(valid_files)}")
    print(f"无效文件: {len(invalid_files)}")
    
    if valid_files:
        print(f"\n有效文件示例:")
        for i, stat in enumerate(file_stats[:5]):
            print(f"  {stat['stock']}: {stat['rows']}行, "
                  f"收益率均值={stat['return_mean']:.4f}, "
                  f"缺失={stat['missing_returns']}")
    
    if invalid_files:
        print(f"\n无效文件示例:")
        for stock, issue in invalid_files[:10]:
            print(f"  {stock}: {issue}")
    
    # 分析数据分布
    if file_stats:
        print(f"\n数据统计:")
        rows_list = [stat['rows'] for stat in file_stats]
        print(f"  平均行数: {np.mean(rows_list):.1f}")
        print(f"  行数范围: {min(rows_list)} - {max(rows_list)}")
        
        return_list = [stat['return_mean'] for stat in file_stats if not np.isnan(stat['return_mean'])]
        if return_list:
            print(f"  平均收益率: {np.mean(return_list):.4f}")
            print(f"  收益率标准差: {np.std(return_list):.4f}")
    
    return valid_files, invalid_files

def check_stock_code_format(stock_list):
    """检查股票代码格式"""
    print(f"\n股票代码格式分析:")
    
    sz_count = sum(1 for s in stock_list if s.endswith('.sz'))
    sh_count = sum(1 for s in stock_list if s.endswith('.sh'))
    ss_count = sum(1 for s in stock_list if s.endswith('.ss'))
    other_count = len(stock_list) - sz_count - sh_count - ss_count
    
    print(f"  .sz (深圳): {sz_count}")
    print(f"  .sh (上海): {sh_count}")
    print(f"  .ss (上海): {ss_count}")
    print(f"  其他格式: {other_count}")
    
    # 检查是否有混合格式
    if sz_count > 0 and (sh_count > 0 or ss_count > 0):
        print("  警告: 发现混合的股票代码格式")
    
    return {
        'sz': sz_count,
        'sh': sh_count, 
        'ss': ss_count,
        'other': other_count
    }

def main():
    """主函数"""
    config_path = 'config_cmin-cn.yml'
    data_path = 'data/preprocessed_cmin-cn'
    
    # 检查数据路径
    if not os.path.exists(data_path):
        print(f"错误: 数据路径不存在: {data_path}")
        return
    
    # 加载配置
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        stock_list = config['stocks']['cmin']
    except Exception as e:
        print(f"错误: 无法加载配置文件: {e}")
        return
    
    # 检查股票代码格式
    format_stats = check_stock_code_format(stock_list)
    
    # 检查数据质量
    valid_files, invalid_files = check_data_format(data_path, config_path)
    
    # 总结
    print(f"\n" + "=" * 60)
    print("检查总结:")
    print(f"  总股票数: {len(stock_list)}")
    print(f"  有效文件: {len(valid_files)}")
    print(f"  无效文件: {len(invalid_files)}")
    print(f"  有效率: {len(valid_files)/len(stock_list)*100:.1f}%")
    
    if len(valid_files) < 10:
        print("  警告: 有效文件数量不足，可能影响训练效果")
    
    print("=" * 60)

if __name__ == "__main__":
    main()





