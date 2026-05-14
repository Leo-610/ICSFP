#!/usr/bin/env python3
"""
A股因果图计算脚本
使用Granger因果分析计算股票间的因果关系
"""

import os
import sys
import json
import numpy as np
import pandas as pd
from datetime import datetime
import matplotlib.pyplot as plt
import seaborn as sns
from tqdm import tqdm
import argparse
import logging

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from granger_causality import GrangerCausalityAnalyzer

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class AStockCausalGraphBuilder:
    """A股因果图构建器"""
    
    def __init__(self, 
                 price_dir: str = 'data/astock_formatted/price',
                 output_dir: str = 'graphs_astock',
                 max_lags: int = 5,
                 significance_level: float = 0.05):
        """
        初始化
        
        Args:
            price_dir: 价格数据目录
            output_dir: 输出目录
            max_lags: Granger检验最大滞后期
            significance_level: 显著性水平
        """
        self.price_dir = price_dir
        self.output_dir = output_dir
        self.max_lags = max_lags
        self.significance_level = significance_level
        
        os.makedirs(output_dir, exist_ok=True)
        
        self.analyzer = GrangerCausalityAnalyzer(
            max_lags=max_lags,
            significance_level=significance_level
        )
        
        logger.info(f"初始化A股因果图构建器")
        logger.info(f"  价格数据: {price_dir}")
        logger.info(f"  输出目录: {output_dir}")
        logger.info(f"  最大滞后期: {max_lags}")
        logger.info(f"  显著性水平: {significance_level}")
    
    def load_stock_returns(self, start_date: str = None, end_date: str = None):
        """
        加载股票收益率数据
        
        Args:
            start_date: 开始日期 (YYYY-MM-DD)
            end_date: 结束日期 (YYYY-MM-DD)
            
        Returns:
            returns_matrix: 收益率矩阵 (T, N)
            stock_codes: 股票代码列表
            dates: 日期列表
        """
        logger.info("加载股票收益率数据...")
        
        # 获取所有股票文件
        price_files = [f for f in os.listdir(self.price_dir) if f.endswith('.csv')]
        stock_codes = [f.replace('.csv', '') for f in price_files]
        stock_codes = sorted(stock_codes)
        
        logger.info(f"找到 {len(stock_codes)} 只股票")
        
        # 加载每只股票的收益率
        returns_dict = {}
        common_dates = None
        
        for stock_code in tqdm(stock_codes, desc="加载数据"):
            file_path = os.path.join(self.price_dir, f'{stock_code}.csv')
            df = pd.read_csv(file_path)
            
            # 转换日期
            df['Date'] = pd.to_datetime(df['Date'])
            
            # 过滤日期范围
            if start_date:
                df = df[df['Date'] >= start_date]
            if end_date:
                df = df[df['Date'] <= end_date]
            
            # 计算收益率
            df = df.sort_values('Date')
            df['Return'] = df['Close'].pct_change()
            df = df.dropna()
            
            # 存储
            returns_dict[stock_code] = df.set_index('Date')['Return']
            
            # 找到共同日期
            if common_dates is None:
                common_dates = set(df['Date'])
            else:
                common_dates = common_dates.intersection(set(df['Date']))
        
        # 对齐日期并构建矩阵
        common_dates = sorted(list(common_dates))
        logger.info(f"共同交易日: {len(common_dates)} 天")
        
        T = len(common_dates)
        N = len(stock_codes)
        returns_matrix = np.zeros((T, N))
        
        for j, stock_code in enumerate(stock_codes):
            for i, date in enumerate(common_dates):
                if date in returns_dict[stock_code].index:
                    returns_matrix[i, j] = returns_dict[stock_code].loc[date]
        
        logger.info(f"收益率矩阵形状: {returns_matrix.shape}")
        
        return returns_matrix, stock_codes, common_dates
    
    def compute_causal_graph(self, returns_matrix, stock_codes):
        """
        计算因果图
        
        Args:
            returns_matrix: 收益率矩阵 (T, N)
            stock_codes: 股票代码列表
            
        Returns:
            causal_graph: 因果邻接矩阵 (N, N)
            p_values: p值矩阵 (N, N)
        """
        logger.info("\n" + "=" * 60)
        logger.info("开始计算因果图...")
        logger.info("=" * 60)
        
        # 计算因果矩阵
        causal_matrix, p_values = self.analyzer.compute_causality_matrix(
            returns_matrix, 
            stock_codes
        )
        
        logger.info(f"\n因果图统计:")
        logger.info(f"  矩阵形状: {causal_matrix.shape}")
        logger.info(f"  因果关系数: {np.sum(causal_matrix > 0)} / {causal_matrix.size}")
        logger.info(f"  平均连接度: {np.mean(np.sum(causal_matrix > 0, axis=1)):.2f}")
        logger.info(f"  最大出度: {np.max(np.sum(causal_matrix > 0, axis=1))}")
        logger.info(f"  最小出度: {np.min(np.sum(causal_matrix > 0, axis=1))}")
        
        return causal_matrix, p_values
    
    def normalize_causal_graph(self, causal_matrix):
        """
        归一化因果图（行归一化）
        
        Args:
            causal_matrix: 原始因果矩阵
            
        Returns:
            normalized_matrix: 归一化后的矩阵
        """
        # 转为邻接矩阵（1/0）
        adj_matrix = (causal_matrix > 0).astype(float)
        
        # 行归一化
        row_sums = adj_matrix.sum(axis=1, keepdims=True)
        row_sums[row_sums == 0] = 1  # 避免除零
        normalized_matrix = adj_matrix / row_sums
        
        return normalized_matrix.astype(np.float32)
    
    def visualize_causal_graph(self, causal_matrix, stock_codes, top_k=20):
        """
        可视化因果图
        
        Args:
            causal_matrix: 因果矩阵
            stock_codes: 股票代码列表
            top_k: 显示前k个最强的因果关系
        """
        logger.info("\n生成可视化...")
        
        # 1. 完整因果矩阵热图
        plt.figure(figsize=(20, 18))
        sns.heatmap(causal_matrix, 
                   xticklabels=stock_codes, 
                   yticklabels=stock_codes,
                   cmap='YlOrRd',
                   cbar_kws={'label': 'Causal Strength'},
                   square=True)
        plt.title(f'A股因果关系矩阵 ({len(stock_codes)}只股票)', fontsize=16, pad=20)
        plt.xlabel('原因股票', fontsize=12)
        plt.ylabel('结果股票', fontsize=12)
        plt.xticks(rotation=90, ha='right', fontsize=8)
        plt.yticks(rotation=0, fontsize=8)
        plt.tight_layout()
        plt.savefig(os.path.join(self.output_dir, 'causal_matrix_heatmap.png'), 
                   dpi=300, bbox_inches='tight')
        plt.close()
        
        # 2. Top-K因果关系
        N = len(stock_codes)
        causal_pairs = []
        for i in range(N):
            for j in range(N):
                if i != j and causal_matrix[i, j] > 0:
                    causal_pairs.append({
                        'cause': stock_codes[j],
                        'effect': stock_codes[i],
                        'strength': causal_matrix[i, j]
                    })
        
        # 按强度排序
        causal_pairs = sorted(causal_pairs, key=lambda x: x['strength'], reverse=True)
        
        # 保存Top-K
        top_k_pairs = causal_pairs[:top_k]
        
        # 可视化Top-K
        if top_k_pairs:
            fig, ax = plt.subplots(figsize=(12, 8))
            causes = [p['cause'] for p in top_k_pairs]
            effects = [p['effect'] for p in top_k_pairs]
            strengths = [p['strength'] for p in top_k_pairs]
            labels = [f"{p['cause']} → {p['effect']}" for p in top_k_pairs]
            
            y_pos = np.arange(len(top_k_pairs))
            ax.barh(y_pos, strengths, color='steelblue')
            ax.set_yticks(y_pos)
            ax.set_yticklabels(labels, fontsize=10)
            ax.set_xlabel('因果强度', fontsize=12)
            ax.set_title(f'Top-{top_k} 最强因果关系', fontsize=14, pad=15)
            ax.invert_yaxis()
            plt.tight_layout()
            plt.savefig(os.path.join(self.output_dir, f'top{top_k}_causal_relationships.png'), 
                       dpi=300, bbox_inches='tight')
            plt.close()
        
        # 3. 出度和入度分布
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
        
        out_degree = np.sum(causal_matrix > 0, axis=1)
        in_degree = np.sum(causal_matrix > 0, axis=0)
        
        ax1.bar(range(len(stock_codes)), out_degree, color='coral')
        ax1.set_xlabel('股票索引', fontsize=12)
        ax1.set_ylabel('出度（影响其他股票数）', fontsize=12)
        ax1.set_title('因果图出度分布', fontsize=14)
        ax1.grid(True, alpha=0.3)
        
        ax2.bar(range(len(stock_codes)), in_degree, color='skyblue')
        ax2.set_xlabel('股票索引', fontsize=12)
        ax2.set_ylabel('入度（被其他股票影响数）', fontsize=12)
        ax2.set_title('因果图入度分布', fontsize=14)
        ax2.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(os.path.join(self.output_dir, 'degree_distribution.png'), 
                   dpi=300, bbox_inches='tight')
        plt.close()
        
        logger.info(f"✓ 可视化图表已保存到 {self.output_dir}")
        
        return causal_pairs
    
    def save_results(self, causal_matrix, p_values, stock_codes, causal_pairs):
        """
        保存结果
        
        Args:
            causal_matrix: 因果矩阵
            p_values: p值矩阵
            stock_codes: 股票代码列表
            causal_pairs: 因果关系对列表
        """
        logger.info("\n保存结果...")
        
        # 1. 保存归一化因果图（用于模型训练）
        normalized_matrix = self.normalize_causal_graph(causal_matrix)
        np.save(os.path.join(self.output_dir, 'astock_causal_graph.npy'), normalized_matrix)
        logger.info(f"✓ 归一化因果图: {self.output_dir}/astock_causal_graph.npy")
        
        # 2. 保存原始因果矩阵
        np.save(os.path.join(self.output_dir, 'astock_causal_matrix_raw.npy'), causal_matrix)
        
        # 3. 保存p值矩阵
        np.save(os.path.join(self.output_dir, 'astock_p_values.npy'), p_values)
        
        # 4. 保存股票代码映射
        with open(os.path.join(self.output_dir, 'stock_codes.txt'), 'w', encoding='utf-8') as f:
            for code in stock_codes:
                f.write(f"{code}\n")
        
        # 5. 保存因果关系详情
        causal_details = {
            'n_stocks': len(stock_codes),
            'n_relationships': len([p for p in causal_pairs if p['strength'] > 0]),
            'avg_degree': float(np.mean(np.sum(causal_matrix > 0, axis=1))),
            'max_degree': int(np.max(np.sum(causal_matrix > 0, axis=1))),
            'top_causers': [],
            'top_affected': [],
            'causal_pairs': causal_pairs[:50]  # 保存前50个
        }
        
        # 找出最有影响力的股票
        out_degree = np.sum(causal_matrix > 0, axis=1)
        top_causers_idx = np.argsort(out_degree)[-10:][::-1]
        causal_details['top_causers'] = [
            {'stock': stock_codes[i], 'out_degree': int(out_degree[i])}
            for i in top_causers_idx
        ]
        
        # 找出最受影响的股票
        in_degree = np.sum(causal_matrix > 0, axis=0)
        top_affected_idx = np.argsort(in_degree)[-10:][::-1]
        causal_details['top_affected'] = [
            {'stock': stock_codes[i], 'in_degree': int(in_degree[i])}
            for i in top_affected_idx
        ]
        
        with open(os.path.join(self.output_dir, 'causal_analysis_report.json'), 'w', encoding='utf-8') as f:
            json.dump(causal_details, f, ensure_ascii=False, indent=2)
        
        logger.info(f"✓ 分析报告: {self.output_dir}/causal_analysis_report.json")
    
    def build_and_save(self, start_date=None, end_date=None, visualize=True, top_k=20):
        """
        构建并保存因果图
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
            visualize: 是否生成可视化
            top_k: 可视化Top-K因果关系
        """
        logger.info("=" * 60)
        logger.info("A股因果图构建流程开始")
        logger.info("=" * 60)
        
        # 1. 加载数据
        returns_matrix, stock_codes, dates = self.load_stock_returns(start_date, end_date)
        
        # 2. 计算因果图
        causal_matrix, p_values = self.compute_causal_graph(returns_matrix, stock_codes)
        
        # 3. 可视化
        causal_pairs = []
        if visualize:
            causal_pairs = self.visualize_causal_graph(causal_matrix, stock_codes, top_k)
        
        # 4. 保存结果
        self.save_results(causal_matrix, p_values, stock_codes, causal_pairs)
        
        logger.info("\n" + "=" * 60)
        logger.info("✅ A股因果图构建完成！")
        logger.info("=" * 60)
        logger.info(f"输出文件:")
        logger.info(f"  • astock_causal_graph.npy (用于模型训练)")
        logger.info(f"  • astock_causal_matrix_raw.npy")
        logger.info(f"  • astock_p_values.npy")
        logger.info(f"  • causal_analysis_report.json")
        logger.info(f"  • stock_codes.txt")
        if visualize:
            logger.info(f"  • causal_matrix_heatmap.png")
            logger.info(f"  • top{top_k}_causal_relationships.png")
            logger.info(f"  • degree_distribution.png")
        logger.info("=" * 60)


def main():
    parser = argparse.ArgumentParser(description='A股因果图计算')
    parser.add_argument('--price-dir', default='data/astock_formatted/price',
                       help='价格数据目录')
    parser.add_argument('--output-dir', default='graphs_astock',
                       help='输出目录')
    parser.add_argument('--start-date', default='2020-01-02',
                       help='开始日期 (YYYY-MM-DD)')
    parser.add_argument('--end-date', default='2024-04-08',
                       help='结束日期 (YYYY-MM-DD), 默认使用训练集')
    parser.add_argument('--max-lags', type=int, default=5,
                       help='Granger检验最大滞后期')
    parser.add_argument('--significance', type=float, default=0.05,
                       help='显著性水平')
    parser.add_argument('--top-k', type=int, default=30,
                       help='可视化Top-K因果关系')
    parser.add_argument('--no-visualize', action='store_true',
                       help='不生成可视化图表')
    
    args = parser.parse_args()
    
    # 创建构建器
    builder = AStockCausalGraphBuilder(
        price_dir=args.price_dir,
        output_dir=args.output_dir,
        max_lags=args.max_lags,
        significance_level=args.significance
    )
    
    # 构建因果图
    builder.build_and_save(
        start_date=args.start_date,
        end_date=args.end_date,
        visualize=not args.no_visualize,
        top_k=args.top_k
    )


if __name__ == '__main__':
    main()
