"""
Enhanced API Routes for Phase 3 Features
集成性能优化器、CUTS+、UnifiedPipeline 等新功能
"""

from flask import Blueprint, jsonify, request, current_app
import numpy as np
import logging
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)

# 创建增强路由蓝图
enhanced_bp = Blueprint('enhanced', __name__, url_prefix='/api/v1/enhanced')

# 全局实例（延迟加载）
_performance_optimizer = None
_causal_manager = None
_unified_pipeline = None


def get_performance_optimizer():
    """获取性能优化器实例"""
    global _performance_optimizer
    if _performance_optimizer is None:
        from utils.performance_optimizer import PerformanceOptimizer
        _performance_optimizer = PerformanceOptimizer(
            device='cuda',
            cache_dir='./cache',
            max_cache_mb=1024,
            batch_size=32
        )
        logger.info("✅ Performance Optimizer initialized")
    return _performance_optimizer


def get_causal_manager():
    """获取因果发现管理器实例"""
    global _causal_manager
    if _causal_manager is None:
        import sys
        import os
        # 添加项目根目录到路径
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        if project_root not in sys.path:
            sys.path.insert(0, project_root)
        
        from causal_discovery_manager import CausalDiscoveryManager
        _causal_manager = CausalDiscoveryManager()
        logger.info("✅ Causal Discovery Manager initialized")
    return _causal_manager


def get_unified_pipeline():
    """获取统一管道实例"""
    global _unified_pipeline
    if _unified_pipeline is None:
        from unified_pipeline import UnifiedPipeline
        config_path = current_app.config.get('CONFIG_PATH', 'config.yml')
        # 使用 cikm18 作为默认数据集
        _unified_pipeline = UnifiedPipeline(
            dataset_name='cikm18',
            config_path=config_path,
            enable_cache=True
        )
        logger.info("✅ Unified Pipeline initialized")
    return _unified_pipeline


# ============================================================================
# 性能优化相关端点
# ============================================================================

@enhanced_bp.route('/performance/optimize_causal', methods=['POST'])
def optimize_causal_discovery():
    """
    GPU 加速的因果发现
    
    Request Body:
    {
        "data": [[1.0, 2.0, ...], ...],  # 时间序列数据 (n_samples, n_features)
        "method": "granger",              # 方法: 'granger', 'correlation'
        "max_lag": 5,                     # Granger 方法的最大滞后
        "use_cache": true                 # 是否使用缓存
    }
    
    Response:
    {
        "status": "success",
        "data": {
            "causal_matrix": [[0.0, 0.5, ...], ...],
            "execution_time": 0.123,
            "cache_hit": false,
            "gpu_used": true
        }
    }
    """
    try:
        data_dict = request.get_json()
        
        # 验证必需参数
        if 'data' not in data_dict:
            return jsonify({
                'status': 'error',
                'message': 'Missing required parameter: data'
            }), 400
        
        # 解析参数
        data = np.array(data_dict['data'])
        method = data_dict.get('method', 'correlation')
        max_lag = data_dict.get('max_lag', 5)
        use_cache = data_dict.get('use_cache', True)
        
        # 验证方法
        if method not in ['granger', 'correlation']:
            return jsonify({
                'status': 'error',
                'message': f'Invalid method: {method}. Must be "granger" or "correlation"'
            }), 400
        
        # 执行优化的因果发现
        import time
        start_time = time.time()
        
        optimizer = get_performance_optimizer()
        causal_matrix = optimizer.optimize_causal_discovery(
            data,
            method=method,
            max_lag=max_lag if method == 'granger' else None,
            use_cache=use_cache
        )
        
        execution_time = time.time() - start_time
        
        # 获取系统状态
        system_status = optimizer.get_system_status()
        
        return jsonify({
            'status': 'success',
            'data': {
                'causal_matrix': causal_matrix.tolist(),
                'shape': list(causal_matrix.shape),
                'execution_time': execution_time,
                'method': method,
                'gpu_memory': system_status['gpu'],
                'cache_stats': system_status['cache']
            }
        })
        
    except ValueError as e:
        return jsonify({'status': 'error', 'message': str(e)}), 400
    except Exception as e:
        logger.error(f"Optimize causal discovery error: {e}", exc_info=True)
        return jsonify({'status': 'error', 'message': 'Internal server error'}), 500


@enhanced_bp.route('/performance/status', methods=['GET'])
def get_performance_status():
    """
    获取性能优化器状态
    
    Response:
    {
        "status": "success",
        "data": {
            "gpu": {
                "available": true,
                "device_name": "NVIDIA RTX 4060",
                "memory_allocated_gb": 0.01,
                "memory_free_gb": 8.58
            },
            "cache": {
                "memory_items": 10,
                "memory_size_mb": 0.5,
                "disk_items": 15,
                "hit_rate": 0.75
            }
        }
    }
    """
    try:
        optimizer = get_performance_optimizer()
        status = optimizer.get_system_status()
        
        return jsonify({
            'status': 'success',
            'data': status
        })
        
    except Exception as e:
        logger.error(f"Get performance status error: {e}", exc_info=True)
        return jsonify({'status': 'error', 'message': 'Internal server error'}), 500


@enhanced_bp.route('/performance/cache/clear', methods=['POST'])
def clear_cache():
    """
    清空缓存
    
    Response:
    {
        "status": "success",
        "message": "Cache cleared successfully"
    }
    """
    try:
        optimizer = get_performance_optimizer()
        optimizer.cache.clear()
        
        return jsonify({
            'status': 'success',
            'message': 'Cache cleared successfully'
        })
        
    except Exception as e:
        logger.error(f"Clear cache error: {e}", exc_info=True)
        return jsonify({'status': 'error', 'message': 'Internal server error'}), 500


# ============================================================================
# CUTS+ 因果发现端点
# ============================================================================

@enhanced_bp.route('/causal/cutsplus', methods=['POST'])
def discover_with_cutsplus():
    """
    使用 CUTS+ 方法进行因果发现
    
    Request Body:
    {
        "data": [[1.0, 2.0, ...], ...],
        "threshold_type": "adaptive",  # 'fixed', 'adaptive', 'percentile'
        "threshold_value": 0.3,         # fixed 类型时使用
        "percentile": 90                # percentile 类型时使用
    }
    
    Response:
    {
        "status": "success",
        "data": {
            "causal_graph": [[0, 1, ...], ...],
            "statistics": {
                "nodes": 20,
                "edges": 45,
                "density": 0.12,
                "sparsity": 0.88
            },
            "threshold_used": 0.35
        }
    }
    """
    try:
        data_dict = request.get_json()
        
        # 验证必需参数
        if 'data' not in data_dict:
            return jsonify({
                'status': 'error',
                'message': 'Missing required parameter: data'
            }), 400
        
        # 解析参数
        data = np.array(data_dict['data'])
        threshold_type = data_dict.get('threshold_type', 'adaptive')
        threshold_value = data_dict.get('threshold_value', 0.3)
        percentile = data_dict.get('percentile', 90)
        
        # 验证阈值类型
        valid_types = ['fixed', 'adaptive', 'percentile']
        if threshold_type not in valid_types:
            return jsonify({
                'status': 'error',
                'message': f'Invalid threshold_type. Must be one of: {valid_types}'
            }), 400
        
        # 执行 CUTS+ 因果发现
        manager = get_causal_manager()
        causal_graph = manager.discover_with_cutsplus(
            data,
            threshold_type=threshold_type,
            threshold_value=threshold_value,
            percentile=percentile
        )
        
        # 获取图统计信息
        stats = manager.get_graph_statistics(causal_graph)
        
        return jsonify({
            'status': 'success',
            'data': {
                'causal_graph': causal_graph.tolist(),
                'shape': list(causal_graph.shape),
                'statistics': stats,
                'method': 'CUTS+',
                'threshold_type': threshold_type
            }
        })
        
    except ValueError as e:
        return jsonify({'status': 'error', 'message': str(e)}), 400
    except Exception as e:
        logger.error(f"CUTS+ discovery error: {e}", exc_info=True)
        return jsonify({'status': 'error', 'message': 'Internal server error'}), 500


@enhanced_bp.route('/causal/methods', methods=['GET'])
def get_causal_methods():
    """
    获取支持的因果发现方法列表
    
    Response:
    {
        "status": "success",
        "data": {
            "methods": [
                {
                    "name": "granger",
                    "description": "Granger Causality Test",
                    "parameters": ["max_lag"],
                    "gpu_accelerated": true
                },
                ...
            ]
        }
    }
    """
    try:
        methods = [
            {
                'name': 'granger',
                'description': 'Granger Causality Test',
                'parameters': ['max_lag'],
                'gpu_accelerated': True,
                'complexity': 'O(n²m)',
                'best_for': 'Time series with temporal dependencies'
            },
            {
                'name': 'cutsplus',
                'description': 'CUTS+ (Correlation-based approximation)',
                'parameters': ['threshold_type', 'threshold_value', 'percentile'],
                'gpu_accelerated': False,
                'complexity': 'O(n²)',
                'best_for': 'Fast discovery with correlation-based relationships'
            },
            {
                'name': 'correlation',
                'description': 'Correlation Matrix',
                'parameters': [],
                'gpu_accelerated': True,
                'complexity': 'O(n²)',
                'best_for': 'Quick correlation analysis'
            }
        ]
        
        return jsonify({
            'status': 'success',
            'data': {
                'methods': methods,
                'total_methods': len(methods)
            }
        })
        
    except Exception as e:
        logger.error(f"Get causal methods error: {e}", exc_info=True)
        return jsonify({'status': 'error', 'message': 'Internal server error'}), 500


# ============================================================================
# UnifiedPipeline 端点
# ============================================================================

@enhanced_bp.route('/pipeline/run', methods=['POST'])
def run_unified_pipeline():
    """
    运行端到端统一管道
    
    Request Body:
    {
        "stocks": ["AAPL", "GOOGL", "MSFT"],
        "start_date": "2015-10-01",
        "end_date": "2015-10-05",
        "causal_method": "granger",
        "prediction_horizon": 1,
        "use_optimization": true
    }
    
    Response:
    {
        "status": "success",
        "data": {
            "causal_graph": {...},
            "predictions": {...},
            "performance_stats": {...}
        }
    }
    """
    try:
        data = request.get_json()
        
        # 验证必需参数
        required_params = ['stocks', 'start_date', 'end_date']
        for param in required_params:
            if param not in data:
                return jsonify({
                    'status': 'error',
                    'message': f'Missing required parameter: {param}'
                }), 400
        
        # 解析参数
        stocks = data['stocks']
        start_date = data['start_date']
        end_date = data['end_date']
        causal_method = data.get('causal_method', 'granger')
        prediction_horizon = data.get('prediction_horizon', 1)
        use_optimization = data.get('use_optimization', True)
        
        # 执行统一管道
        pipeline = get_unified_pipeline()
        
        # 如果启用优化，设置优化器
        if use_optimization:
            optimizer = get_performance_optimizer()
            pipeline.optimizer = optimizer
        
        result = pipeline.run_end_to_end(
            stocks=stocks,
            start_date=start_date,
            end_date=end_date,
            causal_method=causal_method,
            prediction_horizon=prediction_horizon
        )
        
        return jsonify({
            'status': 'success',
            'data': result
        })
        
    except ValueError as e:
        return jsonify({'status': 'error', 'message': str(e)}), 400
    except Exception as e:
        logger.error(f"Run unified pipeline error: {e}", exc_info=True)
        return jsonify({'status': 'error', 'message': 'Internal server error'}), 500


@enhanced_bp.route('/pipeline/status', methods=['GET'])
def get_pipeline_status():
    """
    获取管道状态
    
    Response:
    {
        "status": "success",
        "data": {
            "loaded": true,
            "components": {
                "data_loader": "ready",
                "causal_manager": "ready",
                "predictor": "ready"
            }
        }
    }
    """
    try:
        pipeline = get_unified_pipeline()
        
        status = {
            'loaded': True,
            'components': {
                'data_loader': 'ready' if hasattr(pipeline, 'data_loader') else 'not_loaded',
                'causal_manager': 'ready' if hasattr(pipeline, 'causal_manager') else 'not_loaded',
                'predictor': 'ready' if hasattr(pipeline, 'predictor') else 'not_loaded'
            },
            'config_path': pipeline.config_path if hasattr(pipeline, 'config_path') else None
        }
        
        return jsonify({
            'status': 'success',
            'data': status
        })
        
    except Exception as e:
        logger.error(f"Get pipeline status error: {e}", exc_info=True)
        return jsonify({'status': 'error', 'message': 'Internal server error'}), 500


# ============================================================================
# 系统监控端点
# ============================================================================

@enhanced_bp.route('/monitor/system', methods=['GET'])
def get_system_monitor():
    """
    获取系统综合监控信息
    
    Response:
    {
        "status": "success",
        "data": {
            "performance": {...},
            "causal": {...},
            "pipeline": {...}
        }
    }
    """
    try:
        # 性能优化器状态
        optimizer = get_performance_optimizer()
        perf_status = optimizer.get_system_status()
        
        # 管道状态
        pipeline = get_unified_pipeline()
        pipeline_loaded = hasattr(pipeline, 'data_loader')
        
        return jsonify({
            'status': 'success',
            'data': {
                'performance': perf_status,
                'pipeline': {
                    'loaded': pipeline_loaded,
                    'ready': pipeline_loaded
                },
                'timestamp': str(np.datetime64('now'))
            }
        })
        
    except Exception as e:
        logger.error(f"Get system monitor error: {e}", exc_info=True)
        return jsonify({'status': 'error', 'message': 'Internal server error'}), 500


def register_enhanced_routes(app):
    """注册增强路由到应用"""
    app.register_blueprint(enhanced_bp)
    logger.info('✅ Enhanced API routes registered successfully')
