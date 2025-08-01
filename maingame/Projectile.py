import math
import os
import sys
import uuid
import math

import pygame

from maingame import WIDTH, HEIGHT

def get_resource_path(relative_path):
    """获取资源文件的绝对路径，兼容开发环境和PyInstaller打包环境"""
    try:
        # PyInstaller创建临时文件夹，并将路径存储在_MEIPASS中
        base_path = sys._MEIPASS
    except Exception:
        # 开发环境下使用当前脚本所在目录的上级目录
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)


class Projectile:
    def __init__(self, x, y, direction_x, direction_y, damage, owner_id, max_bounces=2, max_distance=None, weapon_type="meowmere"):
        self.x = x
        self.y = y
        self.start_x = x  # 记录起始位置
        self.start_y = y
        
        # 根据武器类型设置不同的弹幕大小
        if weapon_type == "nadir":
            self.width = 204  # nadir弹幕更小
            self.height = 56
            self.collision_width = 195  # 对应的碰撞体积也更小
            self.collision_height = 45
        else:
            self.width = 32  # 喵刀等其他武器保持原大小
            self.height = 32
            self.collision_width = 20
            self.collision_height = 20
        self.vel_x = direction_x * 10  # 弹幕速度（进一步降低）
        self.vel_y = direction_y * 10
        self.damage = damage
        self.owner_id = owner_id
        self.max_bounces = max_bounces
        self.bounces = 0
        self.active = True
        self.projectile_id = str(uuid.uuid4())
        self.max_distance = max_distance  # 最大飞行距离
        self.weapon_type = weapon_type  # 武器类型，用于加载对应的弹幕图像

        # 拖尾效果相关
        self.trail_positions = []  # 存储历史位置
        self.max_trail_length = 10  # 拖尾最大长度

        # 计算弹幕的旋转角度（基于飞行方向）
        self.rotation_angle = math.degrees(math.atan2(direction_y, direction_x))
        
        # 加载弹幕图像
        self.load_projectile_image()

        # 使用较小的碰撞盒，居中对齐
        offset_x = (self.width - self.collision_width) // 2
        offset_y = (self.height - self.collision_height) // 2
        self.rect = pygame.Rect(x + offset_x, y + offset_y, self.collision_width, self.collision_height)

    def load_projectile_image(self):
        """根据武器类型加载对应的弹幕图像"""
        try:
            # 根据武器类型选择不同的弹幕图像路径
            if self.weapon_type == "nadir":
                # nadir武器使用其自身的图像作为弹幕
                projectile_relative_path = os.path.join("weapon", "nadir", "nadir_rotated_45.png")
            else:
                # 默认使用喵刀的弹幕图像
                projectile_relative_path = os.path.join("weapon", "meowmere", "Meowmere_(projectile).webp")
            
            projectile_path = get_resource_path(projectile_relative_path)
            if os.path.exists(projectile_path):
                self.original_image = pygame.image.load(projectile_path).convert_alpha()
                self.original_image = pygame.transform.scale(self.original_image, (self.width, self.height))
                

                self.image = pygame.transform.rotate(self.original_image, -self.rotation_angle)
                self.rotated_offset_x = (self.image.get_width() - self.width) // 2
                self.rotated_offset_y = (self.image.get_height() - self.height) // 2
                
                print(f"投掷物图片加载成功: {projectile_path}")
            else:
                # 创建默认弹幕图像，根据武器类型使用不同颜色
                self.original_image = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
                if self.weapon_type == "nadir":
                    # nadir武器使用金色弹幕
                    pygame.draw.circle(self.original_image, (255, 215, 0), (self.width//2, self.height//2), self.width//3)
                else:
                    # 其他武器使用紫色弹幕
                    pygame.draw.circle(self.original_image, (255, 100, 255), (self.width//2, self.height//2), self.width//3)
                
                # 根据武器类型旋转图像
                self.image = pygame.transform.rotate(self.original_image, -self.rotation_angle)
                self.rotated_offset_x = (self.image.get_width() - self.width) // 2
                self.rotated_offset_y = (self.image.get_height() - self.height) // 2
                print(f"弹幕图像文件未找到: {projectile_path}，使用默认图像")
        except Exception as e:
            # 创建默认弹幕图像
            self.original_image = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
            if self.weapon_type == "nadir":
                # nadir武器使用金色弹幕
                pygame.draw.circle(self.original_image, (255, 215, 0), (self.width//2, self.height//2), self.width//3)
            else:
                # 其他武器使用紫色弹幕
                pygame.draw.circle(self.original_image, (255, 100, 255), (self.width//2, self.height//2), self.width//3)
            
            # 根据武器类型旋转图像
            self.image = pygame.transform.rotate(self.original_image, -self.rotation_angle)
            self.rotated_offset_x = (self.image.get_width() - self.width) // 2
            self.rotated_offset_y = (self.image.get_height() - self.height) // 2
            print(f"加载弹幕图像时出错: {e}，使用默认图像")

    def update(self, dt, platforms, weapon_type):
        """更新弹幕位置和碰撞检测"""
        # 不覆盖弹幕自身的weapon_type，保持弹幕创建时的武器类型
        if not self.active:
            return

        # 只有喵刀武器才记录拖尾
        if self.weapon_type == "meowmere":
            self.trail_positions.append((self.x, self.y))
            if len(self.trail_positions) > self.max_trail_length:
                self.trail_positions.pop(0)

        # 更新位置
        self.x += self.vel_x * dt * 60
        self.y += self.vel_y * dt * 60
        # 更新碰撞盒位置，保持居中对齐
        offset_x = (self.width - self.collision_width) // 2
        offset_y = (self.height - self.collision_height) // 2
        self.rect.x = int(self.x + offset_x)
        self.rect.y = int(self.y + offset_y)

        # 检查飞行距离（如果设置了最大距离）
        if self.max_distance is not None:
            distance_traveled = ((self.x - self.start_x) ** 2 + (self.y - self.start_y) ** 2) ** 0.5
            if distance_traveled >= self.max_distance:
                self.active = False
                return

        # 只有喵刀武器才检查平台碰撞和反弹
        if self.weapon_type == "meowmere":
            for platform in platforms:
                if self.rect.colliderect(platform.rect):
                    self.bounce_off_platform(platform)
                    break

        # 检查屏幕边界
        if self.x < 0 or self.x > WIDTH or self.y < 0 or self.y > HEIGHT:
            if self.weapon_type == "meowmere" and self.bounces < self.max_bounces:
                self.bounce_off_screen()
            else:
                self.active = False

    def bounce_off_platform(self, platform):
        """从平台反弹"""
        if self.bounces >= self.max_bounces:
            self.active = False
            return

        # 计算反弹方向
        center_x = self.rect.centerx
        center_y = self.rect.centery
        platform_center_x = platform.rect.centerx
        platform_center_y = platform.rect.centery

        # 判断碰撞面并调整位置
        if abs(center_x - platform_center_x) > abs(center_y - platform_center_y):
            # 水平碰撞
            self.vel_x = -self.vel_x
            # 将弹幕移出平台
            if center_x < platform_center_x:
                # 弹幕在平台左侧
                self.x = platform.rect.left - self.width
            else:
                # 弹幕在平台右侧
                self.x = platform.rect.right
        else:
            # 垂直碰撞
            self.vel_y = -self.vel_y
            # 将弹幕移出平台
            if center_y < platform_center_y:
                # 弹幕在平台上方
                self.y = platform.rect.top - self.height
            else:
                # 弹幕在平台下方
                self.y = platform.rect.bottom

        # 更新碰撞盒位置
        offset_x = (self.width - self.collision_width) // 2
        offset_y = (self.height - self.collision_height) // 2
        self.rect.x = int(self.x + offset_x)
        self.rect.y = int(self.y + offset_y)

        self.bounces += 1
        self.damage = int(self.damage * 0.5)  # 每次反弹伤害减半

        # 移除频繁的调试打印以提高性能
        # print(f"弹幕反弹！反弹次数: {self.bounces}/{self.max_bounces}, 剩余伤害: {self.damage}")

    def bounce_off_screen(self):
        """从屏幕边界反弹"""
        if self.x <= 0 or self.x >= WIDTH:
            self.vel_x = -self.vel_x
        if self.y <= 0 or self.y >= HEIGHT:
            self.vel_y = -self.vel_y

        self.bounces += 1
        self.damage = int(self.damage * 0.5)  # 每次反弹伤害减半

    def draw(self, screen):
        """绘制弹幕"""
        if self.active:
            # 只有喵刀武器才绘制拖尾
            if self.weapon_type == "meowmere":
                for i, (trail_x, trail_y) in enumerate(self.trail_positions):
                    alpha = int(255 * (i + 1) / len(self.trail_positions) * 0.5)  # 透明度渐变
                    trail_surface = pygame.Surface((8, 8), pygame.SRCALPHA)
                    trail_surface.fill((255, 255, 100, alpha))  # 黄色拖尾
                    screen.blit(trail_surface, (int(trail_x), int(trail_y)))


            # 其他武器正常绘制（考虑旋转后的图像尺寸变化）
            if self.weapon_type == "meowmere":
                rotated_rect = self.image.get_rect(center=(self.x + self.width//2, self.y + self.height//2))
                screen.blit(self.image, rotated_rect)
            else:
                rotated_rect = self.image.get_rect(center=(self.x, self.y))
                screen.blit(self.image, rotated_rect)
