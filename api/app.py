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
from api.trading_routes import register_trading_routes
from api.realtime_routes import register_realtime_routes
from api.enhanced_routes import register_enhanced_routes
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
    
    # 添加安全响应头
    @app.after_request
    def add_security_headers(response):
        """添加安全相关的HTTP头部"""
        # 设置Content-Type字符集为UTF-8
        if 'Content-Type' in response.headers:
            content_type = response.headers['Content-Type']
            if 'charset' not in content_type.lower():
                if 'text/html' in content_type or 'application/json' in content_type:
                    response.headers['Content-Type'] = f"{content_type}; charset=utf-8"
        
        # 使用CSP替代X-Frame-Options
        response.headers['Content-Security-Policy'] = "frame-ancestors 'self'"
        
        # 设置Cache-Control（替代Expires）
        if request.path.startswith('/static/'):
            # 静态资源缓存1小时
            response.headers['Cache-Control'] = 'public, max-age=3600'
        else:
            # 动态内容不缓存
            response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
            response.headers['Pragma'] = 'no-cache'
        
        # 移除不必要的头部
        response.headers.pop('X-XSS-Protection', None)
        
        # 其他安全头部
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        
        return response
    
    # 注册路由
    register_routes(app)
    register_trading_routes(app)
    register_realtime_routes(app, enable_websocket=True)
    register_enhanced_routes(app)  # Phase 3 增强功能路由
    
    logger.info("✅ All routes registered successfully")
    logger.info("📊 Enhanced routes available at /api/v1/enhanced/*")
    
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
    
    # 交易页面路由
    @app.route('/trading')
    def trading():
        """返回模拟交易页面"""
        return app.send_static_file('trading.html')
    
    # 系统状态页面路由
    @app.route('/health')
    def health_page():
        """返回系统状态监控页面"""
        # 如果是浏览器访问，返回HTML页面
        if request.headers.get('Accept') and 'text/html' in request.headers.get('Accept'):
            return app.send_static_file('health.html')
        # 如果是API请求，返回JSON
        return jsonify({
            'status': 'healthy',
            'service': 'ICSFP API',
            'version': '1.0.0'
        })
    
    # 实时数据监控页面路由
    @app.route('/realtime')
    def realtime_page():
        """返回实时数据监控页面"""
        return app.send_static_file('realtime.html')
    
    # 可视化页面路由
    @app.route('/visualization')
    def visualization_page():
        """返回高级可视化页面"""
        return app.send_static_file('advanced_visualization.html')
    
    # 基础可视化页面路由
    @app.route('/visualization/basic')
    def basic_visualization_page():
        """返回基础可视化页面"""
        return app.send_static_file('visualization.html')
    
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
    
    logger.info('ICSFP API application created successfully')
    return app


if __name__ == '__main__':
    app = create_app()
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=True
    )
