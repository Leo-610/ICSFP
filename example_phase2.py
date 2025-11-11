#!/usr/bin/env python3
"""
Phase 2 快速示例：多数据集因果发现
展示如何使用统一数据加载器和因果发现管理器
"""

import numpy as np
import matplotlib.pyplot as plt
from unified_data_loader import create_data_loader
from causal_discovery_manager import CausalDiscoveryManager

def example_1_basic_usage():
    """示例1: 基本使用"""
    print("=" * 70)
    print("示例 1: 基本使用 - 加载数据集并计算因果图")
    print("=" * 70)
    
    # 1. 创建数据加载器
    loader = create_data_loader('cikm18')
    info = loader.get_dataset_info()
    print(f"\n数据集: {info['name']}")
    print(f"市场: {info['market']}")
    print(f"股票数量: {info['n_stocks']}")
    
    # 2. 获取股票列表
    stocks = loader.get_stock_list()[:10]
    print(f"\n选择的股票: {stocks}")
    
    # 3. 生成模拟数据（实际应该从文件加载）
    n_days = 200
    data = np.cumsum(np.random.randn(n_days, len(stocks)), axis=0)
    
    # 4. 创建因果发现管理器
    manager = CausalDiscoveryManager(
        cache_dir='example_cache',
        enable_cache=True
    )
    
    # 5. 计算因果图
    graph, info = manager.compute_causal_graph(
        data, stocks, method='granger'
    )
    
    print(f"\n因果图计算完成:")
    print(f"  计算时间: {info['computation_time']:.2f}秒")
    print(f"  边数: {info['n_edges']}")
    print(f"  稀疏度: {info['sparsity']:.2%}")
    
    # 清理
    manager.clear_cache()
    print("\n✓ 示例完成！")


def example_2_compare_methods():
    """示例2: 对比多种因果发现方法"""
    print("\n" + "=" * 70)
    print("示例 2: 对比多种因果发现方法")
    print("=" * 70)
    
    # 生成有因果关系的测试数据
    n_stocks = 10
    n_days = 200
    np.random.seed(42)
    
    # 创建数据：Stock 0 -> Stock 1 -> Stock 2
    data = np.zeros((n_days, n_stocks))
    data[:, 0] = np.cumsum(np.random.randn(n_days))
    
    for t in range(2, n_days):
        data[t, 1] = 0.7 * data[t-1, 1] + 0.3 * data[t-1, 0] + np.random.randn() * 0.1
        data[t, 2] = 0.6 * data[t-1, 2] + 0.4 * data[t-1, 1] + np.random.randn() * 0.1
    
    # 其他股票独立
    for i in range(3, n_stocks):
        data[:, i] = np.cumsum(np.random.randn(n_days))
    
    stock_names = [f'Stock_{i}' for i in range(n_stocks)]
    
    # 创建管理器
    manager = CausalDiscoveryManager(cache_dir='example_cache')
    
    # 对比方法
    print("\n计算中...")
    comparison = manager.compare_methods(
        data, stock_names,
        methods=['granger', 'transfer_entropy']
    )
    
    # 显示结果
    print("\n性能对比:")
    performance = comparison['performance_comparison']
    for method, time in performance['computation_time'].items():
        edges = performance['n_edges'][method]
        sparsity = performance['sparsity'][method]
        print(f"  {method:20s}: {time:6.2f}秒, {edges:3d}边, {sparsity:6.2%}稀疏度")
    
    # 一致性分析
    agreement = comparison['agreement_analysis']
    print(f"\n一致性分析:")
    print(f"  共识边数: {agreement['consensus_edges']}")
    print(f"  共识率: {agreement['consensus_rate']:.2%}")
    
    # 清理
    manager.clear_cache()
    print("\n✓ 示例完成！")


def example_3_transfer_entropy():
    """示例3: 使用传递熵分析"""
    print("\n" + "=" * 70)
    print("示例 3: 传递熵因果分析")
    print("=" * 70)
    
    from transfer_entropy import TransferEntropyAnalyzer
    
    # 生成有明确因果关系的数据
    n_days = 200
    np.random.seed(42)
    
    # X 独立
    x = np.cumsum(np.random.randn(n_days))
    
    # Y 受 X 影响
    y = np.zeros(n_days)
    for t in range(2, n_days):
        y[t] = 0.6 * y[t-1] + 0.4 * x[t-1] + np.random.randn() * 0.1
    
    # 创建分析器
    analyzer = TransferEntropyAnalyzer(
        k_history=2,
        l_delay=2,
        method='binning',
        n_surrogates=50
    )
    
    # 测试 X -> Y
    print("\n测试 X -> Y (应该显著):")
    result_xy = analyzer.compute_transfer_entropy(y, x, test_significance=True)
    print(f"  传递熵: {result_xy['transfer_entropy']:.4f}")
    print(f"  P值: {result_xy['p_value']:.4f}")
    print(f"  显著性: {'✓ 是' if result_xy['significant'] else '✗ 否'}")
    
    # 测试 Y -> X (反向，应该不显著)
    print("\n测试 Y -> X (不应该显著):")
    result_yx = analyzer.compute_transfer_entropy(x, y, test_significance=True)
    print(f"  传递熵: {result_yx['transfer_entropy']:.4f}")
    print(f"  P值: {result_yx['p_value']:.4f}")
    print(f"  显著性: {'✓ 是' if result_yx['significant'] else '✗ 否'}")
    
    print("\n✓ 示例完成！")


def example_4_visualization():
    """示例4: 因果图可视化"""
    print("\n" + "=" * 70)
    print("示例 4: 因果图可视化")
    print("=" * 70)
    
    # 生成测试数据
    n_stocks = 8
    n_days = 150
    np.random.seed(42)
    
    data = np.zeros((n_days, n_stocks))
    data[:, 0] = np.cumsum(np.random.randn(n_days))
    
    # 创建一些因果关系
    for t in range(2, n_days):
        data[t, 1] = 0.7 * data[t-1, 1] + 0.3 * data[t-1, 0] + np.random.randn() * 0.1
        data[t, 2] = 0.6 * data[t-1, 2] + 0.4 * data[t-1, 0] + np.random.randn() * 0.1
        data[t, 3] = 0.5 * data[t-1, 3] + 0.3 * data[t-1, 1] + 0.2 * data[t-1, 2] + np.random.randn() * 0.1
    
    for i in range(4, n_stocks):
        data[:, i] = np.cumsum(np.random.randn(n_days))
    
    stock_names = [f'S{i}' for i in range(n_stocks)]
    
    # 计算因果图
    manager = CausalDiscoveryManager(cache_dir='example_cache')
    graph, info = manager.compute_causal_graph(
        data, stock_names, method='granger'
    )
    
    # 可视化
    fig, ax = plt.subplots(figsize=(10, 8))
    im = ax.imshow(graph, cmap='Blues', aspect='auto')
    
    # 设置刻度
    ax.set_xticks(range(n_stocks))
    ax.set_yticks(range(n_stocks))
    ax.set_xticklabels(stock_names)
    ax.set_yticklabels(stock_names)
    
    # 添加颜色条
    plt.colorbar(im, ax=ax, label='Causal Strength')
    
    # 标题
    ax.set_title(f'Causal Graph - {info["n_edges"]} edges, {info["sparsity"]:.1%} sparsity')
    ax.set_xlabel('Source Stock')
    ax.set_ylabel('Target Stock')
    
    # 保存
    plt.tight_layout()
    plt.savefig('example_causal_graph.png', dpi=150)
    print("\n✓ 因果图已保存到 example_causal_graph.png")
    
    # 清理
    manager.clear_cache()
    print("✓ 示例完成！")


def main():
    """运行所有示例"""
    print("\n" + "=" * 70)
    print("Phase 2 多数据集因果发现系统 - 示例集")
    print("=" * 70)
    
    try:
        example_1_basic_usage()
        example_2_compare_methods()
        example_3_transfer_entropy()
        example_4_visualization()
        
        print("\n" + "=" * 70)
        print("所有示例运行完成！")
        print("=" * 70)
        
    except Exception as e:
        print(f"\n错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
