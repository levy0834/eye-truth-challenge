#!/usr/bin/env python3
"""
获取沪深300成分股列表并批量下载20年数据
"""
import sys
import time
import yaml
import pandas as pd
from datetime import datetime
from pathlib import Path

sys.path.insert(0, '.')
from src.data.fetchers import DataFetcher

def get_hs300_components():
    """获取沪深300成分股列表（优先AKShare）"""
    # 1. 尝试AKShare
    components = get_hs300_components_akshare()
    if components:
        return components

    # 2. 尝试本地静态列表
    list_file = Path('data/hs300_components.txt')
    if list_file.exists():
        with open(list_file, 'r') as f:
            codes = [line.strip() for line in f if line.strip()]
        print(f"✅ 从本地加载 {len(codes)} 只成分股")
        return codes

    print("❌ 无法获取沪深300成分股列表")
    return []

def get_hs300_components():
    """获取沪深300成分股列表（优先AKShare）"""
    comps = get_hs300_components_akshare()
    if comps:
        return comps
    # 备用：本地静态文件
    list_file = Path('data/hs300_components.txt')
    if list_file.exists():
        with open(list_file, 'r') as f:
            codes = [line.strip() for line in f if line.strip()]
        print(f"✅ 从本地加载 {len(codes)} 只成分股")
        return codes
    print("❌ 无法获取沪深300成分股列表")
    return []

def get_hs300_components_akshare():
    """通过AKShare获取沪深300成分股列表"""
    import akshare as ak
    print("正在从AKShare拉取沪深300成分股...")
    try:
        df = ak.index_stock_cons(symbol="000300")
        if df is not None and len(df) > 0:
            # 提取股票代码
            code_col = '品种代码'
            if code_col not in df.columns:
                print(f"❌ 未找到代码列，可用列: {df.columns.tolist()}")
                return []
            codes = df[code_col].astype(str).tolist()
            # 补全市场后缀
            components = []
            for code in codes:
                # 补全为 baostock 格式
                if code.startswith('6'):
                    components.append(f"{code}.SH")
                elif code.startswith('0') or code.startswith('3'):
                    components.append(f"{code}.SZ")
                else:
                    components.append(code)  # 其他格式保留
            print(f"✅ 从AKShare获取到 {len(components)} 只成分股")
            return components
        else:
            print("AKShare返回空数据")
            return []
    except Exception as e:
        print(f"AKShare异常: {e}")
        return []

def ensure_baostock_fetcher_ready():
    """确保BaostockFetcher正确配置"""
    # 检查是否存在 BaostockFetcher 类，不存在则添加
    import importlib.util
    spec = importlib.util.spec_from_file_location("fetchers", "src/data/fetchers.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    # 如果BaostockFetcher不在DataFetcher.fetchers中，动态添加
    with open('config/settings.yaml', 'r') as f:
        config = yaml.safe_load(f)

    # 核心：确保baostock在首位（如果可用）
    if 'baostock' not in config.get('data_sources', {}).get('a_share', []):
        print("⚠️ 配置中未启用baostock，正在更新...")
        config['data_sources']['a_share'] = ['baostock', 'akshare', 'yfinance', 'mock']
        with open('config/settings.yaml', 'w', encoding='utf-8') as f:
            yaml.dump(config, f, allow_unicode=True)

    return config

def batch_download_components(components, start_date="2006-01-01", end_date="2025-12-31", delay=1.0):
    """批量下载成分股数据"""
    config = ensure_baostock_fetcher_ready()
    fetcher = DataFetcher(config)

    total = len(components)
    success = []
    failed = []
    stats = []

    print(f"\n开始批量下载沪深300成分股 ({start_date}~{end_date})")
    print("="*60)

    for idx, code in enumerate(components, 1):
        # 标准化为带市场后缀
        symbol = code if '.' in code else f"{code}.SH" if code.startswith('6') else f"{code}.SZ"

        print(f"[{idx:3d}/{total}] 下载中: {symbol}")

        try:
            df = fetcher.fetch(symbol, start_date, end_date, source_priority=['baostock', 'mock'])
            if df is not None and len(df) > 0:
                # 保存到原始数据目录
                raw_dir = Path('data/raw/a_share')
                raw_dir.mkdir(parents=True, exist_ok=True)
                safe_name = symbol.replace('.', '_')
                out_file = raw_dir / f"{safe_name}.csv"
                df.to_csv(out_file, index=False, encoding='utf-8-sig')

                # 统计信息
                stats.append({
                    'symbol': symbol,
                    'rows': len(df),
                    'start': df['date'].min().strftime('%Y-%m-%d'),
                    'end': df['date'].max().strftime('%Y-%m-%d'),
                    'missing': df[['open','high','low','close','volume']].isnull().sum().sum()
                })

                print(f"        ✅ 成功: {len(df)} 行 ({df['date'].min()}~{df['date'].max()})")
                success.append(symbol)
            else:
                print(f"        ❌ 失败: 无数据")
                failed.append(symbol)
        except Exception as e:
            print(f"        ❌ 失败: {e}")
            failed.append(symbol)

        # 礼貌延迟
        time.sleep(delay)

    # 生成报告
    print("\n" + "="*60)
    print("批量下载完成！")
    print(f"  总计: {total}")
    print(f"  成功: {len(success)}")
    print(f"  失败: {len(failed)}")

    if failed:
        print("\n失败列表 (前10):")
        for s in failed[:10]:
            print(f"  - {s}")

    # 保存详细统计
    if stats:
        report_df = pd.DataFrame(stats)
        report_file = Path('data/hs300_data_quality_report.csv')
        report_df.to_csv(report_file, index=False, encoding='utf-8-sig')
        print(f"\n📊 数据质量报告: {report_file}")

        # 汇总
        print("\n📈 汇总统计:")
        print(f"  平均每只股票数据行数: {report_df['rows'].mean():.0f}")
        print(f"  最早起始日期: {report_df['start'].min()}")
        print(f"  最晚结束日期: {report_df['end'].max()}")
        print(f"  总缺失值: {report_df['missing'].sum()}")

    # 保存成分股列表
    components_file = Path('data/hs300_components.txt')
    with open(components_file, 'w') as f:
        for code in components:
            f.write(f"{code}\n")
    print(f"\n📋 成分股列表已保存: {components_file}")

    return success, failed

if __name__ == "__main__":
    print("步骤1: 获取沪深300成分股列表")
    components = get_hs300_components()

    if not components:
        print("❌ 未获取到成分股，退出")
        sys.exit(1)

    print(f"\n步骤2: 开始批量下载 ({len(components)} 只)")
    success, failed = batch_download_components(components)

    print("\n" + "="*60)
    print("任务结束。")
