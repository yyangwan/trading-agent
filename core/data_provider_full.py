"""
完整数据提供者 - 实现真实的数据获取
支持tushare和akshare双数据源
"""
import pandas as pd
import time
import logging
from datetime import datetime, timedelta
from typing import Optional, List

logger = logging.getLogger(__name__)


class FullDataProvider:
    """完整数据提供者"""

    def __init__(self, config: dict):
        self.config = config
        self.tushare_token = None
        self.tushare_pro = None
        self._init_tushare()

    def _init_tushare(self):
        """初始化Tushare"""
        try:
            # 从配置中获取token
            primary_config = self.config.get('primary', {})
            self.tushare_token = primary_config.get('token', '')

            if not self.tushare_token or self.tushare_token == 'your_tushare_token_here':
                logger.warning("未配置Tushare token，部分功能将无法使用")
                return

            import tushare as ts
            self.tushare_pro = ts.pro_api(self.tushare_token)
            logger.info("Tushare初始化成功")

        except Exception as e:
            logger.error(f"Tushare初始化失败: {e}")

    def get_stock_list(self) -> pd.DataFrame:
        """
        获取A股全部未退市股票列表

        Returns:
            股票列表DataFrame
        """
        if not self.tushare_pro:
            logger.error("Tushare未初始化，无法获取股票列表")
            return pd.DataFrame()

        try:
            # 获取股票列表
            df = self.tushare_pro.stock_basic(
                exchange='',
                list_status='L',  # L上市 D退市 P暂停上市
                fields='ts_code,symbol,name,area,industry,list_date'
            )

            if df is not None and not df.empty:
                logger.info(f"获取到 {len(df)} 只上市股票")
                return df.sort_values('ts_code').reset_index(drop=True)
            else:
                logger.error("获取股票列表失败")
                return pd.DataFrame()

        except Exception as e:
            logger.error(f"获取股票列表失败: {e}")
            return pd.DataFrame()

    def get_stock_data(
        self,
        ts_code: str,
        start_date: str = None,
        end_date: str = None,
        period: str = 'daily'
    ) -> Optional[pd.DataFrame]:
        """
        获取单只股票历史数据

        Args:
            ts_code: 股票代码（如 000001.SZ）
            start_date: 开始日期（YYYYMMDD格式）
            end_date: 结束日期（YYYYMMDD格式）
            period: 数据周期（daily/weekly/monthly）

        Returns:
            股票数据DataFrame
        """
        if not self.tushare_pro:
            logger.error("Tushare未初始化")
            return None

        try:
            # 默认获取最近180天数据
            if not end_date:
                end_date = datetime.now().strftime('%Y%m%d')

            if not start_date:
                start_date = (datetime.now() - timedelta(days=180)).strftime('%Y%m%d')

            # 获取日线数据
            df = self.tushare_pro.daily(
                ts_code=ts_code,
                start_date=start_date,
                end_date=end_date
            )

            # 复权处理（后复权，适合真实交易）
            df_adj = self.tushare_pro.adj_factor(
                ts_code=ts_code,
                start_date=start_date,
                end_date=end_date
            )

            if df is not None and not df.empty:
                # 合并复权因子
                if df_adj is not None and not df_adj.empty:
                    df = df.merge(df_adj, on=['ts_code', 'trade_date'], how='left')

                # 重命名列
                df = df.rename(columns={
                    'trade_date': 'date',
                    'ts_code': 'ts_code'
                })

                # 按日期排序
                df = df.sort_values('date').reset_index(drop=True)

                return df

            return None

        except Exception as e:
            logger.error(f"获取{ts_code}数据失败: {e}")
            return None

    def get_all_stocks_data(
        self,
        stock_list: List[str] = None,
        start_date: str = None,
        end_date: str = None,
        save_path: str = None,
        progress_callback = None
    ) -> dict:
        """
        批量获取所有股票数据

        Args:
            stock_list: 股票代码列表（None则获取全部）
            start_date: 开始日期
            end_date: 结束日期
            save_path: 保存路径
            progress_callback: 进度回调函数

        Returns:
            结果字典 {ts_code: DataFrame}
        """
        # 获取股票列表
        if stock_list is None:
            stock_df = self.get_stock_list()
            if stock_df.empty:
                return {}
            stock_list = stock_df['ts_code'].tolist()

        logger.info(f"开始获取 {len(stock_list)} 只股票的数据")

        results = {}
        failed = []

        for i, ts_code in enumerate(stock_list):
            try:
                # 进度回调
                if progress_callback:
                    progress_callback(i + 1, len(stock_list), ts_code)

                # 延迟避免频率限制
                if i > 0 and i % 100 == 0:
                    time.sleep(1)

                # 获取数据
                df = self.get_stock_data(ts_code, start_date, end_date)

                if df is not None and not df.empty:
                    results[ts_code] = df
                else:
                    failed.append(ts_code)

            except Exception as e:
                logger.error(f"处理{ts_code}失败: {e}")
                failed.append(ts_code)
                continue

        logger.info(f"数据获取完成：成功 {len(results)} 只，失败 {len(failed)} 只")

        if failed:
            logger.warning(f"失败的股票: {failed[:10]}...")

        return results

    def update_daily_data(self, save_path: str = None):
        """
        每日更新数据

        Args:
            save_path: 数据保存路径
        """
        logger.info("开始每日数据更新")

        # 获取股票列表
        stock_df = self.get_stock_list()
        if stock_df.empty:
            return

        stock_list = stock_df['ts_code'].tolist()

        # 获取最近1天的数据（增量更新）
        today = datetime.now().strftime('%Y%m%d')
        yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y%m%d')

        results = self.get_all_stocks_data(
            stock_list=stock_list,
            start_date=yesterday,
            end_date=today,
            progress_callback=lambda current, total, code: print(f"进度: {current}/{total} - {code}")
        )

        logger.info(f"每日更新完成：{len(results)} 只股票")

        return results

    def save_to_csv(self, data: dict, output_dir: str):
        """
        保存数据到CSV文件

        Args:
            data: {ts_code: DataFrame} 格式的数据
            output_dir: 输出目录
        """
        import os
        os.makedirs(output_dir, exist_ok=True)

        for ts_code, df in data.items():
            file_path = os.path.join(output_dir, f"{ts_code}.csv")
            df.to_csv(file_path, index=False, encoding='utf-8')

        logger.info(f"数据已保存到: {output_dir}")


# 测试代码
if __name__ == "__main__":
    # 测试配置
    test_config = {
        'primary': {
            'token': '632a9e8aedcabe96101ae6dcca1bb3ba5837dd20be1069bf48fe7775'
        }
    }

    # 创建数据提供者
    provider = FullDataProvider(test_config)

    # 测试获取股票列表
    print("=" * 50)
    print("测试1: 获取股票列表")
    print("=" * 50)
    stock_list = provider.get_stock_list()
    if not stock_list.empty:
        print(f"✓ 获取到 {len(stock_list)} 只股票")
        print(stock_list.head(10))
    else:
        print("✗ 获取失败")

    # 测试获取单只股票数据
    print("\n" + "=" * 50)
    print("测试2: 获取单只股票数据")
    print("=" * 50)
    stock_data = provider.get_stock_data('000001.SZ')
    if stock_data is not None:
        print(f"✓ 获取到 {len(stock_data)} 条数据")
        print(stock_data.tail(5))
    else:
        print("✗ 获取失败")
