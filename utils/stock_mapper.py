"""
股票代码映射工具
提供股票代码与索引之间的双向映射功能
"""

import os
import json
import logging
import pandas as pd
from typing import Dict, List, Optional, Tuple
from pathlib import Path

logger = logging.getLogger(__name__)


class StockMapper:
    """
    股票代码映射器
    
    功能：
    - 股票代码 <-> 索引映射
    - 从配置文件加载股票列表
    - 从数据文件推断股票列表
    - 支持板块分类
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        初始化映射器
        
        Args:
            config_path: 股票配置文件路径 (JSON/CSV)
        """
        self.code_to_idx: Dict[str, int] = {}
        self.idx_to_code: Dict[int, str] = {}
        self.stock_info: Dict[str, Dict] = {}
        self.sectors: Dict[str, List[str]] = {}
        
        if config_path and os.path.exists(config_path):
            self.load_from_file(config_path)
        else:
            logger.warning("No config file provided, mapper initialized empty")
    
    def load_from_file(self, file_path: str):
        """
        从文件加载股票映射
        
        支持格式:
        - JSON: {"stocks": [{"code": "AAPL", "name": "Apple", "sector": "tech"}, ...]}
        - CSV: code,name,sector
        
        Args:
            file_path: 文件路径
        """
        file_path = Path(file_path)
        
        try:
            if file_path.suffix == '.json':
                self._load_from_json(file_path)
            elif file_path.suffix == '.csv':
                self._load_from_csv(file_path)
            else:
                raise ValueError(f"Unsupported file format: {file_path.suffix}")
            
            logger.info(f"Loaded {len(self.code_to_idx)} stocks from {file_path}")
            
        except Exception as e:
            logger.error(f"Error loading stock list from {file_path}: {e}")
            raise
    
    def _load_from_json(self, file_path: Path):
        """从JSON文件加载"""
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # 支持两种格式：{'stocks': [...]} 或直接 [...]
        if isinstance(data, dict):
            stocks = data.get('stocks', [])
        elif isinstance(data, list):
            stocks = data
        else:
            raise ValueError(f"Invalid JSON format: expected dict or list, got {type(data)}")
        
        for stock in stocks:
            # 获取索引，如果没有提供则自动分配
            idx = stock.get('index', len(self.code_to_idx))
            code = stock['code']
            
            self.code_to_idx[code] = idx
            self.idx_to_code[idx] = code
            self.stock_info[code] = {
                'name': stock.get('name', code),
                'sector': stock.get('sector', 'unknown'),
                'index': idx
            }
            
            # 按板块分类
            sector = stock.get('sector', 'unknown')
            if sector not in self.sectors:
                self.sectors[sector] = []
            self.sectors[sector].append(code)

    
    def _load_from_csv(self, file_path: Path):
        """从CSV文件加载"""
        df = pd.read_csv(file_path)
        
        # 要求CSV至少有'code'列
        if 'code' not in df.columns:
            raise ValueError("CSV must have 'code' column")
        
        for idx, row in df.iterrows():
            code = str(row['code'])
            self.code_to_idx[code] = idx
            self.idx_to_code[idx] = code
            self.stock_info[code] = {
                'name': row.get('name', code),
                'sector': row.get('sector', 'unknown'),
                'index': idx
            }
            
            # 按板块分类
            sector = row.get('sector', 'unknown')
            if sector not in self.sectors:
                self.sectors[sector] = []
            self.sectors[sector].append(code)
    
    def load_from_data_file(self, data_path: str, column_names: Optional[List[str]] = None):
        """
        从数据文件推断股票列表
        
        Args:
            data_path: 数据文件路径 (CSV/NPZ)
            column_names: 列名列表（对于NPZ文件）
        """
        data_path = Path(data_path)
        
        try:
            if data_path.suffix == '.csv':
                df = pd.read_csv(data_path)
                # 假设第一行是股票代码
                if 'stock' in df.columns or 'code' in df.columns:
                    codes = df['stock'].unique() if 'stock' in df.columns else df['code'].unique()
                else:
                    # 假设第一列是股票代码
                    codes = df.iloc[:, 0].unique()
                
                for idx, code in enumerate(codes):
                    self.add_stock(str(code), idx)
            
            elif data_path.suffix == '.npz':
                import numpy as np
                data = np.load(data_path)
                
                if column_names:
                    for idx, code in enumerate(column_names):
                        self.add_stock(code, idx)
                else:
                    # 从数据形状推断股票数量
                    n_stocks = data['data'].shape[1] if 'data' in data else 0
                    for idx in range(n_stocks):
                        self.add_stock(f'Stock_{idx}', idx)
            
            logger.info(f"Loaded {len(self.code_to_idx)} stocks from {data_path}")
            
        except Exception as e:
            logger.error(f"Error loading from data file {data_path}: {e}")
            raise
    
    def add_stock(
        self, 
        code: str, 
        index: Optional[int] = None,
        name: Optional[str] = None,
        sector: Optional[str] = None
    ):
        """
        添加单个股票映射
        
        Args:
            code: 股票代码
            index: 索引（None表示自动分配）
            name: 股票名称
            sector: 所属板块
        """
        if index is None:
            index = len(self.code_to_idx)
        
        self.code_to_idx[code] = index
        self.idx_to_code[index] = code
        self.stock_info[code] = {
            'name': name or code,
            'sector': sector or 'unknown',
            'index': index
        }
        
        # 更新板块
        sector = sector or 'unknown'
        if sector not in self.sectors:
            self.sectors[sector] = []
        if code not in self.sectors[sector]:
            self.sectors[sector].append(code)
    
    def get_index(self, code: str) -> int:
        """获取股票索引"""
        if code not in self.code_to_idx:
            raise KeyError(f"Stock code '{code}' not found in mapper")
        return self.code_to_idx[code]
    
    def get_code(self, index: int) -> str:
        """获取股票代码"""
        if index not in self.idx_to_code:
            raise KeyError(f"Index {index} not found in mapper")
        return self.idx_to_code[index]
    
    def get_indices(self, codes: List[str]) -> List[int]:
        """批量获取索引"""
        return [self.get_index(code) for code in codes]
    
    def get_codes(self, indices: List[int]) -> List[str]:
        """批量获取代码"""
        return [self.get_code(idx) for idx in indices]
    
    def get_info(self, code: str) -> Dict:
        """获取股票详细信息"""
        if code not in self.stock_info:
            raise KeyError(f"Stock code '{code}' not found")
        return self.stock_info[code]
    
    def get_stocks_by_sector(self, sector: str) -> List[str]:
        """根据板块获取股票列表"""
        return self.sectors.get(sector, [])
    
    def get_all_codes(self) -> List[str]:
        """获取所有股票代码"""
        return list(self.code_to_idx.keys())
    
    def get_all_sectors(self) -> List[str]:
        """获取所有板块"""
        return list(self.sectors.keys())
    
    def contains(self, code: str) -> bool:
        """检查股票代码是否存在"""
        return code in self.code_to_idx
    
    def size(self) -> int:
        """获取股票总数"""
        return len(self.code_to_idx)
    
    def save_to_file(self, file_path: str):
        """
        保存映射到文件
        
        Args:
            file_path: 保存路径 (JSON或CSV)
        """
        file_path = Path(file_path)
        
        if file_path.suffix == '.json':
            stocks = [
                {
                    'code': code,
                    'name': info['name'],
                    'sector': info['sector'],
                    'index': info['index']
                }
                for code, info in self.stock_info.items()
            ]
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump({'stocks': stocks}, f, indent=2, ensure_ascii=False)
        
        elif file_path.suffix == '.csv':
            df = pd.DataFrame([
                {
                    'code': code,
                    'name': info['name'],
                    'sector': info['sector'],
                    'index': info['index']
                }
                for code, info in self.stock_info.items()
            ])
            df.to_csv(file_path, index=False)
        
        logger.info(f"Saved {len(self.code_to_idx)} stocks to {file_path}")
    
    def __repr__(self) -> str:
        return f"StockMapper(stocks={len(self.code_to_idx)}, sectors={len(self.sectors)})"
    
    def __len__(self) -> int:
        return len(self.code_to_idx)


def create_stock_list_from_directory(
    data_dir: str,
    output_path: str,
    pattern: str = '*.csv'
) -> StockMapper:
    """
    从数据目录创建股票列表
    
    Args:
        data_dir: 数据目录
        output_path: 输出文件路径
        pattern: 文件匹配模式
    
    Returns:
        StockMapper对象
    """
    mapper = StockMapper()
    data_dir = Path(data_dir)
    
    # 扫描所有匹配的文件
    files = list(data_dir.glob(pattern))
    logger.info(f"Found {len(files)} data files in {data_dir}")
    
    # 从文件名或内容提取股票代码
    for idx, file_path in enumerate(files):
        # 假设文件名就是股票代码
        code = file_path.stem
        mapper.add_stock(code, idx)
    
    # 保存到文件
    mapper.save_to_file(output_path)
    return mapper


if __name__ == '__main__':
    # 测试代码
    print("测试StockMapper...")
    
    # 创建测试映射器
    mapper = StockMapper()
    
    # 添加测试股票
    test_stocks = [
        ('AAPL', 'Apple Inc.', 'Technology'),
        ('GOOGL', 'Alphabet Inc.', 'Technology'),
        ('JPM', 'JPMorgan Chase', 'Finance'),
        ('BAC', 'Bank of America', 'Finance'),
        ('JNJ', 'Johnson & Johnson', 'Healthcare')
    ]
    
    for idx, (code, name, sector) in enumerate(test_stocks):
        mapper.add_stock(code, idx, name, sector)
    
    print(f"\n{mapper}")
    print(f"所有代码: {mapper.get_all_codes()}")
    print(f"所有板块: {mapper.get_all_sectors()}")
    print(f"科技股: {mapper.get_stocks_by_sector('Technology')}")
    
    # 测试映射
    print(f"\nAAPL索引: {mapper.get_index('AAPL')}")
    print(f"索引0的代码: {mapper.get_code(0)}")
    print(f"AAPL信息: {mapper.get_info('AAPL')}")
    
    # 保存测试
    test_file = 'test_stocks.json'
    mapper.save_to_file(test_file)
    print(f"\n已保存到 {test_file}")
    
    # 重新加载测试
    mapper2 = StockMapper(test_file)
    print(f"重新加载: {mapper2}")
    
    # 清理
    if os.path.exists(test_file):
        os.remove(test_file)
        print(f"已删除测试文件")
