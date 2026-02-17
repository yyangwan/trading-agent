#!/usr/bin/env python3
"""
分批数据更新脚本
避免Tushare API频率限制
"""
import sys
import os
import yaml
import logging
import time
from datetime import datetime

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.data_provider_full import FullDataProvider

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('logs/batch_update.log', encoding='utf-8')
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


def get_total_batches(total_stocks=5484, batch_size=500):
    """计算需要多少批次"""
    return (total_stocks + batch_size - 1) // batch_size


def update_batch(batch_num=1, batch_size=500):
    """
    更新指定批次的数据

    Args:
        batch_num: 批次编号（从1开始）
        batch_size: 每批股票数量
    """
    logger.info("=" * 60)
    logger.info(f"开始第 {batch_num} 批数据更新")
    logger.info("=" * 60)

    config = load_config()
    provider = FullDataProvider(config.get('data_sources', {}))

    # 获取股票列表
    stock_list_df = provider.get_stock_list()

    if stock_list_df.empty:
        logger.error("获取股票列表失败")
        return False

    # 计算本批次的股票范围
    all_stocks = stock_list_df['ts_code'].tolist()
    total_stocks = len(all_stocks)
    total_batches = get_total_batches(total_stocks, batch_size)

    start_idx = (batch_num - 1) * batch_size
    end_idx = min(start_idx + batch_size, total_stocks)

    batch_stocks = all_stocks[start_idx:end_idx]

    logger.info(f"批次 {batch_num}/{total_batches}")
    logger.info(f"股票范围: {start_idx+1}-{end_idx} (共 {len(batch_stocks)} 只)")

    # 获取数据
    results = provider.get_all_stocks_data(
        stock_list=batch_stocks,
        progress_callback=lambda current, total, code: logger.info(f"进度: {current}/{total} - {code}")
    )

    # 保存数据
    if results:
        provider.save_to_csv(results, 'data/stock_data/csv')
        logger.info(f"✓ 第 {batch_num} 批完成：{len(results)} 只股票")

        # 保存进度
        save_progress(batch_num, total_batches)
        return True
    else:
        logger.error(f"✗ 第 {batch_num} 批失败")
        return False


def save_progress(current_batch, total_batches):
    """保存进度"""
    progress_file = 'data/update_progress.json'
    try:
        import json
        with open(progress_file, 'w') as f:
            json.dump({
                'current_batch': current_batch,
                'total_batches': total_batches,
                'updated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'status': 'in_progress'
            }, f)
    except Exception as e:
        logger.error(f"保存进度失败: {e}")


def load_progress():
    """加载进度"""
    progress_file = 'data/update_progress.json'
    try:
        import json
        if os.path.exists(progress_file):
            with open(progress_file, 'r') as f:
                return json.load(f)
    except Exception as e:
        logger.error(f"加载进度失败: {e}")

    return None


def update_all_batches(batch_size=500, wait_minutes=60):
    """
    自动更新所有批次

    Args:
        batch_size: 每批股票数量
        wait_minutes: 批次之间等待时间（分钟）
    """
    config = load_config()
    provider = FullDataProvider(config.get('data_sources', {}))

    # 获取股票列表
    stock_list_df = provider.get_stock_list()

    if stock_list_df.empty:
        logger.error("获取股票列表失败")
        return

    total_stocks = len(stock_list_df['ts_code'].tolist())
    total_batches = get_total_batches(total_stocks, batch_size)

    logger.info("=" * 60)
    logger.info(f"分批数据更新：共 {total_stocks} 只股票，分 {total_batches} 批")
    logger.info(f"每批: {batch_size} 只，间隔: {wait_minutes} 分钟")
    logger.info(f"预计总时间: {total_batches * wait_minutes} 分钟（约 {total_batches * wait_minutes // 60} 小时）")
    logger.info("=" * 60)

    # 检查之前的进度
    progress = load_progress()
    start_batch = 1
    if progress and progress.get('status') == 'in_progress':
        start_batch = progress.get('current_batch', 1) + 1
        logger.info(f"继续之前的进度，从第 {start_batch} 批开始")

    # 逐批更新
    for batch_num in range(start_batch, total_batches + 1):
        logger.info(f"\n{'=' * 60}")
        logger.info(f"批次 {batch_num}/{total_batches}")
        logger.info(f"{'=' * 60}")

        success = update_batch(batch_num, batch_size)

        if not success:
            logger.error(f"第 {batch_num} 批失败，停止更新")
            break

        # 如果不是最后一批，等待一段时间
        if batch_num < total_batches:
            logger.info(f"等待 {wait_minutes} 分钟后继续下一批...")
            logger.info(f"预计下次开始时间: {datetime.now().strftime('%H:%M')}")
            time.sleep(wait_minutes * 60)

    # 全部完成
    logger.info("=" * 60)
    logger.info("✓ 全部分批更新完成！")
    logger.info("=" * 60)

    # 更新进度状态
    progress_file = 'data/update_progress.json'
    try:
        import json
        with open(progress_file, 'w') as f:
            json.dump({
                'current_batch': total_batches,
                'total_batches': total_batches,
                'updated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'status': 'completed'
            }, f)
    except Exception as e:
        logger.error(f"保存进度失败: {e}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='分批数据更新工具')
    parser.add_argument('--batch', type=int, help='指定批次号（1-N）')
    parser.add_argument('--batch-size', type=int, default=500, help='每批股票数量')
    parser.add_argument('--wait', type=int, default=60, help='批次间隔时间（分钟）')
    parser.add_argument('--all', action='store_true', help='自动更新所有批次')
    parser.add_argument('--test', action='store_true', help='测试模式（小批量）')

    args = parser.parse_args()

    try:
        if args.test:
            logger.info("测试模式：小批量快速测试")
            update_batch(batch_num=1, batch_size=50)

        elif args.batch:
            logger.info(f"手动更新批次: {args.batch}")
            update_batch(args.batch, args.batch_size)

        elif args.all:
            logger.info("自动更新所有批次")
            update_all_batches(args.batch_size, args.wait)

        else:
            parser.print_help()

    except Exception as e:
        logger.error(f"更新失败: {e}")
        sys.exit(1)
