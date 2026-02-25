"""
数据智能体 - 负责数据获取、更新和验证
"""
import asyncio
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, Any, List
import os

from agents.base_agent import BaseAgent


class DataAgent(BaseAgent):
    """数据智能体"""
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__("DataAgent", config)
        self.data_dir = "data/stock_data/csv"
        self.cache_dir = "data/cache"
        
    def get_capabilities(self) -> List[str]:
        return [
            "fetch_stock_list",
            "fetch_stock_data",
            "validate_data",
            "update_data",
            "get_data_status"
        ]
    
    async def process(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """处理数据相关任务"""
        action = task.get("action")
        self.log_action(f"Processing: {action}")
        
        try:
            if action == "fetch_stock_list":
                return await self._fetch_stock_list(task)
            elif action == "fetch_stock_data":
                return await self._fetch_stock_data(task)
            elif action == "validate_data":
                return await self._validate_data(task)
            elif action == "update_data":
                return await self._update_data(task)
            elif action == "get_status":
                return self._get_status()
            else:
                return {"error": f"Unknown action: {action}"}
        except Exception as e:
            self.logger.error(f"Error processing {action}: {e}")
            return {"error": str(e)}
    
    async def _fetch_stock_list(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """获取股票列表"""
        import tushare as ts
        import yaml
        
        # 读取配置
        with open('configs/system_config.yaml', 'r') as f:
            config = yaml.safe_load(f)
        
        token = config.get('data_sources', {}).get('primary', {}).get('token', '')
        pro = ts.pro_api(token)
        
        # 获取股票列表
        df = pro.stock_basic(exchange='', list_status='L')
        
        # 保存缓存
        os.makedirs(self.cache_dir, exist_ok=True)
        df.to_pickle(f'{self.cache_dir}/stock_list.pkl')
        
        self.log_action(f"Fetched {len(df)} stocks")
        
        return {
            "success": True,
            "stock_count": len(df),
            "timestamp": datetime.now().isoformat()
        }
    
    async def _fetch_stock_data(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """获取股票数据"""
        import tushare as ts
        import yaml
        
        stock_list = task.get("stock_list", [])
        period = task.get("period", 180)
        
        # 读取配置
        with open('configs/system_config.yaml', 'r') as f:
            config = yaml.safe_load(f)
        
        token = config.get('data_sources', {}).get('primary', {}).get('token', '')
        pro = ts.pro_api(token)
        
        # 计算日期
        end_date = datetime.now().strftime('%Y%m%d')
        start_date = (datetime.now() - timedelta(days=period)).strftime('%Y%m%d')
        
        success_count = 0
        failed_count = 0
        
        for ts_code in stock_list:
            try:
                df = pro.daily(ts_code=ts_code, start_date=start_date, end_date=end_date)
                
                if df.empty:
                    failed_count += 1
                    continue
                
                df = df.rename(columns={'trade_date': 'date'})
                
                os.makedirs(self.data_dir, exist_ok=True)
                df.to_csv(f'{self.data_dir}/{ts_code}.csv', index=False)
                success_count += 1
                
            except Exception as e:
                self.logger.error(f"Failed to fetch {ts_code}: {e}")
                failed_count += 1
        
        self.log_action(f"Fetched data: {success_count} success, {failed_count} failed")
        
        return {
            "success": True,
            "success_count": success_count,
            "failed_count": failed_count,
            "timestamp": datetime.now().isoformat()
        }
    
    async def _validate_data(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """验证数据质量"""
        ts_code = task.get("ts_code")
        
        file_path = f'{self.data_dir}/{ts_code}.csv'
        
        if not os.path.exists(file_path):
            return {"valid": False, "error": "File not found"}
        
        df = pd.read_csv(file_path)
        
        # 检查必要列
        required_cols = ['date', 'open', 'high', 'low', 'close', 'vol']
        missing_cols = [col for col in required_cols if col not in df.columns]
        
        if missing_cols:
            return {"valid": False, "error": f"Missing columns: {missing_cols}"}
        
        # 检查数据量
        if len(df) < 10:
            return {"valid": False, "error": "Insufficient data"}
        
        return {
            "valid": True,
            "data_points": len(df),
            "date_range": f"{df['date'].iloc[0]} to {df['date'].iloc[-1]}"
        }
    
    async def _update_data(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """更新数据"""
        # 先获取股票列表
        stock_list_result = await self._fetch_stock_list({})
        
        if not stock_list_result.get("success"):
            return {"error": "Failed to fetch stock list"}
        
        # 获取已有数据
        existing_stocks = set()
        if os.path.exists(self.data_dir):
            for f in os.listdir(self.data_dir):
                if f.endswith('.csv'):
                    existing_stocks.add(f.replace('.csv', ''))
        
        # 找出需要更新的股票
        # 这里简化处理，获取全部股票
        cache_file = f'{self.cache_dir}/stock_list.pkl'
        if os.path.exists(cache_file):
            df = pd.read_pickle(cache_file)
            stock_list = df['ts_code'].tolist()
        else:
            return {"error": "Stock list not found"}
        
        # 获取数据
        result = await self._fetch_stock_data({"stock_list": stock_list})
        
        return result
    
    def _get_status(self) -> Dict[str, Any]:
        """获取数据状态"""
        total_stocks = 0
        if os.path.exists(self.data_dir):
            total_stocks = len([f for f in os.listdir(self.data_dir) if f.endswith('.csv')])
        
        return {
            "total_stocks": total_stocks,
            "data_directory": self.data_dir,
            "cache_directory": self.cache_dir
        }
