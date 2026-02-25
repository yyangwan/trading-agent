#!/usr/bin/env python3
"""
智能体系统启动器
"""
import asyncio
import logging
from datetime import datetime

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


async def main():
    """主函数"""
    from agents import initialize_agents, run_agent_workflow
    
    # 初始化智能体
    logger.info("=" * 60)
    logger.info("A股选股智能体系统启动")
    logger.info("=" * 60)
    
    manager = initialize_agents()
    
    # 显示智能体状态
    logger.info("\n已加载智能体:")
    for name, agent in manager.get_all_agents().items():
        status = agent.get_status()
        logger.info(f"  - {name}: {', '.join(status['capabilities'][:3])}...")
    
    # 运行工作流
    logger.info("\n开始执行工作流...")
    
    result = await run_agent_workflow("quick_pick")
    
    logger.info("\n工作流执行结果:")
    logger.info(f"  选股结果: {result.get('stock_pick', {}).get('picks_count', 0)} 只")
    
    logger.info("\n" + "=" * 60)
    logger.info("智能体系统运行完成")
    logger.info("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
