#!/usr/bin/env python3
"""
测试akshare数据获取
"""
import akshare as ak
import pandas as pd

print("测试akshare获取单只股票数据...")

try:
    # 测试获取平安银行（000001.SZ）
    symbol = "sz000001"
    
    # 获取历史数据
    df = ak.stock_zh_a_hist(symbol=symbol, period="daily",
                            start_date="20250801", end_date="20260217", adjust="qfq")
    
    if df.empty:
        print("❌ 返回数据为空")
        print("可能的原因：")
        print("1. 日期格式问题")
        print("2. akshare API变更")
        print("3. 网络问题")
    else:
        print(f"✓ 成功获取数据: {len(df)} 条")
        print(df.head())
        print(df.columns.tolist())

except Exception as e:
    print(f"❌ 获取失败: {e}")
    import traceback
    traceback.print_exc()
