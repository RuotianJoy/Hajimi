#!/usr/bin/env python3
"""
游戏服务器启动脚本

使用方法:
    python3 start_server.py

服务器将在 localhost:12345 启动
玩家可以通过在游戏中按 C 键连接到服务器
"""

from network import start_server

if __name__ == "__main__":
    print("="*50)
    print("横版联机游戏服务器")
    print("="*50)
    print("服务器将在 localhost:12345 启动")
    print("按 Ctrl+C 停止服务器")
    print("="*50)
    
    try:
        start_server()
    except KeyboardInterrupt:
        print("\n服务器已停止")