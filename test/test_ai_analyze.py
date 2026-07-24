#!/usr/bin/env python3
"""
test_ai_analyze.py - 测试 AI 智能数据提取功能

演示如何使用 ai_analyze 提取规则让 AI 智能分析脚本输出
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from task_planner import TaskPlanner
from ai_integration import AIIntegration


def test_ai_data_extraction():
    """测试 AI 智能数据提取功能"""
    
    print("=" * 80)
    print("🧪 测试 AI 智能数据提取功能")
    print("=" * 80)
    
    # 初始化组件
    api_url = "http://localhost:8080"
    api_key = "test"
    
    ai = AIIntegration(api_url, api_key, verbose=True)
    planner = TaskPlanner(verbose=True, ai_integration=ai)
    
    # 测试用例 1：系统命令输出
    print("\n" + "=" * 80)
    print("📋 测试用例 1：系统命令输出")
    print("=" * 80)
    
    system_output = """Exit Code: 0
Execution Time: 0.123s

STDOUT:
Linux myserver 5.4.0-150-generic #167-Ubuntu SMP Mon May 15 22:48:48 UTC 2023 x86_64 x86_64 x86_64 GNU/Linux
Filesystem      Size  Used Avail Use% Mounted on
/dev/sda1        98G   45G   48G  48% /
tmpfs           7.8G     0  7.8G   0% /dev/shm
              total        used        free      shared  buff/cache   available
Mem:          15951        8234        2156         512        5560        6890
Swap:          2048         256        1792

STDERR:
"""
    
    print("\n原始输出:")
    print(system_output[:300] + "...")
    
    # 使用 AI 分析提取
    result = planner.extract_data_from_result(system_output, "ai_analyze")
    
    print(f"\n✅ AI 提取结果:")
    print(f"   值: {result.get('value', 'N/A')[:200]}")
    print(f"   说明: {result.get('explanation', 'N/A')}")
    print(f"   方法: {result.get('method', 'N/A')}")
    
    # 测试用例 2：JSON 格式输出
    print("\n" + "=" * 80)
    print("📋 测试用例 2：JSON 格式输出")
    print("=" * 80)
    
    json_output = """Exit Code: 0
Execution Time: 0.045s

STDOUT:
{
  "name": "test-project",
  "version": "1.2.3",
  "description": "A sample project",
  "dependencies": {
    "express": "^4.18.0",
    "lodash": "^4.17.21"
  },
  "scripts": {
    "start": "node index.js",
    "test": "jest"
  }
}

STDERR:
"""
    
    print("\n原始输出:")
    print(json_output[:300] + "...")
    
    result = planner.extract_data_from_result(json_output, "ai_analyze")
    
    print(f"\n✅ AI 提取结果:")
    print(f"   值: {result.get('value', 'N/A')[:200]}")
    print(f"   说明: {result.get('explanation', 'N/A')}")
    print(f"   方法: {result.get('method', 'N/A')}")
    
    # 测试用例 3：错误日志输出
    print("\n" + "=" * 80)
    print("📋 测试用例 3：错误日志输出")
    print("=" * 80)
    
    error_output = """Exit Code: 1
Execution Time: 2.345s

STDOUT:
[2024-01-15 10:30:45] INFO: Starting application...
[2024-01-15 10:30:46] INFO: Loading configuration...
[2024-01-15 10:30:47] WARNING: Config file not found, using defaults
[2024-01-15 10:30:48] ERROR: Database connection failed
Traceback (most recent call last):
  File "/app/main.py", line 45, in connect_db
    conn = psycopg2.connect(host=db_host, port=db_port)
  File "/usr/lib/python3/dist-packages/psycopg2/__init__.py", line 122, in connect
    conn = _connect(dsn, connection_factory=connection_factory, **kwasync)
psycopg2.OperationalError: could not connect to server: Connection refused
	Is the server running on host "localhost" (::1) and accepting
	TCP/IP connections on port 5432?

STDERR:
Failed to start application
"""
    
    print("\n原始输出:")
    print(error_output[:300] + "...")
    
    result = planner.extract_data_from_result(error_output, "ai_analyze")
    
    print(f"\n✅ AI 提取结果:")
    print(f"   值: {result.get('value', 'N/A')[:200]}")
    print(f"   说明: {result.get('explanation', 'N/A')}")
    print(f"   方法: {result.get('method', 'N/A')}")
    
    # 测试用例 4：对比传统提取方式
    print("\n" + "=" * 80)
    print("📋 测试用例 4：对比传统提取方式")
    print("=" * 80)
    
    complex_output = """Exit Code: 0
Execution Time: 1.234s

STDOUT:
=== System Report ===
Date: 2024-01-15 10:30:45
Hostname: production-server-01
OS: Ubuntu 22.04 LTS
Kernel: 5.15.0-91-generic

CPU Usage: 45.2%
Memory Usage: 62.8% (10.1 GB / 16 GB)
Disk Usage: 78.5% (156 GB / 200 GB)

Active Processes: 127
Uptime: 15 days, 3 hours, 22 minutes

Network Interfaces:
  eth0: UP (192.168.1.100)
  lo: UP (127.0.0.1)

Services Status:
  nginx: running
  postgresql: running
  redis: stopped ⚠️

Warnings:
  - Redis service is not running
  - Disk usage above 75%

STDERR:
"""
    
    print("\n原始输出（前 300 字符）:")
    print(complex_output[:300] + "...")
    
    # 传统方式：first_line
    result_first_line = planner.extract_data_from_result(complex_output, "first_line")
    print(f"\n📊 first_line 提取结果:")
    print(f"   值: {result_first_line.get('value', 'N/A')}")
    
    # 传统方式：full_output
    result_full = planner.extract_data_from_result(complex_output, "full_output")
    print(f"\n📊 full_output 提取结果:")
    print(f"   值长度: {len(result_full.get('value', ''))} 字符")
    print(f"   前 100 字符: {result_full.get('value', '')[:100]}...")
    
    # AI 智能提取
    result_ai = planner.extract_data_from_result(complex_output, "ai_analyze")
    print(f"\n🤖 AI 智能提取结果:")
    print(f"   值: {result_ai.get('value', 'N/A')[:200]}")
    print(f"   说明: {result_ai.get('explanation', 'N/A')}")
    
    print("\n" + "=" * 80)
    print("✅ 所有测试完成！")
    print("=" * 80)


if __name__ == "__main__":
    test_ai_data_extraction()
