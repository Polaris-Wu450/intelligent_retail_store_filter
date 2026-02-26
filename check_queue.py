#!/usr/bin/env python
"""
Utility script to check Redis queue status
Usage: python check_queue.py
"""

import os
import redis
from dotenv import load_dotenv

load_dotenv()

def check_queue():
    """Check pending tasks in Redis queue"""
    redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
    queue_name = 'actionplan_queue'
    
    try:
        client = redis.from_url(redis_url)
        
        client.ping()
        print("✅ Redis connection successful\n")
        
        queue_length = client.llen(queue_name)
        print(f"📊 Queue name: {queue_name}")
        print(f"📊 Queue length: {queue_length}\n")
        
        if queue_length > 0:
            tasks = client.lrange(queue_name, 0, -1)
            print(f"📝 Task IDs in queue:")
            for i, task_id in enumerate(tasks, 1):
                print(f"   {i}. ActionPlan ID: {task_id.decode('utf-8')}")
        else:
            print("✨ Queue is empty, no pending tasks")
        
        print(f"\n🔧 Redis server: {redis_url}")
        
    except redis.ConnectionError:
        print("❌ Cannot connect to Redis")
        print(f"   Make sure Redis is running: docker-compose up redis")
        print(f"   Redis URL: {redis_url}")
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == '__main__':
    check_queue()
