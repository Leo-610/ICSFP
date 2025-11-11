"""
CUTS+集成测试
测试CUTS+方法在因果发现管理器中的集成
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import numpy as np
import pytest
from causal_discovery_manager import CausalDiscoveryManager

class TestCUTSPlusIntegration:
    """CUTS+集成测试类"""
    
    @pytest.fixture
    def sample_data(self):
        """生成测试数据"""
        np.random.seed(42)
        T, N = 100, 5
        
        # 生成有因果关系的时间序列
        data = np.zeros((T, N))
        data[:, 0] = np.random.randn(T)
        
        # 添加因果关系: 0->1, 1->2, 0->3
        for t in range(1, T):
            data[t, 1] = 0.6 * data[t-1, 0] + 0.3 * np.random.randn()
            data[t, 2] = 0.5 * data[t-1, 1] + 0.3 * np.random.randn()
            data[t, 3] = 0.4 * data[t-1, 0] + 0.3 * np.random.randn()
            data[t, 4] = 0.3 * np.random.randn()
        
        return data
    
    @pytest.fixture
    def manager(self):
        """创建因果发现管理器"""
        return CausalDiscoveryManager()
    
    def test_cuts_plus_basic(self, manager, sample_data):
        """测试CUTS+基本功能"""
        stock_names = [f'stock_{i}' for i in range(sample_data.shape[1])]
        
        # 使用CUTS+
        causal_graph, info = manager.compute_causal_graph(
            data=sample_data,
            stock_names=stock_names,
            method='cuts_plus',
            custom_config={
                'epochs': 20,  # 少量epochs用于快速测试
                'sparsity_alpha': 0.2
            }
        )
        
        # 检查因果图形状
        assert causal_graph.shape == (5, 5)
        
        # 检查对角线为0
        assert np.allclose(np.diag(causal_graph), 0)
        
        # 检查元数据
        assert 'n_edges' in info
        assert 'sparsity' in info
        assert info['n_edges'] >= 0
        assert 0 <= info['sparsity'] <= 1
        assert info['method'] == 'cuts_plus'
    
    def test_cuts_plus_edge_detection(self, manager, sample_data):
        """测试CUTS+边检测能力"""
        stock_names = [f'stock_{i}' for i in range(sample_data.shape[1])]
        
        causal_graph, info = manager.compute_causal_graph(
            data=sample_data,
            stock_names=stock_names,
            method='cuts_plus',
            custom_config={'sparsity_alpha': 0.15}
        )
        
        # 应该检测到一些边（因为数据有因果关系）
        assert info['n_edges'] > 0
        
        # 稀疏性应该合理
        assert info['sparsity'] > 0.5  # 至少50%稀疏
    
    def test_cuts_plus_comparison(self, manager, sample_data):
        """比较CUTS+与其他方法"""
        stock_names = [f'stock_{i}' for i in range(sample_data.shape[1])]
        
        # 运行三种方法
        methods = ['granger', 'transfer_entropy', 'cuts_plus']
        results = {}
        
        for method in methods:
            if method == 'granger':
                config = {'max_lag': 5, 'alpha': 0.05}
            elif method == 'transfer_entropy':
                config = {'k': 3, 'method': 'kraskov', 'n_shuffles': 50}
            else:  # cuts_plus
                config = {'epochs': 20, 'sparsity_alpha': 0.2}
            
            causal_graph, info = manager.compute_causal_graph(
                data=sample_data,
                stock_names=stock_names,
                method=method,
                custom_config=config
            )
            results[method] = (causal_graph, info)
        
        # 所有方法都应该成功
        for method, (graph, info) in results.items():
            assert graph.shape == (5, 5), f"{method} failed"
        
        # 打印比较
        print("\n=== Method Comparison ===")
        for method, (graph, info) in results.items():
            print(f"{method}:")
            print(f"  Edges: {info['n_edges']}")
            print(f"  Sparsity: {info.get('sparsity', 'N/A'):.2%}")
            print(f"  Time: {info.get('computation_time', 0):.2f}s")
    
    def test_cuts_plus_config_validation(self, manager, sample_data):
        """测试配置验证"""
        stock_names = [f'stock_{i}' for i in range(sample_data.shape[1])]
        
        # 测试不同配置
        configs = [
            {'epochs': 10, 'sparsity_alpha': 0.1},
            {'epochs': 30, 'sparsity_alpha': 0.3},
            {'learning_rate': 0.01},
            {}  # 默认配置
        ]
        
        for config in configs:
            causal_graph, info = manager.compute_causal_graph(
                data=sample_data,
                stock_names=stock_names,
                method='cuts_plus',
                custom_config=config
            )
            assert causal_graph.shape == (5, 5)
            assert 'method' in info
    
    def test_cuts_plus_sparse_output(self, manager, sample_data):
        """测试CUTS+稀疏输出"""
        stock_names = [f'stock_{i}' for i in range(sample_data.shape[1])]
        
        # 高稀疏性阈值
        causal_graph, info = manager.compute_causal_graph(
            data=sample_data,
            stock_names=stock_names,
            method='cuts_plus',
            custom_config={'sparsity_alpha': 0.5}  # 高阈值
        )
        
        # 应该产生稀疏图
        assert info['sparsity'] > 0.7
        assert info['n_edges'] < 10
    
    def test_cuts_plus_large_dataset(self, manager):
        """测试大规模数据集"""
        # 生成更大的数据集
        T, N = 200, 15
        np.random.seed(42)
        
        data = np.zeros((T, N))
        data[:, 0] = np.random.randn(T)
        
        # 添加一些因果关系
        for t in range(1, T):
            for i in range(1, N):
                # 从前面的变量获取影响
                if i > 0:
                    data[t, i] = 0.3 * data[t-1, i-1] + 0.5 * np.random.randn()
        
        stock_names = [f'stock_{i}' for i in range(N)]
        
        causal_graph, info = manager.compute_causal_graph(
            data=data,
            stock_names=stock_names,
            method='cuts_plus',
            custom_config={'epochs': 15, 'sparsity_alpha': 0.25}
        )
        
        assert causal_graph.shape == (N, N)
        print(f"\nLarge dataset: {N} stocks, {info['n_edges']} edges")

def run_tests():
    """运行所有测试"""
    pytest.main([__file__, '-v', '-s'])

if __name__ == '__main__':
    run_tests()
