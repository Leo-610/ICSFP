"""
API Middleware
请求日志和错误处理
"""

from flask import request, jsonify
import logging
import time
import traceback

logger = logging.getLogger(__name__)


def request_logger():
    """请求日志中间件"""
    request.start_time = time.time()
    logger.info(f"Request: {request.method} {request.path}")


def error_handler(error):
    """全局错误处理器"""
    logger.error(f"Error handling request: {error}")
    logger.error(traceback.format_exc())
    
    return jsonify({
        'status': 'error',
        'message': str(error),
        'type': type(error).__name__
    }), 500


def response_time_logger(response):
    """响应时间日志"""
    if hasattr(request, 'start_time'):
        duration = time.time() - request.start_time
        logger.info(f"Response: {request.method} {request.path} - {duration:.3f}s")
    return response
