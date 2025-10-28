"""
ICSFP API Application
Intelligent Causal Stock Forecasting Platform - Flask-based REST API
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
import logging
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.routes import register_routes
from api.middleware import error_handler, request_logger

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def create_app(config_path='config.yml'):
    """创建Flask应用"""
    
    # 获取项目根目录
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    static_folder = os.path.join(root_dir, 'static')
    
    # 创建Flask应用，配置静态文件
    app = Flask(__name__, 
                static_folder=static_folder,
                static_url_path='/static')
    
    # 配置CORS
    CORS(app, resources={r"/api/*": {"origins": "*"}})
    
    # 应用配置
    app.config['JSON_AS_ASCII'] = False
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max request size
    app.config['CONFIG_PATH'] = config_path
    
    # 注册中间件
    app.before_request(request_logger)
    app.register_error_handler(Exception, error_handler)
    
    # 注册路由
    register_routes(app)
    
    # 首页路由 - 提供Web界面
    @app.route('/')
    def index():
        """返回Web界面"""
        return app.send_static_file('index.html')
    
    # 关于页面路由
    @app.route('/about')
    def about():
        """返回关于页面"""
        return app.send_static_file('about.html')
    
    # Favicon 路由
    @app.route('/favicon.ico')
    def favicon():
        """返回favicon或404"""
        from flask import send_from_directory
        import os
        favicon_path = os.path.join(app.root_path, 'static', 'favicon.ico')
        if os.path.exists(favicon_path):
            return send_from_directory(os.path.join(app.root_path, 'static'),
                                     'favicon.ico', mimetype='image/vnd.microsoft.icon')
        return '', 204  # No Content
    
    # 健康检查端点
    @app.route('/health', methods=['GET'])
    def health_check():
        return jsonify({
            'status': 'healthy',
            'service': 'ICSFP API',
            'version': '1.0.0'
        })
    
    logger.info('ICSFP API application created successfully')
    return app


if __name__ == '__main__':
    app = create_app()
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=True
    )
