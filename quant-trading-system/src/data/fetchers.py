"""
统一数据获取接口
支持多源自动降级：baostock → akshare → yfinance → ccxt → mock
"""
import os
import time
import pandas as pd
import numpy as np
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

from src.utils.logger import setup_logger

logger = setup_logger(__name__)

class BaseFetcher(ABC):
    """数据源基类"""
    def __init__(self, cache_dir: str = None):
        self.cache_dir = cache_dir or "data/cache"
        os.makedirs(self.cache_dir, exist_ok=True)

    @abstractmethod
    def fetch(self, symbol: str, start_date: str, end_date: str, **kwargs) -> Optional[pd.DataFrame]:
        """获取数据，返回标准OHLCV DataFrame"""
        pass

    def _get_cache_path(self, symbol: str, start: str, end: str) -> str:
        safe_symbol = symbol.replace('/', '_').replace('@', '_')
        return os.path.join(self.cache_dir, f"{safe_symbol}_{start}_{end}.parquet")

    def _save_cache(self, df: pd.DataFrame, symbol: str, start: str, end: str):
        try:
            cache_path = self._get_cache_path(symbol, start, end)
            df.to_parquet(cache_path, index=False)
            logger.debug(f"缓存已保存: {cache_path}")
        except Exception as e:
            logger.warning(f"缓存保存失败: {e}")

    def _load_cache(self, symbol: str, start: str, end: str) -> Optional[pd.DataFrame]:
        try:
            cache_path = self._get_cache_path(symbol, start, end)
            if os.path.exists(cache_path):
                df = pd.read_parquet(cache_path)
                logger.debug(f"从缓存加载: {symbol} ({len(df)} 行)")
                return df
        except Exception as e:
            logger.warning(f"缓存加载失败: {e}")
        return None

class BaostockFetcher(BaseFetcher):
    """A股数据源（Baostock）- 支持分钟级和日线，历史完整"""
    def fetch(self, symbol: str, start_date: str, end_date: str, freq='d', adjust='2', **kwargs) -> Optional[pd.DataFrame]:
        """
        通过 Baostock 获取数据
        :param freq: 'd'=日线, '5'=5分钟, '15'=15分钟, '30'=30分钟, '60'=60分钟
        :param adjust: 复权方式 '1'=前复权, '2'=后复权, '3'=不复位
        """
        try:
            import baostock as bs
            # 先查缓存
            cache_key = f"{symbol}_{freq}_{adjust}"
            cached = self._load_cache(cache_key, start_date, end_date)
            if cached is not None:
                return cached

            # 转换 symbol 为 Baostock 格式：sh.510300 或 sz.159915
            if '.' in symbol:
                market = symbol.split('.')[-1].upper()
                code = symbol.split('.')[0]
                if market == 'SH':
                    bs_symbol = f"sh.{code}"
                elif market == 'SZ':
                    bs_symbol = f"sz.{code}"
                else:
                    bs_symbol = symbol
            else:
                # 6位数字，默认沪市（sh）
                bs_symbol = f"sh.{symbol}" if symbol.startswith('6') else f"sz.{symbol}"

            logger.info(f"Baostock: 下载 {symbol} (内部格式: {bs_symbol}) ({start_date} ~ {end_date}, freq={freq}, adjust={adjust})")
            
            # 登录 Baostock
            lg = bs.login()
            if lg.error_code != '0':
                logger.error(f"Baostock 登录失败: {lg.error_msg}")
                return None
            
            try:
                # 查询方法：bs.query_history_k_data_plus
                # 字段参考：date,code,open,high,low,close,volume,amount,adjustflag,turn,pctChg,isST
                fields = "date,open,high,low,close,volume,amount,pctChg"
                rs = bs.query_history_k_data_plus(
                    code=bs_symbol,
                    fields=fields,
                    start_date=start_date,
                    end_date=end_date,
                    frequency=freq,
                    adjustflag=adjust  # 前复权
                )
                
                if rs is None:
                    logger.warning(f"Baostock: {symbol} 无数据")
                    return None
                
                # 转换为 DataFrame
                data_list = []
                while (rs.error_code == '0') and rs.next():
                    row = rs.get_row_data()
                    data_list.append(row)
                
                if not data_list:
                    logger.warning(f"Baostock: {symbol} 返回空数据")
                    return None
                
                # 注意：字段顺序必须与 query 一致
                df = pd.DataFrame(data_list, columns=['date', 'open', 'high', 'low', 'close', 'volume', 'amount', 'pct_change'])
                
                # 类型转换
                for col in ['open', 'high', 'low', 'close', 'volume', 'amount', 'pct_change']:
                    df[col] = pd.to_numeric(df[col], errors='coerce')
                df['date'] = pd.to_datetime(df['date'])
                df = df.dropna(subset=['date', 'open', 'high', 'low', 'close', 'volume'])
                df['symbol'] = symbol
                
                # 排序
                df = df.sort_values('date').reset_index(drop=True)
                
                # 缓存
                self._save_cache(df, cache_key, start_date, end_date)
                logger.info(f"Baostock: {symbol} 下载完成 ({len(df)} 行)")
                return df
                
            finally:
                bs.logout()
                
        except ImportError:
            logger.error("Baostock 未安装，请运行: pip3 install baostock")
            return None
        except Exception as e:
            logger.warning(f"Baostock: {symbol} 下载失败: {e}")
            return None

class AKShareFetcher(BaseFetcher):
    """A股ETF/个股数据源（AKShare）+ 延迟防封"""
    def fetch(self, symbol: str, start_date: str, end_date: str, **kwargs) -> Optional[pd.DataFrame]:
        try:
            import akshare as ak
            import time
            # 先查缓存
            cached = self._load_cache(symbol, start_date, end_date)
            if cached is not None:
                return cached

            logger.info(f"AKShare: 下载 {symbol} ({start_date} ~ {end_date})")
            code = symbol.split('.')[0] if '.' in symbol else symbol
            
            # 重试机制
            max_retries = 3
            df = None
            for attempt in range(max_retries):
                try:
                    # 先尝试 ETF 接口
                    df = ak.fund_etf_hist_em(symbol=code, period="daily")
                    if df is None or len(df) == 0:
                        # 备选：个股接口
                        df = ak.stock_zh_a_hist(symbol=code, period="daily")
                    
                    if df is not None and len(df) > 0:
                        break
                    else:
                        logger.warning(f"AKShare: {symbol} 第{attempt+1}次尝试无数据")
                except Exception as e:
                    logger.warning(f"AKShare: {symbol} 第{attempt+1}次失败: {e}")
                
                if attempt < max_retries - 1:
                    time.sleep(2)  # 等待后重试
            
            if df is None or len(df) == 0:
                logger.warning(f"AKShare: {symbol} 无数据")
                return None

            # 标准化列名
            rename_map = {
                '日期': 'date', '开盘': 'open', '收盘': 'close',
                '最高': 'high', '最低': 'low', '成交量': 'volume',
                '成交额': 'amount', '振幅': 'amplitude',
                '涨跌幅': 'pct_change', '涨跌额': 'change', '换手率': 'turnover'
            }
            df.rename(columns={k: v for k, v in rename_map.items() if k in df.columns}, inplace=True)

            # 确保必要列存在
            required = ['date', 'open', 'high', 'low', 'close', 'volume']
            if not all(col in df.columns for col in required):
                logger.warning(f"AKShare: {symbol} 缺少必要列")
                return None

            df['date'] = pd.to_datetime(df['date'])
            df = df[(df['date'] >= pd.to_datetime(start_date)) & (df['date'] <= pd.to_datetime(end_date))].copy()
            df['symbol'] = symbol

            # 缓存
            self._save_cache(df, symbol, start_date, end_date)
            logger.info(f"AKShare: {symbol} 下载完成 ({len(df)} 行)")
            
            # 礼貌性延迟，避免被封
            time.sleep(1)
            return df

        except ImportError:
            logger.error("AKShare 未安装，请运行: pip3 install akshare")
            return None
        except Exception as e:
            logger.warning(f"AKShare: {symbol} 下载失败: {e}")
            return None

class YFinanceFetcher(BaseFetcher):
    """美股/通用数据源（yfinance）"""
    def fetch(self, symbol: str, start_date: str, end_date: str, **kwargs) -> Optional[pd.DataFrame]:
        try:
            import yfinance as yf
            # 查缓存
            cached = self._load_cache(symbol, start_date, end_date)
            if cached is not None:
                return cached

            logger.info(f"yfinance: 下载 {symbol} ({start_date} ~ {end_date})")
            ticker = yf.Ticker(symbol)
            df = ticker.history(start=pd.to_datetime(start_date), end=pd.to_datetime(end_date), progress=False)

            if df is None or len(df) == 0:
                logger.warning(f"yfinance: {symbol} 无数据")
                return None

            # 重置索引并标准化
            df = df.reset_index()
            df.rename(columns={
                'Date': 'date', 'Open': 'open', 'High': 'high',
                'Low': 'low', 'Close': 'close', 'Volume': 'volume'
            }, inplace=True)

            # 计算额外列
            df['pct_change'] = df['close'].pct_change() * 100
            df['change'] = df['close'].diff()

            df['date'] = pd.to_datetime(df['date'])
            df['symbol'] = symbol

            # 缓存
            self._save_cache(df, symbol, start_date, end_date)
            logger.info(f"yfinance: {symbol} 下载完成 ({len(df)} 行)")
            return df

        except ImportError:
            logger.error("yfinance 未安装，请运行: pip3 install yfinance")
            return None
        except Exception as e:
            logger.warning(f"yfinance: {symbol} 下载失败: {e}")
            return None

class CCXTFetcher(BaseFetcher):
    """加密货币数据源（CCXT）"""
    def fetch(self, symbol: str, start_date: str, end_date: str, **kwargs) -> Optional[pd.DataFrame]:
        try:
            import ccxt
            # 查缓存
            cached = self._load_cache(symbol, start_date, end_date)
            if cached is not None:
                return cached

            logger.info(f"CCXT: 下载 {symbol} ({start_date} ~ {end_date})")
            exchange = ccxt.binance()  # 默认币安，可配置
            since = exchange.parse8601(f"{start_date}T00:00:00Z")
            until = exchange.parse8601(f"{end_date}T23:59:59Z")

            ohlcv = exchange.fetch_ohlcv(symbol, '1d', since=since, limit=1000)
            if not ohlcv:
                logger.warning(f"CCXT: {symbol} 无数据")
                return None

            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['date'] = pd.to_datetime(df['timestamp'], unit='ms')
            df = df[df['date'] <= pd.to_datetime(end_date)]
            df['pct_change'] = df['close'].pct_change() * 100
            df['change'] = df['close'].diff()
            df['symbol'] = symbol
            df = df.drop(columns=['timestamp'])

            # 缓存
            self._save_cache(df, symbol, start_date, end_date)
            logger.info(f"CCXT: {symbol} 下载完成 ({len(df)} 行)")
            return df

        except ImportError:
            logger.error("ccxt 未安装，请运行: pip3 install ccxt")
            return None
        except Exception as e:
            logger.warning(f"CCXT: {symbol} 下载失败: {e}")
            return None

class MockFetcher(BaseFetcher):
    """模拟数据生成器（当所有真实源失败时使用）"""
    def fetch(self, symbol: str, start_date: str, end_date: str, **kwargs) -> Optional[pd.DataFrame]:
        try:
            start = pd.to_datetime(start_date)
            end = pd.to_datetime(end_date)
            days = (end - start).days
            if days <= 0:
                return None
            # 生成日期序列（仅交易日，约 252天/年）
            dates = pd.date_range(start=start, end=end, freq='B')  # Business days
            n = len(dates)

            # 根据 symbol 生成不同特性的数据
            if 'BTC' in symbol.upper():
                # 加密货币：高波动
                initial_price = 45000.0
                volatility = 0.025
            elif symbol in ['SPY', 'QQQ', 'DIA']:
                initial_price = 400.0
                volatility = 0.010
            else:  # A股ETF
                initial_price = 3.0
                volatility = 0.015

            # 几何布朗运动模拟
            returns = np.random.normal(loc=0.0002, scale=volatility, size=n)
            prices = initial_price * np.exp(np.cumsum(returns))
            prices[0] = initial_price

            # 生成 OHLC
            df = pd.DataFrame({
                'date': dates,
                'open': prices * (1 + np.random.uniform(-0.005, 0.005, n)),
                'high': prices * (1 + np.abs(np.random.normal(0, 0.01, n))),
                'low': prices * (1 - np.abs(np.random.normal(0, 0.01, n))),
                'close': prices,
                'volume': np.random.randint(1000000, 10000000, n),
                'pct_change': np.nan,
                'change': np.nan
            })
            df['pct_change'] = df['close'].pct_change() * 100
            df['change'] = df['close'].diff()
            df['symbol'] = symbol

            logger.info(f"Mock: 生成 {symbol} 模拟数据 ({n} 行)")
            return df

        except Exception as e:
            logger.error(f"Mock 数据生成失败: {e}")
            return None

class DataFetcher:
    """统一数据获取入口"""
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.cache_dir = config.get('data_cache', 'data/cache')
        os.makedirs(self.cache_dir, exist_ok=True)

        # 初始化各数据源
        self.fetchers = {
            'baostock': BaostockFetcher(self.cache_dir),
            'akshare': AKShareFetcher(self.cache_dir),
            'yfinance': YFinanceFetcher(self.cache_dir),
            'ccxt': CCXTFetcher(self.cache_dir),
            'mock': MockFetcher(self.cache_dir)
        }

    def fetch(self, symbol: str, start_date: str, end_date: str, source_priority: list = None) -> Optional[pd.DataFrame]:
        """
        获取数据，按优先级尝试多个源
        """
        # 推断市场类型，选择数据源优先级
        if source_priority is None:
            source_priority = self._infer_sources(symbol)

        logger.info(f"开始下载 {symbol}，使用数据源优先级: {source_priority}")

        for source in source_priority:
            fetcher = self.fetchers.get(source)
            if fetcher is None:
                logger.warning(f"数据源 {source} 不存在，跳过")
                continue

            # 准备参数
            fetch_kwargs = {}
            if source == 'baostock':
                # Baostock 支持分钟级和复权参数，可以从 config 或 kwargs 传入
                fetch_kwargs['freq'] = 'd'  # 默认日线
                fetch_kwargs['adjust'] = '2'  # 默认前复权

            df = fetcher.fetch(symbol, start_date, end_date, **fetch_kwargs)
            if df is not None and len(df) > 0:
                logger.info(f"✅ {symbol} 下载成功（数据源: {source}）")
                return df
            else:
                logger.warning(f"❌ {source} 失败，尝试下一个...")

        logger.error(f"所有数据源均失败: {symbol}")
        return None

    def _infer_sources(self, symbol: str) -> list:
        """根据symbol推断市场类型，返回数据源优先级"""
        # A股
        if symbol.endswith('.SH') or symbol.endswith('.SZ') or (symbol.isdigit() and len(symbol) == 6):
            return self.config.get('data_sources', {}).get('a_share', ['baostock', 'akshare', 'yfinance', 'mock'])
        # 加密货币（包含 "/"）
        if '/' in symbol:
            return self.config.get('data_sources', {}).get('crypto', ['ccxt', 'mock'])
        # 默认为美股ETF
        return self.config.get('data_sources', {}).get('us_etf', ['yfinance', 'mock'])