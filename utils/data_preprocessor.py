"""
数据预处理工具
提供数据归一化、时间窗口切分、缺失值处理等功能
"""

import numpy as np
import pandas as pd
import logging
from typing import Dict, List, Tuple, Optional, Union
from sklearn.preprocessing import StandardScaler, MinMaxScaler
import warnings
warnings.filterwarnings('ignore')

logger = logging.getLogger(__name__)


class DataPreprocessor:
    """
    数据预处理器
    
    功能：
    - 归一化/标准化
    - 时间窗口切分
    - 缺失值处理
    - 异常值检测与处理
    - 特征工程
    """
    
    def __init__(
        self,
        normalization: str = 'standard',  # 'standard', 'minmax', 'none'
        fill_method: str = 'forward',      # 'forward', 'backward', 'mean', 'zero'
        window_size: int = 5,
        handle_outliers: bool = True,
        outlier_std: float = 3.0
    ):
        """
        初始化预处理器
        
        Args:
            normalization: 归一化方法
            fill_method: 缺失值填充方法
            window_size: 时间窗口大小
            handle_outliers: 是否处理异常值
            outlier_std: 异常值标准差阈值
        """
        self.normalization = normalization
        self.fill_method = fill_method
        self.window_size = window_size
        self.handle_outliers = handle_outliers
        self.outlier_std = outlier_std
        
        # 保存归一化参数（用于反归一化）
        self.scalers: Dict[str, Union[StandardScaler, MinMaxScaler]] = {}
        self.fitted = False
    
    def fit(self, data: np.ndarray):
        """
        拟合数据（学习归一化参数）
        
        Args:
            data: 形状 (T, n_features) 的数据
        """
        if self.normalization == 'standard':
            for i in range(data.shape[1]):
                scaler = StandardScaler()
                scaler.fit(data[:, i].reshape(-1, 1))
                self.scalers[f'feat_{i}'] = scaler
        
        elif self.normalization == 'minmax':
            for i in range(data.shape[1]):
                scaler = MinMaxScaler()
                scaler.fit(data[:, i].reshape(-1, 1))
                self.scalers[f'feat_{i}'] = scaler
        
        self.fitted = True
        logger.info(f"Data preprocessor fitted with {len(self.scalers)} features")
    
    def transform(self, data: np.ndarray) -> np.ndarray:
        """
        转换数据（应用归一化）
        
        Args:
            data: 形状 (T, n_features) 的数据
        
        Returns:
            归一化后的数据
        """
        if self.normalization == 'none':
            return data
        
        if not self.fitted:
            raise ValueError("Preprocessor not fitted. Call fit() first.")
        
        transformed = data.copy()
        for i in range(data.shape[1]):
            scaler = self.scalers[f'feat_{i}']
            transformed[:, i] = scaler.transform(data[:, i].reshape(-1, 1)).flatten()
        
        return transformed
    
    def fit_transform(self, data: np.ndarray) -> np.ndarray:
        """拟合并转换数据"""
        self.fit(data)
        return self.transform(data)
    
    def inverse_transform(self, data: np.ndarray) -> np.ndarray:
        """
        反归一化
        
        Args:
            data: 归一化后的数据
        
        Returns:
            原始尺度的数据
        """
        if self.normalization == 'none':
            return data
        
        if not self.fitted:
            raise ValueError("Preprocessor not fitted")
        
        inversed = data.copy()
        for i in range(data.shape[1]):
            scaler = self.scalers[f'feat_{i}']
            inversed[:, i] = scaler.inverse_transform(data[:, i].reshape(-1, 1)).flatten()
        
        return inversed
    
    def handle_missing_values(self, data: np.ndarray) -> np.ndarray:
        """
        处理缺失值
        
        Args:
            data: 可能包含NaN的数据
        
        Returns:
            处理后的数据
        """
        if not np.isnan(data).any():
            return data
        
        data = data.copy()
        
        if self.fill_method == 'forward':
            # 前向填充
            for col in range(data.shape[1]):
                mask = np.isnan(data[:, col])
                if mask.any():
                    # 用前一个非NaN值填充
                    data[:, col] = pd.Series(data[:, col]).fillna(method='ffill').values
        
        elif self.fill_method == 'backward':
            # 后向填充
            for col in range(data.shape[1]):
                mask = np.isnan(data[:, col])
                if mask.any():
                    data[:, col] = pd.Series(data[:, col]).fillna(method='bfill').values
        
        elif self.fill_method == 'mean':
            # 均值填充
            for col in range(data.shape[1]):
                mask = np.isnan(data[:, col])
                if mask.any():
                    col_mean = np.nanmean(data[:, col])
                    data[mask, col] = col_mean
        
        elif self.fill_method == 'zero':
            # 零填充
            data[np.isnan(data)] = 0.0
        
        # 如果仍有NaN（例如整列都是NaN），用0填充
        if np.isnan(data).any():
            data[np.isnan(data)] = 0.0
            logger.warning("Some NaN values remained after filling, replaced with 0")
        
        return data
    
    def detect_outliers(self, data: np.ndarray) -> np.ndarray:
        """
        检测异常值
        
        Args:
            data: 形状 (T, n_features) 的数据
        
        Returns:
            布尔数组，True表示异常值
        """
        outliers = np.zeros_like(data, dtype=bool)
        
        for col in range(data.shape[1]):
            mean = np.mean(data[:, col])
            std = np.std(data[:, col])
            
            if std > 0:
                z_scores = np.abs((data[:, col] - mean) / std)
                outliers[:, col] = z_scores > self.outlier_std
        
        return outliers
    
    def remove_outliers(self, data: np.ndarray) -> np.ndarray:
        """
        处理异常值（用边界值替换）
        
        Args:
            data: 原始数据
        
        Returns:
            处理后的数据
        """
        if not self.handle_outliers:
            return data
        
        data = data.copy()
        outliers = self.detect_outliers(data)
        
        for col in range(data.shape[1]):
            if outliers[:, col].any():
                mean = np.mean(data[:, col])
                std = np.std(data[:, col])
                
                # 用 mean ± 3*std 作为边界
                upper_bound = mean + self.outlier_std * std
                lower_bound = mean - self.outlier_std * std
                
                data[outliers[:, col], col] = np.clip(
                    data[outliers[:, col], col],
                    lower_bound,
                    upper_bound
                )
        
        n_outliers = outliers.sum()
        if n_outliers > 0:
            logger.info(f"Handled {n_outliers} outliers")
        
        return data
    
    def create_windows(
        self,
        data: np.ndarray,
        window_size: Optional[int] = None,
        stride: int = 1,
        return_indices: bool = False
    ) -> Union[np.ndarray, Tuple[np.ndarray, np.ndarray]]:
        """
        创建滑动时间窗口
        
        Args:
            data: 形状 (T, n_features) 的数据
            window_size: 窗口大小（None使用默认值）
            stride: 滑动步长
            return_indices: 是否返回窗口的起始索引
        
        Returns:
            windows: 形状 (n_windows, window_size, n_features)
            [indices]: 窗口起始索引（可选）
        """
        if window_size is None:
            window_size = self.window_size
        
        T, n_features = data.shape
        n_windows = (T - window_size) // stride + 1
        
        windows = np.zeros((n_windows, window_size, n_features))
        indices = np.zeros(n_windows, dtype=int)
        
        for i in range(n_windows):
            start_idx = i * stride
            end_idx = start_idx + window_size
            windows[i] = data[start_idx:end_idx]
            indices[i] = start_idx
        
        if return_indices:
            return windows, indices
        return windows
    
    def create_sequences(
        self,
        data: np.ndarray,
        seq_length: int,
        pred_horizon: int = 1,
        include_target: bool = True
    ) -> Tuple[np.ndarray, Optional[np.ndarray]]:
        """
        创建序列数据用于时间序列预测
        
        Args:
            data: 形状 (T, n_features) 的数据
            seq_length: 输入序列长度
            pred_horizon: 预测视野（预测未来多少步）
            include_target: 是否返回目标值
        
        Returns:
            X: 输入序列 (n_samples, seq_length, n_features)
            y: 目标值 (n_samples, pred_horizon, n_features) 或 None
        """
        T, n_features = data.shape
        n_samples = T - seq_length - pred_horizon + 1
        
        if n_samples <= 0:
            raise ValueError(f"Data too short for seq_length={seq_length} and pred_horizon={pred_horizon}")
        
        X = np.zeros((n_samples, seq_length, n_features))
        y = np.zeros((n_samples, pred_horizon, n_features)) if include_target else None
        
        for i in range(n_samples):
            X[i] = data[i:i+seq_length]
            if include_target:
                y[i] = data[i+seq_length:i+seq_length+pred_horizon]
        
        return X, y
    
    def compute_returns(
        self,
        prices: np.ndarray,
        method: str = 'log'  # 'log' or 'simple'
    ) -> np.ndarray:
        """
        计算收益率
        
        Args:
            prices: 价格数据 (T, n_stocks)
            method: 'log'对数收益率 或 'simple'简单收益率
        
        Returns:
            收益率数据 (T-1, n_stocks)
        """
        if method == 'log':
            returns = np.log(prices[1:] / prices[:-1])
        elif method == 'simple':
            returns = (prices[1:] - prices[:-1]) / prices[:-1]
        else:
            raise ValueError(f"Unknown method: {method}")
        
        # 处理inf和nan
        returns = np.nan_to_num(returns, nan=0.0, posinf=0.0, neginf=0.0)
        
        return returns
    
    def add_technical_indicators(
        self,
        data: np.ndarray,
        window_sizes: List[int] = [5, 10, 20]
    ) -> np.ndarray:
        """
        添加技术指标特征
        
        Args:
            data: 价格数据 (T, n_stocks)
            window_sizes: 移动平均窗口大小列表
        
        Returns:
            扩展特征 (T, n_stocks * (1 + len(window_sizes)))
        """
        T, n_stocks = data.shape
        features = [data]  # 原始价格
        
        for window in window_sizes:
            # 移动平均
            ma = pd.DataFrame(data).rolling(window=window, min_periods=1).mean().values
            features.append(ma)
        
        return np.concatenate(features, axis=1)
    
    def preprocess(
        self,
        data: np.ndarray,
        fit: bool = False
    ) -> np.ndarray:
        """
        完整的预处理流程
        
        Args:
            data: 原始数据
            fit: 是否拟合参数
        
        Returns:
            预处理后的数据
        """
        # 1. 处理缺失值
        data = self.handle_missing_values(data)
        
        # 2. 处理异常值
        data = self.remove_outliers(data)
        
        # 3. 归一化
        if fit:
            data = self.fit_transform(data)
        else:
            data = self.transform(data)
        
        return data
    
    def get_config(self) -> Dict:
        """获取配置信息"""
        return {
            'normalization': self.normalization,
            'fill_method': self.fill_method,
            'window_size': self.window_size,
            'handle_outliers': self.handle_outliers,
            'outlier_std': self.outlier_std,
            'fitted': self.fitted,
            'n_features': len(self.scalers)
        }


def preprocess_stock_data(
    data: np.ndarray,
    method: str = 'standard',
    seq_length: int = 5,
    pred_horizon: int = 1
) -> Tuple[np.ndarray, np.ndarray]:
    """
    便捷函数：预处理股票数据用于预测
    
    Args:
        data: 原始价格数据 (T, n_stocks)
        method: 归一化方法
        seq_length: 输入序列长度
        pred_horizon: 预测视野
    
    Returns:
        X: 输入序列
        y: 目标值
    """
    processor = DataPreprocessor(normalization=method)
    
    # 预处理
    processed_data = processor.preprocess(data, fit=True)
    
    # 创建序列
    X, y = processor.create_sequences(processed_data, seq_length, pred_horizon)
    
    return X, y


if __name__ == '__main__':
    # 测试代码
    print("测试DataPreprocessor...")
    
    # 生成测试数据
    np.random.seed(42)
    T, n_stocks = 100, 5
    prices = 100 * np.exp(np.cumsum(np.random.randn(T, n_stocks) * 0.02, axis=0))
    
    # 添加一些缺失值和异常值
    prices[10:15, 0] = np.nan
    prices[50, 2] = prices[50, 2] * 5  # 异常值
    
    print(f"原始数据形状: {prices.shape}")
    print(f"缺失值数量: {np.isnan(prices).sum()}")
    
    # 创建预处理器
    preprocessor = DataPreprocessor(
        normalization='standard',
        fill_method='forward',
        window_size=5,
        handle_outliers=True
    )
    
    # 预处理
    processed = preprocessor.preprocess(prices, fit=True)
    print(f"\n预处理后形状: {processed.shape}")
    print(f"缺失值数量: {np.isnan(processed).sum()}")
    print(f"数据范围: [{processed.min():.2f}, {processed.max():.2f}]")
    
    # 创建序列
    X, y = preprocessor.create_sequences(processed, seq_length=10, pred_horizon=1)
    print(f"\n序列数据:")
    print(f"X形状: {X.shape}")
    print(f"y形状: {y.shape}")
    
    # 创建窗口
    windows = preprocessor.create_windows(processed, window_size=7, stride=1)
    print(f"\n滑动窗口:")
    print(f"窗口形状: {windows.shape}")
    
    # 计算收益率
    returns = preprocessor.compute_returns(prices, method='log')
    print(f"\n收益率:")
    print(f"收益率形状: {returns.shape}")
    print(f"平均收益: {np.nanmean(returns, axis=0)}")
    
    # 配置信息
    print(f"\n配置: {preprocessor.get_config()}")
    
    print("\n✅ 所有测试通过！")
