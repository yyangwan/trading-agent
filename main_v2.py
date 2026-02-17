#!/usr/bin/env python3
"""
A股选股策略系统 - 主程序入口（改进版）
"""
import sys
import yaml
import logging
import argparse
from pathlib import Path
from datetime import datetime

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent))

# 使用改进的选股引擎
from core.stock_picker_v2 import StockPicker

# 配置日志
logging.basicConfig(
    level=getattr(logging, 'INFO'),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)

# 文件日志
log_config = {'level': 'INFO', 'file': True, 'file_path': 'logs/stock_picker.log'}
file_handler = logging.FileHandler('logs/stock_picker.log', encoding='utf-8')
file_handler.setFormatter(logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
))
logging.getLogger().addHandler(file_handler)

logger = logging.getLogger(__name__)


def load_config(config_file: str = "configs/system_config.yaml") -> dict:
    """加载系统配置"""
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    except Exception as e:
        logger.error(f"加载配置失败: {e}")
        return {}


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='A股选股策略系统（改进版）')
    parser.add_argument('--date', type=str, help='选股日期 (YYYY-MM-DD)')
    parser.add_argument('--strategies', type=str, nargs='+', help='指定策略')
    parser.add_argument('--config', type=str, default='configs/system_config.yaml', help='配置文件路径')
    parser.add_argument('--test', action='store_true', help='测试模式（仅验证配置）')

    args = parser.parse_args()

    # 加载配置
    config = load_config(args.config)

    logger.info("=" * 50)
    logger.info("A股选股策略系统启动")
    logger.info("=" * 50)

    # 测试模式
    if args.test:
        logger.info("测试模式：验证配置")
        from core.strategy_manager import StrategyManager

        manager = StrategyManager("configs/strategies_config.yaml")
        manager.load_strategies()

        logger.info(f"✓ 配置文件: {args.config}")
        logger.info(f"✓ 已加载策略: {len(manager.get_all_strategies())}个")
        logger.info(f"✓ 启用策略: {list(manager.get_enabled_strategies().keys())}")
        logger.info("✓ 本地数据: 系统将使用本地CSV数据")

        # 显示本地数据状态
        import os
        csv_dir = 'data/stock_data/csv'
        if os.path.exists(csv_dir):
            files = [f for f in os.listdir(csv_dir) if f.endswith('.csv')]
            logger.info(f"✓ 本地股票数据: {len(files)} 只")

        logger.info("测试通过！")
        return

    # 创建选股引擎
    picker = StockPicker(config)

    # 执行选股
    date = args.date or datetime.now().strftime('%Y-%m-%d')

    logger.info(f"开始选股: {date}")

    results = picker.pick_stocks(
        date=date,
        strategies=args.strategies
    )

    # 输出结果
    if not results.empty:
        output_file = f"output/picks/picks_{date}.csv"
        Path(output_file).parent.mkdir(parents=True, exist_ok=True)

        results.to_csv(output_file, index=False, encoding='utf-8-sig')

        logger.info(f"✓ 选股完成: {len(results)}只股票")
        logger.info(f"✓ 结果已保存: {output_file}")

        # 显示前10只
        print("\n" + "=" * 60)
        print(f"选股结果 ({date}):")
        print("=" * 60)
        print(results[['ts_code', 'close', 'change_pct', 'matched_strategies', 'avg_score']].head(10).to_string(index=False))
        print("=" * 60)

        # 发送到企业微信（可选）
        try:
            from test_message_format import format_pick_message
            message = format_pick_message(results, date)
            logger.info("✓ 消息已格式化，可以手动发送")
            print("\n" + message)
        except Exception as e:
            logger.error(f"格式化消息失败: {e}")

    else:
        logger.warning("未找到符合条件的股票")
        print("\n未找到符合条件的股票，请检查：")
        print("1. 本地数据是否充足（python3 manage_data.py --status）")
        print("2. 策略参数是否合理（configs/strategies_config.yaml）")

    logger.info("=" * 50)
    logger.info("选股结束")
    logger.info("=" * 50)


if __name__ == "__main__":
    main()
