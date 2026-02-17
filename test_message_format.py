"""
测试消息推送格式
"""
from datetime import datetime


def format_pick_message(results_df, date=None):
    """
    格式化选股结果消息

    Args:
        results_df: 选股结果DataFrame
        date: 选股日期

    Returns:
        格式化的消息字符串
    """
    if results_df is None or results_df.empty:
        return f"📊 【选股结果】{date or datetime.now().strftime('%Y-%m-%d')}\n\n未找到符合条件的股票 ❌"

    # 统计信息
    total_count = len(results_df)
    top_picks = results_df.head(10)  # 前10只

    # 构建消息
    message = f"📊 【选股结果】{date or datetime.now().strftime('%Y-%m-%d')}\n\n"
    message += f"✅ 共找到 {total_count} 只符合条件的股票\n\n"

    # 前10只股票详情
    message += "━━━━━━━━━━━━━━━━━━\n"
    message += "🏆 TOP10 推荐股票：\n"
    message += "━━━━━━━━━━━━━━━━━━\n\n"

    for idx, row in top_picks.iterrows():
        # 策略数量徽章
        strategy_count = int(row.get('strategy_count', 1))
        badge = "🔥" if strategy_count >= 3 else "⭐" if strategy_count == 2 else "✓"

        message += f"{badge} {row.get('name', 'N/A')} ({row.get('ts_code', 'N/A')})\n"
        message += f"   💰 价格: ¥{row.get('close', 0):.2f}  "
        message += f"📈 {row.get('change_pct', 0):+.2f}%\n"

        # 匹配的策略
        strategies = row.get('matched_strategies', '')
        if strategies:
            strategy_names = strategies.replace('_', ' ').title()
            message += f"   🎯 策略: {strategy_names}\n"

        # 评分
        avg_score = row.get('avg_score', 0)
        message += f"   ⭐ 评分: {avg_score:.1f}/100\n"

        # 止损止盈
        stop_loss = row.get('stop_loss', 0.05) * 100
        take_profit = row.get('take_profit', 0.15) * 100
        message += f"   🛡️ 止损: -{stop_loss:.1f}%  |  🎯 止盈: +{take_profit:.1f}%\n"

        message += "\n"

    # 风险提示
    message += "━━━━━━━━━━━━━━━━━━\n"
    message += "⚠️  风险提示：\n"
    message += "• 本系统仅供参考，不构成投资建议\n"
    message += "• 股市有风险，投资需谨慎\n"
    message += "• 建议结合多维度分析判断\n"
    message += "• 严格执行止损纪律\n"
    message += "━━━━━━━━━━━━━━━━━━\n"

    return message


def format_simple_message(results_df, date=None):
    """
    简化版消息格式（适合手机阅读）

    Args:
        results_df: 选股结果DataFrame
        date: 选股日期

    Returns:
        格式化的消息字符串
    """
    if results_df is None or results_df.empty:
        return f"📊 {date or datetime.now().strftime('%Y-%m-%d')} 选股结果：无符合条件的股票"

    total_count = len(results_df)
    top_picks = results_df.head(5)  # 只显示前5只

    message = f"📊 【{date or datetime.now().strftime('%m-%d')}】找到 {total_count} 只\n\n"

    for idx, row in top_picks.iterrows():
        message += f"{'🔥' if row.get('strategy_count', 1) >= 2 else '✓'} "
        message += f"{row.get('name', 'N/A')}\n"
        message += f"   ¥{row.get('close', 0):.2f}  {row.get('change_pct', 0):+.2f}%\n"
        message += f"   止损:{int(row.get('stop_loss', 0.05)*100)}%  "
        message += f"止盈:{int(row.get('take_profit', 0.15)*100)}%\n\n"

    message += "⚠️ 仅供参考，严格止损"

    return message


# 测试代码
if __name__ == "__main__":
    import pandas as pd

    # 模拟数据
    mock_data = {
        'ts_code': ['000001.SZ', '000002.SZ', '600000.SH'],
        'name': ['平安银行', '万科A', '浦发银行'],
        'date': ['2026-02-16', '2026-02-16', '2026-02-16'],
        'close': [12.50, 8.88, 7.65],
        'change_pct': [2.35, -0.89, 1.25],
        'matched_strategies': ['ma_trend', 'ma_trend,breakout', 'oversold_rebound'],
        'strategy_count': [1, 2, 1],
        'avg_score': [75.5, 82.3, 68.9],
        'stop_loss': [0.05, 0.05, 0.08],
        'take_profit': [0.15, 0.18, 0.20]
    }

    df = pd.DataFrame(mock_data)

    print("=" * 50)
    print("完整版格式：")
    print("=" * 50)
    print(format_pick_message(df, "2026-02-16"))

    print("\n" + "=" * 50)
    print("简化版格式：")
    print("=" * 50)
    print(format_simple_message(df, "2026-02-16"))
