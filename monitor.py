import urllib.request
import socket
import json
import time
import os
import ssl
import subprocess
import platform
from datetime import datetime, timedelta

# Configuration
URL = "https://watgpu.cs.uwaterloo.ca/"
SSH_HOST = "watgpu.cs.uwaterloo.ca"
SSH_PORT = 22
HISTORY_FILE = "history.json"
OUTPUT_HTML = "index.html"
MAX_HISTORY_DAYS = 100000000000 # Keep forever

def check_http(url):
    try:
        req = urllib.request.Request(
            url, 
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
        )
        context = ssl._create_unverified_context()
        with urllib.request.urlopen(req, timeout=10, context=context) as response:
            return response.getcode() == 200
    except Exception as e:
        print(f"HTTP Check failed: {e}")
        return False

def check_ssh(host, port):
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        result = sock.connect_ex((host, port))
        sock.close()
        return result == 0
    except:
        return False

def check_ping(host):
    try:
        param = '-n' if platform.system().lower() == 'windows' else '-c'
        # Ping 1 packet, timeout 2 seconds (if supported by ping, otherwise standard timeout)
        # Note: standard ping doesn't always support timeout easily across platforms without flags
        command = ['ping', param, '1', host]
        
        # Run ping command, suppressing output
        return subprocess.call(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL) == 0
    except:
        return False

def load_history():
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, 'r') as f:
            return json.load(f)
    return []

def save_history(history):
    # Prune old history (if MAX_HISTORY_DAYS is set to a reasonable value)
    # If MAX_HISTORY_DAYS is very large, skip pruning to keep forever
    if MAX_HISTORY_DAYS < 36500:  # Less than 100 years, do pruning
        cutoff = datetime.now() - timedelta(days=MAX_HISTORY_DAYS)
        new_history = [
            entry for entry in history 
            if datetime.fromisoformat(entry['timestamp']) > cutoff
        ]
    else:
        # Keep all history
        new_history = history
    
    with open(HISTORY_FILE, 'w') as f:
        json.dump(new_history, f, indent=2)
    return new_history

def calculate_uptime(history, days):
    if not history:
        return 100.0
        
    cutoff = datetime.now() - timedelta(days=days)
    relevant_entries = [
        entry for entry in history 
        if datetime.fromisoformat(entry['timestamp']) > cutoff
    ]
    
    if not relevant_entries:
        return 100.0
        
    # Consider UP only if ALL services are UP (HTTP, SSH, and Ping if available)
    up_count = sum(
        1 for entry in relevant_entries 
        if entry.get('http_up', False) and entry.get('ssh_up', False) and entry.get('ping_up', True)
    )
    return (up_count / len(relevant_entries)) * 100

def generate_html(history):
    uptime_24h = calculate_uptime(history, 1)
    uptime_7d = calculate_uptime(history, 7)
    uptime_30d = calculate_uptime(history, 30)
    
    latest = history[-1] if history else None
    
    # Safe get for ping_up since old history might not have it
    ping_status = latest.get('ping_up', False) if latest else False
    
    # Status logic: ALL tests must pass
    is_up = latest and latest.get('http_up', False) and latest.get('ssh_up', False) and ping_status

    status_color = "green" if is_up else "red"
    status_text = "ONLINE" if is_up else "DOWN"
    
    # Convert timestamps to Toronto time for display
    # Assuming stored timestamps are in UTC (GitHub Actions runs in UTC)
    def convert_to_toronto_time(dt):
        """Convert datetime to Toronto time (EST/EDT)"""
        # DST calculation: 2nd Sunday in March to 1st Sunday in November
        def is_dst(dt):
            # 2nd Sunday in March
            dst_start = datetime(dt.year, 3, 8)
            while dst_start.weekday() != 6:
                dst_start += timedelta(days=1)
            
            # 1st Sunday in November
            dst_end = datetime(dt.year, 11, 1)
            while dst_end.weekday() != 6:
                dst_end += timedelta(days=1)
            
            return dst_start <= dt < dst_end
        
        offset = -4 if is_dst(dt) else -5
        return dt + timedelta(hours=offset)
    
    if latest:
        utc_time = datetime.fromisoformat(latest['timestamp'])
        toronto_time = convert_to_toronto_time(utc_time)
        last_checked = toronto_time.strftime("%Y-%m-%d %H:%M:%S") + " ET (checks every 15 mins)"
    else:
        last_checked = "Never"
    
    # Determine start date
    if history:
        first_entry = history[0]
        utc_start = datetime.fromisoformat(first_entry['timestamp'])
        toronto_start = convert_to_toronto_time(utc_start)
        start_date = toronto_start.strftime("%Y-%m-%d")
    else:
        start_date = datetime.now().strftime("%Y-%m-%d")

    html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Is WatGPU Down?</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; text-align: center; padding: 50px; background-color: #f4f4f9; color: #333; }}
        .status-card {{ background: white; padding: 40px; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); display: inline-block; max-width: 600px; width: 100%; }}
        .status {{ font-size: 48px; font-weight: bold; color: {status_color}; margin: 20px 0; }}
        .metrics {{ display: flex; justify-content: space-around; margin-top: 30px; }}
        .metric {{ text-align: center; }}
        .metric-value {{ font-size: 24px; font-weight: bold; }}
        .metric-label {{ color: #666; font-size: 14px; }}
        .details {{ margin-top: 30px; text-align: left; font-size: 14px; color: #666; }}
        .timestamp {{ color: #888; margin-top: 20px; font-size: 12px; }}
    </style>
</head>
<body>
    <div class="status-card">
        <h1>Is WatGPU Down?</h1>
        <div class="status">{status_text}</div>
        <div class="metrics">
            <div class="metric">
                <div class="metric-value">{uptime_24h:.1f}%</div>
                <div class="metric-label">24h Uptime</div>
            </div>
            <div class="metric">
                <div class="metric-value">{uptime_7d:.1f}%</div>
                <div class="metric-label">7d Uptime</div>
            </div>
            <div class="metric">
                <div class="metric-value">{uptime_30d:.1f}%</div>
                <div class="metric-label">30d Uptime</div>
            </div>
        </div>
        <div class="timestamp">Statistics start from {start_date}</div>
        <div class="details">
            <p><strong>SSH Status (HPC):</strong> {'✅ OK' if latest and latest['ssh_up'] else '❌ FAIL'}</p>
            <p><strong>Ping Status:</strong> {'✅ OK' if ping_status else '❌ FAIL'}</p>
            <p><strong>Website (HTTP):</strong> {'✅ OK' if latest and latest['http_up'] else '❌ FAIL'}</p>
        </div>
        <div class="timestamp">Last checked: {last_checked}</div>
    </div>
</body>
</html>
    """
    
    with open(OUTPUT_HTML, 'w') as f:
        f.write(html_content)

def main():
    http_up = check_http(URL)
    ssh_up = check_ssh(SSH_HOST, SSH_PORT)
    ping_up = check_ping(SSH_HOST)
    
    timestamp = datetime.now().isoformat()
    
    entry = {
        "timestamp": timestamp,
        "http_up": http_up,
        "ssh_up": ssh_up,
        "ping_up": ping_up
    }
    
    history = load_history()
    history.append(entry)
    history = save_history(history)
    generate_html(history)
    
    print(f"Check complete. HTTP: {http_up}, SSH: {ssh_up}, Ping: {ping_up}")

if __name__ == "__main__":
    main()

