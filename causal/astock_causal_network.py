"""
A股专用因果关系网络
考虑A股市场特有的因果结构和传导机制
"""

import numpy as np
import pandas as pd
import torch
import logging
from typing import Dict, List, Tuple, Optional
from statsmodels.tsa.stattools import grangercausalitytests
from sklearn.preprocessing import StandardScaler
import warnings
warnings.filterwarnings('ignore')

logger = logging.getLogger(__name__)


class AStockCausalNetwork:
    """A股因果关系网络"""
    
    # A股特有的因果层级结构
    CAUSAL_LAYERS = {
        'macro': {  # 宏观层：政策、市场指标
            'factors': [
                'shanghai_index',  # 上证指数
                'shenzhen_index',  # 深证成指
                'cyb_index',  # 创业板指
                'monetary_policy',  # 货币政策
                'fiscal_policy',  # 财政政策
                'northbound_flow',  # 北向资金
                'margin_balance',  # 融资融券余额
            ]
        },
        'industry': {  # 行业层：申万一级行业
            'factors': [
                'finance',  # 金融
                'real_estate',  # 房地产
                'healthcare',  # 医药生物
                'technology',  # 电子/计算机
                'consumer',  # 食品饮料/家电
                'manufacturing',  # 高端制造
                'materials',  # 基础材料
                'utilities',  # 公用事业
                'energy',  # 能源/化工
            ]
        },
        'concept': {  # 概念层：热点概念
            'factors': [
                'chipset',  # 芯片半导体
                'new_energy',  # 新能源
                'ai',  # 人工智能
                'metaverse',  # 元宇宙
                'military',  # 军工
                'liquor',  # 白酒
            ]
        },
        'individual': {  # 个股层
            'factors': []  # 动态添加
        }
    }
    
    def __init__(
        self,
        max_lag: int = 5,
        significance: float = 0.05,
        device: str = 'cuda',
        use_industry: bool = True,
        use_concept: bool = True
    ):
        """
        初始化A股因果网络
        
        Args:
            max_lag: 最大滞后阶数
            significance: 显著性水平
            device: 计算设备
            use_industry: 是否使用行业因果
            use_concept: 是否使用概念板块因果
        """
        self.max_lag = max_lag
        self.significance = significance
        self.device = device if torch.cuda.is_available() else 'cpu'
        self.use_industry = use_industry
        self.use_concept = use_concept
        
        self.causal_graph = None
        self.industry_graph = None
        self.concept_graph = None
        self.macro_influence = None
        
        logger.info(f"A股因果网络初始化: device={self.device}")
    
    def build_hierarchical_graph(
        self,
        stock_data: pd.DataFrame,
        industry_data: Optional[pd.DataFrame] = None,
        concept_data: Optional[pd.DataFrame] = None,
        macro_data: Optional[pd.DataFrame] = None
    ) -> Dict[str, np.ndarray]:
        """
        构建分层因果图
        
        Args:
            stock_data: 个股收益率数据 (T, n_stocks)
            industry_data: 行业指数数据 (T, n_industries)
            concept_data: 概念指数数据 (T, n_concepts)
            macro_data: 宏观指标数据 (T, n_macros)
        
        Returns:
            包含多层因果图的字典
        """
        logger.info("开始构建A股分层因果图...")
        
        results = {}
        
        # 1. 宏观→行业因果
        if macro_data is not None and industry_data is not None and not industry_data.empty:
            logger.info("计算宏观→行业因果关系...")
            results['macro_to_industry'] = self._compute_cross_layer_causality(
                macro_data, industry_data
            )
        
        # 2. 行业→个股因果
        if industry_data is not None and not industry_data.empty and self.use_industry:
            logger.info("计算行业→个股因果关系...")
            results['industry_to_stock'] = self._compute_cross_layer_causality(
                industry_data, stock_data
            )
        
        # 3. 概念→个股因果  
        if concept_data is not None and not concept_data.empty and self.use_concept:
            logger.info("计算概念→个股因果关系...")
            results['concept_to_stock'] = self._compute_cross_layer_causality(
                concept_data, stock_data
            )
        
        # 4. 个股内部因果（股票之间）
        logger.info("计算个股间因果关系...")
        results['stock_to_stock'] = self._compute_granger_causality(stock_data)
        
        # 5. 整合为完整因果网络
        self.causal_graph = self._integrate_hierarchical_graphs(results)
        
        logger.info(f"因果图构建完成: shape={self.causal_graph.shape}")
        
        return results
    
    def _compute_granger_causality(
        self,
        data: pd.DataFrame,
        parallel: bool = True
    ) -> np.ndarray:
        """
        计算Granger因果关系（A股优化版）
        
        考虑A股特点：
        - T+1交易制度的滞后效应
        - 10%涨跌停限制
        - 集合竞价机制
        """
        n_stocks = data.shape[1]
        causality_matrix = np.zeros((n_stocks, n_stocks))
        
        # 数据预处理：考虑涨跌停
        data_clean = self._preprocess_astock_data(data)
        
        for i in range(n_stocks):
            for j in range(n_stocks):
                if i == j:
                    continue
                
                try:
                    # X[j] -> X[i] 的因果关系
                    test_data = data_clean.iloc[:, [i, j]].values
                    
                    # Granger检验
                    result = grangercausalitytests(
                        test_data,
                        maxlag=self.max_lag,
                        verbose=False
                    )
                    
                    # 提取最显著的p值
                    p_values = [result[lag][0]['ssr_ftest'][1] 
                               for lag in range(1, self.max_lag + 1)]
                    min_p_value = min(p_values)
                    
                    if min_p_value < self.significance:
                        # 使用1-p值作为因果强度
                        causality_matrix[i, j] = 1 - min_p_value
                    
                except Exception as e:
                    logger.debug(f"Granger测试失败 ({i}->{j}): {e}")
                    continue
        
        return causality_matrix
    
    def _compute_cross_layer_causality(
        self,
        source_data: pd.DataFrame,
        target_data: pd.DataFrame
    ) -> np.ndarray:
        """
        计算跨层因果关系（如行业→个股）
        """
        n_source = source_data.shape[1]
        n_target = target_data.shape[1]
        causality_matrix = np.zeros((n_target, n_source))
        
        source_clean = self._preprocess_astock_data(source_data)
        target_clean = self._preprocess_astock_data(target_data)
        
        for i in range(n_target):
            for j in range(n_source):
                try:
                    test_data = pd.concat([
                        target_clean.iloc[:, i],
                        source_clean.iloc[:, j]
                    ], axis=1).values
                    
                    result = grangercausalitytests(
                        test_data,
                        maxlag=self.max_lag,
                        verbose=False
                    )
                    
                    p_values = [result[lag][0]['ssr_ftest'][1] 
                               for lag in range(1, self.max_lag + 1)]
                    min_p_value = min(p_values)
                    
                    if min_p_value < self.significance:
                        causality_matrix[i, j] = 1 - min_p_value
                
                except Exception as e:
                    logger.debug(f"跨层因果测试失败 ({j}->{i}): {e}")
                    continue
        
        return causality_matrix
    
    def _preprocess_astock_data(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        A股数据预处理
        
        处理：
        1. 涨跌停异常值（±10%）
        2. 停牌数据
        3. 标准化
        """
        if data.empty:
            return data
        
        data_processed = data.copy()
        
        # 1. 处理涨跌停（超过±9.9%的视为异常）
        returns = data_processed.pct_change()
        extreme_mask = (returns.abs() > 0.099)
        
        # 将涨跌停替换为前一天的值（模拟无法交易）
        data_processed[extreme_mask] = np.nan
        data_processed = data_processed.fillna(method='ffill')
        
        # 2. 标准化
        scaler = StandardScaler()
        data_processed = pd.DataFrame(
            scaler.fit_transform(data_processed),
            columns=data_processed.columns,
            index=data_processed.index
        )
        
        return data_processed
    
    def _integrate_hierarchical_graphs(
        self,
        graphs: Dict[str, np.ndarray]
    ) -> np.ndarray:
        """
        整合分层因果图为完整网络
        
        整合策略：
        1. 直接因果 + 间接因果（通过行业/概念传递）
        2. 加权融合
        """
        if 'stock_to_stock' not in graphs:
            raise ValueError("缺少个股因果图")
        
        # 基础因果图
        base_graph = graphs['stock_to_stock'].copy()
        n_stocks = base_graph.shape[0]
        
        # 添加行业传递的因果
        if 'industry_to_stock' in graphs and 'stock_to_stock' in graphs:
            industry_causality = graphs['industry_to_stock']
            
            # 计算通过行业传递的因果: Stock_i -> Industry_k -> Stock_j
            for i in range(n_stocks):
                for j in range(n_stocks):
                    if i != j:
                        # 间接因果 = max(行业k的贡献)
                        indirect = 0
                        for k in range(industry_causality.shape[1]):
                            indirect = max(
                                indirect,
                                industry_causality[i, k] * industry_causality[j, k]
                            )
                        
                        # 融合直接和间接因果
                        base_graph[i, j] = max(
                            base_graph[i, j],
                            indirect * 0.5  # 间接因果权重降低
                        )
        
        # 添加概念传递的因果（类似处理）
        if 'concept_to_stock' in graphs:
            concept_causality = graphs['concept_to_stock']
            
            for i in range(n_stocks):
                for j in range(n_stocks):
                    if i != j:
                        indirect = 0
                        for k in range(concept_causality.shape[1]):
                            indirect = max(
                                indirect,
                                concept_causality[i, k] * concept_causality[j, k]
                            )
                        
                        base_graph[i, j] = max(
                            base_graph[i, j],
                            indirect * 0.3  # 概念因果权重更低
                        )
        
        return base_graph
    
    def predict_with_causal(
        self,
        target_stock_idx: int,
        historical_data: pd.DataFrame,
        causal_graph: Optional[np.ndarray] = None
    ) -> Dict:
        """
        基于因果图的预测
        
        Args:
            target_stock_idx: 目标股票索引
            historical_data: 历史数据
            causal_graph: 因果图（可选）
        
        Returns:
            预测结果字典
        """
        if causal_graph is None:
            causal_graph = self.causal_graph
        
        if causal_graph is None:
            raise ValueError("请先构建因果图")
        
        # 找出对目标股票有显著因果影响的股票
        causal_sources = np.where(causal_graph[target_stock_idx] > 0.5)[0]
        
        logger.info(f"发现{len(causal_sources)}个因果源影响目标股票{target_stock_idx}")
        
        # 基于因果源的加权预测
        target_data = historical_data.iloc[:, target_stock_idx].values
        predictions = []
        
        for source_idx in causal_sources:
            source_data = historical_data.iloc[:, source_idx].values
            strength = causal_graph[target_stock_idx, source_idx]
            
            # 简单的滞后预测
            pred = source_data[-1] * strength  # 可以改进为更复杂的模型
            predictions.append(pred)
        
        if predictions:
            final_prediction = np.mean(predictions)
        else:
            # 无因果信息时使用历史均值
            final_prediction = np.mean(target_data[-5:])
        
        return {
            'prediction': final_prediction,
            'causal_sources': causal_sources.tolist(),
            'n_sources': len(causal_sources),
            'confidence': min(len(causal_sources) / 10.0, 1.0)  # 归一化置信度
        }
    
    def visualize_network(
        self,
        stock_names: List[str],
        save_path: str = 'astock_causal_network.png',
        top_k: int = 100
    ):
        """
        可视化A股因果网络
        
        Args:
            stock_names: 股票名称列表
            save_path: 保存路径
            top_k: 只显示前k个最强的因果关系
        """
        import matplotlib.pyplot as plt
        import networkx as nx
        
        if self.causal_graph is None:
            raise ValueError("请先构建因果图")
        
        # 创建有向图
        G = nx.DiGraph()
        
        # 添加节点
        for name in stock_names:
            G.add_node(name)
        
        # 添加边（只保留最强的top_k个）
        edges = []
        for i in range(len(stock_names)):
            for j in range(len(stock_names)):
                if i != j and self.causal_graph[i, j] > 0:
                    edges.append((
                        stock_names[j],
                        stock_names[i],
                        self.causal_graph[i, j]
                    ))
        
        # 按权重排序并取top_k
        edges.sort(key=lambda x: x[2], reverse=True)
        edges = edges[:top_k]
        
        for source, target, weight in edges:
            G.add_edge(source, target, weight=weight)
        
        # 绘图
        plt.figure(figsize=(20, 20))
        pos = nx.spring_layout(G, k=2, iterations=50)
        
        # 绘制节点
        nx.draw_networkx_nodes(
            G, pos,
            node_size=500,
            node_color='lightblue',
            alpha=0.8
        )
        
        # 绘制边
        edges_list = [(u, v) for (u, v, d) in edges]
        weights = [d for (u, v, d) in edges]
        
        nx.draw_networkx_edges(
            G, pos,
            edgelist=edges_list,
            width=[w*3 for w in weights],
            alpha=0.5,
            edge_color='gray',
            arrows=True,
            arrowsize=20
        )
        
        # 绘制标签
        nx.draw_networkx_labels(
            G, pos,
            font_size=8,
            font_family='SimHei'  # 中文字体
        )
        
        plt.title(f'A股因果关系网络 (Top {top_k} 因果关系)', 
                 fontsize=16, fontproperties='SimHei')
        plt.axis('off')
        plt.tight_layout()
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        logger.info(f"因果网络图已保存到: {save_path}")
        
        return G
    
    def get_market_leaders(self, top_n: int = 10) -> List[Tuple[int, float]]:
        """
        识别市场领涨股（因果影响力最强的股票）
        
        Returns:
            (股票索引, 影响力得分) 的列表
        """
        if self.causal_graph is None:
            raise ValueError("请先构建因果图")
        
        # 计算每只股票的出度（影响其他股票的程度）
        out_degree = np.sum(self.causal_graph, axis=0)
        
        # 排序
        leaders = sorted(
            enumerate(out_degree),
            key=lambda x: x[1],
            reverse=True
        )[:top_n]
        
        return leaders
    
    def save_graph(self, save_path: str = 'astock_causal_graph.npy'):
        """保存因果图"""
        if self.causal_graph is None:
            raise ValueError("没有可保存的因果图")
        
        np.save(save_path, self.causal_graph)
        logger.info(f"因果图已保存到: {save_path}")
    
    def load_graph(self, load_path: str = 'astock_causal_graph.npy'):
        """加载因果图"""
        self.causal_graph = np.load(load_path)
        logger.info(f"因果图已从 {load_path} 加载: shape={self.causal_graph.shape}")


def demo_astock_causal():
    """演示A股因果网络使用"""
    
    # 1. 创建因果网络
    network = AStockCausalNetwork(
        max_lag=5,
        significance=0.05,
        use_industry=True,
        use_concept=True
    )
    
    # 2. 准备模拟数据（实际使用时替换为真实数据）
    n_stocks = 50
    n_days = 200
    stock_data = pd.DataFrame(
        np.random.randn(n_days, n_stocks).cumsum(axis=0),
        columns=[f'Stock_{i}' for i in range(n_stocks)]
    )
    
    # 行业数据
    n_industries = 10
    industry_data = pd.DataFrame(
        np.random.randn(n_days, n_industries).cumsum(axis=0),
        columns=[f'Industry_{i}' for i in range(n_industries)]
    )
    
    # 3. 构建因果图
    print("构建A股因果网络...")
    graphs = network.build_hierarchical_graph(
        stock_data=stock_data,
        industry_data=industry_data
    )
    
    print(f"个股因果图: {graphs['stock_to_stock'].shape}")
    print(f"非零因果关系: {np.sum(graphs['stock_to_stock'] > 0)}")
    
    # 4. 识别市场领涨股
    print("\n市场领涨股（因果影响力Top 5）:")
    leaders = network.get_market_leaders(top_n=5)
    for idx, score in leaders:
        print(f"  Stock_{idx}: 影响力 = {score:.3f}")
    
    # 5. 预测示例
    print("\n基于因果图的预测示例:")
    pred_result = network.predict_with_causal(
        target_stock_idx=0,
        historical_data=stock_data
    )
    print(f"  预测值: {pred_result['prediction']:.4f}")
    print(f"  因果源数量: {pred_result['n_sources']}")
    print(f"  置信度: {pred_result['confidence']:.2f}")
    
    # 6. 保存因果图
    network.save_graph('astock_causal_demo.npy')
    
    print("\n因果网络演示完成！")


if __name__ == '__main__':
    demo_astock_causal()
