#!/usr/bin/env python3
"""
数据更新脚本
用于获取和更新A股股票数据
"""
import sys
import os
import yaml
import logging
from datetime import datetime

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.data_provider_full import FullDataProvider

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('logs/data_update.log', encoding='utf-8')
    ]
)

logger = logging.getLogger(__name__)


def load_config():
    """加载配置"""
    try:
        with open('configs/system_config.yaml', 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    except Exception as e:
        logger.error(f"加载配置失败: {e}")
        return {}


def update_all_data():
    """更新所有数据（首次运行或完整更新）"""
    logger.info("=" * 60)
    logger.info("开始完整数据更新")
    logger.info("=" * 60)

    config = load_config()
    provider = FullDataProvider(config.get('data_sources', {}))

    # 获取股票列表
    stock_list_df = provider.get_stock_list()

    if stock_list_df.empty:
        logger.error("获取股票列表失败，退出")
        return

    stock_count = len(stock_list_df)
    logger.info(f"共 {stock_count} 只股票需要更新")

    # 获取最近180天数据
    results = provider.get_all_stocks_data(
        stock_list=stock_list_df['ts_code'].tolist(),
        progress_callback=lambda current, total, code: logger.info(f"进度: {current}/{total} ({current*100//total}%) - {code}")
    )

    # 保存数据
    if results:
        provider.save_to_csv(results, 'data/stock_data/csv')
        logger.info(f"✓ 数据已保存：{len(results)} 只股票")
    else:
        logger.error("✗ 数据更新失败")


def update_daily_data():
    """每日增量更新"""
    logger.info("=" * 60)
    logger.info("开始每日增量更新")
    logger.info("=" * 60)

    config = load_config()
    provider = FullDataProvider(config.get('data_sources', {}))

    results = provider.update_daily_data(save_path='data/stock_data/csv')

    if results:
        provider.save_to_csv(results, 'data/stock_data/csv')
        logger.info(f"✓ 每日更新完成：{len(results)} 只股票")
    else:
        logger.warning("今日可能为非交易日或无新数据")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='A股数据更新工具')
    parser.add_argument('--mode', type=str, default='daily', choices=['daily', 'full'],
                        help='更新模式：daily(每日增量) 或 full(完整更新)')
    parser.add_argument('--test', action='store_true', help='测试模式（仅获取少量股票）')

    args = parser.parse_args()

    try:
        if args.test:
            logger.info("测试模式：仅获取前10只股票")
            config = load_config()
            provider = FullDataProvider(config.get('data_sources', {}))

            stock_list_df = provider.get_stock_list()
            if not stock_list_df.empty:
                test_stocks = stock_list_df.head(10)['ts_code'].tolist()
                logger.info(f"测试股票: {test_stocks}")

                results = provider.get_all_stocks_data(
                    stock_list=test_stocks,
                    progress_callback=lambda current, total, code: logger.info(f"进度: {current}/{total} - {code}")
                )

                if results:
                    provider.save_to_csv(results, 'data/stock_data/csv')
                    logger.info(f"✓ 测试完成：{len(results)} 只股票")

        elif args.mode == 'full':
            update_all_data()
        else:
            update_daily_data()

    except Exception as e:
        logger.error(f"更新失败: {e}")
        sys.exit(1)
