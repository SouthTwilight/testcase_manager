# 初始化colorama（自动重置终端颜色）
import os
import time
import logging
import colorama
from colorama import Fore, Back, Style

# 关键修复1：正确初始化Colorama（Windows必需，其他平台可选）
colorama.init(autoreset=True)  # 添加autoreset自动重置样式[1,2](@ref)


class ColoredFormatter(logging.Formatter):
    """自定义彩色日志格式器（修复颜色设置问题）"""
    # 修复2：定义字段颜色映射
    FIELD_COLORS = {
        'asctime': Fore.GREEN,
        'filename': Fore.CYAN,
        'lineno': Fore.YELLOW,
        'message': Fore.WHITE
    }

    # 修复3：定义级别颜色映射
    LEVEL_COLORS = {
        logging.DEBUG: Fore.GREEN,
        logging.INFO: Fore.BLUE,
        logging.WARNING: Fore.YELLOW,
        logging.ERROR: Fore.RED,
        logging.CRITICAL: Fore.RED + Style.BRIGHT
    }

    # 修复4：定义级别名称映射
    LEVEL_NAMES = {
        logging.DEBUG: "DEBUG",
        logging.INFO: "INFO",
        logging.WARNING: "WARNING",
        logging.ERROR: "ERROR",
        logging.CRITICAL: "CRITICAL"
    }

    def format(self, record):
        # 关键修复：调用父类方法处理基础格式化
        message = super().format(record)

        reset = Style.RESET_ALL
        asctime = self.formatTime(record, self.datefmt)
        levelname = self.LEVEL_NAMES.get(record.levelno, record.levelname)

        # 应用颜色到各个字段
        colored_asctime = f"{self.FIELD_COLORS['asctime']}{asctime}{reset}"
        colored_filename = f"{self.FIELD_COLORS['filename']}{record.filename}{reset}"
        colored_lineno = f"{self.FIELD_COLORS['lineno']}{record.lineno}{reset}"
        colored_message = f"{self.LEVEL_COLORS.get(record.levelno, '')}{record.msg}{reset}"
        colored_levelname = f"{self.LEVEL_COLORS.get(record.levelno, '')}{levelname}{reset}"

        return (f"[{colored_asctime}]"
                f"[{colored_filename} {colored_lineno}]"
                f"[{colored_levelname}]: "
                f"{colored_message}")


class Logger:

    def __init__(self, log_path):  # 添加log_path参数
        # 定义日志位置和文件名
        self.logname = os.path.join(log_path, "{}.log".format(time.strftime("%Y%m%d")))

        # 创建日志收集器
        self.logger = logging.getLogger("log")
        self.logger.setLevel(logging.DEBUG)
        if not self.logger.hasHandlers():
            # 文件日志格式（无颜色）
            file_formatter = logging.Formatter('[%(asctime)s][%(filename)s %(lineno)d][%(levelname)s]: %(message)s')

            # 控制台日志格式（带颜色）
            console_formatter = ColoredFormatter()  # 使用自定义格式器

            # 文件处理器
            file_handler = logging.FileHandler(self.logname, mode='a', encoding="UTF-8")
            file_handler.setLevel(logging.INFO)
            file_handler.setFormatter(file_formatter)

            # 控制台处理器
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.DEBUG)
            console_handler.setFormatter(console_formatter)  # 应用彩色格式器

            # 添加处理器到日志收集器
            self.logger.addHandler(file_handler)
            self.logger.addHandler(console_handler)


root_path = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
log_path = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), 'log')
if not os.path.exists(log_path):
    os.makedirs(log_path)
# 全局日志收集器
logger = Logger(log_path).logger

if __name__ == '__main__':
    logger.debug("我打印debug日志")
    logger.info("获取任务名......")
    logger.warning("我打印warning日志")
    logger.error("我打印error日志")
