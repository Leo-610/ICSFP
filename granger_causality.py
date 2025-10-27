#!/usr/bin/env python3
"""
Granger因果检验实现
用于发现股票之间的因果关系
"""

import numpy as np
import pandas as pd
from scipy import stats
from statsmodels.tsa.stattools import grangercausalitytests
from statsmodels.tsa.vector_ar.var_model import VAR
import warnings
warnings.filterwarnings('ignore')

class GrangerCausalityAnalyzer:
    """Granger因果检验分析器"""
    
    def __init__(self, max_lags=5, significance_level=0.05):
        """
        初始化Granger因果检验分析器
        
        Args:
            max_lags: 最大滞后期数
            significance_level: 显著性水平
        """
        self.max_lags = max_lags
        self.significance_level = significance_level
        self.causality_matrix = None
        self.p_values = None
        self.stock_names = None
        
    def prepare_data(self, data, stock_names=None):
        """
        准备数据用于Granger因果检验
        
        Args:
            data: 时间序列数据，形状为 (T, N) - T个时间点，N个股票
            stock_names: 股票名称列表
            
        Returns:
            pandas DataFrame
        """
        if stock_names is None:
            stock_names = [f'Stock_{i}' for i in range(data.shape[1])]
            
        self.stock_names = stock_names
        
        # 转换为DataFrame
        df = pd.DataFrame(data, columns=stock_names)
        
        # 移除缺失值
        df = df.dropna()
        
        # 确保数据是平稳的（简单的一阶差分）
        df_diff = df.diff().dropna()
        
        return df_diff
    
    def granger_test_pairwise(self, data, stock_i, stock_j, max_lags=None):
        """
        对两个股票进行Granger因果检验
        
        Args:
            data: 包含股票数据的DataFrame
            stock_i: 股票i的名称
            stock_j: 股票j的名称
            max_lags: 最大滞后期数
            
        Returns:
            dict: 包含检验结果的字典
        """
        if max_lags is None:
            max_lags = self.max_lags
            
        try:
            # 准备数据：股票j是否Granger引起股票i
            test_data = data[[stock_i, stock_j]].dropna()
            
            if len(test_data) < max_lags + 10:  # 确保有足够的数据
                return {
                    'causality': False,
                    'p_value': 1.0,
                    'f_statistic': 0.0,
                    'lags': 0,
                    'error': 'Insufficient data'
                }
            
            # 进行Granger因果检验
            result = grangercausalitytests(test_data, maxlag=max_lags, verbose=False)
            
            # 选择最佳滞后期（基于AIC或BIC）
            best_lag = 1
            best_p_value = 1.0
            best_f_stat = 0.0
            
            for lag in range(1, min(max_lags + 1, len(result))):
                f_stat = result[lag][0]['ssr_ftest'][0]
                p_value = result[lag][0]['ssr_ftest'][1]
                
                if p_value < best_p_value:
                    best_p_value = p_value
                    best_f_stat = f_stat
                    best_lag = lag
            
            # 判断是否存在因果关系
            causality = best_p_value < self.significance_level
            
            return {
                'causality': causality,
                'p_value': best_p_value,
                'f_statistic': best_f_stat,
                'lags': best_lag,
                'error': None
            }
            
        except Exception as e:
            return {
                'causality': False,
                'p_value': 1.0,
                'f_statistic': 0.0,
                'lags': 0,
                'error': str(e)
            }
    
    def compute_causality_matrix(self, data, stock_names=None):
        """
        计算所有股票对的Granger因果矩阵
        
        Args:
            data: 时间序列数据，形状为 (T, N)
            stock_names: 股票名称列表
            
        Returns:
            tuple: (因果矩阵, p值矩阵)
        """
        # 准备数据
        df = self.prepare_data(data, stock_names)
        n_stocks = len(self.stock_names)
        
        # 初始化结果矩阵
        causality_matrix = np.zeros((n_stocks, n_stocks))
        p_values = np.ones((n_stocks, n_stocks))
        
        print(f"开始Granger因果检验，共 {n_stocks} 只股票...")
        
        # 对每对股票进行检验
        for i in range(n_stocks):
            for j in range(n_stocks):
                if i != j:
                    stock_i = self.stock_names[i]
                    stock_j = self.stock_names[j]
                    
                    result = self.granger_test_pairwise(df, stock_i, stock_j)
                    
                    causality_matrix[i, j] = 1 if result['causality'] else 0
                    p_values[i, j] = result['p_value']
                    
                    if result['causality']:
                        print(f"  {stock_j} -> {stock_i}: p={result['p_value']:.4f}, lag={result['lags']}")
        
        self.causality_matrix = causality_matrix
        self.p_values = p_values
        
        return causality_matrix, p_values
    
    def get_top_causal_relationships(self, top_k=20):
        """
        获取最强的因果关系
        
        Args:
            top_k: 返回前k个最强的因果关系
            
        Returns:
            list: 因果关系列表
        """
        if self.causality_matrix is None or self.p_values is None:
            raise ValueError("请先运行 compute_causality_matrix")
        
        relationships = []
        
        for i in range(len(self.stock_names)):
            for j in range(len(self.stock_names)):
                if i != j and self.causality_matrix[i, j] == 1:
                    relationships.append({
                        'cause': self.stock_names[j],
                        'effect': self.stock_names[i],
                        'p_value': self.p_values[i, j],
                        'strength': 1 - self.p_values[i, j]  # 强度 = 1 - p值
                    })
        
        # 按强度排序
        relationships.sort(key=lambda x: x['strength'], reverse=True)
        
        return relationships[:top_k]
    
    def save_results(self, output_path='granger_causality_results.npz'):
        """
        保存结果到文件
        
        Args:
            output_path: 输出文件路径
        """
        if self.causality_matrix is None:
            raise ValueError("没有结果可保存")
        
        np.savez(
            output_path,
            causality_matrix=self.causality_matrix,
            p_values=self.p_values,
            stock_names=np.array(self.stock_names)
        )
        print(f"结果已保存到: {output_path}")
    
    def load_results(self, input_path='granger_causality_results.npz'):
        """
        从文件加载结果
        
        Args:
            input_path: 输入文件路径
        """
        data = np.load(input_path, allow_pickle=True)
        self.causality_matrix = data['causality_matrix']
        self.p_values = data['p_values']
        self.stock_names = data['stock_names'].tolist()
        print(f"结果已从 {input_path} 加载")


def run_granger_causality_analysis(data_path='data/preprocessed_cmin-cn/', 
                                  config_path='config_cmin-cn.yml',
                                  output_path='granger_causality_results.npz',
                                  max_stocks=50):
    """
    运行Granger因果检验分析
    
    Args:
        data_path: 数据文件路径
        config_path: 配置文件路径
        output_path: 输出结果路径
        max_stocks: 最大分析股票数量（避免计算量过大）
    """
    import yaml
    import os
    from datetime import datetime
    
    # 加载配置
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    # 获取股票列表
    stock_list = config['stocks']['cmin'][:max_stocks]  # 限制股票数量
    print(f"分析 {len(stock_list)} 只股票...")
    
    # 加载数据
    data_list = []
    valid_stocks = []
    
    for stock in stock_list:
        file_path = os.path.join(data_path, f'{stock}.txt')
        if os.path.exists(file_path):
            try:
                # 读取股票数据
                df = pd.read_csv(file_path, sep='\t', header=None, 
                               names=['date', 'return', 'volume', 'high', 'low', 'close'])
                
                # 使用收益率数据
                returns = df['return'].values
                
                if len(returns) > 100:  # 确保有足够的数据
                    data_list.append(returns)
                    valid_stocks.append(stock)
                    
            except Exception as e:
                print(f"读取 {stock} 数据失败: {e}")
                continue
    
    if len(data_list) < 2:
        print("有效股票数据不足，无法进行因果分析")
        return
    
    # 对齐数据长度
    min_length = min(len(data) for data in data_list)
    aligned_data = np.array([data[:min_length] for data in data_list]).T
    
    print(f"数据形状: {aligned_data.shape}")
    print(f"有效股票: {len(valid_stocks)}")
    
    # 创建分析器
    analyzer = GrangerCausalityAnalyzer(max_lags=3, significance_level=0.05)
    
    # 计算因果矩阵
    causality_matrix, p_values = analyzer.compute_causality_matrix(
        aligned_data, valid_stocks
    )
    
    # 获取最强的因果关系
    top_relationships = analyzer.get_top_causal_relationships(top_k=20)
    
    print(f"\n发现 {np.sum(causality_matrix)} 个因果关系")
    print("\n前20个最强的因果关系:")
    for i, rel in enumerate(top_relationships, 1):
        print(f"{i:2d}. {rel['cause']} -> {rel['effect']}: "
              f"p={rel['p_value']:.4f}, strength={rel['strength']:.4f}")
    
    # 保存结果
    analyzer.save_results(output_path)
    
    return analyzer, causality_matrix, p_values


if __name__ == "__main__":
    # 运行分析
    analyzer, causality_matrix, p_values = run_granger_causality_analysis()





