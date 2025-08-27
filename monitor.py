#!/usr/bin/env python3
"""
AI Learning Tutor - Performance Monitor
Monitors API performance, resource usage, and system health
"""

import time
import psutil
import requests
from datetime import datetime
import sqlite3
import json

def check_api_health():
    """Check API responsiveness"""
    try:
        start_time = time.time()
        response = requests.get("http://localhost:8000/", timeout=5)
        response_time = (time.time() - start_time) * 1000
        
        return {
            "status": "healthy" if response.status_code == 200 else "unhealthy",
            "response_time_ms": response_time,
            "status_code": response.status_code
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "response_time_ms": None
        }

def check_ai_services():
    """Check AI services status"""
    try:
        response = requests.get("http://localhost:8000/api/health/ai", timeout=10)
        return response.json() if response.status_code == 200 else {"error": "AI services unavailable"}
    except:
        return {"error": "Cannot connect to AI services"}

def get_system_metrics():
    """Get system resource usage"""
    return {
        "cpu_percent": psutil.cpu_percent(),
        "memory_percent": psutil.virtual_memory().percent,
        "disk_percent": psutil.disk_usage('/').percent,
        "timestamp": datetime.now().isoformat()
    }

def get_database_stats():
    """Get database statistics"""
    try:
        conn = sqlite3.connect('data/ai_tutor.db')
        cursor = conn.cursor()
        
        stats = {}
        
        # Count records in each table
        tables = ['users', 'user_profiles', 'curriculum_modules', 
                 'user_progress', 'quiz_sessions', 'spaced_repetition_schedule']
        
        for table in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            stats[f"{table}_count"] = cursor.fetchone()[0]
        
        conn.close()
        return stats
        
    except Exception as e:
        return {"error": str(e)}

def main():
    """Monitor system and generate report"""
    print("🔍 AI Learning Tutor - System Monitor")
    print("=" * 50)
    
    # Check API health
    api_health = check_api_health()
    print(f"🌐 API Status: {api_health['status']}")
    if api_health['response_time_ms']:
        print(f"   Response time: {api_health['response_time_ms']:.2f}ms")
    
    # Check AI services
    ai_status = check_ai_services()
    print(f"🤖 AI Services:")
    if 'status' in ai_status:
        for service, status in ai_status['status'].items():
            print(f"   {service}: {status}")
    
    # System metrics
    metrics = get_system_metrics()
    print(f"💻 System Resources:")
    print(f"   CPU: {metrics['cpu_percent']:.1f}%")
    print(f"   Memory: {metrics['memory_percent']:.1f}%")
    print(f"   Disk: {metrics['disk_percent']:.1f}%")
    
    # Database stats
    db_stats = get_database_stats()
    if 'error' not in db_stats:
        print(f"🗄️ Database:")
        print(f"   Users: {db_stats.get('users_count', 0)}")
        print(f"   Quiz sessions: {db_stats.get('quiz_sessions_count', 0)}")
        print(f"   Progress records: {db_stats.get('user_progress_count', 0)}")
    
    # Generate alerts
    print("\n⚠️ Alerts:")
    alerts = []
    
    if api_health['status'] != 'healthy':
        alerts.append("API is not responding properly")
    
    if api_health.get('response_time_ms', 0) > 2000:
        alerts.append("API response time is slow (>2s)")
    
    if metrics['cpu_percent'] > 80:
        alerts.append("High CPU usage detected")
    
    if metrics['memory_percent'] > 85:
        alerts.append("High memory usage detected")
    
    if not alerts:
        print("   All systems normal ✅")
    else:
        for alert in alerts:
            print(f"   🚨 {alert}")

if __name__ == "__main__":
    main()
