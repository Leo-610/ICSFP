#!/usr/bin/env python3
"""
传递熵 (Transfer Entropy) 因果发现方法
基于信息论的因果推断，用于发现时间序列之间的信息流动
"""

import numpy as np
import logging
from typing import Dict, List, Tuple, Optional
from scipy import stats
from scipy.special import digamma
from sklearn.neighbors import NearestNeighbors
import warnings
warnings.filterwarnings('ignore')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class TransferEntropyAnalyzer:
    """
    传递熵分析器
    
    传递熵 (Transfer Entropy, TE) 衡量从时间序列 Y 到 X 的信息传递量：
    TE(Y→X) = I(X_t; Y_{t-l} | X_{t-k})
    
    其中：
    - X_t: 目标变量在时间 t 的值
    - X_{t-k}: 目标变量的历史（k步）
    - Y_{t-l}: 源变量的历史（l步）
    - I: 互信息
    
    如果 TE(Y→X) > 0 且显著，则认为 Y Granger-cause X
    """
    
    def __init__(
        self,
        k_history: int = 3,
        k_future: int = 1,
        l_delay: int = 1,
        method: str = 'kraskov',
        n_bins: int = 10,
        n_neighbors: int = 5,
        significance_level: float = 0.05,
        n_surrogates: int = 100
    ):
        """
        初始化传递熵分析器
        
        Args:
            k_history: 目标变量的历史长度
            k_future: 预测未来的步数
            l_delay: 源变量的延迟/历史长度
            method: 估计方法 ('kraskov' 或 'binning')
            n_bins: 分箱法的箱数
            n_neighbors: Kraskov法的近邻数
            significance_level: 显著性水平
            n_surrogates: 置换检验的次数
        """
        self.k_history = k_history
        self.k_future = k_future
        self.l_delay = l_delay
        self.method = method
        self.n_bins = n_bins
        self.n_neighbors = n_neighbors
        self.significance_level = significance_level
        self.n_surrogates = n_surrogates
        
        logger.info(f"TransferEntropyAnalyzer initialized: k={k_history}, l={l_delay}, method={method}")
    
    def _prepare_embedding(
        self,
        x: np.ndarray,
        y: np.ndarray
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        """
        准备嵌入向量用于传递熵计算
        
        Args:
            x: 目标时间序列
            y: 源时间序列
            
        Returns:
            x_future: X_{t+k_future}
            x_history: X_{t-k_history:t}
            y_history: Y_{t-l_delay:t}
            x_history_only: X_{t-k_history:t} (用于条件熵)
        """
        n = len(x)
        max_lag = max(self.k_history, self.l_delay)
        
        # 确保有足够的数据
        if n < max_lag + self.k_future + 1:
            raise ValueError(f"Time series too short: {n} < {max_lag + self.k_future + 1}")
        
        # 构建嵌入
        valid_indices = range(max_lag, n - self.k_future)
        n_samples = len(valid_indices)
        
        x_future = np.zeros((n_samples, self.k_future))
        x_history = np.zeros((n_samples, self.k_history))
        y_history = np.zeros((n_samples, self.l_delay))
        
        for i, t in enumerate(valid_indices):
            x_future[i] = x[t:t + self.k_future]
            x_history[i] = x[t - self.k_history:t]
            y_history[i] = y[t - self.l_delay:t]
        
        return x_future, x_history, y_history, x_history
    
    def _estimate_mi_kraskov(
        self,
        x: np.ndarray,
        y: np.ndarray,
        z: Optional[np.ndarray] = None
    ) -> float:
        """
        使用Kraskov方法估计互信息 I(X;Y|Z)
        
        Args:
            x: 变量X
            y: 变量Y
            z: 条件变量Z (可选)
            
        Returns:
            mutual_information: 互信息值
        """
        n = len(x)
        
        # 确保是2D数组
        if x.ndim == 1:
            x = x.reshape(-1, 1)
        if y.ndim == 1:
            y = y.reshape(-1, 1)
        
        if z is not None:
            if z.ndim == 1:
                z = z.reshape(-1, 1)
            # 条件互信息: I(X;Y|Z) = H(X,Z) + H(Y,Z) - H(X,Y,Z) - H(Z)
            xz = np.hstack([x, z])
            yz = np.hstack([y, z])
            xyz = np.hstack([x, y, z])
            
            h_xz = self._entropy_knn(xz)
            h_yz = self._entropy_knn(yz)
            h_xyz = self._entropy_knn(xyz)
            h_z = self._entropy_knn(z)
            
            mi = h_xz + h_yz - h_xyz - h_z
        else:
            # 无条件互信息: I(X;Y) = H(X) + H(Y) - H(X,Y)
            xy = np.hstack([x, y])
            
            h_x = self._entropy_knn(x)
            h_y = self._entropy_knn(y)
            h_xy = self._entropy_knn(xy)
            
            mi = h_x + h_y - h_xy
        
        return max(0, mi)  # 互信息非负
    
    def _entropy_knn(self, x: np.ndarray) -> float:
        """
        使用k近邻方法估计熵
        
        Args:
            x: 数据矩阵 (n_samples, n_features)
            
        Returns:
            entropy: 熵值
        """
        n, d = x.shape
        
        # 使用k近邻
        nbrs = NearestNeighbors(n_neighbors=self.n_neighbors + 1, algorithm='kd_tree').fit(x)
        distances, _ = nbrs.kneighbors(x)
        
        # 第k个近邻的距离（排除自己）
        rho = distances[:, self.n_neighbors]
        
        # Kozachenko-Leonenko估计器
        # H = -ψ(k) + ψ(n) + log(c_d) + (d/n) * Σlog(ρ_i)
        # 其中 c_d 是d维单位球的体积
        
        c_d = np.pi ** (d / 2) / np.exp(np.log(np.math.factorial(d // 2)) if d % 2 == 0 else 
                                       (d / 2) * np.log(np.pi) - np.log(np.math.factorial(d // 2)))
        
        entropy = -digamma(self.n_neighbors) + digamma(n) + np.log(c_d) + (d / n) * np.sum(np.log(rho + 1e-10))
        
        return entropy
    
    def _estimate_mi_binning(
        self,
        x: np.ndarray,
        y: np.ndarray,
        z: Optional[np.ndarray] = None
    ) -> float:
        """
        使用分箱法估计互信息
        
        Args:
            x: 变量X
            y: 变量Y
            z: 条件变量Z (可选)
            
        Returns:
            mutual_information: 互信息值
        """
        # 离散化
        x_binned = self._discretize(x)
        y_binned = self._discretize(y)
        
        if z is not None:
            z_binned = self._discretize(z)
            # 条件互信息
            mi = self._conditional_mi_binning(x_binned, y_binned, z_binned)
        else:
            # 无条件互信息
            mi = self._mi_binning(x_binned, y_binned)
        
        return mi
    
    def _discretize(self, x: np.ndarray) -> np.ndarray:
        """将连续变量离散化"""
        if x.ndim == 1:
            x = x.reshape(-1, 1)
        
        x_binned = np.zeros_like(x, dtype=int)
        for i in range(x.shape[1]):
            x_binned[:, i] = np.digitize(x[:, i], np.linspace(x[:, i].min(), x[:, i].max(), self.n_bins))
        
        return x_binned
    
    def _mi_binning(self, x: np.ndarray, y: np.ndarray) -> float:
        """计算离散化后的互信息"""
        # 确保是2D数组
        if x.ndim == 1:
            x = x.reshape(-1, 1)
        if y.ndim == 1:
            y = y.reshape(-1, 1)
        
        # 联合分布和边缘分布
        xy = np.hstack([x, y])
        
        # 计算概率
        # 将多列转换为单一标识符
        x_ids = np.apply_along_axis(lambda a: hash(tuple(a)), 1, x)
        y_ids = np.apply_along_axis(lambda a: hash(tuple(a)), 1, y)
        xy_ids = np.apply_along_axis(lambda a: hash(tuple(a)), 1, xy)
        
        unique_xy, counts_xy = np.unique(xy_ids, return_counts=True)
        p_xy = counts_xy / len(xy_ids)
        
        unique_x, counts_x = np.unique(x_ids, return_counts=True)
        p_x = counts_x / len(x_ids)
        
        unique_y, counts_y = np.unique(y_ids, return_counts=True)
        p_y = counts_y / len(y_ids)
        
        # 计算互信息
        mi = 0.0
        for i, xy_id in enumerate(unique_xy):
            # 找到对应的x和y
            mask = xy_ids == xy_id
            if np.sum(mask) == 0:
                continue
            
            x_id = x_ids[mask][0]
            y_id = y_ids[mask][0]
            
            p_joint = p_xy[i]
            p_x_val = p_x[unique_x == x_id][0] if np.any(unique_x == x_id) else 0
            p_y_val = p_y[unique_y == y_id][0] if np.any(unique_y == y_id) else 0
            
            if p_joint > 0 and p_x_val > 0 and p_y_val > 0:
                mi += p_joint * np.log2(p_joint / (p_x_val * p_y_val))
        
        return max(0, mi)
    
    def _conditional_mi_binning(self, x: np.ndarray, y: np.ndarray, z: np.ndarray) -> float:
        """计算条件互信息: I(X;Y|Z)"""
        # I(X;Y|Z) = H(X,Z) + H(Y,Z) - H(X,Y,Z) - H(Z)
        # 确保所有数组都是相同的行数
        if x.ndim == 1:
            x = x.reshape(-1, 1)
        if y.ndim == 1:
            y = y.reshape(-1, 1)
        if z.ndim == 1:
            z = z.reshape(-1, 1)
        
        xz = np.hstack([x, z])
        yz = np.hstack([y, z])
        xyz = np.hstack([x, y, z])
        
        h_xz = self._entropy_binning(xz)
        h_yz = self._entropy_binning(yz)
        h_xyz = self._entropy_binning(xyz)
        h_z = self._entropy_binning(z)
        
        return max(0, h_xz + h_yz - h_xyz - h_z)
    
    def _entropy_binning(self, x: np.ndarray) -> float:
        """计算离散化后的熵"""
        unique, counts = np.unique(x, axis=0, return_counts=True)
        p = counts / len(x)
        
        entropy = -np.sum(p * np.log2(p + 1e-10))
        return entropy
    
    def compute_transfer_entropy(
        self,
        x: np.ndarray,
        y: np.ndarray,
        test_significance: bool = True
    ) -> Dict:
        """
        计算从Y到X的传递熵
        
        Args:
            x: 目标时间序列
            y: 源时间序列
            test_significance: 是否进行显著性检验
            
        Returns:
            result: 包含TE值、p值等信息的字典
        """
        # 准备嵌入
        x_future, x_history, y_history, x_history_only = self._prepare_embedding(x, y)
        
        # 计算传递熵: TE(Y→X) = I(X_future; Y_history | X_history)
        if self.method == 'kraskov':
            te = self._estimate_mi_kraskov(x_future, y_history, x_history)
        else:
            te = self._estimate_mi_binning(x_future, y_history, x_history)
        
        result = {
            'transfer_entropy': float(te),
            'significant': False,
            'p_value': 1.0
        }
        
        # 显著性检验（置换检验）
        if test_significance:
            null_tes = []
            for _ in range(self.n_surrogates):
                # 随机打乱源变量
                y_shuffled = np.random.permutation(y)
                _, _, y_history_shuffled, _ = self._prepare_embedding(x, y_shuffled)
                
                if self.method == 'kraskov':
                    te_null = self._estimate_mi_kraskov(x_future, y_history_shuffled, x_history)
                else:
                    te_null = self._estimate_mi_binning(x_future, y_history_shuffled, x_history)
                
                null_tes.append(te_null)
            
            # 计算p值
            p_value = np.mean(np.array(null_tes) >= te)
            result['p_value'] = float(p_value)
            result['significant'] = p_value < self.significance_level
        
        return result
    
    def compute_causality_matrix(
        self,
        data: np.ndarray,
        stock_names: Optional[List[str]] = None,
        verbose: bool = True
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        计算所有股票对的传递熵矩阵
        
        Args:
            data: 时间序列数据 (T, n_stocks)
            stock_names: 股票名称列表
            verbose: 是否显示进度
            
        Returns:
            te_matrix: 传递熵矩阵 (n_stocks, n_stocks)
            p_matrix: p值矩阵 (n_stocks, n_stocks)
        """
        T, n_stocks = data.shape
        
        if stock_names is None:
            stock_names = [f'Stock_{i}' for i in range(n_stocks)]
        
        te_matrix = np.zeros((n_stocks, n_stocks))
        p_matrix = np.ones((n_stocks, n_stocks))
        
        if verbose:
            logger.info(f"Computing Transfer Entropy for {n_stocks} stocks...")
        
        total_pairs = n_stocks * (n_stocks - 1)
        completed = 0
        
        for i in range(n_stocks):
            for j in range(n_stocks):
                if i != j:
                    x = data[:, i]
                    y = data[:, j]
                    
                    result = self.compute_transfer_entropy(x, y, test_significance=True)
                    
                    te_matrix[i, j] = result['transfer_entropy']
                    p_matrix[i, j] = result['p_value']
                    
                    if result['significant'] and verbose:
                        logger.info(f"  {stock_names[j]} → {stock_names[i]}: TE={result['transfer_entropy']:.4f}, p={result['p_value']:.4f}")
                    
                    completed += 1
                    if verbose and completed % 10 == 0:
                        progress = 100 * completed / total_pairs
                        logger.info(f"  Progress: {progress:.1f}% ({completed}/{total_pairs})")
        
        return te_matrix, p_matrix


# 便捷函数
def compute_transfer_entropy_matrix(
    data: np.ndarray,
    stock_names: Optional[List[str]] = None,
    k_history: int = 3,
    l_delay: int = 1,
    method: str = 'kraskov',
    **kwargs
) -> Tuple[np.ndarray, np.ndarray]:
    """
    便捷函数：计算传递熵矩阵
    
    Args:
        data: 时间序列数据 (T, n_stocks)
        stock_names: 股票名称列表
        k_history: 历史长度
        l_delay: 延迟长度
        method: 估计方法
        **kwargs: 其他参数
        
    Returns:
        te_matrix: 传递熵矩阵
        p_matrix: p值矩阵
    """
    analyzer = TransferEntropyAnalyzer(
        k_history=k_history,
        l_delay=l_delay,
        method=method,
        **kwargs
    )
    
    return analyzer.compute_causality_matrix(data, stock_names)


if __name__ == '__main__':
    # 测试代码
    print("=" * 70)
    print("TRANSFER ENTROPY ANALYZER - TEST")
    print("=" * 70)
    
    # 生成测试数据
    np.random.seed(42)
    n_stocks = 5
    n_timepoints = 200
    
    # 创建有因果关系的数据
    # Stock 0 → Stock 1 (有因果)
    # Stock 2 (独立)
    data = np.zeros((n_timepoints, n_stocks))
    data[:, 0] = np.cumsum(np.random.randn(n_timepoints))  # 随机游走
    data[:, 2] = np.cumsum(np.random.randn(n_timepoints))  # 独立的随机游走
    
    # Stock 1 受 Stock 0 影响
    for t in range(3, n_timepoints):
        data[t, 1] = 0.7 * data[t-1, 1] + 0.3 * data[t-2, 0] + np.random.randn() * 0.1
    
    # Stock 3 受 Stock 1 影响
    for t in range(3, n_timepoints):
        data[t, 3] = 0.6 * data[t-1, 3] + 0.4 * data[t-1, 1] + np.random.randn() * 0.1
    
    # Stock 4 独立
    data[:, 4] = np.cumsum(np.random.randn(n_timepoints))
    
    stock_names = [f'Stock_{i}' for i in range(n_stocks)]
    
    print(f"\nTest data: {n_timepoints} timepoints, {n_stocks} stocks")
    print("Expected causal links: Stock_0 → Stock_1 → Stock_3")
    
    # 测试1: Kraskov方法
    print("\n" + "=" * 70)
    print("TEST 1: Kraskov Method")
    print("=" * 70)
    analyzer_kraskov = TransferEntropyAnalyzer(
        k_history=2,
        l_delay=2,
        method='kraskov',
        n_neighbors=3,
        n_surrogates=50
    )
    
    te_matrix, p_matrix = analyzer_kraskov.compute_causality_matrix(data, stock_names, verbose=True)
    
    print("\nTransfer Entropy Matrix (Kraskov):")
    print(te_matrix)
    print("\nSignificant causal links (p < 0.05):")
    for i in range(n_stocks):
        for j in range(n_stocks):
            if p_matrix[i, j] < 0.05:
                print(f"  {stock_names[j]} → {stock_names[i]}: TE={te_matrix[i, j]:.4f}, p={p_matrix[i, j]:.4f}")
    
    # 测试2: Binning方法
    print("\n" + "=" * 70)
    print("TEST 2: Binning Method")
    print("=" * 70)
    analyzer_binning = TransferEntropyAnalyzer(
        k_history=2,
        l_delay=2,
        method='binning',
        n_bins=5,
        n_surrogates=50
    )
    
    te_matrix_bin, p_matrix_bin = analyzer_binning.compute_causality_matrix(data, stock_names, verbose=False)
    
    print("\nTransfer Entropy Matrix (Binning):")
    print(te_matrix_bin)
    print("\nSignificant causal links (p < 0.05):")
    for i in range(n_stocks):
        for j in range(n_stocks):
            if p_matrix_bin[i, j] < 0.05:
                print(f"  {stock_names[j]} → {stock_names[i]}: TE={te_matrix_bin[i, j]:.4f}, p={p_matrix_bin[i, j]:.4f}")
    
    print("\n" + "=" * 70)
    print("ALL TESTS COMPLETED!")
    print("=" * 70)
