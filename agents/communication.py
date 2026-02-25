"""
智能体通信总线
"""
import asyncio
import logging
from typing import Dict, Any, Callable, List
from datetime import datetime
import json


class Message:
    """消息类"""
    
    def __init__(self, sender: str, receiver: str, content: Dict[str, Any]):
        self.sender = sender
        self.receiver = receiver
        self.content = content
        self.timestamp = datetime.now().isoformat()
        self.id = f"{sender}_{receiver}_{datetime.now().timestamp()}"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "sender": self.sender,
            "receiver": self.receiver,
            "content": self.content,
            "timestamp": self.timestamp
        }


class MessageBus:
    """消息总线"""
    
    def __init__(self):
        self.queues: Dict[str, List[Message]] = {}
        self.handlers: Dict[str, Callable] = {}
        self.logger = logging.getLogger("MessageBus")
        self._running = False
    
    async def send(self, sender: str, receiver: str, content: Dict[str, Any]):
        """发送消息"""
        message = Message(sender, receiver, content)
        
        if receiver not in self.queues:
            self.queues[receiver] = []
        
        self.queues[receiver].append(message)
        self.logger.info(f"Message from {sender} to {receiver}: {content.get('action', 'unknown')}")
    
    async def receive(self, receiver: str) -> Message:
        """接收消息"""
        if receiver in self.queues and self.queues[receiver]:
            return self.queues[receiver].pop(0)
        return None
    
    def register_handler(self, agent_name: str, handler: Callable):
        """注册消息处理器"""
        self.handlers[agent_name] = handler
    
    async def start(self):
        """启动消息总线"""
        self._running = True
        self.logger.info("MessageBus started")
    
    async def stop(self):
        """停止消息总线"""
        self._running = False
        self.logger.info("MessageBus stopped")


# 全局消息总线实例
message_bus = MessageBus()
