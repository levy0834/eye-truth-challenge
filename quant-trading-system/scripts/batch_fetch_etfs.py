#!/usr/bin/env python3
"""
批量下载核心ETF数据（20年日线）
支持断点续传、延迟控制、重试机制
"""
import sys
import time
import yaml
from pathlib import Path
from datetime import datetime

sys.path.insert(0, '.')
from src.data.fetchers import DataFetcher

def load_etf_list():
    """加载ETF列表"""
    config_path = Path('config/etf_list.yaml')
    if not config_path.exists():
        print(f"❌ 找不到ETF列表文件: {config_path}")
        return []
    
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    etfs = config.get('etf_list', [])
    print(f"✅ 加载ETF列表: {len(etfs)} 只")
    return etfs

def already_downloaded(symbol: str) -> bool:
    """检查是否已下载"""
    # 检查 raw 目录
    raw_dir = Path('data/raw/a_share')
    safe_name = symbol.replace('.', '_')
    csv_file = raw_dir / f"{safe_name}.csv"
    return csv_file.exists()

def batch_fetch(start_date="2006-01-01", end_date="2025-12-31", delay=1.5):
    """批量下载所有ETF"""
    etfs = load_etf_list()
    if not etfs:
        return
    
    # 加载配置并创建fetcher
    with open('config/settings.yaml', 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    fetcher = DataFetcher(config)
    
    total = len(etfs)
    success = []
    failed = []
    skipped = []
    
    print(f"\n开始批量下载 (共{total}只ETF，时间范围{start_date}~{end_date})")
    print("="*60)
    
    for idx, etf in enumerate(etfs, 1):
        symbol = f"{etf['code']}.{etf['market']}"
        name = etf['name']
        
        # 检查是否已下载
        if already_downloaded(symbol):
            print(f"[{idx:2d}/{total}] ✅ 已存在: {symbol} - {name}")
            skipped.append(symbol)
            continue
        
        print(f"[{idx:2d}/{total}] 下载中: {symbol} - {name}")
        
        try:
            df = fetcher.fetch(symbol, start_date, end_date, source_priority=['akshare', 'mock'])
            if df is not None and len(df) > 0:
                # 手动保存到正确位置（fetcher返回的已缓存，但确保在raw目录）
                raw_dir = Path('data/raw/a_share')
                raw_dir.mkdir(parents=True, exist_ok=True)
                safe_name = symbol.replace('.', '_')
                out_file = raw_dir / f"{safe_name}.csv"
                if not out_file.exists():
                    df.to_csv(out_file, index=False, encoding='utf-8-sig')
                print(f"        ✅ 成功: {len(df)} 行")
                success.append(symbol)
            else:
                print(f"        ❌ 失败: 无数据")
                failed.append(symbol)
        except Exception as e:
            print(f"        ❌ 失败: {e}")
            failed.append(symbol)
        
        # 礼貌性延迟，避免被封
        if idx < total:  # 最后一个不用等
            time.sleep(delay)
    
    # 输出报告
    print("\n" + "="*60)
    print("批量下载完成！")
    print(f"  总计: {total}")
    print(f"  成功: {len(success)}")
    print(f"  跳过: {len(skipped)} (已存在)")
    print(f"  失败: {len(failed)}")
    
    if failed:
        print("\n失败的标的:")
        for sym in failed:
            print(f"  - {sym}")
    
    # 保存结果
    report = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "total": total,
        "success": success,
        "skipped": skipped,
        "failed": failed,
        "start_date": start_date,
        "end_date": end_date
    }
    report_file = Path('logs/batch_fetch_report.yaml')
    report_file.parent.mkdir(exist_ok=True)
    with open(report_file, 'w', encoding='utf-8') as f:
        yaml.dump(report, f, allow_unicode=True, sort_keys=False)
    print(f"\n详细报告已保存: {report_file}")

if __name__ == "__main__":
    batch_fetch()