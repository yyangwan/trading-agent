#!/usr/bin/env python3
"""
Web界面 - 更新配置以显示实际选股结果
"""
import os
import sys

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask, render_template, jsonify
import pandas as pd
import yaml
from datetime import datetime

app = Flask(__name__)

def load_config():
    """加载配置"""
    with open('configs/system_config.yaml', 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def get_latest_picks():
    """获取最新选股结果"""
    picks_dir = 'output/picks'
    
    if not os.path.exists(picks_dir):
        return pd.DataFrame()
    
    # 获取最新的选股文件
    files = [f for f in os.listdir(picks_dir) if f.endswith('.csv')]
    
    if not files:
        return pd.DataFrame()
    
    # 按日期排序，获取最新的
    files.sort(reverse=True)
    latest_file = os.path.join(picks_dir, files[0])
    
    try:
        df = pd.read_csv(latest_file)
        return df
    except:
        return pd.DataFrame()

def get_strategies():
    """获取策略列表"""
    with open('configs/strategies_config.yaml', 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    strategies = []
    for name, conf in config.get('strategies', {}).items():
        if conf.get('enabled', False):
            strategies.append({
                'name': conf.get('description', name),
                'module': name,
                'weight': conf.get('weight', 1.0)
            })
    
    return strategies

@app.route('/')
def index():
    """主页"""
    return render_template('index.html')

@app.route('/api/strategies')
def api_strategies():
    """获取策略列表"""
    strategies = get_strategies()
    return jsonify({'strategies': strategies})

@app.route('/api/picks')
def api_picks():
    """获取选股结果"""
    df = get_latest_picks()
    
    if df.empty:
        return jsonify({
            'date': datetime.now().strftime('%Y-%m-%d'),
            'total': 0,
            'picks': []
        })
    
    # 提取日期
    date_str = df['date'].iloc[0] if 'date' in df.columns else datetime.now().strftime('%Y-%m-%d')
    
    # 转换为字典列表
    picks = df.to_dict('records')
    
    return jsonify({
        'date': date_str,
        'total': len(picks),
        'picks': picks
    })

@app.route('/api/status')
def api_status():
    """获取系统状态"""
    import os
    
    # 数据统计
    csv_dir = 'data/stock_data/csv'
    total_stocks = 0
    if os.path.exists(csv_dir):
        total_stocks = len([f for f in os.listdir(csv_dir) if f.endswith('.csv')])
    
    # 选股结果
    df = get_latest_picks()
    picks_count = len(df) if not df.empty else 0
    
    # 策略数量
    strategies = get_strategies()
    
    return jsonify({
        'total_stocks': total_stocks,
        'picks_count': picks_count,
        'strategies_count': len(strategies),
        'last_update': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    })

if __name__ == '__main__':
    # 生产环境建议使用Gunicorn
    # 开发环境使用Flask内置服务器
    app.run(host='0.0.0.0', port=5000, debug=False)
