"""
实时预测模块
整合实时数据获取和预测模型，提供实时股票预测功能
"""

import logging
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import torch

from api.realtime_data import get_realtime_manager
from api.predictor_enhanced import EnhancedStockPredictor

logger = logging.getLogger(__name__)


class RealtimePredictor:
    """实时预测器 - 整合实时数据和预测模型"""
    
    def __init__(self, config_path='config.yml'):
        """
        初始化实时预测器
        
        Args:
            config_path: 配置文件路径
        """
        self.config_path = config_path
        
        # 初始化组件
        self.data_manager = get_realtime_manager()
        self.predictor = EnhancedStockPredictor(config_path)
        
        logger.info("Realtime predictor initialized")
    
    def predict_realtime(self, symbol: str, use_causal: bool = True) -> Dict[str, Any]:
        """
        实时预测单只股票
        
        Args:
            symbol: 股票代码
            use_causal: 是否使用因果图增强
        
        Returns:
            预测结果字典
        """
        try:
            # 1. 获取实时数据
            logger.info(f"Fetching realtime data for {symbol}")
            current_quote = self.data_manager.get_realtime_quote(symbol, use_cache=True)
            
            if 'error' in current_quote:
                raise ValueError(f"Failed to fetch data: {current_quote['error']}")
            
            # 2. 获取历史数据用于预测
            end_date = datetime.now()
            start_date = end_date - timedelta(days=30)  # 最近30天
            
            df = self.data_manager.get_historical_data(
                symbol,
                start_date.strftime('%Y-%m-%d'),
                end_date.strftime('%Y-%m-%d')
            )
            
            # 3. 数据预处理
            features = self._prepare_features(df, current_quote)
            
            # 4. 执行预测
            prediction = self._predict(symbol, features, use_causal)
            
            # 5. 整合结果
            result = {
                'symbol': symbol,
                'timestamp': datetime.now().isoformat(),
                'current_price': current_quote['price'],
                'prediction': prediction,
                'market_data': {
                    'open': current_quote.get('open'),
                    'high': current_quote.get('high'),
                    'low': current_quote.get('low'),
                    'volume': current_quote.get('volume'),
                    'previous_close': current_quote.get('previous_close'),
                    'change_percent': current_quote.get('change_percent')
                },
                'use_causal': use_causal
            }
            
            logger.info(f"Realtime prediction completed for {symbol}: {prediction['direction']}")
            return result
            
        except Exception as e:
            logger.error(f"Error in realtime prediction for {symbol}: {e}", exc_info=True)
            raise
    
    def predict_realtime_batch(self, symbols: List[str], use_causal: bool = True) -> Dict[str, Dict]:
        """
        批量实时预测
        
        Args:
            symbols: 股票代码列表
            use_causal: 是否使用因果图增强
        
        Returns:
            股票代码到预测结果的字典
        """
        results = {}
        
        for symbol in symbols:
            try:
                results[symbol] = self.predict_realtime(symbol, use_causal)
            except Exception as e:
                logger.warning(f"Failed to predict {symbol}: {e}")
                results[symbol] = {
                    'symbol': symbol,
                    'error': str(e),
                    'timestamp': datetime.now().isoformat()
                }
        
        return results
    
    def predict_with_horizon(self, symbol: str, horizon_days: int = 5, 
                            use_causal: bool = True) -> Dict[str, Any]:
        """
        预测未来多天的走势
        
        Args:
            symbol: 股票代码
            horizon_days: 预测天数
            use_causal: 是否使用因果图
        
        Returns:
            包含多天预测的结果
        """
        try:
            # 获取基础预测
            base_prediction = self.predict_realtime(symbol, use_causal)
            
            # 生成未来多天的预测
            predictions = []
            current_date = datetime.now()
            
            for day in range(horizon_days):
                pred_date = current_date + timedelta(days=day+1)
                
                # 这里可以扩展为更复杂的多步预测
                # 目前使用简化版本
                day_prediction = {
                    'date': pred_date.strftime('%Y-%m-%d'),
                    'day_offset': day + 1,
                    'predicted_direction': base_prediction['prediction']['direction'],
                    'confidence': base_prediction['prediction']['confidence'] * (0.95 ** day),  # 置信度递减
                    'probabilities': base_prediction['prediction']['probabilities']
                }
                
                predictions.append(day_prediction)
            
            # 计算置信度分析
            confidences = [p['confidence'] for p in predictions]
            confidence_analysis = {
                'mean': np.mean(confidences),
                'std': np.std(confidences),
                'max': np.max(confidences),
                'min': np.min(confidences)
            }
            
            # 计算统计信息
            up_count = sum(1 for p in predictions if p['predicted_direction'] == 'UP')
            down_count = len(predictions) - up_count
            avg_confidence = np.mean(confidences)
            
            statistics = {
                'average_confidence': avg_confidence * 100,  # 转为百分比
                'consistency_score': max(up_count, down_count) / len(predictions),
                'recommendation': 'BUY' if up_count > down_count else 'SELL' if down_count > up_count else 'HOLD',
                'up_days': up_count,
                'down_days': down_count
            }
            
            return {
                'symbol': symbol,
                'timestamp': datetime.now().isoformat(),
                'current_price': base_prediction['current_price'],
                'horizon_days': horizon_days,
                'predictions': predictions,
                'confidence_analysis': confidence_analysis,
                'statistics': statistics,
                'market_data': base_prediction['market_data']
            }
            
        except Exception as e:
            logger.error(f"Error in horizon prediction for {symbol}: {e}", exc_info=True)
            raise
    
    def _prepare_features(self, df: pd.DataFrame, current_quote: Dict) -> np.ndarray:
        """
        准备预测特征
        
        Args:
            df: 历史数据DataFrame
            current_quote: 当前实时报价
        
        Returns:
            特征数组
        """
        try:
            # 提取价格数据
            if 'Close' in df.columns:
                prices = df['Close'].values
            elif 'close' in df.columns:
                prices = df['close'].values
            else:
                raise ValueError("No close price column found")
            
            # 计算收益率
            returns = np.diff(prices) / prices[:-1]
            
            # 计算技术指标
            features = []
            
            # 1. 最近收益率
            if len(returns) > 0:
                features.append(returns[-1])  # 最近1天
            if len(returns) > 4:
                features.append(np.mean(returns[-5:]))  # 最近5天平均
            if len(returns) > 9:
                features.append(np.mean(returns[-10:]))  # 最近10天平均
            
            # 2. 波动率
            if len(returns) > 9:
                features.append(np.std(returns[-10:]))
            
            # 3. 价格趋势
            if len(prices) > 4:
                trend = (prices[-1] - prices[-5]) / prices[-5]
                features.append(trend)
            
            # 4. 成交量变化
            if 'Volume' in df.columns and len(df) > 1:
                volume_change = (df['Volume'].iloc[-1] - df['Volume'].iloc[-2]) / df['Volume'].iloc[-2]
                features.append(volume_change)
            elif 'volume' in df.columns and len(df) > 1:
                volume_change = (df['volume'].iloc[-1] - df['volume'].iloc[-2]) / df['volume'].iloc[-2]
                features.append(volume_change)
            
            # 5. 当前涨跌幅
            if current_quote.get('change_percent'):
                features.append(current_quote['change_percent'] / 100)
            
            # 转换为numpy数组
            features_array = np.array(features, dtype=np.float32)
            
            return features_array
            
        except Exception as e:
            logger.error(f"Error preparing features: {e}", exc_info=True)
            # 返回默认特征
            return np.zeros(7, dtype=np.float32)
    
    def _predict(self, symbol: str, features: np.ndarray, use_causal: bool) -> Dict[str, Any]:
        """
        执行预测
        
        Args:
            symbol: 股票代码
            features: 特征数组
            use_causal: 是否使用因果图
        
        Returns:
            预测结果
        """
        try:
            # 如果模型已加载且DataPipe可用，尝试使用真实模型
            if (self.predictor.model_loaded and 
                self.predictor.model is not None and 
                self.predictor.pipe is not None):
                try:
                    # 调用predictor_enhanced的真实模型预测
                    result = self.predictor.predict_single(
                        stock_symbol=symbol,
                        start_date=None,  # 使用默认日期范围
                        end_date=None,
                        use_causal=use_causal
                    )
                    
                    # 提取第一个预测结果
                    if result and 'predictions' in result and len(result['predictions']) > 0:
                        pred = result['predictions'][0]
                        return {
                            'direction': pred['predicted_direction'],
                            'confidence': pred['confidence'],
                            'probabilities': pred['probabilities'],
                            'method': pred.get('method', 'deep_learning'),
                            'features_used': len(features)
                        }
                except Exception as e:
                    logger.warning(f"Model prediction failed for {symbol}, using feature-based: {e}")
            
            # 回退到基于特征的预测
            if len(features) > 0:
                # 使用收益率作为主要判断依据
                recent_return = features[0] if len(features) > 0 else 0
                avg_return = features[1] if len(features) > 1 else 0
                
                # 预测方向
                prediction_score = recent_return * 0.6 + avg_return * 0.4
                
                if prediction_score > 0:
                    direction = 'UP'
                    up_prob = min(0.5 + prediction_score * 10, 0.95)
                    down_prob = 1 - up_prob
                else:
                    direction = 'DOWN'
                    down_prob = min(0.5 - prediction_score * 10, 0.95)
                    up_prob = 1 - down_prob
                
                confidence = max(up_prob, down_prob)
            else:
                # 无特征时的默认预测
                direction = 'UP'
                up_prob = 0.52
                down_prob = 0.48
                confidence = 0.52
            
            return {
                'direction': direction,
                'confidence': float(confidence),
                'probabilities': {
                    'UP': float(up_prob),
                    'DOWN': float(down_prob)
                },
                'method': 'feature_based',
                'features_used': len(features)
            }
            
        except Exception as e:
            logger.error(f"Error in prediction: {e}", exc_info=True)
            # 返回默认预测
            return {
                'direction': 'UP',
                'confidence': 0.5,
                'probabilities': {
                    'UP': 0.5,
                    'DOWN': 0.5
                },
                'method': 'fallback',
                'error': str(e)
            }


# 全局实例
_realtime_predictor = None


def get_realtime_predictor(config_path: Optional[str] = None) -> RealtimePredictor:
    """获取实时预测器实例（单例）"""
    global _realtime_predictor
    
    if _realtime_predictor is None:
        if config_path is None:
            config_path = 'config.yml'
        _realtime_predictor = RealtimePredictor(config_path)
    
    return _realtime_predictor
