#!/usr/bin/env python3
"""
Real-time Application Monitor
Monitors API and GUI processes, logs, and system resources.
"""

import time
import psutil
import requests
import json
from datetime import datetime
from pathlib import Path

class RealTimeMonitor:
    """Real-time monitoring for the Therapy Compliance Analyzer."""
    
    def __init__(self):
        self.api_url = "http://127.0.0.1:8001"
        self.log_file = Path("monitor.log")
        self.start_time = datetime.now()
        
    def check_api_status(self):
        """Check API server status."""
        try:
            response = requests.get(f"{self.api_url}/health", timeout=5)
            if response.status_code == 200:
                data = response.json()
                return {
                    'status': 'online',
                    'response_time': response.elapsed.total_seconds(),
                    'data': data
                }
            else:
                return {'status': 'error', 'code': response.status_code}
        except requests.exceptions.RequestException as e:
            return {'status': 'offline', 'error': str(e)}
    
    def get_python_processes(self):
        """Get information about Python processes."""
        processes = []
        for proc in psutil.process_iter(['pid', 'name', 'memory_info', 'cpu_percent', 'create_time']):
            if 'python' in proc.info['name'].lower():
                try:
                    proc.cpu_percent()  # Initialize CPU monitoring
                    processes.append({
                        'pid': proc.info['pid'],
                        'name': proc.info['name'],
                        'memory_mb': proc.info['memory_info'].rss / 1024**2,
                        'cpu_percent': proc.cpu_percent(),
                        'uptime': time.time() - proc.info['create_time']
                    })
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
        return processes
    
    def get_system_stats(self):
        """Get system resource statistics."""
        return {
            'cpu_percent': psutil.cpu_percent(interval=1),
            'memory': psutil.virtual_memory()._asdict(),
            'disk': psutil.disk_usage('.')._asdict(),
            'timestamp': datetime.now().isoformat()
        }
    
    def log_status(self, status_data):
        """Log current status to file."""
        with open(self.log_file, 'a') as f:
            f.write(json.dumps(status_data) + '\n')
    
    def print_status(self, status_data):
        """Print formatted status to console."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        print(f"\n🕐 {timestamp} - Application Status")
        print("-" * 50)
        
        # API Status
        api_status = status_data['api']
        if api_status['status'] == 'online':
            print(f"🌐 API: ✅ Online ({api_status['response_time']:.3f}s)")
        else:
            print(f"🌐 API: ❌ {api_status['status']}")
        
        # Python Processes
        processes = status_data['processes']
        print(f"🐍 Python Processes: {len(processes)}")
        for proc in processes:
            print(f"   PID {proc['pid']}: {proc['memory_mb']:.1f}MB RAM, {proc['cpu_percent']:.1f}% CPU")
        
        # System Resources
        system = status_data['system']
        print(f"💻 System: CPU {system['cpu_percent']:.1f}%, RAM {system['memory']['percent']:.1f}%")
        
        # Uptime
        uptime = datetime.now() - self.start_time
        print(f"⏱️ Monitor Uptime: {uptime}")
    
    def run_monitor(self, interval=5):
        """Run continuous monitoring."""
        print("🚀 Starting Real-Time Monitor")
        print("Press Ctrl+C to stop")
        print("=" * 50)
        
        try:
            while True:
                status_data = {
                    'api': self.check_api_status(),
                    'processes': self.get_python_processes(),
                    'system': self.get_system_stats()
                }
                
                self.print_status(status_data)
                self.log_status(status_data)
                
                time.sleep(interval)
                
        except KeyboardInterrupt:
            print("\n\n🛑 Monitor stopped by user")
            print(f"📊 Log saved to: {self.log_file}")

if __name__ == "__main__":
    import sys
    
    monitor = RealTimeMonitor()
    
    if len(sys.argv) > 1 and sys.argv[1] == "once":
        # Single status check
        status_data = {
            'api': monitor.check_api_status(),
            'processes': monitor.get_python_processes(),
            'system': monitor.get_system_stats()
        }
        monitor.print_status(status_data)
    else:
        # Continuous monitoring
        interval = int(sys.argv[1]) if len(sys.argv) > 1 else 5
        monitor.run_monitor(interval)
