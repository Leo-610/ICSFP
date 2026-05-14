"""
A股因果网络数据获取模块
从Tushare获取个股、行业、概念板块数据
"""

import pandas as pd
import numpy as np
import tushare as ts
import logging
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class AStockDataFetcher:
    """A股数据获取器"""
    
    def __init__(self, token: str):
        """
        初始化数据获取器
        
        Args:
            token: Tushare API token
        """
        ts.set_token(token)
        self.pro = ts.pro_api()
        logger.info("Tushare API初始化成功")
    
    def get_stock_pool(
        self,
        market: str = 'all',
        min_market_cap: float = 50,  # 亿元
        exclude_st: bool = True
    ) -> pd.DataFrame:
        """
        获取股票池
        
        Args:
            market: 市场类型 ('sz'=深圳主板, 'sh'=上海主板, 'cyb'=创业板, 'all'=全部)
            min_market_cap: 最小市值（亿元）
            exclude_st: 是否排除ST股
        
        Returns:
            股票列表DataFrame
        """
        logger.info(f"获取股票池: market={market}, min_cap={min_market_cap}亿")
        
        # 获取所有A股基本信息
        stock_basic = self.pro.stock_basic(
            exchange='',
            list_status='L',  # 上市状态
            fields='ts_code,symbol,name,area,industry,market,list_date'
        )
        
        # 过滤ST股
        if exclude_st:
            stock_basic = stock_basic[~stock_basic['name'].str.contains('ST')]
        
        # 过滤市场
        if market != 'all':
            if market == 'cyb':
                stock_basic = stock_basic[stock_basic['market'] == '创业板']
            elif market == 'sh':
                stock_basic = stock_basic[stock_basic['ts_code'].str.startswith('60')]
            elif market == 'sz':
                stock_basic = stock_basic[stock_basic['ts_code'].str.startswith('00')]
        
        # 获取市值数据并过滤
        if min_market_cap > 0:
            # 获取最近交易日
            trade_date = self._get_latest_trade_date()
            
            # 获取日线数据（包含市值）
            daily_basic = self.pro.daily_basic(
                trade_date=trade_date,
                fields='ts_code,total_mv'  # 总市值（万元）
            )
            
            # 合并并过滤
            stock_basic = stock_basic.merge(daily_basic, on='ts_code', how='left')
            stock_basic = stock_basic[stock_basic['total_mv'] >= min_market_cap * 10000]
        
        logger.info(f"筛选出{len(stock_basic)}只股票")
        
        return stock_basic
    
    def get_stock_returns(
        self,
        ts_codes: List[str],
        start_date: str,
        end_date: str,
        adj: str = 'qfq'  # 前复权
    ) -> pd.DataFrame:
        """
        获取股票收益率数据
        
        Args:
            ts_codes: 股票代码列表
            start_date: 开始日期 (YYYYMMDD)
            end_date: 结束日期 (YYYYMMDD)
            adj: 复权类型 ('qfq'=前复权, 'hfq'=后复权, None=不复权)
        
        Returns:
            收益率DataFrame (日期×股票)
        """
        logger.info(f"获取{len(ts_codes)}只股票的收益率: {start_date} - {end_date}")
        
        all_data = {}
        
        for i, ts_code in enumerate(ts_codes):
            try:
                # 获取日线数据
                df = ts.pro_bar(
                    ts_code=ts_code,
                    adj=adj,
                    start_date=start_date,
                    end_date=end_date,
                    factors=['tor', 'volume']
                )
                
                if df is not None and not df.empty:
                    # 计算收益率
                    df = df.sort_values('trade_date')
                    df['return'] = df['close'].pct_change()
                    df = df.set_index('trade_date')
                    all_data[ts_code] = df['return']
                
                # 显示进度
                if (i + 1) % 10 == 0:
                    logger.info(f"  进度: {i+1}/{len(ts_codes)}")
            
            except Exception as e:
                logger.warning(f"获取{ts_code}数据失败: {e}")
                continue
        
        # 合并为DataFrame
        returns_df = pd.DataFrame(all_data)
        returns_df = returns_df.fillna(0)  # 停牌填充0
        
        logger.info(f"收益率数据shape: {returns_df.shape}")
        
        return returns_df
    
    def get_industry_indices(
        self,
        start_date: str,
        end_date: str,
        level: str = 'L1'  # L1=一级行业, L2=二级行业
    ) -> pd.DataFrame:
        """
        获取申万行业指数数据
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
            level: 行业层级
        
        Returns:
            行业指数收益率DataFrame
        """
        logger.info(f"获取申万{level}行业指数: {start_date} - {end_date}")
        
        # 获取申万行业分类
        sw_index = self.pro.index_classify(
            level=level,
            src='SW2021'  # 申万2021版
        )
        
        all_indices = {}
        
        for _, row in sw_index.iterrows():
            index_code = row['index_code']
            industry_name = row['industry_name']
            
            try:
                # 获取行业指数日线
                df = self.pro.index_daily(
                    ts_code=index_code,
                    start_date=start_date,
                    end_date=end_date
                )
                
                if df is not None and not df.empty:
                    df = df.sort_values('trade_date')
                    df['return'] = df['close'].pct_change()
                    df = df.set_index('trade_date')
                    all_indices[industry_name] = df['return']
            
            except Exception as e:
                logger.warning(f"获取行业{industry_name}失败: {e}")
                continue
        
        industry_df = pd.DataFrame(all_indices)
        industry_df = industry_df.fillna(0)
        
        logger.info(f"行业指数数据shape: {industry_df.shape}")
        
        return industry_df
    
    def get_concept_indices(
        self,
        start_date: str,
        end_date: str,
        hot_concepts: Optional[List[str]] = None
    ) -> pd.DataFrame:
        """
        获取概念板块指数
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
            hot_concepts: 热点概念列表（可选）
        
        Returns:
            概念指数收益率DataFrame
        """
        logger.info(f"获取概念板块指数: {start_date} - {end_date}")
        
        # 获取概念分类
        concept_list = self.pro.concept()
        
        # 如果指定了热点概念，则过滤
        if hot_concepts:
            concept_list = concept_list[
                concept_list['name'].isin(hot_concepts)
            ]
        
        all_concepts = {}
        
        for _, row in concept_list.iterrows():
            code = row['code']
            name = row['name']
            
            try:
                # 获取概念成分股
                concept_detail = self.pro.concept_detail(id=code)
                
                if concept_detail is not None and not concept_detail.empty:
                    # 获取成分股数据并计算等权指数
                    stocks = concept_detail['ts_code'].tolist()[:30]  # 限制30只
                    
                    stock_returns = self.get_stock_returns(
                        stocks, start_date, end_date
                    )
                    
                    # 等权平均
                    concept_return = stock_returns.mean(axis=1)
                    all_concepts[name] = concept_return
            
            except Exception as e:
                logger.warning(f"获取概念{name}失败: {e}")
                continue
        
        concept_df = pd.DataFrame(all_concepts)
        concept_df = concept_df.fillna(0)
        
        logger.info(f"概念指数数据shape: {concept_df.shape}")
        
        return concept_df
    
    def get_macro_factors(
        self,
        start_date: str,
        end_date: str
    ) -> pd.DataFrame:
        """
        获取宏观因子
        
        Returns:
            宏观因子DataFrame
        """
        logger.info(f"获取宏观因子: {start_date} - {end_date}")
        
        factors = {}
        
        try:
            # 1. 市场指数
            for index_code, name in [
                ('000001.SH', 'shanghai_index'),
                ('399001.SZ', 'shenzhen_index'),
                ('399006.SZ', 'cyb_index')
            ]:
                df = self.pro.index_daily(
                    ts_code=index_code,
                    start_date=start_date,
                    end_date=end_date
                )
                if df is not None:
                    df = df.sort_values('trade_date')
                    df['return'] = df['close'].pct_change()
                    df = df.set_index('trade_date')
                    factors[name] = df['return']
            
            # 2. 北向资金
            moneyflow = self.pro.moneyflow_hsgt(
                start_date=start_date,
                end_date=end_date
            )
            if moneyflow is not None:
                moneyflow = moneyflow.sort_values('trade_date')
                moneyflow = moneyflow.set_index('trade_date')
                factors['northbound_flow'] = moneyflow['north_money']
            
            # 3. 融资融券余额
            margin = self.pro.margin(
                start_date=start_date,
                end_date=end_date,
                exchange_id='SSE'  # 上交所
            )
            if margin is not None:
                margin = margin.sort_values('trade_date')
                margin = margin.set_index('trade_date')
                factors['margin_balance'] = margin['rzrqye']  # 融资融券余额
        
        except Exception as e:
            logger.error(f"获取宏观因子失败: {e}")
        
        macro_df = pd.DataFrame(factors)
        macro_df = macro_df.fillna(method='ffill')  # 前向填充
        
        logger.info(f"宏观因子数据shape: {macro_df.shape}")
        
        return macro_df
    
    def _get_latest_trade_date(self) -> str:
        """获取最近交易日"""
        today = datetime.now().strftime('%Y%m%d')
        
        # 获取交易日历
        cal = self.pro.trade_cal(
            start_date=(datetime.now() - timedelta(days=10)).strftime('%Y%m%d'),
            end_date=today
        )
        
        # 筛选交易日
        trade_dates = cal[cal['is_open'] == 1]['cal_date']
        
        if not trade_dates.empty:
            return trade_dates.iloc[-1]
        else:
            return today
    
    def prepare_causal_data(
        self,
        n_stocks: int = 50,
        lookback_days: int = 200,
        market: str = 'all'
    ) -> Dict[str, pd.DataFrame]:
        """
        一键准备因果分析所需的全部数据
        
        Args:
            n_stocks: 选取的股票数量
            lookback_days: 回溯天数
            market: 市场类型
        
        Returns:
            包含所有层级数据的字典
        """
        logger.info(f"准备因果分析数据: {n_stocks}只股票, {lookback_days}天")
        
        # 计算日期范围
        end_date = datetime.now()
        start_date = end_date - timedelta(days=lookback_days * 2)  # 多取一些防止节假日
        
        start_str = start_date.strftime('%Y%m%d')
        end_str = end_date.strftime('%Y%m%d')
        
        # 1. 获取股票池
        stock_pool = self.get_stock_pool(market=market, min_market_cap=50)
        stock_pool = stock_pool.head(n_stocks)  # 取前n只
        ts_codes = stock_pool['ts_code'].tolist()
        
        logger.info(f"选定股票: {len(ts_codes)}只")
        
        # 2. 获取各层级数据
        data = {}
        
        try:
            data['stocks'] = self.get_stock_returns(ts_codes, start_str, end_str)
            data['industries'] = self.get_industry_indices(start_str, end_str)
            data['macros'] = self.get_macro_factors(start_str, end_str)
            
            # 概念数据可选（耗时较长）
            # data['concepts'] = self.get_concept_indices(start_str, end_str)
            
            data['stock_info'] = stock_pool
            
        except Exception as e:
            logger.error(f"数据准备失败: {e}")
            raise
        
        logger.info("因果分析数据准备完成")
        
        return data


def demo_data_fetch():
    """演示数据获取"""
    import os
    # 从环境变量读取 Tushare token，不要硬编码
    TOKEN = os.environ.get('TUSHARE_TOKEN', '')
    if not TOKEN:
        raise ValueError("请设置环境变量 TUSHARE_TOKEN")
    
    fetcher = AStockDataFetcher(TOKEN)
    
    print("=== 一键获取因果分析数据 ===")
    data = fetcher.prepare_causal_data(
        n_stocks=30,
        lookback_days=180,
        market='all'
    )
    
    print(f"\n股票收益率: {data['stocks'].shape}")
    print(f"行业指数: {data['industries'].shape}")
    print(f"宏观因子: {data['macros'].shape}")
    print(f"\n选定的股票:")
    print(data['stock_info'][['ts_code', 'name', 'industry']].head(10))
    
    print("\n数据获取演示完成！")


if __name__ == '__main__':
    demo_data_fetch()
