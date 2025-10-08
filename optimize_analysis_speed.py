#!/usr/bin/env python3
"""
Optimize analysis speed - identify and fix performance bottlenecks
"""

import requests
import time
import psutil
import os

def analyze_performance_issues():
    """Analyze what's causing slow analysis performance"""
    print("🔍 Analysis Performance Optimization")
    print("=" * 50)
    
    # Check system resources
    print("\n1️⃣ System Resource Analysis...")
    
    # Memory usage
    memory = psutil.virtual_memory()
    print(f"   💾 Memory: {memory.percent}% used ({memory.used/1024/1024/1024:.1f}GB / {memory.total/1024/1024/1024:.1f}GB)")
    
    # CPU usage
    cpu_percent = psutil.cpu_percent(interval=1)
    print(f"   🖥️  CPU: {cpu_percent}% usage")
    
    # Disk usage
    disk = psutil.disk_usage('.')
    print(f"   💿 Disk: {disk.percent}% used")
    
    # Check AI model status
    print("\n2️⃣ AI Model Performance...")
    try:
        response = requests.get("http://127.0.0.1:8001/ai/status", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"   🤖 AI Status: {data.get('status')}")
            models = data.get('models', {})
            for model, status in models.items():
                print(f"   📊 {model}: {status}")
        else:
            print(f"   ❌ AI status error: {response.status_code}")
    except Exception as e:
        print(f"   ❌ AI status check failed: {e}")
    
    # Performance bottlenecks
    print(f"\n🐌 Common Performance Issues:")
    print(f"   1. Large document size (388KB PDF)")
    print(f"   2. Local AI model processing (CPU-intensive)")
    print(f"   3. Multiple AI models running simultaneously")
    print(f"   4. Complex compliance analysis pipeline")
    print(f"   5. Memory constraints with large models")
    
    # Optimization suggestions
    print(f"\n⚡ Performance Optimizations:")
    print(f"   1. 🔧 Reduce document size or chunk processing")
    print(f"   2. 🚀 Use lighter AI models for faster processing")
    print(f"   3. 💾 Increase system memory if possible")
    print(f"   4. 🎯 Optimize AI pipeline for speed vs accuracy")
    print(f"   5. ⏱️  Add progress indicators for user feedback")
    
    # Quick fixes
    print(f"\n🛠️  Quick Fixes to Try:")
    print(f"   • Test with smaller document (< 100KB)")
    print(f"   • Close other applications to free memory")
    print(f"   • Use 'fast' analysis mode if available")
    print(f"   • Check if GPU acceleration is available")
    
    # Expected timing
    print(f"\n⏱️  Expected Analysis Times:")
    print(f"   • Small document (< 50KB): 30-60 seconds")
    print(f"   • Medium document (50-200KB): 1-3 minutes")
    print(f"   • Large document (200KB+): 3-10 minutes")
    print(f"   • Your document (388KB): 5-15 minutes (expected)")

if __name__ == "__main__":
    analyze_performance_issues()