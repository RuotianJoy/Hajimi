import math
import os
import sys
import math

import pygame

from maingame.Projectile import Projectile

def get_resource_path(relative_path):
    """获取资源文件的绝对路径，兼容开发环境和PyInstaller打包环境"""
    try:
        # PyInstaller创建临时文件夹，并将路径存储在_MEIPASS中
        base_path = sys._MEIPASS
    except Exception:
        # 开发环境下使用当前脚本所在目录的上级目录
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)


class Weapon:
    def __init__(self, weapon_type="meowmere"):
        self.weapon_type = weapon_type
        self.attack_cooldown = 0
        self.attack_cooldown_max = 0.5  # 0.5秒攻击冷却

        # 挥舞动画相关
        self.is_swinging = False
        self.swing_timer = 0
        self.swing_duration = 10  # 挥舞动画持续15帧
        self.swing_angle_offset = 0
        
        # nadir武器特有属性
        self.thrust_distance = 0  # 当前伸出距离
        self.max_thrust_distance = 100  # 最大伸出距离
        self.thrust_speed = 8  # 伸出速度
        self.is_thrusting = False  # 是否正在伸出
        self.thrust_direction = 1  # 1为伸出，-1为收回

        # 加载武器图像
        self.load_weapon_image()

    def load_weapon_image(self):
        """加载武器图像"""

        if self.weapon_type == "nadir":
            # 加载nadir武器图像
            weapon_relative_path = os.path.join("weapon", "nadir", "nadir_rotated_45.png")
            weapon_path = get_resource_path(weapon_relative_path)
            self.image = pygame.image.load(weapon_path).convert_alpha()
            # nadir武器保持原始比例，适当缩放
            self.image = pygame.transform.scale(self.image, (204, 56))

        else:
            # 加载meowmere武器图像
            weapon_relative_path = os.path.join("weapon", "meowmere", "Meowmere.webp")
            weapon_path = get_resource_path(weapon_relative_path)
            if os.path.exists(weapon_path):
                self.image = pygame.image.load(weapon_path).convert_alpha()
                # 增加剑的大小到96x96
                self.image = pygame.transform.scale(self.image, (96, 96))
                #print(f"武器图片加载成功: {weapon_path}")
            else:
                # 创建默认武器图像
                self.image = pygame.Surface((96, 96), pygame.SRCALPHA)
                pygame.draw.rect(self.image, (200, 200, 200), (15, 15, 66, 66))
                #print(f"武器图像文件未找到: {weapon_path}，使用默认图像")


    def can_attack(self):
        """检查是否可以攻击"""
        return self.attack_cooldown <= 0

    def attack(self, player_x, player_y, mouse_x, mouse_y, attack_power):
        """执行攻击，返回弹幕对象"""
        if not self.can_attack():
            return None

        # 计算攻击方向（从玩家中心到鼠标位置）
        player_center_x = player_x + 48  # 玩家中心X
        player_center_y = player_y + 48  # 玩家中心Y
        dx = mouse_x - player_center_x
        dy = mouse_y - player_center_y
        distance = math.sqrt(dx*dx + dy*dy)

        if distance > 0:
            direction_x = dx / distance
            direction_y = dy / distance
        else:
            direction_x = 1
            direction_y = 0

        # 设置攻击冷却和挥舞动画
        self.attack_cooldown = self.attack_cooldown_max
        self.is_swinging = True
        self.swing_timer = 0



        # 创建弹幕
        if self.weapon_type == "nadir":
        # 计算武器发射位置（根据方向动态计算）
            weapon_offset = 0  # 武器距离玩家中心的距离
            weapon_x = player_center_x
            weapon_y = player_center_y
            projectile = Projectile(
                weapon_x,  # 从武器最大伸出位置发射
                weapon_y,
                direction_x,
                direction_y,
                attack_power,  # 100%攻击力
                "player",  # 所有者ID
                max_bounces=2,
                max_distance=100,  # 使用武器的最大伸出距离作为弹幕的最大飞行距离
                weapon_type="nadir"
            )
            return projectile
        else:
            weapon_offset = 40  # 武器距离玩家中心的距离
            weapon_x = player_center_x + direction_x * weapon_offset
            weapon_y = player_center_y + direction_y * weapon_offset
            projectile = Projectile(
                weapon_x,  # 从武器位置发射
                weapon_y,
                direction_x,
                direction_y,
                attack_power,  # 100%攻击力
                "player",  # 所有者ID
                weapon_type=self.weapon_type
            )

            return projectile
        


    def update(self, dt):
        """更新武器状态"""
        if self.attack_cooldown > 0:
            self.attack_cooldown -= dt

        # 更新挥舞动画
        if self.is_swinging:
            self.swing_timer += 1
            # 计算挥舞角度偏移（正弦波动画）
            progress = self.swing_timer / self.swing_duration
            self.swing_angle_offset = math.sin(progress * math.pi)  # 最大45度偏移

            if self.swing_timer >= self.swing_duration:
                self.is_swinging = False
                self.swing_timer = 0
                self.swing_angle_offset = 0
        
        # nadir武器现在使用弹幕攻击，不需要伸缩动画
        # 保留伸缩状态用于动画效果，但不影响攻击逻辑
        if self.weapon_type == "nadir" and self.is_thrusting:
            self.thrust_distance += self.thrust_speed * self.thrust_direction

            # 检查是否达到最大伸出距离
            if self.thrust_distance >= self.max_thrust_distance:
                self.thrust_distance = self.max_thrust_distance
                self.thrust_direction = -1  # 开始收回

            # 检查是否完全收回
            elif self.thrust_distance <= 0:
                self.thrust_distance = 0
                self.is_thrusting = False
                self.thrust_direction = 1

    def draw(self, screen, player_x, player_y, mouse_x, mouse_y, facing_right):
        """绘制武器"""
        if self.weapon_type == "nadir":
            # nadir武器现在使用弹幕攻击，不需要绘制武器本体
            pass
        else:
            # 其他武器的绘制逻辑
            if self.weapon_type == "meowmere":
                # Meowmere武器不绘制
                pass
            else:
                # 其他武器的正常绘制逻辑
                # 计算角色图中心偏右的位置（玩家宽度96，高度96）
                if facing_right:
                    # 面向右边：定位在角色图3/4位置
                    weapon_anchor_x = player_x + 72  # 角色图3/4位置
                    weapon_anchor_y = player_y + 48  # 角色图中点高度
                else:
                    # 面向左边：定位在角色图1/4位置
                    weapon_anchor_x = player_x + 24  # 角色图1/4位置
                    weapon_anchor_y = player_y + 48  # 角色图中点高度

                # 计算武器朝向鼠标的角度
                dx = mouse_x - weapon_anchor_x
                dy = mouse_y - weapon_anchor_y
                angle = math.degrees(math.atan2(dy, dx))

                # 添加挥舞角度偏移和45度顺时针旋转
                final_angle = angle + self.swing_angle_offset + 45

                # 根据朝向决定是否翻转武器
                weapon_image = self.image
                if not facing_right:
                    # 面向左边时，水平翻转武器
                    weapon_image = pygame.transform.flip(self.image, True, False)
                    # 调整角度以适应翻转
                    final_angle = 180 - final_angle

                # 旋转武器图像
                rotated_image = pygame.transform.rotate(weapon_image, -final_angle)

                # 以左下角定位到锚点
                rotated_rect = rotated_image.get_rect()
                if facing_right:
                    # 面向右边：剑的左下角对准锚点
                    rotated_rect.bottomleft = (weapon_anchor_x, weapon_anchor_y)
                else:
                    # 面向左边：剑的右下角对准锚点
                    rotated_rect.bottomright = (weapon_anchor_x, weapon_anchor_y)

                screen.blit(rotated_image, rotated_rect)
        
        return None
