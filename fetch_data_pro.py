#!/usr/bin/env python3
"""
使用Tushare专业版获取完整A股数据
"""
import os
import pandas as pd
import logging
import yaml
from datetime import datetime, timedelta
import time

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def load_config():
    """加载配置"""
    with open('configs/system_config.yaml', 'r') as f:
        return yaml.safe_load(f)


def get_stock_list():
    """获取股票列表"""
    try:
        import tushare as ts

        config = load_config()
        token = config.get('data_sources', {}).get('primary', {}).get('token', '')

        if not token:
            logger.error("Token未配置")
            return pd.DataFrame()

        pro = ts.pro_api(token)

        logger.info("获取股票列表...")
        df = pro.stock_basic(exchange='', list_status='L')

        if df.empty:
            logger.error("股票列表为空")
            return pd.DataFrame()

        logger.info(f"✓ 获取股票列表成功: {len(df)} 只")
        return df

    except Exception as e:
        logger.error(f"获取股票列表失败: {e}")
        return pd.DataFrame()


def get_stock_data(ts_code, pro, period=180):
    """获取单只股票数据"""
    try:
        end_date = datetime.now().strftime('%Y%m%d')
        start_date = (datetime.now() - timedelta(days=period)).strftime('%Y%m%d')

        df = pro.daily(ts_code=ts_code, start_date=start_date, end_date=end_date)

        if df.empty:
            return None

        df = df.rename(columns={'trade_date': 'date'})
        return df

    except Exception as e:
        logger.debug(f"获取{ts_code}失败: {e}")
        return None


def update_all_stocks():
    """更新所有股票数据"""
    logger.info("=" * 60)
    logger.info("开始获取完整A股数据（Tushare专业版）")
    logger.info("=" * 60)

    # 获取股票列表
    stock_df = get_stock_list()
    if stock_df.empty:
        return

    all_stocks = stock_df['ts_code'].tolist()

    # 初始化tushare
    import tushare as ts
    config = load_config()
    token = config.get('data_sources', {}).get('primary', {}).get('token', '')
    pro = ts.pro_api(token)

    # 检查已有数据
    csv_dir = 'data/stock_data/csv'
    os.makedirs(csv_dir, exist_ok=True)

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

    if not missing_stocks:
        logger.info("✓ 所有股票数据已完整！")
        return

    # 开始获取
    success_count = 0
    failed_count = 0
    failed_list = []

    for i, ts_code in enumerate(missing_stocks):
        try:
            if (i + 1) % 100 == 0:
                logger.info(f"进度: {i+1}/{len(missing_stocks)}")

            df = get_stock_data(ts_code, pro)

            if df is not None and not df.empty:
                df.to_csv(f'{csv_dir}/{ts_code}.csv', index=False)
                success_count += 1
            else:
                failed_count += 1
                failed_list.append(ts_code)

            # 控制频率（专业版：每分钟1200次，约0.05秒/次）
            time.sleep(0.05)

        except Exception as e:
            logger.error(f"处理{ts_code}失败: {e}")
            failed_count += 1
            failed_list.append(ts_code)
            continue

    logger.info("=" * 60)
    logger.info("数据获取完成")
    logger.info(f"成功: {success_count} 只")
    logger.info(f"失败: {failed_count} 只")
    logger.info(f"总数据: {len(existing_stocks) + success_count} 只")

    if failed_list:
        logger.info(f"失败列表: {failed_list[:10]}...")

    logger.info("=" * 60)


if __name__ == "__main__":
    update_all_stocks()
