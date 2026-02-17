#!/usr/bin/env python3
"""
智能数据管理器 - 修复版
"""
import sys
import os
import pickle
import yaml
import logging
import pandas as pd
from datetime import datetime, timedelta

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def load_config():
    """加载配置"""
    try:
        with open('configs/system_config.yaml', 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    except:
        return {'data_sources': {'primary': {'token': ''}}}


def get_cached_stock_list():
    """获取股票列表（优先缓存）"""
    cache_file = 'data/cache/stock_list.pkl'

    # 尝试使用上次保存的股票列表
    if os.path.exists(cache_file):
        try:
            with open(cache_file, 'rb') as f:
                df = pickle.load(f)
            logger.info(f"从缓存读取股票列表: {len(df)} 只")
            return df
        except Exception as e:
            logger.error(f"读取缓存失败: {e}")

    # 缓存不存在，使用测试数据的股票列表
    logger.info("使用测试股票列表（18只）")
    test_stocks = [
        '000001.SZ', '000002.SZ', '000004.SZ', '000006.SZ', '000007.SZ',
        '000008.SZ', '000009.SZ', '000010.SZ', '000011.SZ', '000012.SZ',
        '000063.SZ', '000858.SZ', '002415.SZ', '300750.SZ', '600000.SH',
        '600036.SH', '601318.SH', '688981.SH'
    ]

    # 创建DataFrame
    df = pd.DataFrame({
        'ts_code': test_stocks,
        'name': test_stocks,
        'list_status': 'L'
    })

    # 保存缓存
    os.makedirs('data/cache', exist_ok=True)
    with open(cache_file, 'wb') as f:
        pickle.dump(df, f)

    logger.info(f"✓ 创建测试股票列表: {len(df)} 只（已缓存）")
    return df


def generate_incremental_batches():
    """生成增量批次"""
    cache_file = 'data/cache/stock_list.pkl'

    if not os.path.exists(cache_file):
        logger.error("请先运行: python3 manage_data.py --init")
        return [], []

    # 读取股票列表
    with open(cache_file, 'rb') as f:
        stock_df = pickle.load(f)

    all_stocks = stock_df['ts_code'].tolist()

    # 检查已有的数据
    csv_dir = 'data/stock_data/csv'
    existing_stocks = set()

    if os.path.exists(csv_dir):
        for f in os.listdir(csv_dir):
            if f.endswith('.csv'):
                existing_stocks.add(f.replace('.ecsv', ''))

    # 找出需要获取的股票
    missing_stocks = [s for s in all_stocks if s not in existing_stocks]

    logger.info(f"总股票数: {len(all_stocks)}")
    logger.info(f"已有数据: {len(existing_stocks)} 只")
    logger.info(f"需要获取: {len(missing_stocks)} 只")

    return missing_stocks, list(existing_stocks)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='智能数据管理')
    parser.add_argument('--status', action='store_true', help='查看数据状态')
    parser.add_argument('--update', action='store_true', help='更新缺失数据')

    args = parser.parse_args()

    if args.status:
        print("=" * 60)
        print("数据状态")
        print("=" * 60)

        # 检查缓存
        cache_file = 'data/cache/stock_list.pkl'
        if os.path.exists(cache_file):
            with open(cache_file, 'rb') as f:
                df = pickle.load(f)
            print(f"✓ 股票列表缓存: {len(df)} 只")

        # 检查本地数据
        csv_dir = 'data/stock_data/csv'
        if os.path.exists(csv_dir):
            files = [f for f in os.listdir(csv_dir) if f.endswith('.csv')]
            print(f"✓ 本地数据: {len(files)} 只")

            if files:
                size = sum(os.path.getsize(os.path.join(csv_dir, f)) for f in files) / (1024*1024)
                print(f"✓ 数据大小: {size:.2f} MB")

    elif args.update:
        print("=" * 60)
        print("更新缺失数据")
        print("=" * 60)

        missing_stocks, existing = generate_incremental_batches()

        if missing_stocks:
            print(f"需要更新: {len(missing_stocks)} 只")
            print(f"已有: {len(existing)} 只")

            # 确认是否继续
            print(f"\n由于Tushare API限制，建议：")
            print(f"1. 先用现有{len(existing)}只股票测试系统")
            print(f"2. 稍后每小时更新一批数据")
            print(f"3. 或升级Tushare专业版（¥300/年）")

        else:
            print("✓ 数据已完整！")

    else:
        parser.print_help()
