#!/usr/bin/env python3
"""
智能数据提供者 - 使用本地缓存避免API限制
先用测试数据启动系统
"""
import sys
import os
import yaml
import logging
from datetime import datetime, timedelta

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def create_sample_data():
    """创建测试用的样本数据"""
    import pandas as pd
    import numpy as np

    # 创建示例股票数据
    dates = pd.date_range(end=datetime.now(), periods=180, freq='D')

    # 模拟10只股票的数据
    sample_stocks = [
        '000001.SZ', '000002.SZ', '600000.SH', '600036.SH',
        '000858.SZ', '002415.SZ', '300750.SZ', '688981.SH',
        '601318.SH', '000063.SZ'
    ]

    for ts_code in sample_stocks:
        # 生成模拟数据
        data = {
            'date': dates.strftime('%Y%m%d'),
            'open': np.random.uniform(8, 50, 180),
            'high': np.random.uniform(10, 55, 180),
            'low': np.random.uniform(7, 48, 180),
            'close': np.random.uniform(8, 50, 180),
            'vol': np.random.uniform(1000000, 50000000, 180),
            'amount': np.random.uniform(10000000, 500000000, 180)
        }

        df = pd.DataFrame(data)

        # 保存
        os.makedirs('data/stock_data/csv', exist_ok=True)
        df.to_csv(f'data/stock_data/csv/{ts_code}.csv', index=False)

    logger.info(f"已创建 {len(sample_stocks)} 只股票的测试数据")

    return sample_stocks


def update_data_daily():
    """每日数据更新（智能版本）"""
    logger.info("开始智能数据更新")

    # 检查API是否可用
    try:
        import tushare as ts
        token = load_config().get('primary', {}).get('token', '')
        pro = ts.pro_api(token)

        # 测试API
        result = pro.trade_cal(exchange='SSE', start_date='20260101', end_date='20260101')

        if result is not None and not result.empty:
            logger.info("Tushare API可用，尝试获取新数据")
            # 这里可以添加实际的更新逻辑

    except Exception as e:
        logger.warning(f"Tushare API暂时不可用: {e}")
        logger.info("使用本地缓存数据")

    # 检查本地数据
    csv_dir = 'data/stock_data/csv'
    if os.path.exists(csv_dir):
        files = [f for f in os.listdir(csv_dir) if f.endswith('.csv')]
        logger.info(f"本地数据: {len(files)} 只股票")

        # 检查最后更新时间
        if files:
            import glob
            newest = max(
                [os.path.getmtime(os.path.join(csv_dir, f)) for f in files]
            )
            last_update = datetime.fromtimestamp(newest)
            logger.info(f"最后更新: {last_update.strftime('%Y-%m-%d %H:%M:%S')}")

    return len(files) if os.path.exists(csv_dir) else 0


def load_config():
    """加载配置"""
    try:
        with open('configs/system_config.yaml', 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    except Exception as e:
        logger.error(f"加载配置失败: {e}")
        return {'primary': {'token': ''}}


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='智能数据管理工具')
    parser.add_argument('--init', action='store_true', help='初始化测试数据')
    parser.add_argument('--update', action='store_true', help='更新数据')
    parser.add_argument('--status', action='store_true', help='查看数据状态')

    args = parser.parse_args()

    try:
        if args.init:
            logger.info("=" * 60)
            logger.info("初始化测试数据")
            logger.info("=" * 60)
            stocks = create_sample_data()
            logger.info(f"✓ 已创建 {len(stocks)} 只股票的测试数据")

        elif args.update:
            logger.info("=" * 60)
            logger.info("更新数据")
            logger.info("=" * 60)
            count = update_data_daily()
            logger.info(f"✓ 当前有 {count} 只股票的数据")

        elif args.status:
            logger.info("=" * 60)
            logger.info("数据状态")
            logger.info("=" * 60)

            csv_dir = 'data/stock_data/csv'
            if os.path.exists(csv_dir):
                files = [f for f in os.listdir(csv_dir) if f.endswith('.csv')]
                total_size = sum(
                    os.path.getsize(os.path.join(csv_dir, f))
                    for f in files
                ) / (1024 * 1024)

                logger.info(f"股票数量: {len(files)}")
                logger.info(f"数据大小: {total_size:.2f} MB")

                if files:
                    newest = max(
                        [os.path.getmtime(os.path.join(csv_dir, f)) for f in files]
                    )
                    last_update = datetime.fromtimestamp(newest)
                    logger.info(f"最后更新: {last_update.strftime('%Y-%m-%d %H:%M:%S')}")

                # 显示前10只股票
                logger.info(f"前10只: {files[:10]}")
            else:
                logger.warning("暂无数据")

        else:
            parser.print_help()

    except Exception as e:
        logger.error(f"执行失败: {e}")
        sys.exit(1)
