import pygame
import sys
import traceback
from maingame.game import Game
from logger import setup_logger, log_exception, log_game_event

# 设置日志记录器
logger = setup_logger()

def main():
    """主函数，包含全局异常处理"""
    try:
        log_game_event(logger, "启动", "游戏开始启动")
        
        # 初始化pygame
        pygame.init()
        pygame.font.init()
        log_game_event(logger, "初始化", "Pygame初始化完成")
        
        # 创建并运行游戏
        game = Game(logger)
        game.run()
        
    except KeyboardInterrupt:
        log_game_event(logger, "退出", "用户中断游戏")
    except Exception as e:
        log_exception(logger, e, "主程序运行时")
        # 在打包环境下显示错误对话框
        if getattr(sys, 'frozen', False):
            try:
                import tkinter as tk
                from tkinter import messagebox
                root = tk.Tk()
                root.withdraw()  # 隐藏主窗口
                messagebox.showerror(
                    "游戏错误", 
                    f"游戏运行时发生错误：{str(e)}\n\n详细错误信息已保存到logs文件夹中。"
                )
            except:
                pass  # 如果无法显示对话框，忽略错误
    finally:
        log_game_event(logger, "清理", "游戏资源清理完成")
        pygame.quit()

if __name__ == "__main__":
    main()