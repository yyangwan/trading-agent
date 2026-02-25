"""
智能体初始化模块
"""
from agents.base_agent import BaseAgent, AgentManager, agent_manager
from agents.data_agent import DataAgent
from agents.picker_agent import PickerAgent


def initialize_agents(config: dict = None) -> AgentManager:
    """初始化所有智能体"""
    manager = AgentManager()
    
    # 创建数据智能体
    data_agent = DataAgent(config)
    manager.register_agent(data_agent)
    
    # 创建选股智能体
    picker_agent = PickerAgent(config)
    manager.register_agent(picker_agent)
    
    return manager


async def run_agent_workflow(workflow: str, params: dict = None):
    """运行智能体工作流"""
    manager = initialize_agents()
    
    if workflow == "daily_update":
        return await _daily_update_workflow(manager, params)
    elif workflow == "quick_pick":
        return await _quick_pick_workflow(manager, params)
    else:
        return {"error": f"Unknown workflow: {workflow}"}


async def _daily_update_workflow(manager: AgentManager, params: dict = None):
    """每日更新工作流"""
    results = {}
    
    # 1. 数据智能体更新数据
    data_agent = manager.get_agent("DataAgent")
    data_result = await data_agent.process({"action": "update_data"})
    results["data_update"] = data_result
    
    # 2. 选股智能体运行策略
    picker_agent = manager.get_agent("PickerAgent")
    pick_result = await picker_agent.process({"action": "run_strategies"})
    results["stock_pick"] = pick_result
    
    return results


async def _quick_pick_workflow(manager: AgentManager, params: dict = None):
    """快速选股工作流"""
    results = {}
    
    # 直接运行选股
    picker_agent = manager.get_agent("PickerAgent")
    pick_result = await picker_agent.process({"action": "run_strategies"})
    results["stock_pick"] = pick_result
    
    return results
