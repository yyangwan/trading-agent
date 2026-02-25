"""
选股智能体 - 负责执行选股策略
"""
import asyncio
import pandas as pd
from datetime import datetime
from typing import Dict, Any, List

from agents.base_agent import BaseAgent


class PickerAgent(BaseAgent):
    """选股智能体"""
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__("PickerAgent", config)
        self.data_dir = "data/stock_data/csv"
        self.output_dir = "output/picks"
        
    def get_capabilities(self) -> List[str]:
        return [
            "run_strategies",
            "run_single_strategy",
            "get_picks",
            "validate_picks"
        ]
    
    async def process(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """处理选股任务"""
        action = task.get("action")
        self.log_action(f"Processing: {action}")
        
        try:
            if action == "run_strategies":
                return await self._run_strategies(task)
            elif action == "get_picks":
                return await self._get_picks(task)
            elif action == "validate_picks":
                return await self._validate_picks(task)
            else:
                return {"error": f"Unknown action: {action}"}
        except Exception as e:
            self.logger.error(f"Error processing {action}: {e}")
            return {"error": str(e)}
    
    async def _run_strategies(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """运行所有策略"""
        date = task.get("date", datetime.now().strftime('%Y-%m-%d'))
        strategies = task.get("strategies", None)  # None = all strategies
        
        self.log_action(f"Running strategies for {date}")
        
        # 导入选股引擎
        import sys
        sys.path.insert(0, '.')
        from core.stock_picker_v2 import StockPicker
        
        # 创建选股引擎
        picker = StockPicker({})
        
        # 运行选股
        results = picker.pick_stocks(date=date)
        
        if results.empty:
            self.log_action("No stocks found")
            return {
                "success": True,
                "picks_count": 0,
                "date": date
            }
        
        # 保存结果
        import os
        os.makedirs(self.output_dir, exist_ok=True)
        output_file = f"{self.output_dir}/picks_{date}.csv"
        results.to_csv(output_file, index=False, encoding='utf-8-sig')
        
        self.log_action(f"Found {len(results)} stocks")
        
        return {
            "success": True,
            "picks_count": len(results),
            "date": date,
            "output_file": output_file,
            "top_picks": results.head(10).to_dict('records')
        }
    
    async def _get_picks(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """获取选股结果"""
        date = task.get("date", datetime.now().strftime('%Y-%m-%d'))
        output_file = f"{self.output_dir}/picks_{date}.csv"
        
        if not os.path.exists(output_file):
            return {"error": "Picks file not found"}
        
        df = pd.read_csv(output_file)
        
        return {
            "success": True,
            "date": date,
            "picks": df.to_dict('records'),
            "count": len(df)
        }
    
    async def _validate_picks(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """验证选股结果"""
        date = task.get("date", datetime.now().strftime('%Y-%m-%d'))
        
        # 获取选股结果
        picks_result = await self._get_picks({"date": date})
        
        if "error" in picks_result:
            return {"valid": False, "error": picks_result["error"]}
        
        picks = picks_result["picks"]
        
        # 验证
        if not picks:
            return {"valid": True, "warning": "No picks"}
        
        # 检查必要字段
        required_fields = ['ts_code', 'close', 'matched_strategies']
        for pick in picks:
            for field in required_fields:
                if field not in pick:
                    return {"valid": False, "error": f"Missing field: {field}"}
        
        return {
            "valid": True,
            "count": len(picks),
            "strategies": list(set(p['matched_strategies'] for p in picks))
        }
