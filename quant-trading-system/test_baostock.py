#!/usr/bin/env python3
"""测试 Baostock 下载个股数据"""
import baostock as bs
import pandas as pd
import sys

def test_stock(symbol, start, end):
    """测试单只股票"""
    # 转换格式
    if '.' in symbol:
        market = symbol.split('.')[-1].upper()
        code = symbol.split('.')[0]
        bs_symbol = f"{market}.{code}"  # 保持 baostock 格式
    else:
        bs_symbol = f"sh.{symbol}" if symbol.startswith('6') else f"sz.{symbol}"

    print(f"\n测试: {symbol} -> {bs_symbol}")
    print("="*50)

    lg = bs.login()
    if lg.error_code != '0':
        print(f"登录失败: {lg.error_msg}")
        return None

    try:
        rs = bs.query_history_k_data_plus(
            code=bs_symbol,
            fields="date,open,high,low,close,volume,amount,pctChg",
            start_date=start,
            end_date=end,
            frequency="d",
            adjustflag="2"  # 前复权
        )

        if rs is None:
            print("❌ rs is None")
            return None

        print(f"error_code: {rs.error_code}, msg: {rs.error_msg}")

        if rs.error_code != '0':
            print(f"❌ 查询失败: {rs.error_msg}")
            return None

        data = []
        while rs.next():
            row = rs.get_row_data()
            data.append(row)

        if not data:
            print("❌ 无数据返回")
            return None

        print(f"✅ 返回 {len(data)} 行数据")
        df = pd.DataFrame(data, columns=['date','open','high','low','close','volume','amount','pct_change'])
        print("\n前5行:")
        print(df.head())
        return df

    except Exception as e:
        print(f"❌ 异常: {e}")
        import traceback
        traceback.print_exc()
        return None
    finally:
        bs.logout()

if __name__ == "__main__":
    # 测试清单
    tests = [
        ("600519.SH", "2024-01-01", "2024-12-31", "贵州茅台"),
        ("000858.SZ", "2024-01-01", "2024-12-31", "五粮液"),
        ("601318.SH", "2024-01-01", "2024-12-31", "中国平安"),
        ("300750.SZ", "2024-01-01", "2024-12-31", "宁德时代"),
        ("sh.000300", "2024-01-01", "2024-12-31", "沪深300指数"),
    ]

    results = []
    for symbol, start, end, name in tests:
        print(f"\n{'='*60}")
        print(f"测试标的: {name} ({symbol})")
        df = test_stock(symbol, start, end)
        if df is not None:
            results.append((symbol, name, len(df)))
            print(f"✅ 成功: {len(df)} 行")
        else:
            print(f"❌ 失败")

    print("\n" + "="*60)
    print("测试总结:")
    for symbol, name, count in results:
        print(f"  ✅ {name} ({symbol}): {count} 行")
