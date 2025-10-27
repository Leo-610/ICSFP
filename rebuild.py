#!/usr/bin/env python3
"""
简单的数据生成器，完全避免pickle问题
"""

import pandas as pd
import numpy as np
import os
import glob
import json


def create_stock_data_simple():
    """创建股票数据，使用最简单的格式"""

    print("🔄 创建股票数据（简单格式）...")

    data_path = "data/price/raw"
    csv_files = glob.glob(os.path.join(data_path, "*.csv"))

    if len(csv_files) == 0:
        print("❌ 没有找到CSV文件")
        return

    print(f"发现 {len(csv_files)} 个CSV文件")

    # 收集所有股票数据
    all_stock_data = {}

    for csv_file in csv_files:
        symbol = os.path.basename(csv_file).replace('.csv', '')
        try:
            df = pd.read_csv(csv_file)

            if 'Date' not in df.columns or 'Adj Close' not in df.columns:
                continue

            df['Date'] = pd.to_datetime(df['Date'])
            df = df.sort_values('Date')

            # 筛选日期范围
            start_date = pd.to_datetime('2012-09-04')
            end_date = pd.to_datetime('2017-09-01')
            df_filtered = df[(df['Date'] >= start_date) & (df['Date'] <= end_date)]

            if len(df_filtered) > 0:
                all_stock_data[symbol] = df_filtered[['Date', 'Adj Close']].copy()
                print(f"✅ {symbol}: {len(df_filtered)} 条记录")

        except Exception as e:
            print(f"❌ {symbol}: {e}")

    if len(all_stock_data) == 0:
        print("❌ 没有数据")
        return

    # 找到所有日期
    all_dates = set()
    for symbol, data in all_stock_data.items():
        all_dates.update(data['Date'].dt.date)

    date_list = sorted(list(all_dates))
    stock_list = sorted(list(all_stock_data.keys()))

    print(f"📅 {len(date_list)} 个交易日")
    print(f"📈 {len(stock_list)} 只股票")

    # 创建矩阵
    matrix = np.full((len(date_list), len(stock_list)), np.nan, dtype=np.float64)

    for stock_idx, symbol in enumerate(stock_list):
        stock_df = all_stock_data[symbol]
        stock_df['DateOnly'] = stock_df['Date'].dt.date

        for date_idx, date in enumerate(date_list):
            matching = stock_df[stock_df['DateOnly'] == date]
            if len(matching) > 0:
                matrix[date_idx, stock_idx] = float(matching.iloc[0]['Adj Close'])

    # 前向填充
    for col in range(matrix.shape[1]):
        series = pd.Series(matrix[:, col])
        filled = series.fillna(method='ffill')
        matrix[:, col] = filled.values

    # 保存为多个文件，避免复杂格式
    print("💾 保存数据...")

    # 1. 保存矩阵（纯数值）
    np.save('stock_matrix.npy', matrix)

    # 2. 保存日期（文本文件）
    with open('stock_dates.txt', 'w') as f:
        for date in date_list:
            f.write(f"{date}\n")

    # 3. 保存股票名称（文本文件）
    with open('stock_names.txt', 'w') as f:
        for stock in stock_list:
            f.write(f"{stock}\n")

    # 4. 保存元信息（JSON）
    metadata = {
        'shape': list(matrix.shape),
        'date_range': [str(date_list[0]), str(date_list[-1])],
        'n_stocks': len(stock_list),
        'n_days': len(date_list),
        'missing_values': int(np.isnan(matrix).sum())
    }

    with open('stock_metadata.json', 'w') as f:
        json.dump(metadata, f, indent=2)

    print(f"✅ 数据保存完成:")
    print(f"   stock_matrix.npy: {matrix.shape}")
    print(f"   stock_dates.txt: {len(date_list)} 行")
    print(f"   stock_names.txt: {len(stock_list)} 行")
    print(f"   stock_metadata.json: 元信息")

    return matrix, date_list, stock_list


def test_load_data():
    """测试加载数据"""
    print("\n🔍 测试数据加载...")

    try:
        # 加载矩阵
        matrix = np.load('stock_matrix.npy')
        print(f"✅ 矩阵加载成功: {matrix.shape}")

        # 加载日期
        with open('stock_dates.txt', 'r') as f:
            dates = [line.strip() for line in f]
        print(f"✅ 日期加载成功: {len(dates)} 个")

        # 加载股票名称
        with open('stock_names.txt', 'r') as f:
            stocks = [line.strip() for line in f]
        print(f"✅ 股票名称加载成功: {len(stocks)} 个")

        # 加载元信息
        with open('stock_metadata.json', 'r') as f:
            metadata = json.load(f)
        print(f"✅ 元信息加载成功: {metadata}")

        print("\n📊 数据预览:")
        print(f"矩阵形状: {matrix.shape}")
        print(f"日期范围: {dates[0]} ~ {dates[-1]}")
        print(f"股票示例: {stocks[:5]}")
        print(f"数据示例:\n{matrix[:5, :5]}")

        return True

    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False


if __name__ == "__main__":
    create_stock_data_simple()
    test_load_data()