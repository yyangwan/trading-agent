"""
智能体基类 - A股选股策略系统
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, List
from datetime import datetime
import logging
import json
import os


class BaseAgent(ABC):
    """智能体基类"""
    
    def __init__(self, name: str, config: Dict[str, Any] = None):
        self.name = name
        self.config = config or {}
        self.logger = logging.getLogger(f"Agent.{name}")
        self.state = "idle"
        self.last_action = None
        self.last_action_time = None
        
    @abstractmethod
    async def process(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """处理任务"""
        pass
    
    @abstractmethod
    def get_capabilities(self) -> List[str]:
        """获取智能体能力列表"""
        pass
    
    def get_status(self) -> Dict[str, Any]:
        """获取智能体状态"""
        return {
            "name": self.name,
            "state": self.state,
            "last_action": self.last_action,
            "last_action_time": self.last_action_time,
            "capabilities": self.get_capabilities()
        }
    
    def log_action(self, action: str):
        """记录动作"""
        self.last_action = action
        self.last_action_time = datetime.now().isoformat()
        self.logger.info(f"{self.name}: {action}")
    
    async def send_message(self, receiver: str, message: Dict[str, Any]):
        """发送消息给其他智能体"""
        # 这里实现智能体间通信
        from agents.communication import MessageBus
        await MessageBus.send(self.name, receiver, message)
        self.log_action(f"Sent message to {receiver}")
    
    async def receive_message(self, sender: str, message: Dict[str, Any]):
        """接收来自其他智能体的消息"""
        self.log_action(f"Received message from {sender}")
        return await self.process(message)


class AgentManager:
    """智能体管理器"""
    
    def __init__(self):
        self.agents: Dict[str, BaseAgent] = {}
        self.logger = logging.getLogger("AgentManager")
    
    def register_agent(self, agent: BaseAgent):
        """注册智能体"""
        self.agents[agent.name] = agent
        self.logger.info(f"Registered agent: {agent.name}")
    
    def get_agent(self, name: str) -> BaseAgent:
        """获取智能体"""
        return self.agents.get(name)
    
    def get_all_agents(self) -> Dict[str, BaseAgent]:
        """获取所有智能体"""
        return self.agents
    
    def get_agent_status(self) -> Dict[str, Dict[str, Any]]:
        """获取所有智能体状态"""
        return {
            name: agent.get_status() 
            for name, agent in self.agents.items()
        }
    
    async def broadcast(self, message: Dict[str, Any]):
        """广播消息给所有智能体"""
        for agent in self.agents.values():
            await agent.receive_message("system", message)


# 全局智能体管理器实例
agent_manager = AgentManager()
