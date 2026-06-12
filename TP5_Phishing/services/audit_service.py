from flask import Flask, request, jsonify
from datetime import datetime
import json
import os
from threading import Lock

app = Flask(__name__)
lock = Lock()
LOG_FILE = 'storage/audit_logs.json'

def load_logs():
    try:
        with open(LOG_FILE, 'r') as f:
            return json.load(f)
    except:
        return []

def save_log(logs):
    with lock:
        with open(LOG_FILE, 'w') as f:
            json.dump(logs, f, indent=2)

@app.route('/audit/log', methods=['POST'])
def log_event():
    data = request.json
    
    log_entry = {
        'timestamp': datetime.now().isoformat(),
        'event_type': data.get('event_type', 'UNKNOWN'),
        'username': data.get('username', 'anonymous'),
        'action': data.get('action', ''),
        'details': data.get('details', {}),
        'ip': request.remote_addr
    }
    
    logs = load_logs()
    logs.append(log_entry)
    
    # Garder seulement les 1000 derniers logs
    if len(logs) > 1000:
        logs = logs[-1000:]
    
    save_log(logs)
    
    return jsonify({'status': 'logged'})

@app.route('/audit/logs', methods=['GET'])
def get_logs():
    # Vérification admin faite par gateway
    limit = request.args.get('limit', 100, type=int)
    event_type = request.args.get('type', None)
    
    logs = load_logs()
    
    if event_type:
        logs = [l for l in logs if l['event_type'] == event_type]
    
    return jsonify({'logs': logs[-limit:]})

@app.route('/audit/stats', methods=['GET'])
def get_stats():
    logs = load_logs()
    
    stats = {
        'total_events': len(logs),
        'by_type': {}
    }
    
    for log in logs:
        event_type = log['event_type']
        stats['by_type'][event_type] = stats['by_type'].get(event_type, 0) + 1
    
    return jsonify(stats)

if __name__ == '__main__':
    os.makedirs('storage', exist_ok=True)
    app.run(host='localhost', port=8003, debug=False)