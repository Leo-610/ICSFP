"""
CUTS+方法示例
演示如何使用因果发现管理器的CUTS+方法
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import numpy as np
import matplotlib.pyplot as plt
from causal_discovery_manager import CausalDiscoveryManager
from utils.visualization import (
    setup_chinese_font, 
    plot_causal_graph,
    plot_method_comparison,
    plot_sensitivity_analysis
)

# 设置中文字体支持
setup_chinese_font()

def generate_causal_data(n_samples=200, n_stocks=10):
    """
    生成带有因果关系的模拟数据
    
    创建一个链式因果结构：
    股票0 -> 股票1 -> 股票2 -> ...
    """
    np.random.seed(42)
    data = np.zeros((n_samples, n_stocks))
    
    # 初始化第一个股票
    data[:, 0] = np.random.randn(n_samples)
    
    # 创建因果链
    for t in range(1, n_samples):
        for i in range(1, n_stocks):
            # 从前一个股票获取影响
            if i > 0:
                data[t, i] = 0.5 * data[t-1, i-1] + 0.3 * np.random.randn()
    
    return data

def example_basic_cuts_plus():
    """示例1：基本CUTS+使用"""
    print("=" * 60)
    print("示例1：基本CUTS+因果发现")
    print("=" * 60)
    
    # 生成数据
    data = generate_causal_data(n_samples=200, n_stocks=8)
    stock_names = [f'股票{i}' for i in range(8)]
    
    # 创建管理器
    manager = CausalDiscoveryManager()
    
    # 使用CUTS+方法
    causal_graph, info = manager.compute_causal_graph(
        data=data,
        stock_names=stock_names,
        method='cuts_plus',
        custom_config={
            'epochs': 30,
            'sparsity_alpha': 0.2,
            'learning_rate': 0.001
        }
    )
    
    print(f"\n因果图维度: {causal_graph.shape}")
    print(f"检测到的因果边: {info['n_edges']}")
    print(f"稀疏度: {info['sparsity']:.2%}")
    print(f"密度: {info.get('density', 0):.2%}")
    print(f"计算时间: {info['computation_time']:.2f}秒")
    
    # 使用可视化工具绘制因果图
    plot_causal_graph(
        causal_graph=causal_graph,
        stock_names=stock_names,
        title='CUTS+因果图',
        save_path='cuts_plus_causal_graph.png',
        figsize=(10, 8),
        cmap='hot'
    )
    
    return causal_graph, info

def example_compare_methods():
    """示例2：比较三种方法"""
    print("\n" + "=" * 60)
    print("示例2：比较Granger、Transfer Entropy和CUTS+")
    print("=" * 60)
    
    # 生成数据
    data = generate_causal_data(n_samples=150, n_stocks=6)
    stock_names = [f'S{i}' for i in range(6)]
    
    manager = CausalDiscoveryManager()
    
    methods = {
        'Granger': ('granger', {'max_lag': 5}),
        'Transfer Entropy': ('transfer_entropy', {'k': 3, 'method': 'kraskov', 'n_shuffles': 50}),
        'CUTS+': ('cuts_plus', {'epochs': 25, 'sparsity_alpha': 0.25})
    }
    
    results = {}
    
    print("\n正在运行三种方法...")
    for name, (method, config) in methods.items():
        print(f"\n运行 {name}...")
        causal_graph, info = manager.compute_causal_graph(
            data=data,
            stock_names=stock_names,
            method=method,
            custom_config=config
        )
        results[name] = (causal_graph, info)
        print(f"  边数: {info['n_edges']}")
        print(f"  稀疏度: {info['sparsity']:.2%}")
        print(f"  时间: {info['computation_time']:.2f}秒")
    
    # 使用可视化工具绘制对比图
    plot_method_comparison(
        results=results,
        stock_names=stock_names,
        save_path='method_comparison.png',
        figsize=(18, 5)
    )
    
    return results

def example_sensitivity_analysis():
    """示例3：稀疏性参数敏感性分析"""
    print("\n" + "=" * 60)
    print("示例3：CUTS+稀疏性参数敏感性分析")
    print("=" * 60)
    
    # 生成数据
    data = generate_causal_data(n_samples=150, n_stocks=8)
    stock_names = [f'S{i}' for i in range(8)]
    
    manager = CausalDiscoveryManager()
    
    # 测试不同的稀疏性参数
    alphas = [0.1, 0.2, 0.3, 0.4, 0.5]
    results = []
    
    print("\n测试不同稀疏性阈值...")
    for alpha in alphas:
        print(f"\nalpha = {alpha}")
        causal_graph, info = manager.compute_causal_graph(
            data=data,
            stock_names=stock_names,
            method='cuts_plus',
            custom_config={'sparsity_alpha': alpha, 'epochs': 20},
            force_recompute=True  # 强制重新计算
        )
        results.append((alpha, info['n_edges'], info['sparsity']))
        print(f"  边数: {info['n_edges']}")
        print(f"  稀疏度: {info['sparsity']:.2%}")
    
    # 使用可视化工具绘制敏感性分析图
    alphas_list, edges_list, sparsity_list = zip(*results)
    
    plot_sensitivity_analysis(
        param_values=list(alphas_list),
        metrics={
            '检测到的边数': list(edges_list),
            '实际稀疏度': list(sparsity_list)
        },
        param_name='稀疏性阈值 (alpha)',
        title='CUTS+ 稀疏性参数敏感性分析',
        save_path='sensitivity_analysis.png',
        figsize=(12, 4)
    )

def example_large_scale():
    """示例4：大规模数据集"""
    print("\n" + "=" * 60)
    print("示例4：大规模股票网络 (20个股票)")
    print("=" * 60)
    
    # 生成大规模数据
    data = generate_causal_data(n_samples=300, n_stocks=20)
    stock_names = [f'股票{i:02d}' for i in range(20)]
    
    manager = CausalDiscoveryManager()
    
    print("\n使用CUTS+处理大规模数据...")
    causal_graph, info = manager.compute_causal_graph(
        data=data,
        stock_names=stock_names,
        method='cuts_plus',
        custom_config={
            'epochs': 20,  # 减少epochs以加快速度
            'sparsity_alpha': 0.3
        }
    )
    
    print(f"\n数据集大小: {data.shape}")
    print(f"股票数量: {len(stock_names)}")
    print(f"检测到的因果边: {info['n_edges']}")
    print(f"稀疏度: {info['sparsity']:.2%}")
    print(f"计算时间: {info['computation_time']:.2f}秒")
    
    # 分析因果网络的拓扑结构
    in_degrees = np.sum(causal_graph > 0, axis=1)   # 每个股票被影响的次数
    out_degrees = np.sum(causal_graph > 0, axis=0)  # 每个股票影响他人的次数
    
    print(f"\n网络统计:")
    print(f"平均入度: {np.mean(in_degrees):.2f}")
    print(f"平均出度: {np.mean(out_degrees):.2f}")
    print(f"最大入度: {np.max(in_degrees)} (股票{np.argmax(in_degrees)})")
    print(f"最大出度: {np.max(out_degrees)} (股票{np.argmax(out_degrees)})")
    
    # 使用可视化工具绘制大规模网络
    plot_causal_graph(
        causal_graph=causal_graph,
        stock_names=stock_names,
        title=f'大规模因果网络 (20股票)\n边数: {info["n_edges"]}, 稀疏度: {info["sparsity"]:.1%}',
        save_path='large_scale_network.png',
        figsize=(12, 10),
        cmap='hot'
    )

def main():
    """运行所有示例"""
    print("\n" + "=" * 60)
    print("CUTS+因果发现方法示例")
    print("=" * 60)
    
    try:
        # 示例1：基本使用
        example_basic_cuts_plus()
        
        # 示例2：方法比较
        example_compare_methods()
        
        # 示例3：敏感性分析
        example_sensitivity_analysis()
        
        # 示例4：大规模网络
        example_large_scale()
        
        print("\n" + "=" * 60)
        print("所有示例完成！")
        print("生成的图像:")
        print("  - cuts_plus_causal_graph.png")
        print("  - method_comparison.png")
        print("  - sensitivity_analysis.png")
        print("  - large_scale_network.png")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()
