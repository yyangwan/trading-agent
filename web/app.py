"""
Web界面 - A股选股策略系统
展示策略配置和选股结果
"""
from flask import Flask, render_template, jsonify, request
import yaml
import os
from datetime import datetime, timedelta
import pandas as pd
import json

app = Flask(__name__)

# 配置路径
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_PATH = os.path.join(BASE_DIR, 'configs')
OUTPUT_PATH = os.path.join(BASE_DIR, 'output', 'picks')


def load_config():
    """加载配置"""
    try:
        with open(os.path.join(CONFIG_PATH, 'strategies_config.yaml'), 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    except Exception as e:
        return {}


def get_latest_picks():
    """获取最新的选股结果"""
    try:
        # 获取最近的选股文件
        files = sorted([f for f in os.listdir(OUTPUT_PATH) if f.endswith('.csv')], reverse=True)

        if not files:
            return None

        latest_file = files[0]
        df = pd.read_csv(os.path.join(OUTPUT_PATH, latest_file))

        return {
            'date': latest_file.replace('picks_', '').replace('.csv', ''),
            'stocks': df.to_dict('records'),
            'count': len(df)
        }
    except Exception as e:
        return None


@app.route('/')
def index():
    """首页"""
    config = load_config()
    strategies = config.get('strategies', {})

    # 整理策略信息
    strategy_list = []
    for key, value in strategies.items():
        strategy_list.append({
            'id': key,
            'name': value.get('module', key).replace('strategies.', '').replace('_', ' ').title(),
            'enabled': value.get('enabled', False),
            'description': value.get('description', ''),
            'weight': value.get('weight', 1.0),
            'params': value.get('params', {})
        })

    # 获取最新选股结果
    latest_picks = get_latest_picks()

    return render_template('index.html',
                         strategies=strategy_list,
                         latest_picks=latest_picks)


@app.route('/api/strategies')
def api_strategies():
    """获取策略列表API"""
    config = load_config()
    strategies = config.get('strategies', {})

    result = []
    for key, value in strategies.items():
        result.append({
            'id': key,
            'name': value.get('module', key).replace('strategies.', '').replace('_', ' ').title(),
            'enabled': value.get('enabled', False),
            'description': value.get('description', ''),
            'weight': value.get('weight', 1.0),
            'params': value.get('params', {})
        })

    return jsonify({
        'success': True,
        'data': result
    })


@app.route('/api/picks/<date>')
def api_picks(date):
    """获取指定日期的选股结果"""
    try:
        file_path = os.path.join(OUTPUT_PATH, f'picks_{date}.csv')

        if not os.path.exists(file_path):
            return jsonify({
                'success': False,
                'message': '未找到该日期的选股结果'
            })

        df = pd.read_csv(file_path)

        return jsonify({
            'success': True,
            'data': {
                'date': date,
                'count': len(df),
                'stocks': df.to_dict('records')
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        })


@app.route('/api/picks/latest')
def api_latest_picks():
    """获取最新选股结果"""
    latest_picks = get_latest_picks()

    if latest_picks:
        return jsonify({
            'success': True,
            'data': latest_picks
        })
    else:
        return jsonify({
            'success': False,
            'message': '暂无选股结果'
        })


@app.route('/api/picks/dates')
def api_pick_dates():
    """获取所有选股日期列表"""
    try:
        files = sorted([f for f in os.listdir(OUTPUT_PATH) if f.endswith('.csv')], reverse=True)

        dates = [f.replace('picks_', '').replace('.csv', '') for f in files]

        return jsonify({
            'success': True,
            'data': dates
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        })


@app.route('/api/system/status')
def api_system_status():
    """获取系统状态"""
    try:
        config = load_config()
        strategies = config.get('strategies', {})

        enabled_count = sum(1 for v in strategies.values() if v.get('enabled', False))
        total_count = len(strategies)

        latest_picks = get_latest_picks()

        return jsonify({
            'success': True,
            'data': {
                'strategies': {
                    'total': total_count,
                    'enabled': enabled_count,
                    'disabled': total_count - enabled_count
                },
                'latest_picks': {
                    'date': latest_picks['date'] if latest_picks else None,
                    'count': latest_picks['count'] if latest_picks else 0
                },
                'server_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        })


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
