import os
import pandas as pd
import numpy as np
from datetime import datetime


def process_stock_data(raw_folder_path='data/price/raw', output_folder='data/price/processed'):
    """
    遍历raw文件夹下的所有CSV文件，按交易日对齐不同股票的调整收盘价

    Parameters:
    raw_folder_path: 原始数据文件夹路径
    output_folder: 输出文件夹路径
    """

    # 创建输出文件夹（如果不存在）
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    # 存储所有股票数据的字典
    stock_data = {}

    # 遍历raw文件夹下的所有CSV文件
    csv_files = [f for f in os.listdir(raw_folder_path) if f.endswith('.csv')]

    if not csv_files:
        print(f"在 {raw_folder_path} 中没有找到CSV文件")
        return

    print(f"找到 {len(csv_files)} 个CSV文件")

    # 读取每个CSV文件
    for csv_file in csv_files:
        file_path = os.path.join(raw_folder_path, csv_file)
        stock_symbol = csv_file.replace('.csv', '')

        try:
            # 读取CSV文件
            df = pd.read_csv(file_path)

            # 检查必要的列是否存在
            if 'Date' not in df.columns or 'Adj Close' not in df.columns:
                print(f"警告: {csv_file} 缺少必要的列 'Date' 或 'Adj Close'，跳过此文件")
                continue

            # 将Date列转换为datetime类型
            df['Date'] = pd.to_datetime(df['Date'])

            # 设置Date为索引
            df.set_index('Date', inplace=True)

            # 只保留Adj Close列，并重命名为股票代码
            stock_data[stock_symbol] = df['Adj Close']

            print(f"成功读取 {stock_symbol} 的数据，共 {len(df)} 条记录")

        except Exception as e:
            print(f"读取 {csv_file} 时出错: {str(e)}")
            continue

    if not stock_data:
        print("没有成功读取任何股票数据")
        return

    # 创建对齐的DataFrame
    # 使用外连接，保留所有日期
    aligned_df = pd.DataFrame(stock_data)

    # 按日期排序
    aligned_df.sort_index(inplace=True)

    print(f"\n数据对齐完成:")
    print(f"- 总交易日数: {len(aligned_df)}")
    print(f"- 股票数量: {len(aligned_df.columns)}")
    print(f"- 日期范围: {aligned_df.index.min()} 到 {aligned_df.index.max()}")

    # 保存为CSV文件
    csv_output_path = os.path.join(output_folder, 'aligned_adj_close.csv')
    aligned_df.to_csv(csv_output_path)
    print(f"\nCSV文件已保存到: {csv_output_path}")

    # 保存为NumPy文件
    # 将DataFrame转换为NumPy数组
    np_array = aligned_df.values

    # 保存数组数据
    npy_output_path = os.path.join(output_folder, 'aligned_adj_close.npy')
    np.save(npy_output_path, np_array)

    # 同时保存元数据（股票代码和日期）
    metadata = {
        'stocks': aligned_df.columns.tolist(),
        'dates': aligned_df.index.strftime('%Y-%m-%d').tolist()
    }

    metadata_path = os.path.join(output_folder, 'aligned_metadata.npy')
    np.save(metadata_path, metadata)

    print(f"NumPy数组已保存到: {npy_output_path}")
    print(f"元数据已保存到: {metadata_path}")

    # 显示数据预览
    print("\n数据预览（前5行，前5列）:")
    print(aligned_df.iloc[:5, :5])

    # 显示缺失值统计
    print("\n缺失值统计:")
    missing_stats = aligned_df.isnull().sum()
    for stock, missing_count in missing_stats.items():
        if missing_count > 0:
            print(f"- {stock}: {missing_count} 个缺失值 ({missing_count / len(aligned_df) * 100:.2f}%)")

    return aligned_df


def load_aligned_data(processed_folder='data/price/processed'):
    """
    加载对齐后的数据

    Returns:
    df: pandas DataFrame
    np_array: numpy array
    metadata: 包含股票代码和日期的字典
    """
    # 加载CSV文件
    csv_path = os.path.join(processed_folder, 'aligned_adj_close.csv')
    df = pd.read_csv(csv_path, index_col=0, parse_dates=True)

    # 加载NumPy数组
    npy_path = os.path.join(processed_folder, 'aligned_adj_close.npy')
    np_array = np.load(npy_path)

    # 加载元数据
    metadata_path = os.path.join(processed_folder, 'aligned_metadata.npy')
    metadata = np.load(metadata_path, allow_pickle=True).item()

    return df, np_array, metadata


# 主程序
if __name__ == "__main__":
    # 处理数据
    aligned_df = process_stock_data()

    # 演示如何加载数据
    print("\n" + "=" * 50)
    print("演示如何加载保存的数据:")
    print("=" * 50)

    try:
        df, np_array, metadata = load_aligned_data()
        print(f"成功加载数据:")
        print(f"- DataFrame形状: {df.shape}")
        print(f"- NumPy数组形状: {np_array.shape}")
        print(f"- 股票列表: {metadata['stocks'][:5]}...（显示前5个）")
        print(f"- 日期数量: {len(metadata['dates'])}")
    except Exception as e:
        print(f"加载数据时出错: {str(e)}")