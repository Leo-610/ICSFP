"""
可视化工具模块
提供因果图、时间序列等可视化功能，支持中文显示
"""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib
from typing import List, Optional, Dict, Tuple
import seaborn as sns

# 配置中文字体
def setup_chinese_font():
    """
    配置matplotlib支持中文显示
    尝试多种常见中文字体，确保兼容性
    """
    # Windows系统常见中文字体
    chinese_fonts = [
        'Microsoft YaHei',  # 微软雅黑
        'SimHei',           # 黑体
        'SimSun',           # 宋体
        'KaiTi',            # 楷体
        'FangSong',         # 仿宋
        'STSong',           # 华文宋体
        'STKaiti',          # 华文楷体
    ]
    
    # 获取系统可用字体
    available_fonts = set([f.name for f in matplotlib.font_manager.fontManager.ttflist])
    
    # 选择第一个可用的中文字体
    selected_font = None
    for font in chinese_fonts:
        if font in available_fonts:
            selected_font = font
            break
    
    if selected_font:
        plt.rcParams['font.sans-serif'] = [selected_font]
        plt.rcParams['axes.unicode_minus'] = False  # 解决负号显示问题
        print(f"使用中文字体: {selected_font}")
    else:
        # 如果没有找到常见字体，使用系统默认
        plt.rcParams['font.sans-serif'] = chinese_fonts
        plt.rcParams['axes.unicode_minus'] = False
        print("警告: 未找到常见中文字体，使用默认配置")
    
    return selected_font


def plot_causal_graph(
    causal_graph: np.ndarray,
    stock_names: List[str],
    title: str = '因果关系图',
    save_path: Optional[str] = None,
    figsize: Tuple[int, int] = (10, 8),
    cmap: str = 'hot',
    show_values: bool = False,
    threshold: float = 0.0
) -> plt.Figure:
    """
    绘制因果图热图
    
    Args:
        causal_graph: 因果图矩阵 (n, n)
        stock_names: 股票名称列表
        title: 图表标题
        save_path: 保存路径（可选）
        figsize: 图表大小
        cmap: 颜色映射
        show_values: 是否显示数值
        threshold: 显示阈值（小于该值的边不显示）
        
    Returns:
        matplotlib Figure对象
    """
    setup_chinese_font()
    
    fig, ax = plt.subplots(figsize=figsize)
    
    # 应用阈值
    plot_graph = causal_graph.copy()
    if threshold > 0:
        plot_graph[plot_graph < threshold] = 0
    
    # 绘制热图
    im = ax.imshow(plot_graph, cmap=cmap, interpolation='nearest', aspect='auto')
    
    # 添加颜色条
    cbar = plt.colorbar(im, ax=ax)
    cbar.set_label('因果强度', rotation=270, labelpad=20)
    
    # 设置坐标轴
    ax.set_xticks(range(len(stock_names)))
    ax.set_yticks(range(len(stock_names)))
    ax.set_xticklabels(stock_names, rotation=45, ha='right')
    ax.set_yticklabels(stock_names)
    
    ax.set_xlabel('原因股票')
    ax.set_ylabel('结果股票')
    ax.set_title(title, fontsize=14, fontweight='bold')
    
    # 显示数值
    if show_values:
        for i in range(len(stock_names)):
            for j in range(len(stock_names)):
                if plot_graph[i, j] > threshold:
                    text = ax.text(j, i, f'{plot_graph[i, j]:.2f}',
                                 ha="center", va="center", color="white", fontsize=8)
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"图表已保存到: {save_path}")
    
    return fig


def plot_method_comparison(
    results: Dict[str, Tuple[np.ndarray, Dict]],
    stock_names: List[str],
    save_path: Optional[str] = None,
    figsize: Tuple[int, int] = (18, 5),
    cmap: str = 'hot'
) -> plt.Figure:
    """
    比较多种因果发现方法的结果
    
    Args:
        results: 字典，键为方法名，值为(因果图, 信息)元组
        stock_names: 股票名称列表
        save_path: 保存路径（可选）
        figsize: 图表大小
        cmap: 颜色映射
        
    Returns:
        matplotlib Figure对象
    """
    setup_chinese_font()
    
    n_methods = len(results)
    fig, axes = plt.subplots(1, n_methods, figsize=figsize)
    
    if n_methods == 1:
        axes = [axes]
    
    for ax, (method_name, (graph, info)) in zip(axes, results.items()):
        im = ax.imshow(graph, cmap=cmap, interpolation='nearest', aspect='auto')
        
        # 标题包含统计信息
        n_edges = info.get('n_edges', np.sum(graph > 0))
        sparsity = info.get('sparsity', 1.0 - n_edges / (graph.shape[0] * graph.shape[1]))
        time_cost = info.get('computation_time', 0)
        
        ax.set_title(
            f'{method_name}\n'
            f'边数: {n_edges}, 稀疏度: {sparsity:.1%}\n'
            f'时间: {time_cost:.2f}s',
            fontsize=11
        )
        
        ax.set_xlabel('原因股票')
        ax.set_ylabel('结果股票')
        
        # 简化坐标轴标签（如果股票太多）
        if len(stock_names) > 10:
            ax.set_xticks(range(0, len(stock_names), max(1, len(stock_names)//10)))
            ax.set_yticks(range(0, len(stock_names), max(1, len(stock_names)//10)))
        else:
            ax.set_xticks(range(len(stock_names)))
            ax.set_yticks(range(len(stock_names)))
            ax.set_xticklabels(stock_names, rotation=45, ha='right', fontsize=8)
            ax.set_yticklabels(stock_names, fontsize=8)
        
        plt.colorbar(im, ax=ax)
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"对比图已保存到: {save_path}")
    
    return fig


def plot_time_series(
    data: np.ndarray,
    stock_names: List[str],
    title: str = '时间序列数据',
    save_path: Optional[str] = None,
    figsize: Tuple[int, int] = (12, 6),
    max_stocks: int = 10
) -> plt.Figure:
    """
    绘制时间序列数据
    
    Args:
        data: 时间序列数据 (T, n_stocks)
        stock_names: 股票名称列表
        title: 图表标题
        save_path: 保存路径（可选）
        figsize: 图表大小
        max_stocks: 最多显示的股票数量
        
    Returns:
        matplotlib Figure对象
    """
    setup_chinese_font()
    
    fig, ax = plt.subplots(figsize=figsize)
    
    n_stocks = min(data.shape[1], max_stocks)
    
    for i in range(n_stocks):
        ax.plot(data[:, i], label=stock_names[i], alpha=0.7, linewidth=1.5)
    
    ax.set_xlabel('时间步')
    ax.set_ylabel('价格/收益率')
    ax.set_title(title, fontsize=14, fontweight='bold')
    ax.legend(loc='best', fontsize=9)
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"时间序列图已保存到: {save_path}")
    
    return fig


def plot_network_statistics(
    causal_graph: np.ndarray,
    stock_names: List[str],
    title: str = '因果网络统计',
    save_path: Optional[str] = None,
    figsize: Tuple[int, int] = (14, 5)
) -> plt.Figure:
    """
    绘制因果网络的统计特征
    
    Args:
        causal_graph: 因果图矩阵
        stock_names: 股票名称列表
        title: 图表标题
        save_path: 保存路径（可选）
        figsize: 图表大小
        
    Returns:
        matplotlib Figure对象
    """
    setup_chinese_font()
    
    fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=figsize)
    
    # 计算入度和出度
    in_degrees = np.sum(causal_graph > 0, axis=1)   # 被影响次数
    out_degrees = np.sum(causal_graph > 0, axis=0)  # 影响他人次数
    
    # 1. 入度分布
    ax1.bar(range(len(stock_names)), in_degrees, color='steelblue', alpha=0.7)
    ax1.set_xlabel('股票')
    ax1.set_ylabel('入度（被影响次数）')
    ax1.set_title('入度分布')
    ax1.set_xticks(range(len(stock_names)))
    ax1.set_xticklabels(stock_names, rotation=45, ha='right', fontsize=8)
    ax1.grid(True, alpha=0.3, axis='y')
    
    # 2. 出度分布
    ax2.bar(range(len(stock_names)), out_degrees, color='coral', alpha=0.7)
    ax2.set_xlabel('股票')
    ax2.set_ylabel('出度（影响他人次数）')
    ax2.set_title('出度分布')
    ax2.set_xticks(range(len(stock_names)))
    ax2.set_xticklabels(stock_names, rotation=45, ha='right', fontsize=8)
    ax2.grid(True, alpha=0.3, axis='y')
    
    # 3. 因果强度分布
    strengths = causal_graph[causal_graph > 0].flatten()
    if len(strengths) > 0:
        ax3.hist(strengths, bins=20, color='mediumseagreen', alpha=0.7, edgecolor='black')
        ax3.set_xlabel('因果强度')
        ax3.set_ylabel('频数')
        ax3.set_title(f'因果强度分布\n(共{len(strengths)}条边)')
        ax3.grid(True, alpha=0.3, axis='y')
    else:
        ax3.text(0.5, 0.5, '无因果边', ha='center', va='center', fontsize=14)
        ax3.set_title('因果强度分布')
    
    fig.suptitle(title, fontsize=14, fontweight='bold', y=1.02)
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"统计图已保存到: {save_path}")
    
    return fig


def plot_sensitivity_analysis(
    param_values: List[float],
    metrics: Dict[str, List[float]],
    param_name: str = '参数',
    title: str = '参数敏感性分析',
    save_path: Optional[str] = None,
    figsize: Tuple[int, int] = (12, 5)
) -> plt.Figure:
    """
    绘制参数敏感性分析图
    
    Args:
        param_values: 参数值列表
        metrics: 指标字典，键为指标名，值为指标值列表
        param_name: 参数名称
        title: 图表标题
        save_path: 保存路径（可选）
        figsize: 图表大小
        
    Returns:
        matplotlib Figure对象
    """
    setup_chinese_font()
    
    n_metrics = len(metrics)
    fig, axes = plt.subplots(1, n_metrics, figsize=figsize)
    
    if n_metrics == 1:
        axes = [axes]
    
    colors = plt.cm.Set2(range(n_metrics))
    
    for ax, (metric_name, values), color in zip(axes, metrics.items(), colors):
        ax.plot(param_values, values, 'o-', linewidth=2, markersize=8, 
                color=color, markeredgecolor='black', markeredgewidth=1)
        ax.set_xlabel(param_name, fontsize=11)
        ax.set_ylabel(metric_name, fontsize=11)
        ax.set_title(metric_name, fontsize=12, fontweight='bold')
        ax.grid(True, alpha=0.3)
    
    fig.suptitle(title, fontsize=14, fontweight='bold', y=1.02)
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"敏感性分析图已保存到: {save_path}")
    
    return fig


# 预设主题
def set_publication_style():
    """设置适合发表的图表样式"""
    setup_chinese_font()
    plt.style.use('seaborn-v0_8-paper')
    plt.rcParams['figure.dpi'] = 150
    plt.rcParams['savefig.dpi'] = 300
    plt.rcParams['font.size'] = 10


def set_presentation_style():
    """设置适合演示的图表样式"""
    setup_chinese_font()
    plt.style.use('seaborn-v0_8-talk')
    plt.rcParams['figure.dpi'] = 100
    plt.rcParams['savefig.dpi'] = 200
    plt.rcParams['font.size'] = 12


if __name__ == '__main__':
    # 测试字体配置
    print("测试中文字体配置...")
    font = setup_chinese_font()
    
    # 创建测试图表
    fig, ax = plt.subplots(figsize=(8, 6))
    ax.text(0.5, 0.5, '中文显示测试\nChinese Font Test', 
            ha='center', va='center', fontsize=16)
    ax.set_title('字体测试')
    ax.set_xlabel('横坐标')
    ax.set_ylabel('纵坐标')
    
    plt.savefig('font_test.png', dpi=150, bbox_inches='tight')
    print("测试图表已保存到: font_test.png")
    plt.close()
    
    print("\n可用的绘图函数:")
    print("- plot_causal_graph: 绘制因果图热图")
    print("- plot_method_comparison: 比较多种方法")
    print("- plot_time_series: 绘制时间序列")
    print("- plot_network_statistics: 绘制网络统计")
    print("- plot_sensitivity_analysis: 绘制敏感性分析")
