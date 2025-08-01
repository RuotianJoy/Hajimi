import pygame
import os
import sys

from maingame import GREEN, BROWN

def get_resource_path(relative_path):
    """获取资源文件的绝对路径，兼容开发环境和PyInstaller打包环境"""
    try:
        # PyInstaller创建临时文件夹，并将路径存储在_MEIPASS中
        base_path = sys._MEIPASS
    except Exception:
        # 开发环境下使用当前脚本所在目录的上级目录
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)


class Platform:
    def __init__(self, x, y, width, height):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.rect = pygame.Rect(x, y, width, height)

        # 加载平台图片
        try:
            platform_path = get_resource_path('img/platform.svg')
            self.image = pygame.image.load(platform_path)
            # 创建平铺的平台
            self.surface = pygame.Surface((width, height))
            tile_width = 64
            tile_height = 48

            for i in range(0, width, tile_width):
                for j in range(0, height, tile_height):
                    self.surface.blit(self.image, (i, j))
            print("平台图片加载成功: img/platform.svg")
        except Exception as e:
            # 如果加载失败，创建一个简单的矩形
            self.surface = pygame.Surface((width, height))
            self.surface.fill(BROWN)
            # 添加草地顶部
            pygame.draw.rect(self.surface, GREEN, (0, 0, width, 4))
            print(f"平台图片加载失败: {e}，使用默认图像")

    def draw(self, screen):
        screen.blit(self.surface, (self.x, self.y))
