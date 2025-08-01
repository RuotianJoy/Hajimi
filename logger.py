import logging
import os
import sys
from datetime import datetime

def setup_logger():
    """
    设置日志记录器，支持打包后的exe文件
    """
    # 获取可执行文件所在目录
    if getattr(sys, 'frozen', False):
        # 如果是打包后的exe文件
        app_dir = os.path.dirname(sys.executable)
    else:
        # 如果是开发环境
        app_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 创建logs目录
    logs_dir = os.path.join(app_dir, 'logs')
    if not os.path.exists(logs_dir):
        os.makedirs(logs_dir)
    
    # 生成日志文件名（包含时间戳）
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    log_filename = f'game_log_{timestamp}.txt'
    log_filepath = os.path.join(logs_dir, log_filename)
    
    # 配置日志记录器
    logger = logging.getLogger('GameLogger')
    logger.setLevel(logging.DEBUG)
    
    # 清除已有的处理器
    logger.handlers.clear()
    
    # 创建文件处理器
    file_handler = logging.FileHandler(log_filepath, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    
    # 创建控制台处理器（开发环境使用）
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    
    # 创建格式化器
    formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    # 添加处理器到日志记录器
    logger.addHandler(file_handler)
    if not getattr(sys, 'frozen', False):  # 只在开发环境显示控制台日志
        logger.addHandler(console_handler)
    
    # 记录初始化信息
    logger.info(f"日志系统初始化完成，日志文件：{log_filepath}")
    logger.info(f"运行环境：{'打包exe' if getattr(sys, 'frozen', False) else '开发环境'}")
    logger.info(f"工作目录：{app_dir}")
    
    return logger

def log_exception(logger, exception, context=""):
    """
    记录异常信息
    """
    import traceback
    
    error_msg = f"异常发生 {context}: {str(exception)}"
    logger.error(error_msg)
    logger.error(f"异常类型: {type(exception).__name__}")
    logger.error(f"异常详情: {traceback.format_exc()}")

def log_game_event(logger, event_type, message):
    """
    记录游戏事件
    """
    logger.info(f"[{event_type}] {message}")

def log_network_event(logger, event_type, message):
    """
    记录网络事件
    """
    logger.info(f"[网络-{event_type}] {message}")