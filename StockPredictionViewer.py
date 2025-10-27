#!/usr/bin/env python3
import os
import numpy as np
import torch
import json
from datetime import datetime
import matplotlib.pyplot as plt
import seaborn as sns

from Model import Model
from DataPipe import DataPipe
from ConfigLoader import logger, stock_symbols
import metrics


class StockPredictionViewer:
    def __init__(self, model_path=None, device='cuda'):
        """
        股票预测结果查看器 (PyTorch版本 + 因果图分析)

        Args:
            model_path: 训练好的模型路径，如果为None则使用默认路径
            device: 计算设备
        """
        self.device = device
        self.pipe = DataPipe()
        self.model_path = model_path

        # 加载因果图
        try:
            self.graph = np.load('causal_graph.npy')
            logger.info(f'Causal graph loaded with shape: {self.graph.shape}')
        except FileNotFoundError:
            logger.warning('Causal graph not found, using None')
            self.graph = None

        # 创建模型
        self.model = Model(graph=self.graph)
        self.model.to(self.device)

        # 股票代码到名称的映射
        self.stock_names = {
            'AAPL': 'Apple Inc.',
            'GOOG': 'Google',
            'MSFT': 'Microsoft',
            'AMZN': 'Amazon',
            'TSLA': 'Tesla',
            'JPM': 'JPMorgan Chase',
            'JNJ': 'Johnson & Johnson',
            'V': 'Visa',
            'PG': 'Procter & Gamble',
            'MA': 'Mastercard',
            # 可以添加更多股票名称映射
        }

        # 股票代码到ID的映射
        self.stock_to_id = {stock: idx for idx, stock in enumerate(stock_symbols)}

    def load_model(self):
        """加载训练好的模型"""
        checkpoint_path = os.path.join(self.model.tf_checkpoints_path, 'model.pth')

        if os.path.exists(checkpoint_path):
            checkpoint = torch.load(checkpoint_path, map_location=self.device)
            self.model.load_state_dict(checkpoint['model_state_dict'])
            self.model.eval()
            logger.info('Model loaded successfully from: {}'.format(checkpoint_path))
            return True
        else:
            logger.error('No trained model found at: {}'.format(checkpoint_path))
            return False

    def _to_tensor(self, batch_dict):
        """将numpy数组转换为PyTorch张量"""
        tensor_dict = {}
        for key, value in batch_dict.items():
            if isinstance(value, np.ndarray):
                tensor_dict[key] = torch.from_numpy(value).to(self.device)
            else:
                tensor_dict[key] = value
        return tensor_dict

    def predict_single_stock(self, stock_symbol, phase='test'):
        """
        预测单个股票的涨跌

        Args:
            stock_symbol: 股票代码 (如 'AAPL')
            phase: 数据阶段 ('train', 'dev', 'test')

        Returns:
            predictions: 预测结果列表
        """
        if not self.load_model():
            return None

        predictions = []

        # 获取该股票的数据批次
        batch_gen = self.pipe.batch_gen_by_stocks(phase)

        with torch.no_grad():
            for batch_dict in batch_gen:
                if batch_dict['s'] != stock_symbol:
                    continue

                batch_dict = self._to_tensor(batch_dict)

                # 前向传播
                outputs = self.model(
                    word_ph=batch_dict['word_batch'],
                    price_ph=batch_dict['price_batch'],
                    stock_ph=batch_dict['stock_batch'],
                    T_ph=batch_dict['T_batch'],
                    n_words_ph=batch_dict['n_words_batch'],
                    n_msgs_ph=batch_dict['n_msgs_batch'],
                    y_ph=batch_dict['y_batch'],
                    ss_index_ph=batch_dict['ss_index_batch'],
                    is_training=False
                )

                # 获取预测结果
                y_pred = outputs['y_T'].cpu().numpy()
                y_true = outputs['y_T_'].cpu().numpy()
                main_mv_percent = batch_dict['main_mv_percent_batch'].cpu().numpy()

                # 获取因果变量（如果存在）
                causal_Z = outputs['causal_Z']
                causal_influence = None
                if causal_Z is not None:
                    stock_id = self.stock_to_id.get(stock_symbol, 0)
                    causal_Z_np = causal_Z.cpu().numpy()
                    causal_influence = causal_Z_np[:, -1, :]  # 最后一天的因果变量

                # 处理每个样本的预测结果
                for i in range(batch_dict['batch_size']):
                    pred_class = np.argmax(y_pred[i])
                    true_class = np.argmax(y_true[i])
                    pred_prob = y_pred[i]
                    actual_movement = main_mv_percent[i]

                    prediction = {
                        'stock_symbol': stock_symbol,
                        'stock_name': self.stock_names.get(stock_symbol, stock_symbol),
                        'predicted_direction': 'UP' if pred_class == 1 else 'DOWN',
                        'actual_direction': 'UP' if true_class == 1 else 'DOWN',
                        'prediction_confidence': float(pred_prob[pred_class]),
                        'prediction_probabilities': {
                            'DOWN': float(pred_prob[0]),
                            'UP': float(pred_prob[1])
                        },
                        'actual_movement_percent': float(actual_movement),
                        'prediction_correct': pred_class == true_class,
                        'sample_index': i
                    }

                    # 添加因果变量信息
                    if causal_influence is not None:
                        prediction['causal_influence'] = causal_influence[i].tolist()
                        prediction['causal_strength'] = float(np.linalg.norm(causal_influence[i]))

                    predictions.append(prediction)

                break  # 只处理该股票的第一个批次

        return predictions

    def predict_all_stocks(self, phase='test', save_to_file=True):
        """
        预测所有股票的涨跌（包含因果分析）

        Args:
            phase: 数据阶段
            save_to_file: 是否保存结果到文件

        Returns:
            all_predictions: 所有股票的预测结果
            causal_analysis: 因果关系分析结果
        """
        if not self.load_model():
            return None, None

        all_predictions = {}
        total_correct = 0
        total_samples = 0
        causal_influences = {}  # 存储因果影响数据

        # 获取所有股票的数据
        batch_gen = self.pipe.batch_gen_by_stocks(phase)

        with torch.no_grad():
            for batch_dict in batch_gen:
                stock_symbol = batch_dict['s']
                batch_dict = self._to_tensor(batch_dict)

                try:
                    # 前向传播
                    outputs = self.model(
                        word_ph=batch_dict['word_batch'],
                        price_ph=batch_dict['price_batch'],
                        stock_ph=batch_dict['stock_batch'],
                        T_ph=batch_dict['T_batch'],
                        n_words_ph=batch_dict['n_words_batch'],
                        n_msgs_ph=batch_dict['n_msgs_batch'],
                        y_ph=batch_dict['y_batch'],
                        ss_index_ph=batch_dict['ss_index_batch'],
                        is_training=False
                    )

                    y_pred = outputs['y_T'].cpu().numpy()
                    y_true = outputs['y_T_'].cpu().numpy()
                    main_mv_percent = batch_dict['main_mv_percent_batch'].cpu().numpy()

                    # 因果变量分析
                    causal_Z = outputs['causal_Z']
                    if causal_Z is not None:
                        causal_Z_np = causal_Z.cpu().numpy()
                        # 存储该股票的因果影响
                        causal_influences[stock_symbol] = {
                            'temporal_evolution': causal_Z_np.mean(axis=0),  # 时序演化
                            'final_influence': causal_Z_np[:, -1, :].mean(axis=0),  # 最终影响
                            'influence_variance': causal_Z_np[:, -1, :].var(axis=0)  # 影响方差
                        }

                    stock_predictions = []
                    stock_correct = 0

                    for i in range(batch_dict['batch_size']):
                        pred_class = np.argmax(y_pred[i])
                        true_class = np.argmax(y_true[i])
                        pred_prob = y_pred[i]
                        actual_movement = main_mv_percent[i]

                        is_correct = pred_class == true_class
                        if is_correct:
                            stock_correct += 1
                            total_correct += 1
                        total_samples += 1

                        prediction = {
                            'predicted_direction': 'UP' if pred_class == 1 else 'DOWN',
                            'actual_direction': 'UP' if true_class == 1 else 'DOWN',
                            'prediction_confidence': float(pred_prob[pred_class]),
                            'prediction_probabilities': {
                                'DOWN': float(pred_prob[0]),
                                'UP': float(pred_prob[1])
                            },
                            'actual_movement_percent': float(actual_movement),
                            'prediction_correct': is_correct
                        }

                        # 添加因果信息
                        if causal_Z is not None:
                            causal_vec = causal_Z_np[i, -1, :]
                            prediction['causal_influence'] = causal_vec.tolist()
                            prediction['causal_strength'] = float(np.linalg.norm(causal_vec))

                        stock_predictions.append(prediction)

                    stock_accuracy = stock_correct / batch_dict['batch_size'] if batch_dict['batch_size'] > 0 else 0

                    all_predictions[stock_symbol] = {
                        'stock_name': self.stock_names.get(stock_symbol, stock_symbol),
                        'total_predictions': batch_dict['batch_size'],
                        'correct_predictions': stock_correct,
                        'accuracy': stock_accuracy,
                        'predictions': stock_predictions
                    }

                    logger.info(f'Stock {stock_symbol}: {stock_correct}/{batch_dict["batch_size"]} correct, accuracy: {stock_accuracy:.3f}')

                except Exception as e:
                    logger.error(f'Error processing stock {stock_symbol}: {e}')
                    continue

        overall_accuracy = total_correct / total_samples if total_samples > 0 else 0
        logger.info(f'Overall accuracy: {total_correct}/{total_samples} = {overall_accuracy:.3f}')

        # 因果关系分析
        causal_analysis = self._analyze_causal_relationships(causal_influences)

        # 保存结果到文件
        if save_to_file:
            self.save_predictions_with_causal(all_predictions, causal_analysis, overall_accuracy, phase)

        return all_predictions, causal_analysis

    def _analyze_causal_relationships(self, causal_influences):
        """分析因果关系"""
        if not causal_influences or self.graph is None:
            return None

        analysis = {
            'causal_graph_stats': {
                'total_connections': np.count_nonzero(self.graph),
                'sparsity': np.count_nonzero(self.graph) / self.graph.size,
                'max_influence': float(np.max(self.graph)),
                'mean_influence': float(np.mean(self.graph[self.graph > 0]))
            },
            'stock_influences': {},
            'cross_stock_correlations': {}
        }

        # 分析每只股票的因果影响
        influence_matrix = []
        stock_list = []

        for stock, influences in causal_influences.items():
            final_influence = influences['final_influence']
            influence_strength = np.linalg.norm(final_influence)
            influence_variance = np.mean(influences['influence_variance'])

            analysis['stock_influences'][stock] = {
                'influence_strength': float(influence_strength),
                'influence_variance': float(influence_variance),
                'temporal_pattern': influences['temporal_evolution'].tolist()
            }

            influence_matrix.append(final_influence)
            stock_list.append(stock)

        # 计算股票间的因果影响相关性
        if len(influence_matrix) > 1:
            influence_matrix = np.array(influence_matrix)
            correlation_matrix = np.corrcoef(influence_matrix)

            # 找出最强的因果关联
            n_stocks = len(stock_list)
            strong_correlations = []

            for i in range(n_stocks):
                for j in range(i + 1, n_stocks):
                    corr = correlation_matrix[i, j]
                    if abs(corr) > 0.5:  # 阈值可调
                        strong_correlations.append({
                            'stock1': stock_list[i],
                            'stock2': stock_list[j],
                            'correlation': float(corr),
                            'relationship_type': 'positive' if corr > 0 else 'negative'
                        })

            analysis['cross_stock_correlations'] = {
                'correlation_matrix': correlation_matrix.tolist(),
                'stock_order': stock_list,
                'strong_correlations': strong_correlations
            }

        return analysis

    def save_predictions_with_causal(self, predictions, causal_analysis, overall_accuracy, phase):
        """保存包含因果分析的预测结果"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'stock_predictions_with_causal_{phase}_{timestamp}.json'

        result = {
            'timestamp': timestamp,
            'phase': phase,
            'overall_accuracy': overall_accuracy,
            'total_stocks': len(predictions),
            'model_info': {
                'model_name': self.model.model_name,
                'causal_enabled': self.graph is not None,
                'causal_graph_shape': self.graph.shape if self.graph is not None else None
            },
            'predictions': predictions,
            'causal_analysis': causal_analysis
        }

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)

        logger.info(f'Predictions with causal analysis saved to: {filename}')

    def visualize_causal_graph(self, top_k=20, save_path='causal_graph.png'):
        """可视化因果图"""
        if self.graph is None:
            logger.warning('No causal graph available for visualization')
            return

        # 选择影响最强的top_k个连接进行可视化
        flat_indices = np.unravel_index(np.argsort(self.graph.ravel())[-top_k:], self.graph.shape)

        plt.figure(figsize=(12, 10))

        # 创建一个稀疏的图用于可视化
        vis_graph = np.zeros_like(self.graph)
        for i, j in zip(flat_indices[0], flat_indices[1]):
            vis_graph[i, j] = self.graph[i, j]

        # 选择前20个股票进行显示（避免图太拥挤）
        n_show = min(20, len(stock_symbols))
        vis_graph_small = vis_graph[:n_show, :n_show]
        stock_labels = stock_symbols[:n_show]

        # 热图可视化
        sns.heatmap(vis_graph_small,
                    xticklabels=stock_labels,
                    yticklabels=stock_labels,
                    cmap='Reds',
                    annot=True,
                    fmt='.3f',
                    cbar_kws={'label': 'Causal Influence Strength'})

        plt.title(f'Causal Graph Visualization (Top {top_k} Connections)')
        plt.xlabel('Target Stock (Influenced)')
        plt.ylabel('Source Stock (Influencer)')
        plt.xticks(rotation=45)
        plt.yticks(rotation=0)
        plt.tight_layout()
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        plt.show()

        logger.info(f'Causal graph visualization saved to: {save_path}')

    def analyze_prediction_attribution(self, stock_symbol, sample_idx=0, phase='test'):
        """分析预测的归因（文本 vs 价格 vs 因果）"""
        predictions = self.predict_single_stock(stock_symbol, phase)

        if not predictions or sample_idx >= len(predictions):
            logger.error(f'Invalid sample index {sample_idx} for stock {stock_symbol}')
            return None

        prediction = predictions[sample_idx]

        # 重新运行模型获得详细输出
        batch_gen = self.pipe.batch_gen_by_stocks(phase)

        with torch.no_grad():
            for batch_dict in batch_gen:
                if batch_dict['s'] != stock_symbol:
                    continue

                batch_dict = self._to_tensor(batch_dict)
                outputs = self.model(
                    word_ph=batch_dict['word_batch'],
                    price_ph=batch_dict['price_batch'],
                    stock_ph=batch_dict['stock_batch'],
                    T_ph=batch_dict['T_batch'],
                    n_words_ph=batch_dict['n_words_batch'],
                    n_msgs_ph=batch_dict['n_msgs_batch'],
                    y_ph=batch_dict['y_batch'],
                    ss_index_ph=batch_dict['ss_index_batch'],
                    is_training=False
                )

                # 提取各组件的贡献
                attribution = {
                    'prediction_info': prediction,
                    'text_features': None,
                    'price_features': None,
                    'causal_features': None,
                    'attention_weights': None
                }

                if outputs['corpus_embed'] is not None:
                    attribution['text_features'] = outputs['corpus_embed'][sample_idx, -1, :].cpu().numpy().tolist()

                attribution['price_features'] = outputs['price_features'][sample_idx, -1, :].cpu().numpy().tolist()

                if outputs['causal_Z'] is not None:
                    attribution['causal_features'] = outputs['causal_Z'][sample_idx, -1, :].cpu().numpy().tolist()

                if 'v_stared' in outputs:
                    attribution['attention_weights'] = outputs['v_stared'][sample_idx].cpu().numpy().tolist()

                return attribution

        return None


def main():
    """主函数 - 演示因果图预测查看器"""
    viewer = StockPredictionViewer()

    print("开始预测所有股票（包含因果分析）...")
    predictions, causal_analysis = viewer.predict_all_stocks(phase='test')

    if predictions and causal_analysis:
        # 打印摘要
        viewer.print_summary(predictions,
                             sum(p['correct_predictions'] for p in predictions.values()) /
                             sum(p['total_predictions'] for p in predictions.values()))

        # 分析因果关系
        print("\n因果关系分析:")
        print(f"因果图连接数: {causal_analysis['causal_graph_stats']['total_connections']}")
        print(f"图稀疏度: {causal_analysis['causal_graph_stats']['sparsity']:.3f}")

        # 显示因果影响最强的股票
        stock_influences = causal_analysis['stock_influences']
        sorted_influences = sorted(stock_influences.items(),
                                   key=lambda x: x[1]['influence_strength'], reverse=True)

        print("\n因果影响最强的股票:")
        for stock, influence in sorted_influences[:5]:
            print(f"{stock}: 影响强度 {influence['influence_strength']:.3f}")

        # 可视化因果图
        viewer.visualize_causal_graph()

        # 分析特定股票的预测归因
        if 'AAPL' in predictions:
            attribution = viewer.analyze_prediction_attribution('AAPL')
            if attribution:
                print(f"\nAAPL预测归因分析:")
                print(f"预测方向: {attribution['prediction_info']['predicted_direction']}")
                print(f"置信度: {attribution['prediction_info']['prediction_confidence']:.3f}")
                if attribution['causal_features']:
                    causal_strength = np.linalg.norm(attribution['causal_features'])
                    print(f"因果影响强度: {causal_strength:.3f}")

        print(f"\n详细结果已保存到JSON文件中")
    else:
        print("预测失败，请检查模型是否已训练完成")


if __name__ == '__main__':
    main()