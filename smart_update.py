#!/usr/bin/env python3
"""
智能数据管理器 - 绕过API限制
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
        return {}


def get_cached_stock_list():
    """获取缓存的股票列表"""
    cache_file = 'data/cache/stock_list.pkl'

    try:
        # 尝试从Tushare获取（如果有缓存则使用缓存）
        import tushare as ts
        token = load_config().get('data_sources', {}).get('primary', {}).get('token', '')

        if token:
            try:
                pro = ts.pro_api(token)
                df = pro.stock_basic(exchange='', list_status='L')

                if df is not None and not df.empty:
                    # 保存缓存
                    os.makedirs('data/cache', exist_ok=True)
                    with open(cache_file, 'wb') as f:
                        pickle.dump(df, f)
                    logger.info(f"✓ 从Tushare获取股票列表: {len(df)} 只（已缓存）")
                    return df
            except Exception as e:
                logger.warning(f"Tushare API受限: {e}")

        # 从缓存读取
        if os.path.exists(cache_file):
            with open(cache_file, 'rb') as f:
                df = pickle.load(f)
            logger.info(f"✓ 从缓存读取股票列表: {len(df)} 只")
            return df

        logger.error("无法获取股票列表")
        return pd.DataFrame()

    except Exception as e:
        logger.error(f"获取股票列表失败: {e}")
        return pd.DataFrame()


def generate_incremental_batches():
    """生成增量批次（使用本地已有的股票）"""
    cache_file = 'data/cache/stock_list.pkl'

    # 获取股票列表
    if os.path.exists(cache_file):
        with open(cache_file, 'rb') as f:
            stock_df = pickle.load(f)
    else:
        logger.error("请先运行测试模式创建数据: python3 manage_data.py --init")
        return []

    all_stocks = stock_df['ts_code'].tolist()

    # 检查已有的数据
    csv_dir = 'data/stock_data/csv'
    existing_stocks = set()

    if os.path.exists(csv_dir):
        for f in os.listdir(csv_dir):
            if f.endswith('.csv'):
                existing_stocks.add(f.replace('.csv', ''))

    # 找出需要获取的股票
    missing_stocks = [s for s in all_stocks if s not in existing_stocks]

    logger.info(f"总股票数: {len(all_stocks)}")
    logger.info(f"已有数据: {len(existing_stocks)}")
    logger.info(f"需要获取: {len(missing_stocks)}")

    return missing_stocks, existing_stocks


def update_missing_stocks(missing_stocks, batch_size=100):
    """更新缺失的股票数据"""
    if not missing_stocks:
        logger.info("✓ 所有股票数据已完整")
        return True

    logger.info(f"开始更新 {len(missing_stocks)} 只缺失的股票")

    import tushare as ts
    token = load_config().get('data_sources', {}).get('primary', {}).get('token', '')
    pro = ts.pro_api(token)

    success = 0
    failed = 0

    for i, ts_code in enumerate(missing_stocks):
        try:
            logger.info(f"[{i+1}/{len(missing_stocks)}] 获取 {ts_code}")

            # 获取近180天数据
            end_date = datetime.now().strftime('%Y%m%d')
            start_date = (datetime.now() - timedelta(days=180)).strftime('%Y%m%d')

            df = pro.daily(ts_code=ts_code, start_date=start_date, end_date=end_date)

            if df is not None and not df.empty:
                df = df.rename(columns={'trade_date': 'date'})
                df.to_csv(f'data/stock_data/csv/{ts_code}.csv', index=False)
                success += 1

            # 延迟避免频率限制
            if (i + 1) % 10 == 0:
                logger.info("休息10秒...")
                import time
                time.sleep(10)

        except Exception as e:
            logger.error(f"获取{ts_code}失败: {e}")
            failed += 1
            continue

    logger.info(f"✓ 更新完成：成功 {success} 只，失败 {failed} 只")
    return failed == 0


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
            update_missing_stocks(missing_stocks)

        else:
            print("✓ 数据已完整")

    else:
        parser.print_help()
