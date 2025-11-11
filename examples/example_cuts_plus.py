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
    
    # 可视化因果图
    plt.figure(figsize=(10, 8))
    plt.imshow(causal_graph, cmap='hot', interpolation='nearest')
    plt.colorbar(label='因果强度')
    plt.title('CUTS+因果图')
    plt.xlabel('影响股票')
    plt.ylabel('被影响股票')
    plt.xticks(range(len(stock_names)), stock_names, rotation=45)
    plt.yticks(range(len(stock_names)), stock_names)
    plt.tight_layout()
    plt.savefig('cuts_plus_causal_graph.png', dpi=150)
    print("\n因果图已保存到 cuts_plus_causal_graph.png")
    
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
    
    # 可视化比较
    fig, axes = plt.subplots(1, 3, figsize=(18, 5))
    
    for ax, (name, (graph, info)) in zip(axes, results.items()):
        im = ax.imshow(graph, cmap='hot', interpolation='nearest')
        ax.set_title(f'{name}\n边数: {info["n_edges"]}, 稀疏度: {info["sparsity"]:.1%}')
        ax.set_xlabel('影响股票')
        ax.set_ylabel('被影响股票')
        plt.colorbar(im, ax=ax)
    
    plt.tight_layout()
    plt.savefig('method_comparison.png', dpi=150)
    print("\n\n比较图已保存到 method_comparison.png")
    
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
    
    # 绘制结果
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4))
    
    alphas_list, edges_list, sparsity_list = zip(*results)
    
    ax1.plot(alphas_list, edges_list, 'bo-', linewidth=2, markersize=8)
    ax1.set_xlabel('稀疏性阈值 (alpha)')
    ax1.set_ylabel('检测到的边数')
    ax1.set_title('边数 vs 稀疏性阈值')
    ax1.grid(True, alpha=0.3)
    
    ax2.plot(alphas_list, sparsity_list, 'ro-', linewidth=2, markersize=8)
    ax2.set_xlabel('稀疏性阈值 (alpha)')
    ax2.set_ylabel('实际稀疏度')
    ax2.set_title('稀疏度 vs 稀疏性阈值')
    ax2.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('sensitivity_analysis.png', dpi=150)
    print("\n\n敏感性分析图已保存到 sensitivity_analysis.png")

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
    
    # 可视化大规模因果图
    plt.figure(figsize=(12, 10))
    plt.imshow(causal_graph, cmap='hot', interpolation='nearest')
    plt.colorbar(label='因果强度')
    plt.title(f'大规模因果网络 (20股票)\n边数: {info["n_edges"]}, 稀疏度: {info["sparsity"]:.1%}')
    plt.xlabel('影响股票')
    plt.ylabel('被影响股票')
    plt.tight_layout()
    plt.savefig('large_scale_network.png', dpi=150)
    print("\n大规模网络图已保存到 large_scale_network.png")

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
