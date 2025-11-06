#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据集管理器
负责管理和配置多个股票预测数据集
"""

import os
from typing import Dict, List, Optional
import yaml


class DatasetManager:
    """
    多数据集管理器
    提供统一的数据集注册、查询和配置接口
    """
    
    # 数据集注册表
    DATASETS = {
        'ACL18': {
            'name': 'ACL18',
            'full_name': 'ACL 2018 Stock Prediction Dataset',
            'description': '88只美股 (2014-2016) + Twitter推文',
            'source': 'https://github.com/yumoxu/stocknet-dataset',
            'stocks': 88,
            'date_range': {
                'start': '2014-01-01',
                'end': '2016-01-01',
                'train_start': '2014-01-01',
                'train_end': '2015-08-01',
                'dev_start': '2015-08-01',
                'dev_end': '2015-10-01',
                'test_start': '2015-10-01',
                'test_end': '2016-01-01'
            },
            'paths': {
                'data_root': 'data/cikm18',
                'price': 'data/cikm18/price/preprocessed',
                'text': 'data/cikm18/tweet/preprocessed',
                'config': 'config_acl18.yml'
            },
            'format': {
                'price': 'tsv',  # date\tprice_change%\tclose\thigh\tlow\topen\tvolume
                'text': 'json_per_day'  # 每天一个文件,每行一个JSON
            },
            'available': True
        },
        
        'CMIN-CN': {
            'name': 'CMIN-CN',
            'full_name': 'CMIN Chinese Stock Dataset',
            'description': '88只A股 (2015-2017) + 微博/财经评论',
            'source': '需申请',
            'stocks': 88,
            'date_range': {
                'start': '2015-01-01',
                'end': '2017-12-31',
                'train_start': '2015-01-01',
                'train_end': '2016-08-01',
                'dev_start': '2016-08-01',
                'dev_end': '2016-10-01',
                'test_start': '2016-10-01',
                'test_end': '2017-12-31'
            },
            'paths': {
                'data_root': 'data/cmin-cn',
                'price': 'data/cmin-cn/price/preprocessed',
                'text': 'data/cmin-cn/news/preprocessed',
                'config': 'config_cmin-cn.yml'
            },
            'format': {
                'price': 'tsv',
                'text': 'json_per_day'
            },
            'available': False  # 需要额外获取
        },
        
        'CIKM18': {
            'name': 'CIKM18',
            'full_name': 'CIKM 2018 Stock Dataset',
            'description': '38只美股 + Twitter推文',
            'source': 'https://github.com/yumoxu/stocknet-dataset',
            'stocks': 38,
            'date_range': {
                'start': '2014-01-02',
                'end': '2016-01-02',
                'train_start': '2014-01-02',
                'train_end': '2015-08-01',
                'dev_start': '2015-08-01',
                'dev_end': '2015-10-01',
                'test_start': '2015-10-01',
                'test_end': '2016-01-02'
            },
            'paths': {
                'data_root': 'data/cikm18',
                'price': 'data/cikm18/price/preprocessed',
                'text': 'data/cikm18/tweet/preprocessed',
                'config': 'config_cikm18.yml'
            },
            'format': {
                'price': 'tsv',
                'text': 'json_per_day'
            },
            'available': True
        }
    }
    
    def __init__(self):
        """初始化数据集管理器"""
        self.current_dataset = None
    
    def list_datasets(self, verbose=True) -> List[str]:
        """
        列出所有可用数据集
        
        Args:
            verbose: 是否显示详细信息
            
        Returns:
            数据集名称列表
        """
        if verbose:
            print("=" * 80)
            print("📊 可用数据集")
            print("=" * 80)
            
            for name, info in self.DATASETS.items():
                status = "✅ 可用" if info['available'] else "⚠️  需要获取"
                print(f"\n{name} - {info['full_name']}")
                print(f"  状态: {status}")
                print(f"  描述: {info['description']}")
                print(f"  股票数: {info['stocks']}")
                print(f"  时间范围: {info['date_range']['start']} 到 {info['date_range']['end']}")
                print(f"  数据来源: {info['source']}")
                
                # 检查数据是否存在
                if info['available']:
                    price_path = info['paths']['price']
                    if os.path.exists(price_path):
                        files = [f for f in os.listdir(price_path) if f.endswith('.txt')]
                        print(f"  ✅ 价格数据: {len(files)} 个文件")
                    else:
                        print(f"  ❌ 价格数据不存在: {price_path}")
            
            print("\n" + "=" * 80)
        
        return list(self.DATASETS.keys())
    
    def get_dataset(self, name: str) -> Optional[Dict]:
        """
        获取数据集配置
        
        Args:
            name: 数据集名称
            
        Returns:
            数据集配置字典，如果不存在返回None
        """
        if name not in self.DATASETS:
            available = ', '.join(self.DATASETS.keys())
            raise ValueError(
                f"数据集 '{name}' 不存在!\n"
                f"可用数据集: {available}"
            )
        
        return self.DATASETS[name].copy()
    
    def check_dataset(self, name: str) -> Dict:
        """
        检查数据集是否完整
        
        Args:
            name: 数据集名称
            
        Returns:
            检查结果字典
        """
        config = self.get_dataset(name)
        
        result = {
            'name': name,
            'available': config['available'],
            'price_exists': False,
            'text_exists': False,
            'price_count': 0,
            'text_count': 0,
            'ready': False
        }
        
        # 检查价格数据
        price_path = config['paths']['price']
        if os.path.exists(price_path):
            result['price_exists'] = True
            price_files = [f for f in os.listdir(price_path) if f.endswith('.txt')]
            result['price_count'] = len(price_files)
        
        # 检查文本数据
        text_path = config['paths']['text']
        if os.path.exists(text_path):
            result['text_exists'] = True
            # 文本数据是目录结构
            text_dirs = [d for d in os.listdir(text_path) 
                        if os.path.isdir(os.path.join(text_path, d))]
            result['text_count'] = len(text_dirs)
        
        # 判断是否就绪
        result['ready'] = (result['price_exists'] and 
                          result['text_exists'] and 
                          result['price_count'] > 0 and 
                          result['text_count'] > 0)
        
        return result
    
    def generate_config(self, name: str, output_path: Optional[str] = None) -> str:
        """
        生成数据集配置文件
        
        Args:
            name: 数据集名称
            output_path: 输出路径，默认为config_{name}.yml
            
        Returns:
            配置文件路径
        """
        config = self.get_dataset(name)
        
        if output_path is None:
            output_path = f"config_{name.lower()}.yml"
        
        # 构建完整配置
        full_config = {
            'dataset': {
                'name': config['name'],
                'description': config['description'],
                'stocks': config['stocks']
            },
            'dates': config['date_range'],
            'paths': {
                'data': config['paths']['data_root'] + '/',
                'price': config['paths']['price'].replace('data/', ''),
                'tweet_preprocessed': config['paths']['text'].replace('data/', '')
            },
            'model': {
                'batch_size': 32,
                'learning_rate': 0.001,
                'n_epochs': 15,
                'max_n_days': 5,
                'max_n_msgs': 30,
                'max_n_words': 40
            },
            'causal': {
                'method': 'granger',
                'max_lags': 5,
                'significance_level': 0.05
            }
        }
        
        # 保存配置文件
        with open(output_path, 'w', encoding='utf-8') as f:
            yaml.dump(full_config, f, allow_unicode=True, sort_keys=False)
        
        print(f"✅ 配置文件已生成: {output_path}")
        return output_path
    
    def set_current_dataset(self, name: str):
        """设置当前使用的数据集"""
        self.current_dataset = name
        config = self.get_dataset(name)
        print(f"📊 当前数据集: {config['full_name']}")
    
    def get_stock_list(self, name: str) -> List[str]:
        """
        获取数据集的股票列表
        
        Args:
            name: 数据集名称
            
        Returns:
            股票代码列表
        """
        config = self.get_dataset(name)
        price_path = config['paths']['price']
        
        if not os.path.exists(price_path):
            return []
        
        # 从文件名提取股票代码
        stocks = []
        for f in os.listdir(price_path):
            if f.endswith('.txt'):
                stock = f.replace('.txt', '')
                stocks.append(stock)
        
        return sorted(stocks)
    
    def get_summary(self, name: str) -> str:
        """
        获取数据集摘要信息
        
        Args:
            name: 数据集名称
            
        Returns:
            摘要字符串
        """
        config = self.get_dataset(name)
        check = self.check_dataset(name)
        
        summary = f"""
数据集: {config['full_name']}
名称: {config['name']}
描述: {config['description']}
股票数: {config['stocks']}
时间范围: {config['date_range']['start']} ~ {config['date_range']['end']}
状态: {'✅ 就绪' if check['ready'] else '❌ 未就绪'}

数据检查:
  价格数据: {'✅' if check['price_exists'] else '❌'} ({check['price_count']} 个文件)
  文本数据: {'✅' if check['text_exists'] else '❌'} ({check['text_count']} 个目录)

数据路径:
  根目录: {config['paths']['data_root']}
  价格: {config['paths']['price']}
  文本: {config['paths']['text']}
"""
        return summary


def main():
    """测试函数"""
    manager = DatasetManager()
    
    # 列出所有数据集
    manager.list_datasets()
    
    # 检查ACL18数据集
    print("\n" + "=" * 80)
    print("检查 ACL18 数据集")
    print("=" * 80)
    check = manager.check_dataset('ACL18')
    print(f"价格数据: {'✅' if check['price_exists'] else '❌'} ({check['price_count']} 文件)")
    print(f"文本数据: {'✅' if check['text_exists'] else '❌'} ({check['text_count']} 目录)")
    print(f"就绪状态: {'✅' if check['ready'] else '❌'}")
    
    # 生成配置文件
    print("\n" + "=" * 80)
    print("生成配置文件")
    print("=" * 80)
    manager.generate_config('ACL18')
    
    # 获取股票列表
    print("\n" + "=" * 80)
    print("股票列表")
    print("=" * 80)
    stocks = manager.get_stock_list('ACL18')
    print(f"共 {len(stocks)} 只股票")
    print(f"前10只: {', '.join(stocks[:10])}")


if __name__ == '__main__':
    main()
