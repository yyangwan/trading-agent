#!/usr/bin/env python3
"""
获取完整A股数据 - 智能版
使用akshare作为备选数据源（免费无限制）
"""
import sys
import os
import pandas as pd
import logging
from datetime import datetime, timedelta
import time

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def get_stock_list_akshare():
    """使用akshare获取股票列表（免费无限制）"""
    try:
        import akshare as ak

        logger.info("使用akshare获取股票列表...")

        # 获取A股列表
        df = ak.stock_zh_a_spot_em()

        # 转换为标准格式
        stock_list = []
        for _, row in df.iterrows():
            code = row['代码']
            name = row['名称']

            # 转换为tushare格式
            if 'SH' in code or '60' in code[:2]:
                ts_code = code + '.SH'
            else:
                ts_code = code + '.SZ'

            stock_list.append({
                'ts_code': ts_code,
                'name': name,
                'list_status': 'L'
            })

        df_result = pd.DataFrame(stock_list)

        # 保存缓存
        os.makedirs('data/cache', exist_ok=True)
        df_result.to_pickle('data/cache/stock_list.pkl')

        logger.info(f"✓ 获取股票列表成功: {len(df_result)} 只")
        return df_result

    except ImportError:
        logger.error("akshare未安装，正在安装...")
        os.system("pip install akshare -q")
        import akshare as ak
        return get_stock_list_akshare()
    except Exception as e:
        logger.error(f"获取股票列表失败: {e}")
        return pd.DataFrame()


def get_stock_data_akshare(ts_code, period=180):
    """使用akshare获取单只股票数据"""
    try:
        import akshare as ak

        # 提取代码
        code = ts_code.replace('.SH', '').replace('.SZ', '')

        # 确定市场
        symbol = code
        if 'SH' in ts_code or '60' in code[:2]:
            symbol = f"sh{code}"
        else:
            symbol = f"sz{code}"

        # 获取历史数据
        end_date = datetime.now().strftime('%Y%m%d')
        start_date = (datetime.now() - timedelta(days=period)).strftime('%Y%m%d')

        df = ak.stock_zh_a_hist(symbol=symbol, period="daily",
                                start_date=start_date, end_date=end_date, adjust="qfq")

        if df.empty:
            return None

        # 转换为标准格式
        df = df.rename(columns={
            '日期': 'date',
            '开盘': 'open',
            '收盘': 'close',
            '最高': 'high',
            '最低': 'low',
            '成交量': 'vol',
            '成交额': 'amount'
        })

        # 格式化日期
        df['date'] = df['date'].dt.strftime('%Y%m%d')

        return df

    except Exception as e:
        logger.error(f"获取{ts_code}数据失败: {e}")
        return None


def update_all_stocks(batch_size=100):
    """更新所有股票数据"""
    logger.info("=" * 60)
    logger.info("开始获取完整A股数据")
    logger.info("=" * 60)

    # 获取股票列表
    stock_df = get_stock_list_akshare()

    if stock_df.empty:
        logger.error("无法获取股票列表")
        return

    all_stocks = stock_df['ts_code'].tolist()

    # 检查已有的数据
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

    # 分批获取
    success_count = 0
    failed_count = 0

    for i, ts_code in enumerate(missing_stocks):
        try:
            logger.info(f"[{i+1}/{len(missing_stocks)}] 获取 {ts_code}")

            df = get_stock_data_akshare(ts_code)

            if df is not None and not df.empty:
                df.to_csv(f'{csv_dir}/{ts_code}.csv', index=False)
                success_count += 1
            else:
                failed_count += 1

            # 每10只股票休息一下
            if (i + 1) % 10 == 0:
                logger.info(f"进度: {i+1}/{len(missing_stocks)}, 休息2秒...")
                time.sleep(2)

            # 每100只保存进度
            if (i + 1) % 100 == 0:
                logger.info(f"✓ 已完成 {i+1} 只股票")

        except Exception as e:
            logger.error(f"处理{ts_code}失败: {e}")
            failed_count += 1
            continue

    logger.info("=" * 60)
    logger.info("数据获取完成")
    logger.info(f"成功: {success_count} 只")
    logger.info(f"失败: {failed_count} 只")
    logger.info(f"总数据: {len(existing_stocks) + success_count} 只")
    logger.info("=" * 60)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='获取完整A股数据')
    parser.add_argument('--batch-size', type=int, default=100,
                       help='每批处理的股票数量')
    parser.add_argument('--test', action='store_true',
                       help='测试模式：只获取10只股票')

    args = parser.parse_args()

    if args.test:
        logger.info("测试模式：只获取10只股票")
        # 修改batch_size为10
        args.batch_size = 10

    update_all_stocks(args.batch_size)
