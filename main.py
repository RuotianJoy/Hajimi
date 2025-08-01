import pygame
import sys
import os
import json
import math
import uuid
from enum import Enum
from network import NetworkClient
from character_loader import CharacterLoader

# 初始化pygame
pygame.init()
pygame.font.init()

# 游戏常量
WIDTH = 1920
HEIGHT = 1080
FPS = 60
GRAVITY = 1.2
JUMP_STRENGTH = -22
PLAYER_SPEED = 8
PLATFORM_HEIGHT = 48

# 颜色定义
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
BLUE = (65, 105, 225)
GREEN = (34, 139, 34)
BROWN = (139, 69, 19)

# 游戏状态常量
MAIN_MENU = 1
MODE_SELECT = 2
CHARACTER_SELECT = 3
PLAYING = 4
PAUSED = 5
GAME_OVER = 6
SETTINGS = 7
KEY_BINDING = 8
ROOM_SELECT = 9
CREATE_ROOM = 10
JOIN_ROOM = 11
WAITING_ROOM = 12

# 游戏模式常量
OFFLINE = 1
ONLINE = 2
HOST_ROOM = 3
JOIN_ROOM_MODE = 4

class Projectile:
    def __init__(self, x, y, direction_x, direction_y, damage, owner_id, max_bounces=2):
        self.x = x
        self.y = y
        self.width = 32
        self.height = 32
        # 碰撞盒比视觉大小小一些，提高碰撞精度
        self.collision_width = 20
        self.collision_height = 20
        self.vel_x = direction_x * 4  # 弹幕速度（进一步降低）
        self.vel_y = direction_y * 4
        self.damage = damage
        self.owner_id = owner_id
        self.max_bounces = max_bounces
        self.bounces = 0
        self.active = True
        self.projectile_id = str(uuid.uuid4())
        
        # 拖尾效果相关
        self.trail_positions = []  # 存储历史位置
        self.max_trail_length = 8  # 拖尾最大长度
        
        # 加载弹幕图像
        self.load_projectile_image()
        
        # 使用较小的碰撞盒，居中对齐
        offset_x = (self.width - self.collision_width) // 2
        offset_y = (self.height - self.collision_height) // 2
        self.rect = pygame.Rect(x + offset_x, y + offset_y, self.collision_width, self.collision_height)
    
    def load_projectile_image(self):
        """加载弹幕图像"""
        try:
            projectile_path = "/Users/ruotianjoy/PycharmProjects/Hajimi/weapon/meowmere/Meowmere_(projectile).webp"
            if os.path.exists(projectile_path):
                self.image = pygame.image.load(projectile_path).convert_alpha()
                self.image = pygame.transform.scale(self.image, (self.width, self.height))
            else:
                # 创建默认弹幕图像
                self.image = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
                pygame.draw.circle(self.image, (255, 100, 255), (self.width//2, self.height//2), self.width//3)
        except Exception as e:
            # 创建默认弹幕图像
            self.image = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
            pygame.draw.circle(self.image, (255, 100, 255), (self.width//2, self.height//2), self.width//3)
    
    def update(self, dt, platforms):
        """更新弹幕位置和碰撞检测"""
        if not self.active:
            return
        
        # 记录当前位置到拖尾
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
        
        # 检查平台碰撞
        for platform in platforms:
            if self.rect.colliderect(platform.rect):
                self.bounce_off_platform(platform)
                break
        
        # 检查屏幕边界
        if self.x < 0 or self.x > WIDTH or self.y < 0 or self.y > HEIGHT:
            if self.bounces < self.max_bounces:
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
            # 绘制拖尾
            for i, (trail_x, trail_y) in enumerate(self.trail_positions):
                alpha = int(255 * (i + 1) / len(self.trail_positions) * 0.5)  # 透明度渐变
                trail_surface = pygame.Surface((8, 8), pygame.SRCALPHA)
                trail_surface.fill((255, 255, 100, alpha))  # 黄色拖尾
                screen.blit(trail_surface, (int(trail_x), int(trail_y)))
            
            # 绘制弹幕本体
            screen.blit(self.image, (self.rect.x, self.rect.y))

class Weapon:
    def __init__(self, weapon_type="meowmere"):
        self.weapon_type = weapon_type
        self.attack_cooldown = 0
        self.attack_cooldown_max = 0.5  # 0.5秒攻击冷却
        
        # 挥舞动画相关
        self.is_swinging = False
        self.swing_timer = 0
        self.swing_duration = 15  # 挥舞动画持续15帧
        self.swing_angle_offset = 0
        
        # 加载武器图像
        self.load_weapon_image()
    
    def load_weapon_image(self):
        """加载武器图像"""
        try:
            weapon_path = "/Users/ruotianjoy/PycharmProjects/Hajimi/weapon/meowmere/Meowmere.webp"
            if os.path.exists(weapon_path):
                self.image = pygame.image.load(weapon_path).convert_alpha()
                # 增加剑的大小到96x96
                self.image = pygame.transform.scale(self.image, (96, 96))
            else:
                # 创建默认武器图像
                self.image = pygame.Surface((96, 96), pygame.SRCALPHA)
                pygame.draw.rect(self.image, (200, 200, 200), (15, 15, 66, 66))
        except Exception as e:
            # 创建默认武器图像
            self.image = pygame.Surface((96, 96), pygame.SRCALPHA)
            pygame.draw.rect(self.image, (200, 200, 200), (15, 15, 66, 66))
    
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
        
        # 计算武器发射位置（根据方向动态计算）
        weapon_offset = 40  # 武器距离玩家中心的距离
        weapon_x = player_center_x + direction_x * weapon_offset
        weapon_y = player_center_y + direction_y * weapon_offset
        
        # 创建弹幕
        projectile = Projectile(
            weapon_x,  # 从武器位置发射
            weapon_y,
            direction_x,
            direction_y,
            attack_power,  # 100%攻击力
            "player"  # 所有者ID
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
            self.swing_angle_offset = math.sin(progress * math.pi) * 45  # 最大45度偏移
            
            if self.swing_timer >= self.swing_duration:
                self.is_swinging = False
                self.swing_timer = 0
                self.swing_angle_offset = 0
    
    def draw(self, screen, player_x, player_y, mouse_x, mouse_y, facing_right):
        """绘制武器"""
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
        
        # 添加挥舞角度偏移
        final_angle = angle + self.swing_angle_offset
        
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

class Player:
    def __init__(self, x, y, character_folder=None, character_name="哈基为"):
        self.x = x
        self.y = y
        self.width = 96
        self.height = 96
        self.vel_x = 0
        self.vel_y = 0
        self.on_ground = False
        self.facing_right = True
        self.character_folder = character_folder or "gif/CharacterOne/"
        self.character_name = character_name
        self.character_loader = None  # 将在set_character_stats中设置
        
        # 根据角色设置属性
        self.set_character_stats(character_name)
        
        # 动画相关
        self.animation_frames = {}
        self.current_animation = 'idle'
        self.frame_index = 0
        self.animation_speed = 0.2
        self.frame_timer = 0
        
        # 加载GIF动画
        self.load_animations()
        
        self.rect = pygame.Rect(x, y, self.width, self.height)
        
        # 伤害免疫时间
        self.damage_immunity_time = 0
        self.damage_immunity_duration = 1.0  # 1秒免疫时间
        
        # 武器系统（仅哈基为角色拥有）
        if character_name == "哈基为":
            self.weapon = Weapon("meowmere")
        else:
            self.weapon = None
    
    def set_character_stats(self, character_name, character_loader=None):
        """根据角色名称设置属性"""
        # 保存character_loader引用
        self.character_loader = character_loader
        
        # 默认属性（备用）
        default_stats = {
            "attack_power": 3,
            "speed_multiplier": 1.0,
            "defense": 3,
            "jump_multiplier": 1.0,
            "max_health": 100
        }
        
        # 尝试从角色加载器获取属性
        if character_loader:
            # 根据角色名称查找对应的角色ID
            char_data = None
            for char_id, data in character_loader.characters.items():
                if data["name"] == character_name:
                    char_data = data
                    break
            
            if char_data and "stats" in char_data:
                stats = char_data["stats"]
                self.attack_power = stats.get("attack_power", default_stats["attack_power"])
                self.speed_multiplier = stats.get("speed_multiplier", default_stats["speed_multiplier"])
                self.defense = stats.get("defense", default_stats["defense"])
                self.jump_multiplier = stats.get("jump_multiplier", default_stats["jump_multiplier"])
                self.max_health = stats.get("max_health", default_stats["max_health"])
            else:
                # 使用默认属性
                self.attack_power = default_stats["attack_power"]
                self.speed_multiplier = default_stats["speed_multiplier"]
                self.defense = default_stats["defense"]
                self.jump_multiplier = default_stats["jump_multiplier"]
                self.max_health = default_stats["max_health"]
        else:
            # 兼容旧的硬编码方式（备用）
            if character_name == "哈基为":
                self.attack_power = 3
                self.speed_multiplier = 1.0
                self.defense = 3
                self.jump_multiplier = 1.0
                self.max_health = 100
            elif character_name == "哈基阳":
                self.attack_power = 2
                self.speed_multiplier = 1.6
                self.defense = 2
                self.jump_multiplier = 1.3
                self.max_health = 80
            else:  # 战士 (默认)
                self.attack_power = 4
                self.speed_multiplier = 0.7
                self.defense = 5
                self.jump_multiplier = 0.8
                self.max_health = 150
        
        # 初始化当前血量为最大血量
        self.current_health = self.max_health
    
    def load_animations(self):
        """加载GIF动画帧"""
        try:
            # 根据角色文件夹加载对应的动画
            self.animation_frames['idle'] = self.load_gif_frames(self.character_folder + 'noMoveAnimation.gif')
            self.animation_frames['move'] = self.load_gif_frames(self.character_folder + 'MoveAnimation.gif')
            self.animation_frames['sprint'] = self.load_gif_frames(self.character_folder + 'SprintAnimation.gif')
        except Exception as e:
            print(f"加载动画失败: {e}")
            # 创建备用图片
            fallback_surface = pygame.Surface((self.width, self.height))
            fallback_surface.fill(BLUE)
            self.animation_frames = {
                'idle': [fallback_surface],
                'move': [fallback_surface],
                'sprint': [fallback_surface]
            }
    
    def load_gif_frames(self, gif_path):
        """从GIF文件加载所有帧"""
        try:
            from PIL import Image
            frames = []
            
            # 打开GIF文件
            gif = Image.open(gif_path)
            
            # 提取所有帧
            frame_count = 0
            while True:
                try:
                    gif.seek(frame_count)
                    # 转换为RGBA模式
                    frame = gif.convert('RGBA')
                    # 调整大小
                    frame = frame.resize((self.width, self.height), Image.Resampling.LANCZOS)
                    
                    # 转换为pygame surface
                    frame_data = frame.tobytes()
                    pygame_surface = pygame.image.fromstring(frame_data, frame.size, 'RGBA')
                    frames.append(pygame_surface)
                    
                    frame_count += 1
                except EOFError:
                    break
            
            return frames if frames else [self.create_fallback_frame()]
            
        except ImportError:
            print("PIL库未安装，使用静态图片")
            return [self.load_static_image(gif_path)]
        except Exception as e:
            print(f"加载GIF失败 {gif_path}: {e}")
            return [self.create_fallback_frame()]
    
    def load_static_image(self, path):
        """加载静态图片作为备用"""
        try:
            image = pygame.image.load(path)
            return pygame.transform.scale(image, (self.width, self.height))
        except:
            return self.create_fallback_frame()
    
    def create_fallback_frame(self):
        """创建备用帧"""
        surface = pygame.Surface((self.width, self.height))
        surface.fill(BLUE)
        return surface
    
    def update(self, platforms, key_bindings=None, dt=1/60):
        # 处理水平移动
        keys = pygame.key.get_pressed()
        self.vel_x = 0
        is_moving = False
        is_sprinting = False
        
        # 使用自定义按键配置或默认按键
        if key_bindings:
            left_key = key_bindings.get('move_left', pygame.K_a)
            right_key = key_bindings.get('move_right', pygame.K_d)
            jump_key = key_bindings.get('jump', pygame.K_SPACE)
            sprint_key = key_bindings.get('sprint', pygame.K_LSHIFT)
        else:
            left_key = pygame.K_a
            right_key = pygame.K_d
            jump_key = pygame.K_SPACE
            sprint_key = pygame.K_LSHIFT
        
        if keys[left_key] or keys[pygame.K_LEFT]:
            self.vel_x = -PLAYER_SPEED * self.speed_multiplier  # 应用角色速度倍数
            self.facing_right = False
            is_moving = True
        if keys[right_key] or keys[pygame.K_RIGHT]:
            self.vel_x = PLAYER_SPEED * self.speed_multiplier  # 应用角色速度倍数
            self.facing_right = True
            is_moving = True
        
        # 检查是否在冲刺
        if keys[sprint_key] and is_moving:
            self.vel_x *= 1.5  # 冲刺速度加成
            is_sprinting = True
        
        # 跳跃
        if keys[jump_key] and self.on_ground:
            self.vel_y = JUMP_STRENGTH * self.jump_multiplier  # 应用角色跳跃倍数
            self.on_ground = False
        
        # 更新动画状态
        if is_sprinting:
            self.set_animation('sprint')
        elif is_moving:
            self.set_animation('move')
        else:
            self.set_animation('idle')
        
        # 更新动画帧
        self.update_animation()
        
        # 应用重力
        if not self.on_ground:
            self.vel_y += GRAVITY
        
        # 更新位置
        self.x += self.vel_x
        self.y += self.vel_y
        
        # 边界检查
        if self.x < 0:
            self.x = 0
        elif self.x > WIDTH - self.width:
            self.x = WIDTH - self.width
        
        # 更新矩形位置
        self.rect.x = self.x
        self.rect.y = self.y
        
        # 碰撞检测
        self.check_collisions(platforms)
        
        # 防止掉出屏幕底部
        if self.y > HEIGHT:
            self.y = HEIGHT - self.height
            self.vel_y = 0
            self.on_ground = True
        
        # 更新武器
        if self.weapon:
            self.weapon.update(dt)
    
    def set_animation(self, animation_name):
        """设置当前动画"""
        if animation_name != self.current_animation:
            self.current_animation = animation_name
            self.frame_index = 0
            self.frame_timer = 0
    
    def update_animation(self):
        """更新动画帧"""
        if self.current_animation in self.animation_frames:
            frames = self.animation_frames[self.current_animation]
            if len(frames) > 1:
                self.frame_timer += self.animation_speed
                if self.frame_timer >= 1.0:
                    self.frame_timer = 0
                    self.frame_index = (self.frame_index + 1) % len(frames)
    
    def get_current_frame(self):
        """获取当前动画帧"""
        if self.current_animation in self.animation_frames:
            frames = self.animation_frames[self.current_animation]
            if frames:
                return frames[self.frame_index]
        
        # 备用帧
        return self.create_fallback_frame()
    
    def check_collisions(self, platforms):
        self.on_ground = False
        
        for platform in platforms:
            if self.rect.colliderect(platform.rect):
                # 计算角色中心点
                player_center_x = self.x + self.width / 2
                player_center_y = self.y + self.height / 2
                platform_center_x = platform.x + platform.width / 2
                platform_center_y = platform.y + platform.height / 2
                
                # 计算重叠区域
                overlap_x = min(self.rect.right, platform.rect.right) - max(self.rect.left, platform.rect.left)
                overlap_y = min(self.rect.bottom, platform.rect.bottom) - max(self.rect.top, platform.rect.top)
                
                # 更精确的碰撞方向判断
                # 如果垂直重叠很小，说明是水平碰撞
                if overlap_y < overlap_x:
                    # 垂直碰撞（从上方或下方）
                    if self.vel_y > 0 and player_center_y < platform_center_y:
                        # 从上方着陆
                        self.y = platform.rect.top - self.height
                        self.vel_y = 0
                        self.on_ground = True
                    elif self.vel_y < 0 and player_center_y > platform_center_y:
                        # 从下方撞击
                        self.y = platform.rect.bottom
                        self.vel_y = 0
                else:
                    # 水平碰撞（从左侧或右侧）
                    if self.vel_x > 0 and player_center_x < platform_center_x:
                        # 从左侧碰撞
                        self.x = platform.rect.left - self.width
                        self.vel_x = 0
                    elif self.vel_x < 0 and player_center_x > platform_center_x:
                        # 从右侧碰撞
                        self.x = platform.rect.right
                        self.vel_x = 0
                
                # 更新矩形位置
                self.rect.x = self.x
                self.rect.y = self.y
    
    def take_damage(self, damage):
        """玩家受到伤害"""
        import time
        current_time = time.time()
        
        # 检查是否在免疫时间内
        if current_time - self.damage_immunity_time < self.damage_immunity_duration:
            return False  # 免疫伤害
        
        # 计算实际伤害（攻击力 - 防御力，最少1点伤害）
        actual_damage = max(1, damage - self.defense)
        
        # 扣除血量
        self.current_health -= actual_damage
        if self.current_health < 0:
            self.current_health = 0
        
        # 设置免疫时间
        self.damage_immunity_time = current_time
        
        print(f"玩家受到 {actual_damage} 点伤害（原始伤害: {damage}, 防御力: {self.defense}），剩余血量: {self.current_health}/{self.max_health}")
        
        return True  # 成功造成伤害
    
    def draw(self, screen):
        # 获取当前动画帧
        current_frame = self.get_current_frame()
        
        # 检查当前动画是否需要特殊翻转处理
        should_flip_animation = False
        if self.character_loader and hasattr(self, 'character_name'):
            # 根据角色名称查找对应的角色ID
            char_id = None
            for cid, data in self.character_loader.characters.items():
                if data["name"] == self.character_name:
                    char_id = cid
                    break
            
            if char_id:
                should_flip_animation = self.character_loader.should_flip_animation(char_id, self.current_animation)
        
        # 决定是否翻转图片
        need_flip = False
        if should_flip_animation:
            # 如果动画本身需要翻转，则反转facing_right的逻辑
            need_flip = self.facing_right
        else:
            # 正常逻辑：面向左边时翻转
            need_flip = not self.facing_right
        
        # 准备要绘制的帧
        frame_to_draw = current_frame
        if need_flip:
            frame_to_draw = pygame.transform.flip(current_frame, True, False)
        
        # 检查是否在免疫时间内，添加闪烁效果
        import time
        current_time = time.time()
        if current_time - self.damage_immunity_time < self.damage_immunity_duration:
            # 闪烁效果：每0.1秒切换一次透明度
            if int((current_time - self.damage_immunity_time) * 10) % 2 == 0:
                # 创建半透明效果
                alpha_surface = frame_to_draw.copy()
                alpha_surface.set_alpha(128)  # 50%透明度
                screen.blit(alpha_surface, (self.x, self.y))
            else:
                screen.blit(frame_to_draw, (self.x, self.y))
        else:
            # 正常绘制
            screen.blit(frame_to_draw, (self.x, self.y))
        
        # 绘制武器
        if self.weapon:
            mouse_x, mouse_y = pygame.mouse.get_pos()
            self.weapon.draw(screen, self.x, self.y, mouse_x, mouse_y, self.facing_right)

class Platform:
    def __init__(self, x, y, width, height):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.rect = pygame.Rect(x, y, width, height)
        
        # 加载平台图片
        try:
            self.image = pygame.image.load('img/platform.svg')
            # 创建平铺的平台
            self.surface = pygame.Surface((width, height))
            tile_width = 64
            tile_height = 48
            
            for i in range(0, width, tile_width):
                for j in range(0, height, tile_height):
                    self.surface.blit(self.image, (i, j))
        except:
            # 如果加载失败，创建一个简单的矩形
            self.surface = pygame.Surface((width, height))
            self.surface.fill(BROWN)
            # 添加草地顶部
            pygame.draw.rect(self.surface, GREEN, (0, 0, width, 4))
    
    def draw(self, screen):
        screen.blit(self.surface, (self.x, self.y))

class Portal:
    def __init__(self, x, y, width, height, target_map, portal_type="level_portal"):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.target_map = target_map
        self.portal_type = portal_type
        self.rect = pygame.Rect(x, y, width, height)
        self.animation_time = 0
        
    def update(self, dt):
        self.animation_time += dt
        
    def draw(self, screen):
        # 绘制传送门动画效果
        # 外圈发光效果
        glow_color = (100 + int(50 * abs(math.sin(self.animation_time * 3))), 
                     200 + int(55 * abs(math.sin(self.animation_time * 2))), 
                     255)
        pygame.draw.rect(screen, glow_color, 
                        (self.x - 5, self.y - 5, self.width + 10, self.height + 10), 3)
        
        # 内部传送门
        portal_color = (50 + int(30 * abs(math.sin(self.animation_time * 4))), 
                       150 + int(50 * abs(math.sin(self.animation_time * 3))), 
                       200 + int(55 * abs(math.sin(self.animation_time * 2))))
        pygame.draw.rect(screen, portal_color, self.rect)
        
        # 中心亮点
        center_x = self.x + self.width // 2
        center_y = self.y + self.height // 2
        center_color = (255, 255, 255, int(128 + 127 * abs(math.sin(self.animation_time * 5))))
        pygame.draw.circle(screen, center_color[:3], (center_x, center_y), 8)
        
        # 传送门标识文字
        font = pygame.font.Font(None, 24)
        text = font.render("NEXT", True, (255, 255, 255))
        text_rect = text.get_rect(center=(center_x, self.y - 20))
        screen.blit(text, text_rect)

class Enemy:
    def __init__(self, enemy_data):
        self.type = enemy_data['type']
        self.variant = enemy_data['variant']
        self.x = enemy_data['x']
        self.y = enemy_data['y']
        self.width = 64
        self.height = 64
        self.vel_x = 0
        self.vel_y = 0
        self.on_ground = False
        
        # 为多人模式添加唯一ID
        import uuid
        if 'deterministic_id' in enemy_data:
            # 在多人模式下使用确定性ID
            self.enemy_id = enemy_data['deterministic_id']
        else:
            # 单人模式或旧版本兼容，使用随机ID
            self.enemy_id = enemy_data.get('enemy_id', str(uuid.uuid4())[:8])
        
        # 敌怪属性
        self.max_health = enemy_data['health']
        self.current_health = self.max_health
        self.attack_power = enemy_data['attack_power']
        self.speed = enemy_data['speed']
        self.patrol_range = enemy_data['patrol_range']
        self.aggro_range = enemy_data['aggro_range']
        
        # AI状态
        self.state = 'patrol'  # patrol, chase, attack, idle
        self.target_player = None
        self.patrol_start_x = self.x
        self.patrol_direction = 1
        self.last_attack_time = 0
        self.attack_cooldown = 1.0  # 攻击冷却时间
        
        # 特殊属性
        if self.type == 'slime':
            self.jump_strength = enemy_data.get('jump_strength', 75)  # 跳跃高度三倍
            self.jump_timer = 0
            self.jump_interval = 2.0  # 史莱姆跳跃间隔
        elif self.type == 'spider':
            self.wall_crawl = enemy_data.get('wall_crawl', False)
        elif self.type == 'vulture':
            self.flight_height_min = enemy_data.get('flight_height_min', 'HEIGHT - 600')
            self.flight_height_max = enemy_data.get('flight_height_max', 'HEIGHT - 300')
            self.flying = True
        
        # 动画相关
        self.animation_frames = {}
        self.current_animation = 'idle'
        self.frame_index = 0
        self.animation_speed = 0.05  # 加快动画速度，从0.1改为0.05
        self.frame_timer = 0
        self.facing_right = True
        
        # 秃鹫旋转角度
        self.rotation = 0
        
        # 加载动画
        self.load_animations()
        
        self.rect = pygame.Rect(self.x, self.y, self.width, self.height)
    
    def load_animations(self):
        """加载敌怪动画"""
        try:
            if self.type == 'slime':
                gif_path = f'enemy/slime/{self.variant.title()}_Slime.gif'
                frames = self.load_gif_frames(gif_path)
                if frames:
                    self.animation_frames['idle'] = frames
                    self.animation_frames['move'] = frames
                    self.animation_frames['jump'] = frames
            elif self.type == 'spider':
                if self.variant == 'ground_static':
                    gif_path = 'enemy/spider/Black_Recluse_(ground).gif'
                elif self.variant == 'ground_crawling':
                    gif_path = 'enemy/spider/Black_Recluse_(ground).gif'
                else:  # wall_crawling
                    gif_path = 'enemy/spider/Black_Recluse.gif'
                frames = self.load_gif_frames(gif_path)
                if frames:
                    self.animation_frames['idle'] = frames
                    self.animation_frames['move'] = frames
            elif self.type == 'vulture':
                # 加载两个方向的动画
                gif_path_left = 'enemy/vulture/Vulture_(flying).gif'  # 向左飞行（原始）
                gif_path_right = 'enemy/vulture/Vulture_(flying)_flipped.gif'  # 向右飞行（翻转）
                
                frames_left = self.load_gif_frames(gif_path_left)
                frames_right = self.load_gif_frames(gif_path_right)
                
                if frames_left and frames_right:
                    self.animation_frames['fly_left'] = frames_left
                    self.animation_frames['fly_right'] = frames_right
                    # 默认动画使用向左飞行
                    self.animation_frames['idle'] = frames_left
                    self.animation_frames['move'] = frames_left
                    self.animation_frames['fly'] = frames_left
                elif frames_left:
                    # 如果翻转文件不存在，使用原始文件
                    self.animation_frames['idle'] = frames_left
                    self.animation_frames['move'] = frames_left
                    self.animation_frames['fly'] = frames_left
                    self.animation_frames['fly_left'] = frames_left
                    self.animation_frames['fly_right'] = frames_left
        except Exception as e:
            print(f"加载敌怪动画失败: {e}")
            # 创建默认动画帧
            self.create_fallback_frames()
    
    def load_gif_frames(self, gif_path):
        """加载GIF动画帧"""
        try:
            from PIL import Image
            frames = []
            with Image.open(gif_path) as img:
                for frame_num in range(img.n_frames):
                    img.seek(frame_num)
                    frame = img.copy().convert('RGBA')
                    # 调整大小
                    frame = frame.resize((self.width, self.height), Image.Resampling.LANCZOS)
                    # 转换为pygame surface
                    mode = frame.mode
                    size = frame.size
                    data = frame.tobytes()
                    pygame_surface = pygame.image.fromstring(data, size, mode)
                    frames.append(pygame_surface)
            return frames
        except Exception as e:
            print(f"加载GIF失败 {gif_path}: {e}")
            return None
    
    def create_fallback_frames(self):
        """创建默认动画帧"""
        surface = pygame.Surface((self.width, self.height))
        if self.type == 'slime':
            if self.variant == 'blue':
                surface.fill((0, 100, 255))
            elif self.variant == 'green':
                surface.fill((0, 255, 100))
            else:  # lava
                surface.fill((255, 100, 0))
        elif self.type == 'spider':
            surface.fill((50, 50, 50))
        elif self.type == 'vulture':
            surface.fill((139, 69, 19))
        
        self.animation_frames = {
            'idle': [surface],
            'move': [surface],
            'jump': [surface],
            'fly': [surface]
        }
    
    def update(self, dt, player, platforms, other_players=None):
        """更新敌怪状态"""
        if self.current_health <= 0:
            return  # 敌怪已死亡
        
        # 更新AI状态
        self.update_ai(player, other_players)
        
        # 根据类型更新移动
        if self.type == 'slime':
            self.update_slime_movement(dt, platforms)
        elif self.type == 'spider':
            self.update_spider_movement(dt, platforms)
        elif self.type == 'vulture':
            self.update_vulture_movement(dt)
        
        # 更新动画
        self.update_animation(dt)
        
        # 更新矩形位置
        self.rect.x = self.x
        self.rect.y = self.y
    
    def update_physics_only(self, dt, platforms):
        """只更新物理状态，不进行AI计算（用于非房主玩家）"""
        if self.current_health <= 0:
            return  # 敌怪已死亡
        
        # 根据类型更新基本物理（重力、碰撞等），保持当前移动方向
        if self.type == 'slime':
            # 保持水平移动
            self.x += self.vel_x * dt * 60
            # 应用重力
            self.vel_y += GRAVITY
            # 更新位置
            self.y += self.vel_y * dt * 60
            # 检查碰撞
            self.check_collisions(platforms)
        elif self.type == 'spider':
            if self.variant in ['ground_static', 'ground_crawling']:
                # 保持水平移动
                self.x += self.vel_x * dt * 60
                # 应用重力
                self.vel_y += GRAVITY
                # 更新位置
                self.y += self.vel_y * dt * 60
                # 检查碰撞
                self.check_collisions(platforms)
            elif self.variant == 'wall_crawling':
                # 墙爬蜘蛛保持当前移动
                self.x += self.vel_x * dt * 60
                self.y += self.vel_y * dt * 60
        elif self.type == 'vulture':
            # 飞行敌人保持当前移动
            self.x += self.vel_x * dt * 60
            self.y += self.vel_y * dt * 60
        
        # 更新动画
        self.update_animation(dt)
        
        # 更新矩形位置
        self.rect.x = int(self.x)
        self.rect.y = int(self.y)
    
    def update_ai(self, player, other_players=None):
        """更新AI状态 - 仇恨机制"""
        import math
        
        # 收集所有玩家
        all_players = [player]
        if other_players:
            all_players.extend(other_players)
        
        # 寻找最近的玩家作为目标
        target_player = None
        min_distance = float('inf')
        
        for p in all_players:
            if p and hasattr(p, 'x') and hasattr(p, 'y'):
                distance = math.sqrt((self.x - p.x)**2 + (self.y - p.y)**2)
                if distance < min_distance:
                    min_distance = distance
                    target_player = p
        
        if not target_player:
            return
        
        # 根据距离更新AI状态
        if min_distance <= self.aggro_range:
            old_state = self.state
            self.state = 'chase'
            self.target_player = target_player
            # 面向目标玩家
            if target_player.x > self.x:
                self.facing_right = True
            else:
                self.facing_right = False
            
            # 状态变化
            if old_state != self.state:
                pass  # 进入追击状态
        elif min_distance > self.aggro_range * 1.5:  # 脱离仇恨范围
            if self.state != 'patrol':
                pass  # 脱离仇恨，回到巡逻状态
            self.state = 'patrol'
            self.target_player = None
        
        # 在追击状态下，如果距离很近，切换到攻击状态
        if self.state == 'chase' and min_distance <= 80:  # 攻击范围
            self.state = 'attack'
        elif self.state == 'attack' and min_distance > 120:  # 脱离攻击范围
            self.state = 'chase'
    
    def update_slime_movement(self, dt, platforms):
        """更新史莱姆移动"""
        pass
    
    def update_spider_movement(self, dt, platforms):
        """更新蜘蛛移动"""
        pass
    
    def update_vulture_movement(self, dt):
        """更新秃鹫移动"""
        pass
    
    def check_collisions(self, platforms):
        """敌怪碰撞检测"""
        self.on_ground = False
        
        for platform in platforms:
            if self.rect.colliderect(platform.rect):
                # 计算重叠区域
                overlap_x = min(self.rect.right, platform.rect.right) - max(self.rect.left, platform.rect.left)
                overlap_y = min(self.rect.bottom, platform.rect.bottom) - max(self.rect.top, platform.rect.top)
                
                if overlap_y < overlap_x:
                    # 垂直碰撞
                    if self.vel_y > 0:  # 从上方着陆
                        self.y = platform.rect.top - self.height
                        self.vel_y = 0
                        self.on_ground = True
                    elif self.vel_y < 0:  # 从下方撞击
                        self.y = platform.rect.bottom
                        self.vel_y = 0
                else:
                    # 水平碰撞
                    if self.vel_x > 0:  # 从左侧碰撞
                        self.x = platform.rect.left - self.width
                        self.vel_x = 0
                        # 史莱姆碰到墙壁时改变巡逻方向
                        if self.type == 'slime' and self.state == 'patrol':
                            self.patrol_direction *= -1
                    elif self.vel_x < 0:  # 从右侧碰撞
                        self.x = platform.rect.right
                        self.vel_x = 0
                        # 史莱姆碰到墙壁时改变巡逻方向
                        if self.type == 'slime' and self.state == 'patrol':
                            self.patrol_direction *= -1
    
    def update_animation(self, dt):
        """更新动画"""
        if not self.animation_frames or self.current_animation not in self.animation_frames:
            return
        
        self.frame_timer += dt
        if self.frame_timer >= self.animation_speed:
            self.frame_timer = 0
            frames = self.animation_frames[self.current_animation]
            self.frame_index = (self.frame_index + 1) % len(frames)
    
    def get_current_frame(self):
        """获取当前动画帧"""
        if (self.current_animation in self.animation_frames and 
            self.animation_frames[self.current_animation]):
            frames = self.animation_frames[self.current_animation]
            return frames[self.frame_index % len(frames)]
        return None
    
    def draw(self, screen):
        """绘制敌怪"""
        frame = self.get_current_frame()
        if frame:
            # 根据敌怪类型调整尺寸
            if self.type == 'spider':
                if self.variant == 'wall_crawling':
                    # 墙上蜘蛛放大1.5倍
                    frame = pygame.transform.scale(frame, (int(frame.get_width() * 1.5), int(frame.get_height() * 1.5)))
                else:
                    # 普通蜘蛛宽度增加30%
                    frame = pygame.transform.scale(frame, (int(frame.get_width() * 1.3), frame.get_height()))
            elif self.type == 'vulture':
                # 秃鹫放大1.4倍
                frame = pygame.transform.scale(frame, (int(frame.get_width() * 1.4), int(frame.get_height() * 1.4)))
                
                # 秃鹫旋转处理（斜向飞行时应用旋转）
                if hasattr(self, 'rotation') and self.rotation != 0:
                    # 根据飞行方向调整旋转角度
                    if self.facing_right:
                        # 向右飞行，直接应用旋转角度
                        frame = pygame.transform.rotate(frame, -self.rotation)
                    else:
                        # 向左飞行，需要镜像旋转角度
                        frame = pygame.transform.rotate(frame, self.rotation)
                
                # 计算旋转后的绘制位置（居中）
                frame_rect = frame.get_rect()
                draw_x = self.x - (frame_rect.width - self.width) // 2
                draw_y = self.y - (frame_rect.height - self.height) // 2
                screen.blit(frame, (draw_x, draw_y))
                return
            
            # 其他敌怪的正常处理
            # 根据朝向翻转
            if not self.facing_right:
                frame = pygame.transform.flip(frame, True, False)
            screen.blit(frame, (self.x, self.y))
        else:
            # 绘制默认矩形
            color = (255, 0, 0) if self.type == 'slime' else (100, 100, 100)
            pygame.draw.rect(screen, color, self.rect)
        
        # 绘制血条
        if self.current_health < self.max_health:
            bar_width = self.width
            bar_height = 6
            bar_x = self.x
            bar_y = self.y - 10
            
            # 背景
            pygame.draw.rect(screen, (100, 100, 100), (bar_x, bar_y, bar_width, bar_height))
            # 血量
            health_ratio = self.current_health / self.max_health
            health_width = int(bar_width * health_ratio)
            health_color = (255, 0, 0) if health_ratio < 0.3 else (255, 255, 0) if health_ratio < 0.7 else (0, 255, 0)
            pygame.draw.rect(screen, health_color, (bar_x, bar_y, health_width, bar_height))
    
    def take_damage(self, damage):
        """受到伤害"""
        self.current_health -= damage
        if self.current_health <= 0:
            self.current_health = 0
            return True  # 敌怪死亡
        return False
    
    def can_attack(self):
        """检查是否可以攻击"""
        import time
        current_time = time.time()
        
        # 检查攻击冷却时间
        if current_time - self.last_attack_time < self.attack_cooldown:
            return False
        
        # 在追击或攻击状态下都可以攻击
        return self.state in ['chase', 'attack']
    
    def attack(self, player):
        """攻击玩家"""
        import time
        current_time = time.time()
        
        # 更新最后攻击时间
        self.last_attack_time = current_time
        
        # 根据敌怪类型设置攻击力
        if self.type == 'slime':
            damage = 10
        elif self.type == 'vulture':
            damage = 15
        elif self.type == 'spider':
            damage = 25
        else:
            damage = self.attack_power  # 使用默认攻击力
        
        print(f"{self.type}({self.variant}) 攻击玩家，造成 {damage} 点伤害")
        return damage

class Game:
    def __init__(self):
        # 设置相关
        self.fullscreen = False
        self.current_resolution = (WIDTH, HEIGHT)
        # 固定分辨率为1920x1080，不可更改
        self.available_resolutions = [(1920, 1080)]
        self.resolution_index = 0  # 固定1920x1080
        
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("耄耋的家园")
        self.clock = pygame.time.Clock()
        self.state = MAIN_MENU
        
        # 游戏模式和玩家信息
        self.game_mode = None
        self.player_name = ""
        self.selected_character = 0  # 角色选择索引
        
        # 游戏对象（初始化为None，在开始游戏时创建）
        self.player = None
        self.platforms = None
        self.portals = []
        self.enemies = []  # 敌怪列表
        
        # 网络相关
        self.network_client = None
        self.multiplayer_mode = False
        
        # UI相关
        self.menu_selection = 0
        self.mode_selection = 0
        self.settings_selection = 0
        self.room_selection = 0
        self.input_active = False
        self.temp_name = ""
        
        # 房间相关
        self.room_ip = "localhost"
        self.previous_state = None  # 记录进入角色选择前的状态
        self.character_selected = False  # 记录角色是否已选择完成
        self.room_port = "12345"
        self.room_players = {}
        self.local_server = None
        self.ping_time = 0
        
        # 传送门相关
        self.portal_message_timer = 0  # 传送门等待消息显示计时器
        
        # 脏矩形更新相关
        self.dirty_rects = []  # 存储需要更新的矩形区域
        self.use_dirty_rects = True  # 是否启用脏矩形更新
        self.last_frame_objects = {}  # 存储上一帧的对象位置信息
        self.input_field = "ip"  # "ip" 或 "port"
        self.last_character_send_time = 0  # 上次发送角色选择信息的时间
        
        # 房间解散相关
        
        # 地图相关
        self.available_map_series = []
        self.selected_series = 0
        self.selected_level = 0
        self.current_map_data = None
        self.current_series_data = None
        self.load_available_map_series()
        self.room_disbanded_message = None
        self.room_disbanded_time = 0
        self.show_disbanded_message = False
        
        # 字体缓存
        self.font_cache = {}
        
        # 按键配置
        self.key_bindings = {
            'move_left': pygame.K_a,
            'move_right': pygame.K_d,
            'jump': pygame.K_SPACE,
            'sprint': pygame.K_LSHIFT,
            'pause': pygame.K_ESCAPE,
            'confirm': pygame.K_RETURN,
            'cancel': pygame.K_ESCAPE,
            'menu_up': pygame.K_UP,
            'menu_down': pygame.K_DOWN,
            'menu_left': pygame.K_LEFT,
            'menu_right': pygame.K_RIGHT
        }
        self.key_binding_names = {
            'move_left': '向左移动',
            'move_right': '向右移动', 
            'jump': '跳跃',
            'sprint': '冲刺',
            'pause': '暂停/取消',
            'confirm': '确认',
            'cancel': '取消',
            'menu_up': '菜单向上',
            'menu_down': '菜单向下',
            'menu_left': '菜单向左',
            'menu_right': '菜单向右'
        }
        self.waiting_for_key = None
        self.key_binding_selection = 0  # 当前等待设置的按键
        
        # 角色加载器和选项
        self.character_loader = CharacterLoader()
        self.character_options = self.character_loader.get_character_options()
        
        # 角色预览动画
        self.character_preview_animations = {}
        self.load_character_previews()
        
        # 加载背景
        try:
            self.background = pygame.image.load('img/background.svg')
            self.background = pygame.transform.scale(self.background, (WIDTH, HEIGHT))
        except:
            self.background = None
        
        # 音量控制
        self.master_volume = 0.5  # 主音量 (0.0 - 1.0)
        
        # 音乐状态跟踪
        self.current_music = None  # 当前播放的音乐文件
        self.music_files = {
            'menu': 'music/hudmusic.mp3',
            'game': 'music/BackgroundMusic.mp3'
        }
        
        # 初始化音乐系统
        pygame.mixer.init()
        
        # 开始播放菜单音乐
        self.play_music('menu')
        
        # 动画图片相关
        self.crawling_animations = []
        self.load_crawling_animation()
    
    def play_music(self, music_type):
        """播放指定类型的音乐"""
        if music_type not in self.music_files:
            print(f"未知的音乐类型: {music_type}")
            return
        
        music_file = self.music_files[music_type]
        
        # 如果已经在播放相同的音乐，则不需要切换
        if self.current_music == music_file:
            return
        
        try:
            # 停止当前音乐
            pygame.mixer.music.stop()
            
            # 加载新音乐
            pygame.mixer.music.load(music_file)
            pygame.mixer.music.set_volume(self.master_volume)
            pygame.mixer.music.play(-1)  # 循环播放
            
            self.current_music = music_file
            print(f"开始播放音乐: {music_file}")
        except Exception as e:
            print(f"无法加载音乐文件 {music_file}: {e}")
    
    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            elif event.type == pygame.KEYDOWN:
                if self.state == MAIN_MENU:
                    self.handle_main_menu_input(event.key)
                elif self.state == MODE_SELECT:
                    self.handle_mode_select_input(event.key)
                elif self.state == CHARACTER_SELECT:
                    self.handle_character_select_input(event.key)
                elif self.state == PLAYING:
                    if event.key == pygame.K_ESCAPE:
                        self.state = PAUSED
                elif self.state == PAUSED:
                    if event.key == pygame.K_ESCAPE:
                        self.state = PLAYING
                    elif event.key == pygame.K_q:
                        self.state = MAIN_MENU
                        self.cleanup_game()
                elif self.state == SETTINGS:
                    self.handle_settings_input(event.key)
                elif self.state == KEY_BINDING:
                    self.handle_key_binding_input(event.key)
                elif self.state == CREATE_ROOM:
                    self.handle_create_room_input(event.key)
                elif self.state == JOIN_ROOM:
                    self.handle_join_room_input(event.key)
                elif self.state == WAITING_ROOM:
                    self.handle_waiting_room_input(event.key)
                elif event.key == pygame.K_r and self.state == GAME_OVER:
                     self.restart_game()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # 左键点击
                    if self.state == MAIN_MENU:
                        self.handle_main_menu_click(event.pos)
                    elif self.state == MODE_SELECT:
                        self.handle_mode_select_click(event.pos)
                    elif self.state == CHARACTER_SELECT:
                        self.handle_character_select_click(event.pos)
                    elif self.state == SETTINGS:
                        self.handle_settings_click(event.pos)
                    elif self.state == KEY_BINDING:
                        self.handle_key_binding_click(event.pos)
                    elif self.state == CREATE_ROOM:
                        self.handle_create_room_click(event.pos)
                    elif self.state == JOIN_ROOM:
                        self.handle_join_room_click(event.pos)
                    elif self.state == WAITING_ROOM:
                        self.handle_waiting_room_click(event.pos)
                    elif self.state == PAUSED:
                        self.handle_paused_click(event.pos)
                    elif self.state == PLAYING:
                        # 处理武器攻击
                        if hasattr(self, 'player') and self.player and self.player.weapon:
                            if self.player.weapon.can_attack():
                                mouse_x, mouse_y = event.pos
                                projectile = self.player.weapon.attack(
                                    self.player.x,
                                    self.player.y,
                                    mouse_x, mouse_y,
                                    self.player.attack_power
                                )
                                if projectile:
                                    if not hasattr(self, 'projectiles'):
                                        self.projectiles = []
                                    
                                    # 限制弹幕数量以优化性能
                                    if len(self.projectiles) >= self.max_projectiles:
                                        # 移除最旧的弹幕
                                        self.projectiles.pop(0)
                                    
                                    self.projectiles.append(projectile)
                elif event.button == 4:  # 鼠标滚轮向上
                    if self.state == KEY_BINDING:
                        self.handle_key_binding_scroll(-1)
                elif event.button == 5:  # 鼠标滚轮向下
                    if self.state == KEY_BINDING:
                        self.handle_key_binding_scroll(1)
            elif event.type == pygame.TEXTINPUT:
                if self.input_active and len(self.temp_name) < 12:  # 角色名输入
                    self.temp_name += event.text
                elif self.state == JOIN_ROOM:  # 房间IP/端口输入
                    if self.input_field == "ip" and len(self.room_ip) < 15:
                        # 只允许数字、点和字母
                        if event.text.replace('.', '').replace('localhost', '').isdigit() or event.text in '.localhost':
                            self.room_ip += event.text
                    elif self.input_field == "port" and len(self.room_port) < 5:
                        # 只允许数字
                        if event.text.isdigit():
                            self.room_port += event.text
        
        return True
    
    def handle_main_menu_input(self, key):
        if key == pygame.K_UP:
            self.menu_selection = (self.menu_selection - 1) % 3
        elif key == pygame.K_DOWN:
            self.menu_selection = (self.menu_selection + 1) % 3
        elif key == pygame.K_RETURN or key == pygame.K_SPACE:
            if self.menu_selection == 0:  # 开始游戏
                self.state = MODE_SELECT
            elif self.menu_selection == 1:  # 设置
                self.state = SETTINGS
            elif self.menu_selection == 2:  # 退出游戏
                pygame.quit()
                sys.exit()
    
    def handle_main_menu_click(self, mouse_pos):
        """处理主菜单鼠标点击"""
        mouse_x, mouse_y = mouse_pos
        menu_area_y = int(HEIGHT * 0.45)
        
        # 检查每个菜单选项的点击区域
        for i in range(3):  # 3个菜单选项
            y_pos = menu_area_y + i * int(HEIGHT * 0.12)
            option_bg = pygame.Rect(WIDTH//2 - int(WIDTH * 0.15), y_pos - int(HEIGHT * 0.04), int(WIDTH * 0.3), int(HEIGHT * 0.08))
            
            if option_bg.collidepoint(mouse_x, mouse_y):
                self.menu_selection = i
                # 执行选择的操作
                if i == 0:  # 开始游戏
                    self.state = MODE_SELECT
                elif i == 1:  # 设置
                    self.state = SETTINGS
                elif i == 2:  # 退出游戏
                    pygame.quit()
                    sys.exit()
                break
    
    def handle_mode_select_click(self, mouse_pos):
        """处理模式选择页面鼠标点击"""
        mouse_x, mouse_y = mouse_pos
        mode_area_y = int(HEIGHT * 0.4)
        
        # 检查每个模式选项的点击区域
        for i in range(2):  # 2个模式选项
            y_pos = mode_area_y + i * int(HEIGHT * 0.18)
            mode_bg = pygame.Rect(WIDTH//2 - int(WIDTH * 0.35), y_pos - int(HEIGHT * 0.06), int(WIDTH * 0.7), int(HEIGHT * 0.12))
            
            if mode_bg.collidepoint(mouse_x, mouse_y):
                self.mode_selection = i
                # 执行选择的操作
                if i == 0:  # 开房间
                    self.game_mode = HOST_ROOM
                    self.state = CREATE_ROOM
                elif i == 1:  # 加入房间
                    self.game_mode = JOIN_ROOM_MODE
                    self.state = JOIN_ROOM
                break
        
        # 检查返回按钮点击
        back_button_y = int(HEIGHT * 0.85)
        back_bg = pygame.Rect(WIDTH//2 - int(WIDTH * 0.12), back_button_y - int(HEIGHT * 0.035), int(WIDTH * 0.24), int(HEIGHT * 0.07))
        
        if back_bg.collidepoint(mouse_x, mouse_y):
            self.state = MAIN_MENU
    
    def handle_character_select_click(self, mouse_pos):
        """处理角色选择页面鼠标点击"""
        mouse_x, mouse_y = mouse_pos
        
        # 左侧角色显示区域的箭头按钮
        char_area_x = WIDTH // 15
        char_area_y = HEIGHT // 5
        char_area_width = int(WIDTH * 0.375)
        char_area_height = int(HEIGHT * 0.54)
        char_center_y = char_area_y + int(char_area_height * 0.43)
        
        arrow_btn_size = int(min(WIDTH, HEIGHT) * 0.062)
        arrow_offset = int(char_area_width * 0.033)
        
        # 检查左箭头点击
        if self.selected_character > 0:
            left_bg = pygame.Rect(char_area_x + arrow_offset, char_center_y - arrow_btn_size//2, arrow_btn_size, arrow_btn_size)
            if left_bg.collidepoint(mouse_x, mouse_y):
                self.selected_character = (self.selected_character - 1) % len(self.character_options)
                return
        
        # 检查右箭头点击
        if self.selected_character < len(self.character_options) - 1:
            right_bg = pygame.Rect(char_area_x + char_area_width - arrow_offset - arrow_btn_size, char_center_y - arrow_btn_size//2, arrow_btn_size, arrow_btn_size)
            if right_bg.collidepoint(mouse_x, mouse_y):
                self.selected_character = (self.selected_character + 1) % len(self.character_options)
                return
        
        # 检查名称输入框点击
        name_y = int(HEIGHT * 0.89)
        box_width = int(WIDTH * 0.23)
        name_box_rect = pygame.Rect(WIDTH//2 - box_width//2, name_y + 8, box_width, 25)
        
        if name_box_rect.collidepoint(mouse_x, mouse_y):
            if not self.input_active:
                self.input_active = True
                self.temp_name = self.player_name
        else:
            # 点击其他地方时，如果正在输入则确认输入
            if self.input_active:
                self.player_name = self.temp_name
                self.input_active = False
    
    def handle_settings_click(self, mouse_pos):
        """处理设置页面鼠标点击"""
        mouse_x, mouse_y = mouse_pos
        settings_area_y = int(HEIGHT * 0.35)
        
        # 检查全屏设置点击
        fullscreen_y = settings_area_y
        fullscreen_bg = pygame.Rect(WIDTH//2 - int(WIDTH * 0.25), fullscreen_y - int(HEIGHT * 0.04), int(WIDTH * 0.5), int(HEIGHT * 0.08))
        
        if fullscreen_bg.collidepoint(mouse_x, mouse_y):
            self.settings_selection = 0
            self.toggle_fullscreen()
            return
        
        # 检查分辨率设置点击（已禁用调整功能）
        resolution_y = settings_area_y + int(HEIGHT * 0.12)
        resolution_bg = pygame.Rect(WIDTH//2 - int(WIDTH * 0.25), resolution_y - int(HEIGHT * 0.04), int(WIDTH * 0.5), int(HEIGHT * 0.08))
        
        if resolution_bg.collidepoint(mouse_x, mouse_y):
            self.settings_selection = 1
            # 分辨率已固定，不允许调整
            return
        
        # 检查音量控制点击
        volume_y = settings_area_y + int(HEIGHT * 0.24)
        volume_bg = pygame.Rect(WIDTH//2 - int(WIDTH * 0.25), volume_y - int(HEIGHT * 0.04), int(WIDTH * 0.5), int(HEIGHT * 0.08))
        
        if volume_bg.collidepoint(mouse_x, mouse_y):
            self.settings_selection = 2
            # 检查是否点击了左右箭头区域
            left_arrow_area = pygame.Rect(volume_bg.left, volume_bg.top, int(WIDTH * 0.08), volume_bg.height)
            right_arrow_area = pygame.Rect(volume_bg.right - int(WIDTH * 0.08), volume_bg.top, int(WIDTH * 0.08), volume_bg.height)
            
            if left_arrow_area.collidepoint(mouse_x, mouse_y):
                # 减少音量
                self.master_volume = max(0.0, self.master_volume - 0.1)
                pygame.mixer.music.set_volume(self.master_volume)
            elif right_arrow_area.collidepoint(mouse_x, mouse_y):
                # 增加音量
                self.master_volume = min(1.0, self.master_volume + 0.1)
                pygame.mixer.music.set_volume(self.master_volume)
            return
        
        # 检查按键配置点击
        keybind_y = settings_area_y + int(HEIGHT * 0.36)
        keybind_bg = pygame.Rect(WIDTH//2 - int(WIDTH * 0.25), keybind_y - int(HEIGHT * 0.04), int(WIDTH * 0.5), int(HEIGHT * 0.08))
        
        if keybind_bg.collidepoint(mouse_x, mouse_y):
            self.settings_selection = 3
            self.state = KEY_BINDING
            return
        
        # 检查返回主菜单点击
        back_y = settings_area_y + int(HEIGHT * 0.48)
        back_bg = pygame.Rect(WIDTH//2 - int(WIDTH * 0.25), back_y - int(HEIGHT * 0.04), int(WIDTH * 0.5), int(HEIGHT * 0.08))
        
        if back_bg.collidepoint(mouse_x, mouse_y):
            self.settings_selection = 4
            self.state = MAIN_MENU
            return
    
    def handle_key_binding_click(self, mouse_pos):
        """处理按键配置页面鼠标点击"""
        mouse_x, mouse_y = mouse_pos
        settings_area_y = int(HEIGHT * 0.15)
        
        # 初始化滚动偏移（如果没有的话）
        if not hasattr(self, 'key_binding_scroll_offset'):
            self.key_binding_scroll_offset = 0
        
        # 计算可显示的选项数量
        key_names = list(self.key_bindings.keys())
        option_height = int(HEIGHT * 0.065)
        option_spacing = int(HEIGHT * 0.07)
        visible_area_height = int(HEIGHT * 0.7)
        max_visible_options = visible_area_height // option_spacing
        
        # 检查可见按键选项点击
        for i in range(max_visible_options):
            option_index = i + self.key_binding_scroll_offset
            if option_index >= len(key_names):
                break
                
            key_name = key_names[option_index]
            option_y = settings_area_y + i * option_spacing
            option_bg = pygame.Rect(WIDTH//2 - int(WIDTH * 0.4), option_y - int(HEIGHT * 0.025), int(WIDTH * 0.8), option_height)
            
            if option_bg.collidepoint(mouse_x, mouse_y):
                self.key_binding_selection = option_index
                if not self.waiting_for_key:
                    self.waiting_for_key = key_name
                return
        
        # 检查返回设置点击（固定在底部）
        back_y = int(HEIGHT * 0.9)
        back_bg = pygame.Rect(WIDTH//2 - int(WIDTH * 0.2), back_y - int(HEIGHT * 0.025), int(WIDTH * 0.4), option_height)
        
        if back_bg.collidepoint(mouse_x, mouse_y):
            self.key_binding_selection = len(key_names)
            self.state = SETTINGS
            return
    
    def handle_key_binding_scroll(self, direction):
        """处理按键配置页面鼠标滚轮滚动"""
        # 初始化滚动偏移（如果没有的话）
        if not hasattr(self, 'key_binding_scroll_offset'):
            self.key_binding_scroll_offset = 0
        
        key_names = list(self.key_bindings.keys())
        option_spacing = int(HEIGHT * 0.07)
        visible_area_height = int(HEIGHT * 0.7)
        max_visible_options = visible_area_height // option_spacing
        
        # 调整滚动偏移
        old_offset = self.key_binding_scroll_offset
        self.key_binding_scroll_offset += direction
        
        # 限制滚动范围
        max_scroll = max(0, len(key_names) - max_visible_options)
        self.key_binding_scroll_offset = max(0, min(self.key_binding_scroll_offset, max_scroll))
        
        # 如果滚动偏移改变了，调整选中项以保持在可见范围内
        if self.key_binding_scroll_offset != old_offset:
            if self.key_binding_selection < self.key_binding_scroll_offset:
                self.key_binding_selection = self.key_binding_scroll_offset
            elif self.key_binding_selection >= self.key_binding_scroll_offset + max_visible_options:
                self.key_binding_selection = self.key_binding_scroll_offset + max_visible_options - 1
    
    def handle_mode_select_input(self, key):
        if key == pygame.K_UP:
            self.mode_selection = (self.mode_selection - 1) % 2
        elif key == pygame.K_DOWN:
            self.mode_selection = (self.mode_selection + 1) % 2
        elif key == pygame.K_RETURN or key == pygame.K_SPACE:
            if self.mode_selection == 0:  # 开房间
                self.game_mode = HOST_ROOM
                self.state = CREATE_ROOM
            else:  # 加入房间
                self.game_mode = JOIN_ROOM_MODE
                self.state = JOIN_ROOM
        elif key == pygame.K_ESCAPE:
            self.state = MAIN_MENU
    
    def handle_settings_input(self, key):
        if self.waiting_for_key:
            # 正在等待按键设置
            if key == pygame.K_ESCAPE:
                self.waiting_for_key = None
            else:
                # 设置新的按键
                self.key_bindings[self.waiting_for_key] = key
                self.waiting_for_key = None
        else:
            if key == pygame.K_UP:
                self.settings_selection = (self.settings_selection - 1) % 5
            elif key == pygame.K_DOWN:
                self.settings_selection = (self.settings_selection + 1) % 5
            elif key == pygame.K_RETURN or key == pygame.K_SPACE:
                if self.settings_selection == 0:  # 全屏切换
                    self.toggle_fullscreen()
                elif self.settings_selection == 1:  # 分辨率调整
                    pass  # 分辨率通过左右键调整
                elif self.settings_selection == 2:  # 音量控制
                    pass  # 音量通过左右键调整
                elif self.settings_selection == 3:  # 按键配置
                    self.state = KEY_BINDING
                elif self.settings_selection == 4:  # 返回主菜单
                    self.state = MAIN_MENU
            elif key == pygame.K_LEFT:
                if self.settings_selection == 2:  # 音量减小
                    self.master_volume = max(0.0, self.master_volume - 0.1)
                    pygame.mixer.music.set_volume(self.master_volume)
            elif key == pygame.K_RIGHT:
                if self.settings_selection == 2:  # 音量增大
                    self.master_volume = min(1.0, self.master_volume + 0.1)
                    pygame.mixer.music.set_volume(self.master_volume)
            elif key == pygame.K_ESCAPE:
                self.state = MAIN_MENU
    
    def handle_key_binding_input(self, key):
        if self.waiting_for_key:
            # 正在等待按键设置
            if key == pygame.K_ESCAPE:
                self.waiting_for_key = None
            else:
                # 设置新的按键
                self.key_bindings[self.waiting_for_key] = key
                self.waiting_for_key = None
        else:
            if key == pygame.K_UP:
                self.key_binding_selection = (self.key_binding_selection - 1) % (len(self.key_bindings) + 1)
            elif key == pygame.K_DOWN:
                self.key_binding_selection = (self.key_binding_selection + 1) % (len(self.key_bindings) + 1)
            elif key == pygame.K_RETURN or key == pygame.K_SPACE:
                if self.key_binding_selection < len(self.key_bindings):
                    # 选择了某个按键进行设置
                    key_name = list(self.key_bindings.keys())[self.key_binding_selection]
                    self.waiting_for_key = key_name
                else:
                    # 返回设置页面
                    self.state = SETTINGS
            elif key == pygame.K_ESCAPE:
                self.state = SETTINGS
    
    def handle_create_room_input(self, key):
        """处理创建房间页面的键盘输入"""
        if key == pygame.K_ESCAPE:
            self.state = MODE_SELECT
        elif key == pygame.K_RETURN or key == pygame.K_SPACE:
            if not self.local_server:
                # 创建本地服务器
                self.create_local_server()
            else:
                # 连接到自己的服务器并进入等待房间
                if self.connect_to_room():
                    self.state = WAITING_ROOM
    
    def handle_create_room_click(self, mouse_pos):
        """处理创建房间页面的鼠标点击"""
        mouse_x, mouse_y = mouse_pos
        
        # 使用与绘制方法相同的相对坐标系统
        center_x = WIDTH // 2
        scale_factor = min(WIDTH/1200, HEIGHT/650)
        button_width = int(200 * scale_factor)
        button_height = int(50 * scale_factor)
        
        if not self.local_server:
            # 创建房间按钮 - 相对于屏幕高度的62%位置
            create_btn = pygame.Rect(center_x - button_width//2, int(HEIGHT * 0.62), button_width, button_height)
            if create_btn.collidepoint(mouse_x, mouse_y):
                self.create_local_server()
        else:
            # 进入房间按钮 - 相对于屏幕高度的62%位置
            enter_btn = pygame.Rect(center_x - button_width//2, int(HEIGHT * 0.62), button_width, button_height)
            if enter_btn.collidepoint(mouse_x, mouse_y):
                if self.connect_to_room():
                    self.state = WAITING_ROOM
        
        # 返回按钮 - 相对于屏幕高度的74%位置
        back_btn = pygame.Rect(center_x - button_width//2, int(HEIGHT * 0.74), button_width, button_height)
        if back_btn.collidepoint(mouse_x, mouse_y):
            self.state = MODE_SELECT
    
    def handle_join_room_input(self, key):
        """处理加入房间页面的键盘输入"""
        if key == pygame.K_ESCAPE:
            self.state = MODE_SELECT
        elif key == pygame.K_TAB:
            # 切换输入框
            self.input_field = "port" if self.input_field == "ip" else "ip"
        elif key == pygame.K_RETURN:
            if self.input_field == "ip":
                self.input_field = "port"
            else:
                # 尝试连接
                if self.connect_to_room():
                    self.state = WAITING_ROOM
        elif key == pygame.K_BACKSPACE:
            if self.input_field == "ip" and len(self.room_ip) > 0:
                self.room_ip = self.room_ip[:-1]
            elif self.input_field == "port" and len(self.room_port) > 0:
                self.room_port = self.room_port[:-1]
    
    def handle_join_room_click(self, mouse_pos):
        """处理加入房间页面的鼠标点击"""
        mouse_x, mouse_y = mouse_pos
        
        # 使用与绘制方法相同的相对坐标系统
        center_x = WIDTH // 2
        scale_factor = min(WIDTH/1200, HEIGHT/650)
        input_box_width = int(200 * scale_factor)
        input_box_height = int(40 * scale_factor)
        button_width = int(200 * scale_factor)
        button_height = int(50 * scale_factor)
        
        # IP输入框 - 相对于屏幕高度的28%位置
        ip_rect = pygame.Rect(center_x - input_box_width//2, int(HEIGHT * 0.28), input_box_width, input_box_height)
        if ip_rect.collidepoint(mouse_x, mouse_y):
            self.input_field = "ip"
        
        # 端口输入框 - 相对于屏幕高度的41%位置
        port_rect = pygame.Rect(center_x - input_box_width//2, int(HEIGHT * 0.41), input_box_width, input_box_height)
        if port_rect.collidepoint(mouse_x, mouse_y):
            self.input_field = "port"
        
        # 连接按钮 - 相对于屏幕高度的62%位置
        connect_btn = pygame.Rect(center_x - button_width//2, int(HEIGHT * 0.62), button_width, button_height)
        if connect_btn.collidepoint(mouse_x, mouse_y):
            if self.connect_to_room():
                self.mode = JOIN_ROOM_MODE
                self.game_mode = ONLINE
                self.state = WAITING_ROOM
                print(f"成功连接并进入等待房间，模式: {self.mode}, 游戏模式: {self.game_mode}")
        
        # 返回按钮 - 相对于屏幕高度的74%位置
        back_btn = pygame.Rect(center_x - button_width//2, int(HEIGHT * 0.74), button_width, button_height)
        if back_btn.collidepoint(mouse_x, mouse_y):
            self.state = MODE_SELECT
    
    def handle_waiting_room_input(self, key):
        """处理等待房间页面的键盘输入"""
        if key == pygame.K_ESCAPE:
            self.leave_room()
        elif key == pygame.K_RETURN or key == pygame.K_SPACE:
            # 开始游戏（如果是房主且有玩家）
            if self.mode == HOST_ROOM and len(self.room_players) >= 1:
                self.state = CHARACTER_SELECT
        elif key == pygame.K_LEFT:
            # 切换到上一个系列（仅房主可操作）
            if self.mode == HOST_ROOM and self.available_map_series:
                self.selected_series = (self.selected_series - 1) % len(self.available_map_series)
                self.selected_level = 0  # 总是从第一个关卡开始
                
                current_series = self.available_map_series[self.selected_series]
                current_level = current_series['loaded_levels'][self.selected_level]
                print(f"切换到系列: {current_series['series_name']} - {current_level['level_name']}")
                # 发送地图选择给其他玩家
                if self.network_client and self.network_client.connected:
                    self.network_client.send_map_selection(self.selected_series * 100 + self.selected_level, 
                                                         f"{current_series['series_name']} - {current_level['level_name']}")
        elif key == pygame.K_RIGHT:
            # 切换到下一个系列（仅房主可操作）
            if self.mode == HOST_ROOM and self.available_map_series:
                self.selected_series = (self.selected_series + 1) % len(self.available_map_series)
                self.selected_level = 0  # 总是从第一个关卡开始
                
                current_series = self.available_map_series[self.selected_series]
                current_level = current_series['loaded_levels'][self.selected_level]
                print(f"切换到系列: {current_series['series_name']} - {current_level['level_name']}")
                # 发送地图选择给其他玩家
                if self.network_client and self.network_client.connected:
                    self.network_client.send_map_selection(self.selected_series * 100 + self.selected_level, 
                                                         f"{current_series['series_name']} - {current_level['level_name']}")
    
    def handle_waiting_room_click(self, mouse_pos):
        """处理等待房间页面的鼠标点击"""
        mouse_x, mouse_y = mouse_pos
        
        # 使用与绘制方法相同的相对坐标系统
        center_x = WIDTH // 2
        scale_factor = min(WIDTH/1200, HEIGHT/650)
        button_width = int(200 * scale_factor)
        button_height = int(50 * scale_factor)
        
        # 开始游戏按钮（仅房主可见且角色已选择） - 相对于屏幕高度的69%位置
        if self.mode == HOST_ROOM and len(self.room_players) >= 1 and self.character_selected:
            start_btn = pygame.Rect(center_x - button_width//2, int(HEIGHT * 0.69), button_width, button_height)
            if start_btn.collidepoint(mouse_x, mouse_y):
                self.start_game()
        
        # 角色选择按钮 - 相对于屏幕高度的79%位置
        character_btn = pygame.Rect(center_x - button_width//2, int(HEIGHT * 0.79), button_width, button_height)
        if character_btn.collidepoint(mouse_x, mouse_y):
            self.previous_state = WAITING_ROOM
            self.state = CHARACTER_SELECT
        
        # 离开房间按钮 - 相对于屏幕高度的89%位置
        leave_btn = pygame.Rect(center_x - button_width//2, int(HEIGHT * 0.89), button_width, button_height)
        if leave_btn.collidepoint(mouse_x, mouse_y):
            self.leave_room()
    
    def handle_paused_click(self, mouse_pos):
        """处理暂停页面的鼠标点击"""
        if self.game_mode != ONLINE:
            return  # 离线模式不处理点击事件
        
        mouse_x, mouse_y = mouse_pos
        button_width = 200
        button_height = 50
        
        # 检查是否为房主
        is_host = (self.network_client and 
                  hasattr(self.network_client, 'is_host') and 
                  self.network_client.is_host)
        
        if is_host:
            # 房主可以点击返回等待房间按钮
            return_button = pygame.Rect(WIDTH//2 - button_width//2, HEIGHT//2 - 10, button_width, button_height)
            if return_button.collidepoint(mouse_x, mouse_y):
                # 发送返回等待房间信号给服务器
                if self.network_client:
                    self.network_client.send_return_to_waiting_room()
                    self.network_client.game_started = False
                
                # 切换回菜单音乐
                self.play_music('menu')
                
                # 返回等待房间
                self.state = WAITING_ROOM
                print("房主返回等待房间")
                return
            
            # 房主的继续游戏按钮
            continue_button = pygame.Rect(WIDTH//2 - button_width//2, HEIGHT//2 + 60, button_width, button_height)
            if continue_button.collidepoint(mouse_x, mouse_y):
                self.state = PLAYING
                print("继续游戏")
        else:
            # 普通玩家只能点击继续游戏按钮
            continue_button = pygame.Rect(WIDTH//2 - button_width//2, HEIGHT//2 + 30, button_width, button_height)
            if continue_button.collidepoint(mouse_x, mouse_y):
                self.state = PLAYING
                print("继续游戏")
    
    def toggle_fullscreen(self):
        global WIDTH, HEIGHT
        old_width, old_height = WIDTH, HEIGHT
        self.fullscreen = not self.fullscreen
        if self.fullscreen:
            self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
            # 获取全屏模式下的实际屏幕尺寸
            WIDTH, HEIGHT = self.screen.get_size()
        else:
            self.screen = pygame.display.set_mode(self.current_resolution)
            # 恢复到设定的分辨率
            WIDTH, HEIGHT = self.current_resolution
        
        # 如果有游戏元素，重新调整位置（包括等待房间状态）
        if (self.state == PLAYING or self.state == WAITING_ROOM) and self.player and self.platforms:
            self.adjust_game_elements(old_width, old_height, WIDTH, HEIGHT)
    
    def adjust_game_elements(self, old_width, old_height, new_width, new_height):
        """调整游戏元素位置以适应新的屏幕尺寸"""
        # 重新缩放背景图片以覆盖整个屏幕
        if hasattr(self, 'background') and self.background:
            try:
                # 重新加载原始背景图片并缩放到新尺寸
                original_background = pygame.image.load('img/background.svg')
                self.background = pygame.transform.scale(original_background, (new_width, new_height))
            except:
                # 如果加载失败，将现有背景缩放到新尺寸
                self.background = pygame.transform.scale(self.background, (new_width, new_height))
        
        # 使用相对坐标来调整位置，确保在不同分辨率下位置一致
        if self.player:
            # 将当前位置转换为相对坐标
            rel_x = self.player.x / old_width
            rel_y = self.player.y / old_height
            
            # 根据新分辨率计算新位置
            self.player.x = min(rel_x * new_width, new_width - self.player.width)
            self.player.y = min(rel_y * new_height, new_height - self.player.height)
            self.player.rect.x = self.player.x
            self.player.rect.y = self.player.y
        
        # 重新创建平台（基于地图数据，确保精确性）
        if self.platforms:
            if (hasattr(self, 'available_map_series') and self.available_map_series and 
                hasattr(self, 'selected_series') and hasattr(self, 'selected_level')):
                current_series = self.available_map_series[self.selected_series]
                current_map = current_series['loaded_levels'][self.selected_level]
                self.platforms = self.create_platforms_from_map(current_map)
            else:
                # 如果没有地图数据，使用比例调整
                for platform in self.platforms:
                    rel_x = platform.x / old_width
                    rel_y = platform.y / old_height
                    rel_width = platform.width / old_width
                    
                    platform.x = rel_x * new_width
                    platform.y = rel_y * new_height
                    platform.width = rel_width * new_width
                    
                    # 特殊处理地面平台，确保它始终在底部并覆盖整个宽度
                    if rel_y >= 0.9:  # 如果是地面平台（相对位置在90%以下）
                        platform.x = 0
                        platform.y = new_height - 50
                        platform.width = new_width
                        
                    platform.rect = pygame.Rect(platform.x, platform.y, platform.width, platform.height)
    
    def change_resolution(self):
        if not self.fullscreen:
            global WIDTH, HEIGHT
            old_width, old_height = WIDTH, HEIGHT
            self.current_resolution = self.available_resolutions[self.resolution_index]
            self.screen = pygame.display.set_mode(self.current_resolution)
            # 更新全局变量
            WIDTH, HEIGHT = self.current_resolution
            
            # 如果有游戏元素，重新调整位置（包括等待房间状态）
            if (self.state == PLAYING or self.state == WAITING_ROOM) and self.player and self.platforms:
                self.adjust_game_elements(old_width, old_height, WIDTH, HEIGHT)
    
    def handle_character_select_input(self, key):
        if not self.input_active:
            if key == pygame.K_LEFT:
                self.selected_character = (self.selected_character - 1) % len(self.character_options)
            elif key == pygame.K_RIGHT:
                self.selected_character = (self.selected_character + 1) % len(self.character_options)
            elif key == pygame.K_RETURN or key == pygame.K_SPACE:
                if self.player_name.strip():  # 如果已有名字，确认角色选择
                    self.character_selected = True
                    # 发送角色选择信息到服务器
                    if self.network_client and self.network_client.connected:
                        character_name = self.character_options[self.selected_character]['name']
                        self.network_client.send_character_selection(character_name, self.player_name)
                    # 返回等待房间
                    self.state = WAITING_ROOM
                    self.previous_state = None
                else:  # 否则激活输入
                    self.input_active = True
                    self.temp_name = self.player_name
            elif key == pygame.K_ESCAPE:
                # 总是返回等待房间
                self.state = WAITING_ROOM
                self.previous_state = None
        else:  # 输入模式
            if key == pygame.K_RETURN:
                if self.temp_name.strip():
                    self.player_name = self.temp_name.strip()
                    self.input_active = False
                    self.character_selected = True
                    # 发送角色选择信息到服务器
                    if self.network_client and self.network_client.connected:
                        character_name = self.character_options[self.selected_character]['name']
                        self.network_client.send_character_selection(character_name, self.player_name)
                    # 返回等待房间
                    self.state = WAITING_ROOM
                    self.previous_state = None
            elif key == pygame.K_ESCAPE:
                self.input_active = False
                self.temp_name = ""
            elif key == pygame.K_BACKSPACE:
                self.temp_name = self.temp_name[:-1]
    
    def start_game(self):
        """开始游戏，初始化游戏对象"""
        # 获取当前选择的地图数据
        if (self.available_map_series and 
            0 <= self.selected_series < len(self.available_map_series) and
            0 <= self.selected_level < len(self.available_map_series[self.selected_series]['loaded_levels'])):
            self.current_series_data = self.available_map_series[self.selected_series]
            self.current_map_data = self.current_series_data['loaded_levels'][self.selected_level]
        else:
            # 如果没有可用地图系列，使用默认地图系列
            self.create_default_map_series()
            self.current_series_data = self.available_map_series[0]
            self.current_map_data = self.current_series_data['loaded_levels'][0]
        
        print(f"加载地图: {self.current_map_data['name']}")
        
        # 设置当前地图名称，用于敌人ID生成
        self.current_map_name = self.current_map_data.get('level_name', self.current_map_data.get('name', 'default_map'))
        
        # 根据地图数据获取出生点
        spawn_x, spawn_y = self.get_spawn_point_from_map(self.current_map_data)
        
        # 根据选择的角色创建玩家
        character_folder = self.character_options[self.selected_character]['gif_folder']
        character_name = self.character_options[self.selected_character]['name']
        self.player = Player(spawn_x, spawn_y, character_folder, character_name)
        # 使用角色加载器设置角色属性
        self.player.set_character_stats(character_name, self.character_loader)
        
        # 根据地图数据创建平台
        self.platforms = self.create_platforms_from_map(self.current_map_data)
        
        # 根据地图数据创建传送门
        self.portals = self.create_portals_from_map(self.current_map_data)
        
        # 根据游戏模式初始化网络（仅在没有连接时）
        if self.game_mode == ONLINE and (not self.network_client or not self.network_client.connected):
            self.try_connect_to_server()
        
        # 如果是联机模式
        if self.network_client and self.network_client.connected:
            if self.network_client.is_host:
                # 房主发送地图数据到服务端，让服务端统一管理敌人
                self.network_client.send_map_data(self.current_map_data)
                print("房主发送地图数据到服务端")
                
                # 初始化空的敌人列表，等待服务端同步
                self.enemies = []
            else:
                # 非房主客户端也初始化空的敌人列表
                self.enemies = []
            
            self.network_client.send_game_start()
            print("发送游戏开始信号")
            
            # 立即发送当前玩家的游戏位置数据（使用相对坐标）
            rel_x, rel_y = self.absolute_to_relative(self.player.x, self.player.y)
            player_data = {
                'rel_x': rel_x,
                'rel_y': rel_y,
                'facing_right': self.player.facing_right,
                'on_ground': self.player.on_ground,
                'player_name': self.player_name,
                'character_name': self.character_options[self.selected_character]['name'] if self.character_selected else "未选择"
            }
            self.network_client.send_player_data(player_data)
        else:
            # 单机模式，在客户端创建敌人
            self.enemies = self.create_enemies_from_map(self.current_map_data)
        
        # 初始化弹幕列表和性能优化设置
        self.projectiles = []  # 弹幕列表
        self.max_projectiles = 30  # 限制弹幕数量以提高性能
        
        # 切换到游戏音乐
        self.play_music('game')
        
        self.state = PLAYING
    
    def cleanup_game(self):
        """清理游戏资源"""
        # 切换回菜单音乐
        self.play_music('menu')
        
        # 先断开客户端连接，让服务器的延迟停止机制处理服务器关闭
        if self.network_client:
            self.network_client.disconnect()
            self.network_client = None
        
        # 不要立即停止本地服务器，让网络层的延迟停止机制处理
        # 这样其他客户端有时间接收房间解散消息
        if hasattr(self, 'local_server') and self.local_server:
            self.local_server = None  # 只清除引用，不立即停止
        
        # 清理玩家数据
        self.player = None
        self.platforms = None
        
        # 清理角色选择相关数据
        self.character_selected = False
        self.selected_character = 0
        self.player_name = ""
        self.temp_name = ""
        self.input_active = False
        
        # 清理房间相关数据
        self.room_players.clear()
        
        # 重置游戏模式
        self.game_mode = OFFLINE
        self.mode = OFFLINE
        
        print("已清理所有玩家数据")
    
    def update(self):
        # 检查房间解散
        if (self.network_client and hasattr(self.network_client, 'room_disbanded') and 
            self.network_client.room_disbanded):
            print("检测到房间解散，返回模式选择页面")
            # 重置房间解散标志
            self.network_client.room_disbanded = False
            # 显示房间解散消息
            self.room_disbanded_message = "房间已解散，房主离开了房间"
            self.room_disbanded_time = pygame.time.get_ticks()
            self.show_disbanded_message = True
            
            # 如果是普通玩家，清理网络连接和游戏数据
            if not (hasattr(self, 'local_server') and self.local_server):
                # 只断开客户端连接，不停止服务器
                if self.network_client:
                    self.network_client.disconnect()
                    self.network_client = None
                
                # 清理玩家数据但保留服务器
                self.player = None
                self.platforms = None
                self.character_selected = False
                self.selected_character = 0
                self.room_players.clear()
                self.game_mode = OFFLINE
                self.mode = OFFLINE
            else:
                # 如果是房主，完全清理
                self.cleanup_game()
            
            # 返回模式选择页面
            self.state = MODE_SELECT
            return
        
        # 检查房主断开连接（保留兼容性）
        if (self.network_client and hasattr(self.network_client, 'host_disconnected') and 
            self.network_client.host_disconnected):
            print("检测到房主断开连接，返回模式选择页面")
            # 重置房主断开连接标志
            self.network_client.host_disconnected = False
            # 清理网络连接和游戏数据
            self.cleanup_game()
            # 返回模式选择页面
            self.state = MODE_SELECT
            return
        
        # 检查返回等待房间信号
        if (self.network_client and hasattr(self.network_client, 'return_to_waiting_room') and 
            self.network_client.return_to_waiting_room):
            print("收到返回等待房间信号")
            # 重置返回等待房间标志
            self.network_client.return_to_waiting_room = False
            self.network_client.game_started = False
            
            # 切换回菜单音乐
            self.play_music('menu')
            
            # 返回等待房间
            self.state = WAITING_ROOM
            print("返回等待房间")
            return
        
        if self.state == PLAYING and self.player:
            # 更新敌怪
            dt = 1/60  # 时间增量，假设60FPS
            self.player.update(self.platforms, self.key_bindings, dt)
            
            # 收集所有玩家信息用于敌人AI（仇恨机制）
            other_players = []
            if (self.game_mode == ONLINE and self.network_client and 
                hasattr(self.network_client, 'other_players_data') and self.network_client.other_players_data):
                for player_data in self.network_client.other_players_data.values():
                    # 创建临时玩家对象用于敌人AI计算
                    class TempPlayer:
                        def __init__(self, x, y):
                            self.x = x
                            self.y = y
                    
                    if 'x' in player_data and 'y' in player_data:
                        temp_player = TempPlayer(player_data['x'], player_data['y'])
                        other_players.append(temp_player)
            
            # 在多人模式下，使用服务端对象池系统
            if self.game_mode == OFFLINE:
                # 单机模式：正常更新敌人AI和移动
                for enemy in self.enemies[:]:
                    enemy.update(dt, self.player, self.platforms, other_players)
            elif self.game_mode == ONLINE and self.network_client and self.network_client.is_host:
                # 房主：不在客户端计算敌人AI，完全依赖服务端对象池
                # 但仍需要更新AI状态以支持攻击检测
                for enemy in self.enemies[:]:
                    enemy.update_ai(self.player, other_players)
                    enemy.update_animation(dt)
            else:
                # 非房主玩家：更新AI状态以支持攻击检测，等待服务端同步位置数据
                for enemy in self.enemies[:]:
                    enemy.update_ai(self.player, other_players)
                    enemy.update_animation(dt)
            
            # 处理网络伤害
            if (self.game_mode == ONLINE and self.network_client and 
                hasattr(self.network_client, 'pending_damage') and self.network_client.pending_damage > 0):
                damage = self.network_client.pending_damage
                self.network_client.pending_damage = 0  # 重置伤害
                
                self.player.take_damage(damage)
                print(f"玩家受到网络伤害: {damage}点")
                
                # 检查玩家是否死亡
                if self.player.current_health <= 0:
                    print("玩家血量为0，游戏结束")
                    if self.network_client and self.network_client.connected:
                        player_name = self.player_name if self.player_name else "未命名玩家"
                        self.network_client.send_player_death(player_name)
                    self.show_game_over()
                    return
            
            # 检查敌怪攻击所有玩家（仇恨机制）
            all_players = [self.player]
            # 添加其他在线玩家
            if (self.game_mode == ONLINE and self.network_client and 
                hasattr(self.network_client, 'other_players_data') and self.network_client.other_players_data):
                for player_data in self.network_client.other_players_data.values():
                    # 创建临时玩家对象用于碰撞检测
                    temp_player = type('TempPlayer', (), {
                        'x': player_data.get('x', 0),
                        'y': player_data.get('y', 0),
                        'rect': pygame.Rect(player_data.get('x', 0), player_data.get('y', 0), 64, 64),
                        'player_id': player_data.get('player_id', ''),
                        'name': player_data.get('name', '未命名玩家')
                    })()
                    all_players.append(temp_player)
            
            for enemy in self.enemies[:]:
                if enemy.can_attack():
                    # 检查与所有玩家的碰撞
                    for player in all_players:
                        if enemy.rect.colliderect(player.rect):
                            damage = enemy.attack(player)
                            if damage > 0:
                                # 如果是当前玩家受到攻击
                                if player == self.player:
                                    self.player.take_damage(damage)
                                    
                                    # 检查玩家是否死亡
                                    if self.player.current_health <= 0:
                                        print("玩家血量为0，游戏结束")
                                        # 在多人模式下发送玩家死亡信息
                                        if self.game_mode == ONLINE and self.network_client and self.network_client.connected:
                                            player_name = self.player_name if self.player_name else "未命名玩家"
                                            self.network_client.send_player_death(player_name)
                                        self.show_game_over()
                                        return
                                else:
                                    # 其他玩家受到攻击，通过网络发送伤害信息
                                    if (self.game_mode == ONLINE and self.network_client and 
                                        self.network_client.connected and hasattr(player, 'player_id')):
                                        self.network_client.send_player_damage(player.player_id, damage)
                            break  # 每个敌人每次只能攻击一个玩家
                    
            # 处理敌人死亡
            dead_enemies = [enemy for enemy in self.enemies if enemy.current_health <= 0]
            for dead_enemy in dead_enemies:
                # 在多人模式下发送敌人死亡信息
                if self.game_mode == ONLINE and self.network_client and self.network_client.connected:
                    self.network_client.send_enemy_death(dead_enemy.enemy_id)
            
            # 移除死亡的敌怪
            self.enemies = [enemy for enemy in self.enemies if enemy.current_health > 0]
            
            # 处理网络同步的死亡敌人
            if (self.game_mode == ONLINE and self.network_client and 
                hasattr(self.network_client, 'dead_enemies') and self.network_client.dead_enemies):
                # 移除网络同步的死亡敌人
                self.enemies = [enemy for enemy in self.enemies if enemy.enemy_id not in self.network_client.dead_enemies]
                # 清空已处理的死亡敌人列表
                self.network_client.dead_enemies.clear()
            
            # 更新弹幕
            if hasattr(self, 'projectiles'):
                for projectile in self.projectiles[:]:
                    projectile.update(dt, self.platforms)
                    
                    # 检查弹幕与敌怪的碰撞
                    for enemy in self.enemies[:]:
                        if projectile.rect.colliderect(enemy.rect):
                            # 弹幕击中敌怪
                            enemy.take_damage(projectile.damage)
                            # 减少调试打印频率以提高性能
                            if projectile.damage > 1:  # 只在造成有效伤害时打印
                                print(f"弹幕击中敌怪 {enemy.type}，造成 {projectile.damage} 点伤害，敌人剩余血量: {enemy.current_health}/{enemy.max_health}")
                            
                            # 在网络模式下发送敌人受伤信息给服务端
                            if self.game_mode == ONLINE and self.network_client and self.network_client.connected:
                                self.network_client.send_enemy_damage(enemy.enemy_id, projectile.damage, enemy.current_health)
                            
                            # 移除弹幕
                            if projectile in self.projectiles:
                                self.projectiles.remove(projectile)
                            break
                    
                    # 移除超出反弹次数或离开屏幕太远的弹幕
                    if (projectile.bounces >= projectile.max_bounces or 
                        projectile.x < -200 or projectile.x > WIDTH + 200 or 
                        projectile.y < -200 or projectile.y > HEIGHT + 200):
                        if projectile in self.projectiles:
                            self.projectiles.remove(projectile)
            
            # 多人模式下的敌人管理现在由服务端统一处理，客户端只接收同步数据
                
            # 处理服务端同步的敌人数据（所有客户端）
            if (self.game_mode == ONLINE and self.network_client and 
                hasattr(self.network_client, 'enemies_sync_data') and self.network_client.enemies_sync_data):
                # 应用服务端同步的敌人数据
                for enemy_data in self.network_client.enemies_sync_data:
                    enemy_id = enemy_data.get('enemy_id')
                    
                    # 查找对应的敌人
                    enemy_found = False
                    for enemy in self.enemies:
                        if enemy.enemy_id == enemy_id:
                            enemy_found = True
                            # 应用服务端的所有状态更新
                            if 'health' in enemy_data:
                                enemy.current_health = min(enemy_data['health'], enemy.max_health)
                            if 'x' in enemy_data and 'y' in enemy_data:
                                # 直接设置位置，确保同步准确性
                                enemy.x = enemy_data['x']
                                enemy.y = enemy_data['y']
                                enemy.rect.x = int(enemy.x)
                                enemy.rect.y = int(enemy.y)
                            if 'vel_x' in enemy_data:
                                enemy.vel_x = enemy_data['vel_x']
                            if 'vel_y' in enemy_data:
                                enemy.vel_y = enemy_data['vel_y']
                            if 'facing_right' in enemy_data:
                                enemy.facing_right = enemy_data['facing_right']
                            if 'state' in enemy_data:
                                enemy.state = enemy_data['state']
                            if 'current_animation' in enemy_data:
                                enemy.current_animation = enemy_data['current_animation']
                            if 'frame_index' in enemy_data:
                                enemy.frame_index = enemy_data['frame_index']
                            # 同步血量数据（只有在服务端血量更低时才更新，避免覆盖客户端的伤害）
                            if 'health' in enemy_data:
                                server_health = enemy_data['health']
                                if server_health < enemy.current_health:
                                    enemy.current_health = server_health
                                    print(f"同步敌人 {enemy.type} 血量: {enemy.current_health}/{enemy.max_health}")
                            break
                    
                    # 如果敌人不存在，从服务端数据创建新敌人
                    if not enemy_found and enemy_id:
                        try:
                            # 从服务端数据构造敌人创建数据
                            create_enemy_data = {
                                'type': enemy_data.get('type', 'slime'),
                                'variant': enemy_data.get('variant', 'blue'),
                                'x': enemy_data.get('x', 0),
                                'y': enemy_data.get('y', 0),
                                'health': enemy_data.get('health', 50),
                                'attack_power': enemy_data.get('attack_power', 10),
                                'speed': enemy_data.get('speed', 2),
                                'patrol_range': enemy_data.get('patrol_range', 200),
                                'aggro_range': enemy_data.get('aggro_range', 150),
                                'deterministic_id': enemy_id
                            }
                            
                            # 创建敌人对象
                            new_enemy = Enemy(create_enemy_data)
                            
                            # 应用服务端状态
                            if 'vel_x' in enemy_data:
                                new_enemy.vel_x = enemy_data['vel_x']
                            if 'vel_y' in enemy_data:
                                new_enemy.vel_y = enemy_data['vel_y']
                            if 'facing_right' in enemy_data:
                                new_enemy.facing_right = enemy_data['facing_right']
                            if 'state' in enemy_data:
                                new_enemy.state = enemy_data['state']
                            if 'current_animation' in enemy_data:
                                new_enemy.current_animation = enemy_data['current_animation']
                            if 'frame_index' in enemy_data:
                                new_enemy.frame_index = enemy_data['frame_index']
                            
                            self.enemies.append(new_enemy)
                            print(f"客户端从服务端数据创建敌人: {create_enemy_data['type']} ({create_enemy_data['variant']}) ID: {enemy_id}")
                            
                        except Exception as e:
                            print(f"客户端创建敌人失败: {e}, 数据: {enemy_data}")
                
                # 清空已处理的敌人同步数据
                self.network_client.enemies_sync_data.clear()
            
            # 处理传统的敌人更新消息（保持兼容性）
            if (self.game_mode == ONLINE and self.network_client and 
                hasattr(self.network_client, 'enemy_updates') and 
                self.network_client.enemy_updates):
                for enemy_id, enemy_update in self.network_client.enemy_updates.items():
                    # 查找对应的敌人
                    for enemy in self.enemies:
                        if enemy.enemy_id == enemy_id:
                            # 应用血量更新
                            if 'current_health' in enemy_update:
                                enemy.current_health = min(enemy_update['current_health'], enemy.max_health)
                            break
                
                # 清空已处理的敌人更新
                self.network_client.enemy_updates.clear()
            
            # 更新传送门
            for portal in self.portals:
                portal.update(1/60)  # 传入时间增量，假设60FPS
            
            # 检查传送门碰撞
            self.check_portal_collisions()
            
            # 更新传送门等待消息计时器
            if self.portal_message_timer > 0:
                self.portal_message_timer -= 1/FPS
                if self.portal_message_timer <= 0:
                    self.portal_message_timer = 0
            
            # 检查是否收到传送门触发信号
            if (self.game_mode == ONLINE and self.network_client and 
                hasattr(self.network_client, 'portal_triggered') and self.network_client.portal_triggered):
                print(f"收到传送门触发信号，传送到: {self.network_client.portal_target_map}")
                # 重置传送门触发标志
                self.network_client.portal_triggered = False
                # 执行传送
                self.teleport_to_map(self.network_client.portal_target_map)
            
            # 发送玩家数据到服务器（仅线上联机模式）
            if self.game_mode == ONLINE and self.network_client and self.network_client.connected:
                # 使用相对坐标发送位置数据
                rel_x, rel_y = self.absolute_to_relative(self.player.x, self.player.y)
                player_data = {
                    'rel_x': rel_x,
                    'rel_y': rel_y,
                    'facing_right': self.player.facing_right,
                    'on_ground': self.player.on_ground,
                    'player_name': self.player_name,
                    'character_name': self.character_options[self.selected_character]['name'] if self.character_selected else "未选择",
                    'current_animation': self.player.current_animation,
                    'frame_index': self.player.frame_index
                }
                self.network_client.send_player_data(player_data)
                # 添加调试信息（可选）
                # print(f"发送玩家数据: x={self.player.x}, y={self.player.y}, 动画={self.player.current_animation}, 帧={self.player.frame_index}")
        
        # 在等待房间状态下也发送玩家信息，以便其他玩家能看到
        if self.state == WAITING_ROOM and self.network_client and self.network_client.connected:
            # 定期发送角色选择信息，确保其他玩家能看到（每2秒发送一次）
            import time
            current_time = time.time()
            if (self.character_selected and hasattr(self, 'selected_character') and 
                current_time - self.last_character_send_time > 2.0):
                character_name = self.character_options[self.selected_character]['name']
                player_name = self.player_name if self.player_name else "未命名"
                self.network_client.send_character_selection(character_name, player_name)
                self.last_character_send_time = current_time
            
            # 检查是否收到地图更新
            if (hasattr(self.network_client, 'map_updated') and self.network_client.map_updated and 
                self.mode != HOST_ROOM):  # 只有非房主才接收地图更新
                print(f"接收到房主的地图选择: {self.network_client.selected_map_name}")
                # 更新本地地图选择（解码系列和关卡索引）
                map_index = self.network_client.selected_map_index
                self.selected_series = map_index // 100
                self.selected_level = map_index % 100
                # 确保索引有效
                if (0 <= self.selected_series < len(self.available_map_series) and
                    0 <= self.selected_level < len(self.available_map_series[self.selected_series]['loaded_levels'])):
                    pass  # 索引有效
                else:
                    # 索引无效，重置为默认值
                    self.selected_series = 0
                    self.selected_level = 0
                # 重置地图更新标志
                self.network_client.map_updated = False
            
            # 检查是否收到游戏开始信号
            if hasattr(self.network_client, 'game_started') and self.network_client.game_started:
                print("收到游戏开始信号，准备进入游戏")
                # 重置游戏开始标志
                self.network_client.game_started = False
                # 开始游戏
                self.start_game()
                
                # 立即发送当前玩家的游戏位置数据（使用相对坐标）
                if self.player and self.network_client and self.network_client.connected:
                    rel_x, rel_y = self.absolute_to_relative(self.player.x, self.player.y)
                    player_data = {
                        'rel_x': rel_x,
                        'rel_y': rel_y,
                        'facing_right': self.player.facing_right,
                        'on_ground': self.player.on_ground,
                        'player_name': self.player_name,
                        'character_name': self.character_options[self.selected_character]['name'] if self.character_selected else "未选择",
                        'current_animation': self.player.current_animation,
                        'frame_index': self.player.frame_index
                    }
                    self.network_client.send_player_data(player_data)
                return
            
            # 获取当前选择的角色名称
            character_name = "未选择"
            if self.character_selected and hasattr(self, 'selected_character'):
                character_name = self.character_options[self.selected_character]['name']
            
            player_data = {
                'player_name': self.player_name if self.player_name else "未命名",
                'character_name': character_name,
                'character_index': self.selected_character if self.character_selected else -1,
                'x': 100,  # 等待房间默认位置
                'y': 100,
                'facing_right': True,
                'current_animation': 'idle',  # 等待房间默认为静止动画
                'frame_index': 0
            }
            self.network_client.send_player_data(player_data)
        
        # 更新角色预览动画
        if self.state in [CHARACTER_SELECT, WAITING_ROOM]:
            self.update_character_preview_animations()
        
        # 更新爬行动画（在菜单页面显示）
        if self.state in [MAIN_MENU, MODE_SELECT, CHARACTER_SELECT, SETTINGS, KEY_BINDING, CREATE_ROOM, JOIN_ROOM, WAITING_ROOM]:
            self.update_crawling_animations()
    
    def draw(self):
        # 清空脏矩形列表
        self.dirty_rects = []
        
        if self.state == MAIN_MENU:
            self.draw_main_menu()
        elif self.state == MODE_SELECT:
            self.draw_mode_select()
        elif self.state == CHARACTER_SELECT:
            self.draw_character_select()
        elif self.state == SETTINGS:
            self.draw_settings()
        elif self.state == KEY_BINDING:
            self.draw_key_binding()
        elif self.state == CREATE_ROOM:
            self.draw_create_room()
        elif self.state == JOIN_ROOM:
            self.draw_join_room()
        elif self.state == WAITING_ROOM:
            self.draw_waiting_room()
        elif self.state in [PLAYING, PAUSED]:
            self.draw_game()
        
        # 游戏状态下使用混合更新策略：背景全屏更新，动态对象脏矩形更新
        if self.state in [PLAYING, PAUSED]:
            # 游戏状态下始终使用全屏更新，避免地图拖影问题
            pygame.display.flip()
        else:
            # 菜单界面使用全屏更新
            pygame.display.flip()
    
    def optimize_dirty_rects(self, rects):
        """优化脏矩形列表，合并重叠的矩形"""
        if not rects:
            return []
        
        # 移除重复的矩形（通过比较矩形的坐标和尺寸）
        unique_rects = []
        for rect in rects:
            is_duplicate = False
            for existing_rect in unique_rects:
                if (rect.x == existing_rect.x and rect.y == existing_rect.y and 
                    rect.width == existing_rect.width and rect.height == existing_rect.height):
                    is_duplicate = True
                    break
            if not is_duplicate:
                unique_rects.append(rect)
        
        # 简单的合并策略：如果矩形数量较少，直接返回
        if len(unique_rects) <= 3:
            return unique_rects
        
        # 如果脏矩形过多，返回全屏更新
        if len(unique_rects) > 20:
            return [pygame.Rect(0, 0, self.screen.get_width(), self.screen.get_height())]
        
        return unique_rects
    
    def add_dirty_rect(self, rect):
        """添加脏矩形区域"""
        if rect and self.use_dirty_rects:
            # 确保矩形在屏幕范围内
            clipped_rect = rect.clip(pygame.Rect(0, 0, self.screen.get_width(), self.screen.get_height()))
            if clipped_rect.width > 0 and clipped_rect.height > 0:
                self.dirty_rects.append(clipped_rect)
    
    def draw_game(self):
        # 绘制背景，确保覆盖整个屏幕（背景不使用脏矩形，避免拖影）
        if self.background:
            # 如果背景尺寸与当前屏幕尺寸不匹配，重新缩放
            if self.background.get_size() != (WIDTH, HEIGHT):
                self.background = pygame.transform.scale(self.background, (WIDTH, HEIGHT))
            self.screen.blit(self.background, (0, 0))
        else:
            self.screen.fill((135, 206, 235))  # 天蓝色背景
        
        # 绘制平台（静态元素不使用脏矩形）
        for platform in self.platforms:
            platform.draw(self.screen)
        
        # 绘制传送门（静态元素不使用脏矩形）
        for portal in self.portals:
            portal.draw(self.screen)
        
        # 绘制敌怪并记录脏矩形
        for enemy in self.enemies:
            # 记录敌怪当前位置作为脏矩形
            enemy_rect = pygame.Rect(enemy.x - 10, enemy.y - 10, enemy.width + 20, enemy.height + 20)
            self.add_dirty_rect(enemy_rect)
            enemy.draw(self.screen)
        
        # 绘制玩家并记录脏矩形
        player_rect = pygame.Rect(self.player.x - 10, self.player.y - 10, self.player.width + 20, self.player.height + 20)
        self.add_dirty_rect(player_rect)
        self.player.draw(self.screen)
        
        # 绘制弹幕并记录脏矩形
        if hasattr(self, 'projectiles'):
            for projectile in self.projectiles:
                # 记录弹幕位置作为脏矩形
                proj_rect = pygame.Rect(projectile.x - 5, projectile.y - 5, 20, 20)
                self.add_dirty_rect(proj_rect)
                projectile.draw(self.screen)
        
        # 绘制其他玩家并记录脏矩形
        if self.network_client:
            self.draw_other_players()
        
        # 绘制传送门等待消息
        if self.portal_message_timer > 0:
            self.show_portal_waiting_message()
        
        # 绘制UI
        self.draw_ui()
    
    def draw_main_menu(self):
        # 深色奢华背景渐变
        for y in range(HEIGHT):
            color_ratio = y / HEIGHT
            r = int(15 + (25 - 15) * color_ratio)
            g = int(10 + (20 - 10) * color_ratio)
            b = int(25 + (40 - 25) * color_ratio)
            pygame.draw.line(self.screen, (r, g, b), (0, y), (WIDTH, y))
        
        # 装饰性花纹背景
        self.draw_decorative_patterns()
        
        # 绘制爬行动画
        self.draw_crawling_animations()
        
        # 标题区域 - 奢华金色边框
        title_bg_rect = pygame.Rect(WIDTH//2 - int(WIDTH * 0.25), int(HEIGHT * 0.15), int(WIDTH * 0.5), int(HEIGHT * 0.15))
        pygame.draw.rect(self.screen, (20, 15, 30), title_bg_rect)
        pygame.draw.rect(self.screen, (180, 150, 80), title_bg_rect, 3)
        
        # 标题装饰线
        pygame.draw.line(self.screen, (220, 180, 100), (title_bg_rect.left + 20, title_bg_rect.top + 20), (title_bg_rect.right - 20, title_bg_rect.top + 20), 2)
        pygame.draw.line(self.screen, (220, 180, 100), (title_bg_rect.left + 20, title_bg_rect.bottom - 20), (title_bg_rect.right - 20, title_bg_rect.bottom - 20), 2)
        
        # 标题
        title_font = self.get_chinese_font(int(HEIGHT * 0.11))  # 响应式字体大小
        title_text = title_font.render("◆ 耄耋的家园 ◆", True, (220, 180, 100))
        title_rect = title_text.get_rect(center=title_bg_rect.center)
        self.screen.blit(title_text, title_rect)
        
        # 菜单选项区域
        menu_area_y = int(HEIGHT * 0.45)
        menu_font = self.get_chinese_font(int(HEIGHT * 0.074))  # 响应式字体大小
        menu_options = ["开始游戏", "设置", "退出游戏"]
        
        for i, option in enumerate(menu_options):
            y_pos = menu_area_y + i * int(HEIGHT * 0.12)
            
            # 选项背景框
            option_bg = pygame.Rect(WIDTH//2 - int(WIDTH * 0.15), y_pos - int(HEIGHT * 0.04), int(WIDTH * 0.3), int(HEIGHT * 0.08))
            
            if i == self.menu_selection:
                # 选中状态 - 金色边框和背景
                pygame.draw.rect(self.screen, (30, 25, 45), option_bg)
                pygame.draw.rect(self.screen, (180, 150, 80), option_bg, 3)
                color = (220, 180, 100)
                
                # 选中装饰
                self.draw_corner_ornaments(option_bg.x, option_bg.y, option_bg.width, option_bg.height, small=True)
            else:
                # 未选中状态 - 暗色边框
                pygame.draw.rect(self.screen, (25, 20, 35), option_bg)
                pygame.draw.rect(self.screen, (80, 70, 50), option_bg, 2)
                color = (200, 180, 140)
            
            # 选项文字
            text = menu_font.render(option, True, color)
            text_rect = text.get_rect(center=(WIDTH//2, y_pos))
            self.screen.blit(text, text_rect)
        

    
    def draw_mode_select(self):
        # 深色奢华背景渐变
        for y in range(HEIGHT):
            color_ratio = y / HEIGHT
            r = int(15 + (25 - 15) * color_ratio)
            g = int(10 + (20 - 10) * color_ratio)
            b = int(25 + (40 - 25) * color_ratio)
            pygame.draw.line(self.screen, (r, g, b), (0, y), (WIDTH, y))
        
        # 装饰性花纹背景
        self.draw_decorative_patterns()
        
        # 绘制爬行动画
        self.draw_crawling_animations()
        
        # 标题区域 - 奢华金色边框
        title_bg_rect = pygame.Rect(WIDTH//2 - int(WIDTH * 0.25), int(HEIGHT * 0.12), int(WIDTH * 0.5), int(HEIGHT * 0.12))
        pygame.draw.rect(self.screen, (20, 15, 30), title_bg_rect)
        pygame.draw.rect(self.screen, (180, 150, 80), title_bg_rect, 3)
        
        # 标题装饰线
        pygame.draw.line(self.screen, (220, 180, 100), (title_bg_rect.left + 20, title_bg_rect.top + 15), (title_bg_rect.right - 20, title_bg_rect.top + 15), 2)
        pygame.draw.line(self.screen, (220, 180, 100), (title_bg_rect.left + 20, title_bg_rect.bottom - 15), (title_bg_rect.right - 20, title_bg_rect.bottom - 15), 2)
        
        # 标题
        title_font = self.get_chinese_font(int(HEIGHT * 0.086))  # 响应式字体大小
        title_text = title_font.render("◆ 选择游戏模式 ◆", True, (220, 180, 100))
        title_rect = title_text.get_rect(center=title_bg_rect.center)
        self.screen.blit(title_text, title_rect)
        
        # 模式选项
        mode_font = self.get_chinese_font(int(HEIGHT * 0.065))  # 响应式字体大小
        desc_font = self.get_chinese_font(int(HEIGHT * 0.037))  # 响应式字体大小
        mode_options = [
            {"name": "开房间", "desc": "创建房间，朋友可以通过IP加入"},
            {"name": "加入房间", "desc": "输入IP和端口加入朋友的房间"}
        ]
        
        mode_area_y = int(HEIGHT * 0.4)
        
        for i, mode in enumerate(mode_options):
            y_pos = mode_area_y + i * int(HEIGHT * 0.18)
            
            # 模式选项背景框
            mode_bg = pygame.Rect(WIDTH//2 - int(WIDTH * 0.35), y_pos - int(HEIGHT * 0.06), int(WIDTH * 0.7), int(HEIGHT * 0.12))
            
            if i == self.mode_selection:
                # 选中状态 - 金色边框和背景
                pygame.draw.rect(self.screen, (30, 25, 45), mode_bg)
                pygame.draw.rect(self.screen, (180, 150, 80), mode_bg, 3)
                name_color = (220, 180, 100)
                desc_color = (200, 180, 140)
                
                # 选中装饰
                self.draw_corner_ornaments(mode_bg.x, mode_bg.y, mode_bg.width, mode_bg.height, small=True)
            else:
                # 未选中状态 - 暗色边框
                pygame.draw.rect(self.screen, (25, 20, 35), mode_bg)
                pygame.draw.rect(self.screen, (80, 70, 50), mode_bg, 2)
                name_color = (200, 180, 140)
                desc_color = (160, 140, 100)
            
            # 模式名称
            name_text = mode_font.render(mode["name"], True, name_color)
            name_rect = name_text.get_rect(center=(WIDTH//2, y_pos - int(HEIGHT * 0.015)))
            self.screen.blit(name_text, name_rect)
            
            # 模式描述
            desc_text = desc_font.render(mode["desc"], True, desc_color)
            desc_rect = desc_text.get_rect(center=(WIDTH//2, y_pos + int(HEIGHT * 0.025)))
            self.screen.blit(desc_text, desc_rect)
        
        # 返回按钮
        back_button_y = int(HEIGHT * 0.85)
        back_button_font = self.get_chinese_font(int(HEIGHT * 0.055))
        back_bg = pygame.Rect(WIDTH//2 - int(WIDTH * 0.12), back_button_y - int(HEIGHT * 0.035), int(WIDTH * 0.24), int(HEIGHT * 0.07))
        
        # 返回按钮背景和边框
        pygame.draw.rect(self.screen, (25, 20, 35), back_bg)
        pygame.draw.rect(self.screen, (120, 100, 60), back_bg, 2)
        
        # 返回按钮文字
        back_text = back_button_font.render("返回主菜单", True, (180, 160, 120))
        back_rect = back_text.get_rect(center=(WIDTH//2, back_button_y))
        self.screen.blit(back_text, back_rect)
        
        # 显示房间解散消息
        if self.show_disbanded_message and self.room_disbanded_message:
            current_time = pygame.time.get_ticks()
            # 显示消息3秒钟
            if current_time - self.room_disbanded_time < 3000:
                message_font = self.get_chinese_font(int(HEIGHT * 0.04))
                message_bg = pygame.Rect(WIDTH//2 - int(WIDTH * 0.2), int(HEIGHT * 0.3), int(WIDTH * 0.4), int(HEIGHT * 0.1))
                
                # 消息背景 - 红色警告样式
                pygame.draw.rect(self.screen, (60, 20, 20), message_bg)
                pygame.draw.rect(self.screen, (200, 80, 80), message_bg, 3)
                
                # 消息文字
                message_text = message_font.render(self.room_disbanded_message, True, (255, 200, 200))
                message_rect = message_text.get_rect(center=(WIDTH//2, int(HEIGHT * 0.35)))
                self.screen.blit(message_text, message_rect)
            else:
                # 3秒后隐藏消息
                self.show_disbanded_message = False
                self.room_disbanded_message = None

    
    def draw_settings(self):
        # 深色奢华背景渐变
        for y in range(HEIGHT):
            color_ratio = y / HEIGHT
            r = int(15 + (25 - 15) * color_ratio)
            g = int(10 + (20 - 10) * color_ratio)
            b = int(25 + (40 - 25) * color_ratio)
            pygame.draw.line(self.screen, (r, g, b), (0, y), (WIDTH, y))
        
        # 装饰性花纹背景
        self.draw_decorative_patterns()
        
        # 绘制爬行动画
        self.draw_crawling_animations()
        
        # 标题区域 - 奢华金色边框
        title_bg_rect = pygame.Rect(WIDTH//2 - int(WIDTH * 0.2), int(HEIGHT * 0.12), int(WIDTH * 0.4), int(HEIGHT * 0.12))
        pygame.draw.rect(self.screen, (20, 15, 30), title_bg_rect)
        pygame.draw.rect(self.screen, (180, 150, 80), title_bg_rect, 3)
        
        # 标题装饰线
        pygame.draw.line(self.screen, (220, 180, 100), (title_bg_rect.left + 20, title_bg_rect.top + 15), (title_bg_rect.right - 20, title_bg_rect.top + 15), 2)
        pygame.draw.line(self.screen, (220, 180, 100), (title_bg_rect.left + 20, title_bg_rect.bottom - 15), (title_bg_rect.right - 20, title_bg_rect.bottom - 15), 2)
        
        # 标题
        title_font = self.get_chinese_font(int(HEIGHT * 0.086))  # 响应式字体大小
        title_text = title_font.render("◆ 游戏设置 ◆", True, (220, 180, 100))
        title_rect = title_text.get_rect(center=title_bg_rect.center)
        self.screen.blit(title_text, title_rect)
        
        # 设置选项
        settings_font = self.get_chinese_font(int(HEIGHT * 0.055))  # 响应式字体大小
        
        settings_area_y = int(HEIGHT * 0.35)
        
        # 全屏设置
        fullscreen_y = settings_area_y
        fullscreen_bg = pygame.Rect(WIDTH//2 - int(WIDTH * 0.25), fullscreen_y - int(HEIGHT * 0.04), int(WIDTH * 0.5), int(HEIGHT * 0.08))
        
        if self.settings_selection == 0:
            # 选中状态 - 金色边框和背景
            pygame.draw.rect(self.screen, (30, 25, 45), fullscreen_bg)
            pygame.draw.rect(self.screen, (180, 150, 80), fullscreen_bg, 3)
            fullscreen_color = (220, 180, 100)
            
            # 选中装饰
            self.draw_corner_ornaments(fullscreen_bg.x, fullscreen_bg.y, fullscreen_bg.width, fullscreen_bg.height, small=True)
        else:
            # 未选中状态 - 暗色边框
            pygame.draw.rect(self.screen, (25, 20, 35), fullscreen_bg)
            pygame.draw.rect(self.screen, (80, 70, 50), fullscreen_bg, 2)
            fullscreen_color = (200, 180, 140)
        
        fullscreen_status = "开启" if self.fullscreen else "关闭"
        fullscreen_text = settings_font.render(f"全屏模式: {fullscreen_status}", True, fullscreen_color)
        fullscreen_rect = fullscreen_text.get_rect(center=(WIDTH//2, fullscreen_y))
        self.screen.blit(fullscreen_text, fullscreen_rect)
        
        # 分辨率设置
        resolution_y = settings_area_y + int(HEIGHT * 0.12)
        resolution_bg = pygame.Rect(WIDTH//2 - int(WIDTH * 0.25), resolution_y - int(HEIGHT * 0.04), int(WIDTH * 0.5), int(HEIGHT * 0.08))
        
        if self.settings_selection == 1:
            # 选中状态 - 金色边框和背景
            pygame.draw.rect(self.screen, (30, 25, 45), resolution_bg)
            pygame.draw.rect(self.screen, (180, 150, 80), resolution_bg, 3)
            resolution_color = (220, 180, 100)
            
            # 选中装饰
            self.draw_corner_ornaments(resolution_bg.x, resolution_bg.y, resolution_bg.width, resolution_bg.height, small=True)
        else:
            # 未选中状态 - 暗色边框
            pygame.draw.rect(self.screen, (25, 20, 35), resolution_bg)
            pygame.draw.rect(self.screen, (80, 70, 50), resolution_bg, 2)
            resolution_color = (200, 180, 140)
        
        current_res = self.available_resolutions[self.resolution_index]
        resolution_text = settings_font.render(f"分辨率: {current_res[0]}x{current_res[1]} (固定)", True, resolution_color)
        resolution_rect = resolution_text.get_rect(center=(WIDTH//2, resolution_y))
        self.screen.blit(resolution_text, resolution_rect)
        
        # 分辨率已固定，不显示箭头提示
        
        # 音量控制选项
        volume_y = settings_area_y + int(HEIGHT * 0.24)
        volume_bg = pygame.Rect(WIDTH//2 - int(WIDTH * 0.25), volume_y - int(HEIGHT * 0.04), int(WIDTH * 0.5), int(HEIGHT * 0.08))
        
        if self.settings_selection == 2:
            # 选中状态 - 金色边框和背景
            pygame.draw.rect(self.screen, (30, 25, 45), volume_bg)
            pygame.draw.rect(self.screen, (180, 150, 80), volume_bg, 3)
            volume_color = (220, 180, 100)
            
            # 选中装饰
            self.draw_corner_ornaments(volume_bg.x, volume_bg.y, volume_bg.width, volume_bg.height, small=True)
        else:
            # 未选中状态 - 暗色边框
            pygame.draw.rect(self.screen, (25, 20, 35), volume_bg)
            pygame.draw.rect(self.screen, (80, 70, 50), volume_bg, 2)
            volume_color = (200, 180, 140)
        
        volume_percentage = int(self.master_volume * 100)
        volume_text = settings_font.render(f"音量: {volume_percentage}%", True, volume_color)
        volume_rect = volume_text.get_rect(center=(WIDTH//2, volume_y))
        self.screen.blit(volume_text, volume_rect)
        
        if self.settings_selection == 2:
            # 左右箭头提示
            arrow_font = self.get_chinese_font(int(HEIGHT * 0.037))
            left_arrow = arrow_font.render("◀", True, volume_color)
            right_arrow = arrow_font.render("▶", True, volume_color)
            left_rect = left_arrow.get_rect(center=(volume_bg.left + int(WIDTH * 0.04), volume_y))
            right_rect = right_arrow.get_rect(center=(volume_bg.right - int(WIDTH * 0.04), volume_y))
            self.screen.blit(left_arrow, left_rect)
            self.screen.blit(right_arrow, right_rect)
        
        # 按键配置选项
        keybind_y = settings_area_y + int(HEIGHT * 0.36)
        keybind_bg = pygame.Rect(WIDTH//2 - int(WIDTH * 0.25), keybind_y - int(HEIGHT * 0.04), int(WIDTH * 0.5), int(HEIGHT * 0.08))
        
        if self.settings_selection == 3:
            # 选中状态 - 金色边框和背景
            pygame.draw.rect(self.screen, (30, 25, 45), keybind_bg)
            pygame.draw.rect(self.screen, (180, 150, 80), keybind_bg, 3)
            keybind_color = (220, 180, 100)
            
            # 选中装饰
            self.draw_corner_ornaments(keybind_bg.x, keybind_bg.y, keybind_bg.width, keybind_bg.height, small=True)
        else:
            # 未选中状态 - 暗色边框
            pygame.draw.rect(self.screen, (25, 20, 35), keybind_bg)
            pygame.draw.rect(self.screen, (80, 70, 50), keybind_bg, 2)
            keybind_color = (200, 180, 140)
        
        keybind_text = settings_font.render("按键配置", True, keybind_color)
        keybind_rect = keybind_text.get_rect(center=(WIDTH//2, keybind_y))
        self.screen.blit(keybind_text, keybind_rect)
        
        # 返回选项
        back_y = settings_area_y + int(HEIGHT * 0.48)
        back_bg = pygame.Rect(WIDTH//2 - int(WIDTH * 0.25), back_y - int(HEIGHT * 0.04), int(WIDTH * 0.5), int(HEIGHT * 0.08))
        
        if self.settings_selection == 4:
            # 选中状态 - 金色边框和背景
            pygame.draw.rect(self.screen, (30, 25, 45), back_bg)
            pygame.draw.rect(self.screen, (180, 150, 80), back_bg, 3)
            back_color = (220, 180, 100)
            
            # 选中装饰
            self.draw_corner_ornaments(back_bg.x, back_bg.y, back_bg.width, back_bg.height, small=True)
        else:
            # 未选中状态 - 暗色边框
            pygame.draw.rect(self.screen, (25, 20, 35), back_bg)
            pygame.draw.rect(self.screen, (80, 70, 50), back_bg, 2)
            back_color = (200, 180, 140)
        
        back_text = settings_font.render("返回主菜单", True, back_color)
        back_rect = back_text.get_rect(center=(WIDTH//2, back_y))
        self.screen.blit(back_text, back_rect)
    
    def draw_key_binding(self):
        # 绘制背景
        self.screen.fill((15, 10, 25))
        self.draw_decorative_patterns()
        
        # 标题
        title_font = self.get_chinese_font(int(HEIGHT * 0.06))
        title_text = title_font.render("按键配置", True, (220, 180, 100))
        title_rect = title_text.get_rect(center=(WIDTH//2, int(HEIGHT * 0.08)))
        self.screen.blit(title_text, title_rect)
        
        # 设置区域
        settings_area_y = int(HEIGHT * 0.15)
        settings_font = self.get_chinese_font(int(HEIGHT * 0.035))
        
        # 计算可显示的选项数量和滚动偏移
        key_names = list(self.key_bindings.keys())
        option_height = int(HEIGHT * 0.065)
        option_spacing = int(HEIGHT * 0.07)
        visible_area_height = int(HEIGHT * 0.7)
        max_visible_options = visible_area_height // option_spacing
        
        # 初始化滚动偏移（如果没有的话）
        if not hasattr(self, 'key_binding_scroll_offset'):
            self.key_binding_scroll_offset = 0
        
        # 调整滚动偏移以确保选中项可见
        if self.key_binding_selection < self.key_binding_scroll_offset:
            self.key_binding_scroll_offset = self.key_binding_selection
        elif self.key_binding_selection >= self.key_binding_scroll_offset + max_visible_options:
            self.key_binding_scroll_offset = self.key_binding_selection - max_visible_options + 1
        
        # 绘制可见的按键配置选项
        for i in range(max_visible_options):
            option_index = i + self.key_binding_scroll_offset
            if option_index >= len(key_names):
                break
                
            key_name = key_names[option_index]
            option_y = settings_area_y + i * option_spacing
            option_bg = pygame.Rect(WIDTH//2 - int(WIDTH * 0.4), option_y - int(HEIGHT * 0.025), int(WIDTH * 0.8), option_height)
            
            if self.key_binding_selection == option_index:
                # 选中状态
                pygame.draw.rect(self.screen, (30, 25, 45), option_bg)
                pygame.draw.rect(self.screen, (180, 150, 80), option_bg, 3)
                text_color = (220, 180, 100)
                self.draw_corner_ornaments(option_bg.x, option_bg.y, option_bg.width, option_bg.height, small=True)
            else:
                # 未选中状态
                pygame.draw.rect(self.screen, (25, 20, 35), option_bg)
                pygame.draw.rect(self.screen, (80, 70, 50), option_bg, 2)
                text_color = (200, 180, 140)
            
            # 按键名称
            key_display_name = self.key_binding_names[key_name]
            name_text = settings_font.render(key_display_name, True, text_color)
            name_rect = name_text.get_rect(left=option_bg.left + int(WIDTH * 0.03), centery=option_y)
            self.screen.blit(name_text, name_rect)
            
            # 当前按键值
            current_key = self.key_bindings[key_name]
            if self.waiting_for_key == key_name:
                key_text = "按下新按键..."
                key_color = (255, 200, 100)
            else:
                key_text = pygame.key.name(current_key).upper()
                key_color = text_color
            
            key_value_text = settings_font.render(key_text, True, key_color)
            key_value_rect = key_value_text.get_rect(right=option_bg.right - int(WIDTH * 0.03), centery=option_y)
            self.screen.blit(key_value_text, key_value_rect)
        
        # 滚动指示器
        if len(key_names) > max_visible_options:
            # 绘制滚动条
            scrollbar_x = WIDTH - int(WIDTH * 0.02)
            scrollbar_y = settings_area_y
            scrollbar_height = visible_area_height
            scrollbar_width = 4
            
            # 滚动条背景
            pygame.draw.rect(self.screen, (50, 40, 60), (scrollbar_x, scrollbar_y, scrollbar_width, scrollbar_height))
            
            # 滚动条滑块
            total_options = len(key_names)
            slider_height = max(20, scrollbar_height * max_visible_options // total_options)
            slider_y = scrollbar_y + (scrollbar_height - slider_height) * self.key_binding_scroll_offset // (total_options - max_visible_options)
            pygame.draw.rect(self.screen, (180, 150, 80), (scrollbar_x, slider_y, scrollbar_width, slider_height))
        
        # 返回选项（固定在底部）
        back_y = int(HEIGHT * 0.9)
        back_bg = pygame.Rect(WIDTH//2 - int(WIDTH * 0.2), back_y - int(HEIGHT * 0.025), int(WIDTH * 0.4), option_height)
        
        if self.key_binding_selection == len(key_names):
            # 选中状态
            pygame.draw.rect(self.screen, (30, 25, 45), back_bg)
            pygame.draw.rect(self.screen, (180, 150, 80), back_bg, 3)
            back_color = (220, 180, 100)
            self.draw_corner_ornaments(back_bg.x, back_bg.y, back_bg.width, back_bg.height, small=True)
        else:
            # 未选中状态
            pygame.draw.rect(self.screen, (25, 20, 35), back_bg)
            pygame.draw.rect(self.screen, (80, 70, 50), back_bg, 2)
            back_color = (200, 180, 140)
        
        back_text = settings_font.render("返回设置", True, back_color)
        back_rect = back_text.get_rect(center=(WIDTH//2, back_y))
        self.screen.blit(back_text, back_rect)
        

    
    def draw_create_room(self):
        self.screen.fill(BLACK)
        
        # 绘制背景动画
        self.draw_crawling_animations()
        
        # 绘制装饰图案
        self.draw_decorative_patterns()
        
        # 使用相对坐标进行自适应布局
        center_x = WIDTH // 2
        
        # 标题 - 相对于屏幕高度的15%位置
        title_font = self.get_chinese_font(int(48 * min(WIDTH/1200, HEIGHT/650)))
        title_text = title_font.render("创建房间", True, WHITE)
        title_rect = title_text.get_rect(center=(center_x, int(HEIGHT * 0.15)))
        self.screen.blit(title_text, title_rect)
        
        # 房间信息 - 相对于屏幕高度的30-45%位置
        info_font = self.get_chinese_font(int(24 * min(WIDTH/1200, HEIGHT/650)))
        if self.local_server:
            ip_text = info_font.render(f"房间IP: {self.room_ip}", True, WHITE)
            port_text = info_font.render(f"端口: {self.room_port}", True, WHITE)
            status_text = info_font.render("房间已创建，等待玩家加入...", True, GREEN)
        else:
            status_text = info_font.render("准备创建房间...", True, WHITE)
            ip_text = None
            port_text = None
        
        if ip_text:
            ip_rect = ip_text.get_rect(center=(center_x, int(HEIGHT * 0.30)))
            self.screen.blit(ip_text, ip_rect)
        if port_text:
            port_rect = port_text.get_rect(center=(center_x, int(HEIGHT * 0.37)))
            self.screen.blit(port_text, port_rect)
        
        status_rect = status_text.get_rect(center=(center_x, int(HEIGHT * 0.46)))
        self.screen.blit(status_text, status_rect)
        
        # 按钮 - 相对于屏幕尺寸的按钮大小和位置
        button_font = self.get_chinese_font(int(32 * min(WIDTH/1200, HEIGHT/650)))
        button_width = int(200 * WIDTH/1200)
        button_height = int(50 * HEIGHT/650)
        
        if not self.local_server:
            # 创建房间按钮 - 相对于屏幕高度的62%位置
            create_button = pygame.Rect(center_x - button_width//2, int(HEIGHT * 0.62), button_width, button_height)
            pygame.draw.rect(self.screen, BLUE, create_button)
            pygame.draw.rect(self.screen, WHITE, create_button, 2)
            create_text = button_font.render("创建房间", True, WHITE)
            create_text_rect = create_text.get_rect(center=create_button.center)
            self.screen.blit(create_text, create_text_rect)
        else:
            # 进入等待房间按钮 - 相对于屏幕高度的62%位置
            enter_button = pygame.Rect(center_x - button_width//2, int(HEIGHT * 0.62), button_width, button_height)
            pygame.draw.rect(self.screen, GREEN, enter_button)
            pygame.draw.rect(self.screen, WHITE, enter_button, 2)
            enter_text = button_font.render("进入房间", True, WHITE)
            enter_text_rect = enter_text.get_rect(center=enter_button.center)
            self.screen.blit(enter_text, enter_text_rect)
        
        # 返回按钮 - 相对于屏幕高度的74%位置
        back_button = pygame.Rect(center_x - button_width//2, int(HEIGHT * 0.74), button_width, button_height)
        pygame.draw.rect(self.screen, (100, 100, 100), back_button)
        pygame.draw.rect(self.screen, WHITE, back_button, 2)
        back_text = button_font.render("返回", True, WHITE)
        back_text_rect = back_text.get_rect(center=back_button.center)
        self.screen.blit(back_text, back_text_rect)
    
    def draw_join_room(self):
        self.screen.fill(BLACK)
        
        # 绘制背景动画
        self.draw_crawling_animations()
        
        # 绘制装饰图案
        self.draw_decorative_patterns()
        
        # 使用相对坐标进行自适应布局
        center_x = WIDTH // 2
        scale_factor = min(WIDTH/1200, HEIGHT/650)
        
        # 标题 - 相对于屏幕高度的15%位置
        title_font = self.get_chinese_font(int(48 * scale_factor))
        title_text = title_font.render("加入房间", True, WHITE)
        title_rect = title_text.get_rect(center=(center_x, int(HEIGHT * 0.15)))
        self.screen.blit(title_text, title_rect)
        
        # IP输入框 - 相对于屏幕高度的30%位置
        input_font = self.get_chinese_font(int(24 * scale_factor))
        ip_label = input_font.render("房间IP:", True, WHITE)
        ip_label_rect = ip_label.get_rect(center=(center_x - int(150 * scale_factor), int(HEIGHT * 0.30)))
        self.screen.blit(ip_label, ip_label_rect)
        
        input_box_width = int(200 * scale_factor)
        input_box_height = int(40 * scale_factor)
        ip_box = pygame.Rect(center_x - input_box_width//2, int(HEIGHT * 0.28), input_box_width, input_box_height)
        ip_color = BLUE if self.input_field == "ip" else WHITE
        pygame.draw.rect(self.screen, ip_color, ip_box, 2)
        ip_text = input_font.render(self.room_ip, True, WHITE)
        self.screen.blit(ip_text, (ip_box.x + int(5 * scale_factor), ip_box.y + int(8 * scale_factor)))
        
        # 端口输入框 - 相对于屏幕高度的43%位置
        port_label = input_font.render("端口:", True, WHITE)
        port_label_rect = port_label.get_rect(center=(center_x - int(150 * scale_factor), int(HEIGHT * 0.43)))
        self.screen.blit(port_label, port_label_rect)
        
        port_box = pygame.Rect(center_x - input_box_width//2, int(HEIGHT * 0.41), input_box_width, input_box_height)
        port_color = BLUE if self.input_field == "port" else WHITE
        pygame.draw.rect(self.screen, port_color, port_box, 2)
        port_text = input_font.render(self.room_port, True, WHITE)
        self.screen.blit(port_text, (port_box.x + int(5 * scale_factor), port_box.y + int(8 * scale_factor)))
        

        
        # 按钮 - 相对于屏幕尺寸的按钮大小和位置
        button_font = self.get_chinese_font(int(32 * scale_factor))
        button_width = int(200 * scale_factor)
        button_height = int(50 * scale_factor)
        
        # 连接按钮 - 相对于屏幕高度的62%位置
        connect_button = pygame.Rect(center_x - button_width//2, int(HEIGHT * 0.62), button_width, button_height)
        pygame.draw.rect(self.screen, GREEN, connect_button)
        pygame.draw.rect(self.screen, WHITE, connect_button, 2)
        connect_text = button_font.render("连接", True, WHITE)
        connect_text_rect = connect_text.get_rect(center=connect_button.center)
        self.screen.blit(connect_text, connect_text_rect)
        
        # 返回按钮 - 相对于屏幕高度的74%位置
        back_button = pygame.Rect(center_x - button_width//2, int(HEIGHT * 0.74), button_width, button_height)
        pygame.draw.rect(self.screen, (100, 100, 100), back_button)
        pygame.draw.rect(self.screen, WHITE, back_button, 2)
        back_text = button_font.render("返回", True, WHITE)
        back_text_rect = back_text.get_rect(center=back_button.center)
        self.screen.blit(back_text, back_text_rect)
    
    def draw_waiting_room(self):
        self.screen.fill(BLACK)
        
        # 绘制背景动画
        self.draw_crawling_animations()
        
        # 绘制装饰图案
        self.draw_decorative_patterns()
        
        # 使用相对坐标进行自适应布局
        center_x = WIDTH // 2
        scale_factor = min(WIDTH/1200, HEIGHT/650)
        
        # 标题 - 相对于屏幕高度的12%位置
        title_font = self.get_chinese_font(int(48 * scale_factor))
        title_text = title_font.render("等待房间", True, WHITE)
        title_rect = title_text.get_rect(center=(center_x, int(HEIGHT * 0.12)))
        self.screen.blit(title_text, title_rect)
        
        # 房间信息 - 相对于屏幕高度的22%位置
        info_font = self.get_chinese_font(int(24 * scale_factor))
        room_info = info_font.render(f"房间: {self.room_ip}:{self.room_port}", True, WHITE)
        room_info_rect = room_info.get_rect(center=(center_x, int(HEIGHT * 0.22)))
        self.screen.blit(room_info, room_info_rect)
        
        # 玩家列表标题 - 相对于屏幕高度的31%位置
        player_font = self.get_chinese_font(int(28 * scale_factor))
        players_title = player_font.render("房间玩家:", True, WHITE)
        players_title_rect = players_title.get_rect(center=(center_x, int(HEIGHT * 0.31)))
        self.screen.blit(players_title, players_title_rect)
        
        # 显示玩家信息 - 从屏幕高度的38%开始
        y_start = int(HEIGHT * 0.38)
        line_height = int(40 * scale_factor)
        
        # 显示当前玩家信息
        current_player_name = self.player_name if self.player_name else "未命名"
        current_character = "未选择"
        current_character_index = -1
        if self.character_selected and hasattr(self, 'selected_character'):
            current_character = self.character_options[self.selected_character]['name']
            current_character_index = self.selected_character
        
        # 绘制当前玩家的角色头像动画（如果已选择角色）
        avatar_size = int(32 * scale_factor)
        avatar_spacing = int(50 * scale_factor)  # 头像与文字之间的间距，基于缩放因子
        text_offset = avatar_size + int(10 * scale_factor)  # 头像和文字之间的间距
        
        if current_character_index >= 0 and current_character_index in self.character_preview_animations:
            anim_data = self.character_preview_animations[current_character_index]
            current_frame = anim_data['frames'][anim_data['frame_index']]
            # 缩放头像到合适大小
            scaled_avatar = pygame.transform.scale(current_frame, (avatar_size, avatar_size))
            avatar_x = center_x - text_offset // 2 - avatar_size - avatar_spacing  # 头像在文字前面，使用相对间距
            avatar_y = y_start - avatar_size // 2
            self.screen.blit(scaled_avatar, (avatar_x, avatar_y))
        
        current_player_text = f"{current_player_name} ({current_character}) (你)"
        current_player_surface = info_font.render(current_player_text, True, WHITE)
        # 如果有头像，文字向右偏移
        text_x = center_x - text_offset // 2 + (avatar_size + avatar_spacing + int(10 * scale_factor) if current_character_index >= 0 else 0)
        current_player_rect = current_player_surface.get_rect(center=(text_x, y_start))
        self.screen.blit(current_player_surface, current_player_rect)
        
        # 显示其他玩家信息
        if hasattr(self, 'network_client') and self.network_client and self.network_client.other_players:
            for i, (player_id, player_data) in enumerate(self.network_client.other_players.items()):
                player_name = player_data.get('player_name', f'玩家{player_id}')
                character_name = player_data.get('character_name', '未选择')
                
                # 计算延迟（基于时间戳差异）
                import time
                current_time = time.time()
                last_update = player_data.get('timestamp', current_time)
                ping = int((current_time - last_update) * 1000) if current_time > last_update else 0
                # 如果延迟过大，可能是数据问题，显示为0
                ping = ping if ping < 5000 else 0
                ping = min(ping, 999)  # 限制最大显示延迟
                
                # 查找角色索引
                other_character_index = -1
                for j, char_option in enumerate(self.character_options):
                    if char_option['name'] == character_name:
                        other_character_index = j
                        break
                
                player_y = y_start + (i + 1) * line_height
                
                # 绘制其他玩家的角色头像动画（如果已选择角色）
                if other_character_index >= 0 and other_character_index in self.character_preview_animations:
                    anim_data = self.character_preview_animations[other_character_index]
                    current_frame = anim_data['frames'][anim_data['frame_index']]
                    # 缩放头像到合适大小
                    scaled_avatar = pygame.transform.scale(current_frame, (avatar_size, avatar_size))
                    avatar_x = center_x - text_offset // 2 - avatar_size - avatar_spacing  # 头像在文字前面，使用相对间距
                    avatar_y = player_y - avatar_size // 2
                    self.screen.blit(scaled_avatar, (avatar_x, avatar_y))
                
                # 玩家信息包含延迟
                player_text = f"{player_name} ({character_name}) - 延迟: {ping}ms"
                
                player_surface = info_font.render(player_text, True, WHITE)
                # 如果有头像，文字向右偏移
                text_x = center_x - text_offset // 2 + (avatar_size + avatar_spacing + int(10 * scale_factor) if other_character_index >= 0 else 0)
                player_rect = player_surface.get_rect(center=(text_x, player_y))
                self.screen.blit(player_surface, player_rect)
        
        # 网络状态 - 相对于屏幕高度的62%位置
        if self.ping_time > 0:
            ping_text = info_font.render(f"网络延迟: {self.ping_time}ms", True, GREEN if self.ping_time < 100 else (255, 255, 0) if self.ping_time < 200 else (255, 0, 0))
            ping_rect = ping_text.get_rect(center=(center_x, int(HEIGHT * 0.62)))
            self.screen.blit(ping_text, ping_rect)
        
        # 按钮 - 相对于屏幕尺寸的按钮大小和位置
        button_font = self.get_chinese_font(int(32 * scale_factor))
        button_width = int(200 * scale_factor)
        button_height = int(50 * scale_factor)
        
        # 开始游戏按钮（仅房主可见） - 相对于屏幕高度的67%位置
        # 计算总玩家数（包括当前玩家）
        total_players = 1  # 当前玩家
        if hasattr(self, 'network_client') and self.network_client and self.network_client.other_players:
            total_players += len(self.network_client.other_players)
        
        if self.mode == HOST_ROOM and total_players >= 1:
            start_button = pygame.Rect(center_x - button_width//2, int(HEIGHT * 0.67), button_width, button_height)
            if self.character_selected:
                # 角色已选择，可以开始游戏
                pygame.draw.rect(self.screen, GREEN, start_button)
                pygame.draw.rect(self.screen, WHITE, start_button, 2)
                start_text = button_font.render("开始游戏", True, WHITE)
            else:
                # 角色未选择，按钮禁用
                pygame.draw.rect(self.screen, (100, 100, 100), start_button)
                pygame.draw.rect(self.screen, (150, 150, 150), start_button, 2)
                start_text = button_font.render("请先选择角色", True, (200, 200, 200))
            start_text_rect = start_text.get_rect(center=start_button.center)
            self.screen.blit(start_text, start_text_rect)
        elif total_players < 1:
            waiting_text = info_font.render("等待玩家加入...", True, (200, 200, 200))
            waiting_rect = waiting_text.get_rect(center=(center_x, int(HEIGHT * 0.70)))
            self.screen.blit(waiting_text, waiting_rect)
        
        # 地图选择显示（仅房主可见） - 左中位置
        if self.mode == HOST_ROOM and self.available_map_series:
            map_font = self.get_chinese_font(int(20 * scale_factor))
            current_series = self.available_map_series[self.selected_series]
            current_level = current_series['loaded_levels'][self.selected_level]
            
            # 缩略图尺寸和位置
            thumbnail_width = int(200 * scale_factor)
            thumbnail_height = int(130 * scale_factor)
            thumbnail_x = int(WIDTH * 0.15)  # 左侧15%位置
            thumbnail_y = int(HEIGHT * 0.45)  # 中间位置
            
            # 绘制地图缩略图
            self.draw_map_thumbnail(current_level, thumbnail_x, thumbnail_y, thumbnail_width, thumbnail_height)
            
            # 系列名称显示在缩略图下方
            series_text = f"系列: {current_series['series_name']}"
            series_surface = map_font.render(series_text, True, WHITE)
            series_rect = series_surface.get_rect(center=(thumbnail_x + thumbnail_width // 2, thumbnail_y + thumbnail_height + int(15 * scale_factor)))
            self.screen.blit(series_surface, series_rect)
            
            # 关卡名称显示
            level_text = f"关卡: {current_level['level_name']}"
            level_surface = map_font.render(level_text, True, (200, 200, 200))
            level_rect = level_surface.get_rect(center=(thumbnail_x + thumbnail_width // 2, thumbnail_y + thumbnail_height + int(35 * scale_factor)))
            self.screen.blit(level_surface, level_rect)
            
            # 地图切换提示
            hint_text = "← → 切换系列"
            hint_surface = map_font.render(hint_text, True, (150, 150, 150))
            hint_rect = hint_surface.get_rect(center=(thumbnail_x + thumbnail_width // 2, thumbnail_y + thumbnail_height + int(55 * scale_factor)))
            self.screen.blit(hint_surface, hint_rect)
        
        # 角色选择按钮 - 相对于屏幕高度的79%位置
        character_button = pygame.Rect(center_x - button_width//2, int(HEIGHT * 0.79), button_width, button_height)
        pygame.draw.rect(self.screen, BLUE, character_button)
        pygame.draw.rect(self.screen, WHITE, character_button, 2)
        character_text = button_font.render("角色选择", True, WHITE)
        character_text_rect = character_text.get_rect(center=character_button.center)
        self.screen.blit(character_text, character_text_rect)
        
        # 离开房间按钮 - 相对于屏幕高度的89%位置
        leave_button = pygame.Rect(center_x - button_width//2, int(HEIGHT * 0.89), button_width, button_height)
        pygame.draw.rect(self.screen, (100, 100, 100), leave_button)
        pygame.draw.rect(self.screen, WHITE, leave_button, 2)
        leave_text = button_font.render("离开房间", True, WHITE)
        leave_text_rect = leave_text.get_rect(center=leave_button.center)
        self.screen.blit(leave_text, leave_text_rect)
    
    def draw_character_select(self):
        # 深色奢华背景渐变
        for y in range(HEIGHT):
            color_ratio = y / HEIGHT
            r = int(15 + (25 - 15) * color_ratio)
            g = int(10 + (20 - 10) * color_ratio)
            b = int(25 + (40 - 25) * color_ratio)
            pygame.draw.line(self.screen, (r, g, b), (0, y), (WIDTH, y))
        
        # 装饰性花纹背景
        self.draw_decorative_patterns()
        
        # 标题区域 - 奢华金色
        title_bg_rect = pygame.Rect(WIDTH//2 - 200, 20, 400, 80)
        pygame.draw.rect(self.screen, (20, 15, 30), title_bg_rect)
        pygame.draw.rect(self.screen, (180, 150, 80), title_bg_rect, 3)
        
        # 标题装饰线
        pygame.draw.line(self.screen, (220, 180, 100), (WIDTH//2 - 180, 35), (WIDTH//2 + 180, 35), 2)
        pygame.draw.line(self.screen, (220, 180, 100), (WIDTH//2 - 180, 85), (WIDTH//2 + 180, 85), 2)
        
        title_font = self.get_chinese_font(int(HEIGHT * 0.074))  # 基于屏幕高度的字体大小
        title_text = title_font.render("◆ 选择角色 ◆", True, (220, 180, 100))
        title_rect = title_text.get_rect(center=(WIDTH//2, 60))
        self.screen.blit(title_text, title_rect)
        
        # 左侧角色显示区域 - 奢华边框（响应式布局）
        char_area_x = WIDTH // 15  # 相对于屏幕宽度
        char_area_y = HEIGHT // 5  # 相对于屏幕高度
        char_area_width = int(WIDTH * 0.375)  # 屏幕宽度的37.5%
        char_area_height = int(HEIGHT * 0.54)  # 屏幕高度的54%
        
        # 多层边框效果
        pygame.draw.rect(self.screen, (30, 25, 45), (char_area_x - 10, char_area_y - 10, char_area_width + 20, char_area_height + 20))
        pygame.draw.rect(self.screen, (180, 150, 80), (char_area_x - 10, char_area_y - 10, char_area_width + 20, char_area_height + 20), 2)
        pygame.draw.rect(self.screen, (40, 35, 60), (char_area_x, char_area_y, char_area_width, char_area_height))
        pygame.draw.rect(self.screen, (120, 100, 60), (char_area_x, char_area_y, char_area_width, char_area_height), 3)
        
        # 内部装饰花纹
        self.draw_corner_ornaments(char_area_x, char_area_y, char_area_width, char_area_height)
        
        # 当前选中的角色
        current_char = self.character_options[self.selected_character]
        
        # 角色展示台
        char_center_x = char_area_x + char_area_width // 2
        char_center_y = char_area_y + int(char_area_height * 0.43)  # 相对于区域高度
        
        # 角色动画显示
        if self.selected_character in self.character_preview_animations:
            anim_data = self.character_preview_animations[self.selected_character]
            current_frame = anim_data['frames'][anim_data['frame_index']]
            
            # 缩放动画帧到合适大小（基于屏幕尺寸）
            avatar_size = int(min(WIDTH, HEIGHT) * 0.18)  # 基于屏幕最小尺寸的18%
            scaled_frame = pygame.transform.scale(current_frame, (avatar_size, avatar_size))
            
            # 角色光环效果（基于屏幕尺寸）
            base_radius = int(min(WIDTH, HEIGHT) * 0.11)  # 基础半径
            for i in range(3):
                alpha = 30 - i * 10
                radius = base_radius + i * int(min(WIDTH, HEIGHT) * 0.023)
                glow_surface = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
                pygame.draw.circle(glow_surface, (*current_char["color"], alpha), (radius, radius), radius)
                self.screen.blit(glow_surface, (char_center_x - radius, char_center_y - radius))
            
            # 角色边框（基于屏幕尺寸）
            border_radius1 = int(min(WIDTH, HEIGHT) * 0.1)
            border_radius2 = int(min(WIDTH, HEIGHT) * 0.108)
            pygame.draw.circle(self.screen, (220, 180, 100), (char_center_x, char_center_y), border_radius1, 4)
            pygame.draw.circle(self.screen, (180, 150, 80), (char_center_x, char_center_y), border_radius2, 2)
            
            # 显示角色动画
            frame_rect = scaled_frame.get_rect(center=(char_center_x, char_center_y))
            self.screen.blit(scaled_frame, frame_rect)
        else:
            # 备用显示（圆形，基于屏幕尺寸）
            fallback_radius = int(min(WIDTH, HEIGHT) * 0.092)
            pygame.draw.circle(self.screen, current_char["color"], (char_center_x, char_center_y), fallback_radius)
            pygame.draw.circle(self.screen, (220, 180, 100), (char_center_x, char_center_y), fallback_radius, 4)
        
        # 角色名称 - 华丽字体（基于屏幕尺寸）
        char_name_font = self.get_chinese_font(int(HEIGHT * 0.065))
        char_name_text = char_name_font.render(current_char["name"], True, (220, 180, 100))
        char_name_rect = char_name_text.get_rect(center=(char_center_x, char_center_y + int(char_area_height * 0.34)))
        
        # 名称背景
        name_bg_rect = pygame.Rect(char_name_rect.x - 20, char_name_rect.y - 5, char_name_rect.width + 40, char_name_rect.height + 10)
        pygame.draw.rect(self.screen, (20, 15, 30), name_bg_rect)
        pygame.draw.rect(self.screen, (120, 100, 60), name_bg_rect, 2)
        self.screen.blit(char_name_text, char_name_rect)
        
        # 翻页指示器 - 华丽箭头（基于屏幕尺寸）
        if len(self.character_options) > 1:
            arrow_font = self.get_chinese_font(int(HEIGHT * 0.049))
            arrow_btn_size = int(min(WIDTH, HEIGHT) * 0.062)  # 箭头按钮大小
            arrow_offset = int(char_area_width * 0.033)  # 箭头距离边缘的偏移
            
            # 左箭头
            if self.selected_character > 0:
                left_bg = pygame.Rect(char_area_x + arrow_offset, char_center_y - arrow_btn_size//2, arrow_btn_size, arrow_btn_size)
                pygame.draw.rect(self.screen, (30, 25, 45), left_bg)
                pygame.draw.rect(self.screen, (180, 150, 80), left_bg, 2)
                left_arrow = arrow_font.render("<", True, (220, 180, 100))
                arrow_rect = left_arrow.get_rect(center=left_bg.center)
                self.screen.blit(left_arrow, arrow_rect)
            
            # 右箭头
            if self.selected_character < len(self.character_options) - 1:
                right_bg = pygame.Rect(char_area_x + char_area_width - arrow_offset - arrow_btn_size, char_center_y - arrow_btn_size//2, arrow_btn_size, arrow_btn_size)
                pygame.draw.rect(self.screen, (30, 25, 45), right_bg)
                pygame.draw.rect(self.screen, (180, 150, 80), right_bg, 2)
                right_arrow = arrow_font.render(">", True, (220, 180, 100))
                arrow_rect = right_arrow.get_rect(center=right_bg.center)
                self.screen.blit(right_arrow, arrow_rect)
            
            # 页码指示 - 华丽样式（基于屏幕尺寸）
            page_info = f"◆ {self.selected_character + 1} / {len(self.character_options)} ◆"
            page_font = self.get_chinese_font(int(HEIGHT * 0.031))
            page_text = page_font.render(page_info, True, (180, 150, 80))
            page_rect = page_text.get_rect(center=(char_center_x, char_area_y + char_area_height - int(char_area_height * 0.071)))
            self.screen.blit(page_text, page_rect)
        
        # 右侧角色介绍区域 - 奢华设计（响应式布局）
        info_area_x = int(WIDTH * 0.48)  # 屏幕宽度的48%
        info_area_y = HEIGHT // 5  # 相对于屏幕高度
        info_area_width = int(WIDTH * 0.46)  # 屏幕宽度的46%
        info_area_height = int(HEIGHT * 0.54)  # 屏幕高度的54%
        
        # 多层边框
        pygame.draw.rect(self.screen, (30, 25, 45), (info_area_x - 10, info_area_y - 10, info_area_width + 20, info_area_height + 20))
        pygame.draw.rect(self.screen, (180, 150, 80), (info_area_x - 10, info_area_y - 10, info_area_width + 20, info_area_height + 20), 2)
        pygame.draw.rect(self.screen, (35, 30, 50), (info_area_x, info_area_y, info_area_width, info_area_height))
        pygame.draw.rect(self.screen, (120, 100, 60), (info_area_x, info_area_y, info_area_width, info_area_height), 3)
        
        # 装饰花纹
        self.draw_corner_ornaments(info_area_x, info_area_y, info_area_width, info_area_height)
        
        # 标题区域
        title_bg = pygame.Rect(info_area_x + 20, info_area_y + 15, info_area_width - 40, 50)
        pygame.draw.rect(self.screen, (25, 20, 40), title_bg)
        pygame.draw.rect(self.screen, (180, 150, 80), title_bg, 2)
        
        info_title_font = self.get_chinese_font(int(HEIGHT * 0.049))  # 基于屏幕高度
        info_title = info_title_font.render("◆ 角色详情 ◆", True, (220, 180, 100))
        info_title_rect = info_title.get_rect(center=(info_area_x + info_area_width//2, info_area_y + 40))
        self.screen.blit(info_title, info_title_rect)
        
        # 角色描述（基于屏幕尺寸）
        desc_font = self.get_chinese_font(int(HEIGHT * 0.037))
        desc_text = desc_font.render(current_char["description"], True, (200, 180, 140))
        self.screen.blit(desc_text, (info_area_x + 30, info_area_y + 85))
        
        # 分隔线
        pygame.draw.line(self.screen, (180, 150, 80), (info_area_x + 30, info_area_y + 120), (info_area_x + info_area_width - 30, info_area_y + 120), 2)
        
        # 角色属性 - 华丽展示（基于屏幕尺寸）
        attr_font = self.get_chinese_font(int(HEIGHT * 0.034))
        attr_y_start = info_area_y + 140
        
        # 根据角色类型显示不同属性
        if current_char["name"] == "哈基为":
            attributes = [
                ("⚔️ 攻击力", "★★★☆☆", (220, 100, 100)),
                ("🏃 速度", "★★★☆☆", (100, 180, 220)),
                ("🛡️ 防御力", "★★★☆☆", (100, 220, 100)),
                ("🦘 跳跃力", "★★★☆☆", (220, 180, 100))
            ]
        elif current_char["name"] == "哈基阳":
            attributes = [
                ("⚔️ 攻击力", "★★☆☆☆", (220, 100, 100)),
                ("🏃 速度", "★★★★★", (100, 180, 220)),
                ("🛡️ 防御力", "★★☆☆☆", (100, 220, 100)),
                ("🦘 跳跃力", "★★★★☆", (220, 180, 100))
            ]
        else:  # 战士
            attributes = [
                ("⚔️ 攻击力", "★★★★☆", (220, 100, 100)),
                ("🏃 速度", "★★☆☆☆", (100, 180, 220)),
                ("🛡️ 防御力", "★★★★★", (100, 220, 100)),
                ("🦘 跳跃力", "★★☆☆☆", (220, 180, 100))
            ]
        
        for i, (attr_name, stars, color) in enumerate(attributes):
            y_pos = attr_y_start + i * int(HEIGHT * 0.062)  # 基于屏幕高度的间距
            
            # 属性背景
            attr_bg = pygame.Rect(info_area_x + 25, y_pos - 5, info_area_width - 50, 30)
            pygame.draw.rect(self.screen, (25, 20, 40), attr_bg)
            pygame.draw.rect(self.screen, (80, 70, 50), attr_bg, 1)
            
            # 属性名称
            attr_text = attr_font.render(attr_name, True, (200, 180, 140))
            self.screen.blit(attr_text, (info_area_x + 35, y_pos))
            
            # 星级显示
            stars_text = attr_font.render(stars, True, color)
            self.screen.blit(stars_text, (info_area_x + 200, y_pos))
        
        # 玩家名称输入区域 - 奢华设计（响应式布局）
        name_y = int(HEIGHT * 0.89)  # 相对于屏幕高度的89%位置
        name_font = self.get_chinese_font(int(HEIGHT * 0.034))  # 基于屏幕高度的字体大小
        
        # 名称标签
        name_label = name_font.render("◆ 玩家名称 ◆", True, (220, 180, 100))
        name_label_rect = name_label.get_rect(center=(WIDTH//2, name_y - 10))
        self.screen.blit(name_label, name_label_rect)
        
        # 名称输入框（响应式宽度）
        box_width = int(WIDTH * 0.23)  # 屏幕宽度的23%
        name_box_rect = pygame.Rect(WIDTH//2 - box_width//2, name_y + 8, box_width, 25)
        pygame.draw.rect(self.screen, (20, 15, 30), name_box_rect)
        if self.input_active:
            pygame.draw.rect(self.screen, (220, 180, 100), name_box_rect, 2)
        else:
            pygame.draw.rect(self.screen, (120, 100, 60), name_box_rect, 2)
        
        # 名称显示
        if self.input_active:
            display_name = self.temp_name + "_"  # 显示光标
            name_color = (220, 180, 100)
        else:
            display_name = self.player_name if self.player_name else "点击输入名称"
            name_color = (200, 180, 140) if self.player_name else (120, 100, 80)
        
        name_text = self.get_chinese_font(18).render(display_name, True, name_color)
        name_rect = name_text.get_rect(center=(WIDTH//2, name_y + 20))
        self.screen.blit(name_text, name_rect)
        
        # 操作提示 - 华丽样式
        hint_font = self.get_chinese_font(12)  # 更小的字体

    
    def load_character_previews(self):
        """加载角色预览动画"""
        for i, character in enumerate(self.character_options):
            try:
                gif_path = character["gif_folder"] + "noMoveAnimation.gif"
                frames = self.load_gif_frames(gif_path)
                self.character_preview_animations[i] = {
                    'frames': frames,
                    'frame_index': 0,
                    'frame_timer': 0,
                    'animation_speed': 0.025
                }
            except Exception as e:
                print(f"加载角色 {character['name']} 预览动画失败: {e}")
                # 创建备用图片
                fallback_surface = pygame.Surface((64, 64))
                fallback_surface.fill(character["color"])
                self.character_preview_animations[i] = {
                    'frames': [fallback_surface],
                    'frame_index': 0,
                    'frame_timer': 0,
                    'animation_speed': 0.025
                }
    
    def load_gif_frames(self, gif_path):
        """加载GIF动画帧（复用Player类的方法）"""
        try:
            from PIL import Image
            frames = []
            with Image.open(gif_path) as gif:
                for frame_num in range(gif.n_frames):
                    gif.seek(frame_num)
                    frame = gif.copy().convert('RGBA')
                    
                    # 转换为pygame surface
                    frame_data = frame.tobytes()
                    pygame_surface = pygame.image.fromstring(frame_data, frame.size, 'RGBA')
                    
                    # 处理透明度，去除白边
                    pygame_surface = pygame_surface.convert_alpha()
                    
                    # 创建新的surface来处理白边
                    clean_surface = pygame.Surface(frame.size, pygame.SRCALPHA)
                    clean_surface.fill((0, 0, 0, 0))  # 完全透明背景
                    
                    # 逐像素处理，去除白色和接近白色的像素
                    for x in range(frame.size[0]):
                        for y in range(frame.size[1]):
                            pixel = frame.getpixel((x, y))
                            if len(pixel) == 4:  # RGBA
                                r, g, b, a = pixel
                                # 如果不是白色或接近白色，且有一定透明度，则保留
                                if not (r > 240 and g > 240 and b > 240) and a > 50:
                                    clean_surface.set_at((x, y), (r, g, b, a))
                    
                    # 保持原始尺寸，不进行缩放
                    frames.append(clean_surface)
            
            return frames if frames else [self.create_fallback_frame()]
        except Exception as e:
            print(f"加载GIF失败 {gif_path}: {e}")
            return [self.create_fallback_frame()]
    
    def create_fallback_frame(self):
        """创建备用帧"""
        surface = pygame.Surface((64, 64))
        surface.fill(BLUE)
        return surface
    
    def update_character_preview_animations(self):
        """更新角色预览动画"""
        for char_id, anim_data in self.character_preview_animations.items():
            anim_data['frame_timer'] += 1/FPS
            if anim_data['frame_timer'] >= anim_data['animation_speed']:
                anim_data['frame_timer'] = 0
                anim_data['frame_index'] = (anim_data['frame_index'] + 1) % len(anim_data['frames'])
    
    def load_crawling_animation(self):
        """加载爬行动画图片"""
        import random
        try:
            # 加载动画图片帧
            frames = self.load_gif_frames('img/backanimation.jpg')
            if not frames:
                # 如果加载失败，创建备用帧
                frames = [self.create_fallback_frame()]
            
            # 获取图片原始尺寸
            original_width = frames[0].get_width() if frames else 64
            original_height = frames[0].get_height() if frames else 64
            
            # 创建2个跟随鼠标的动画
            for i in range(2):
                crawling_anim = {
                    'type': 'follow_mouse',
                    'frames': frames,
                    'frame_index': 0,
                    'frame_timer': 0,
                    'animation_speed': random.uniform(0.04, 0.08),
                    'x': random.randint(0, WIDTH - original_width),
                    'y': random.randint(0, HEIGHT - original_height),
                    'vel_x': 0,
                    'vel_y': 0,
                    'width': original_width,
                    'height': original_height
                }
                self.crawling_animations.append(crawling_anim)
            
            # 创建5个随机爬行的动画
            for i in range(5):
                crawling_anim = {
                    'type': 'random_crawl',
                    'frames': frames,
                    'frame_index': 0,
                    'frame_timer': 0,
                    'animation_speed': random.uniform(0.04, 0.08),
                    'x': random.randint(0, WIDTH - original_width),
                    'y': random.randint(0, HEIGHT - original_height),
                    'vel_x': random.uniform(-1.5, 1.5),
                    'vel_y': random.uniform(-1.5, 1.5),
                    'width': original_width,
                    'height': original_height,
                    'direction_change_timer': 0,
                    'direction_change_interval': random.uniform(60, 180)  # 1-3秒改变方向
                }
                self.crawling_animations.append(crawling_anim)
            
            # 创建3个沿着页面边缘爬行的动画
            edges = ['top', 'right', 'bottom']  # 三个边缘
            for i, edge in enumerate(edges):
                if edge == 'top':
                    x = random.randint(0, WIDTH - original_width)
                    y = 0
                    vel_x = random.choice([-1, 1]) * random.uniform(1, 2)
                    vel_y = 0
                elif edge == 'right':
                    x = WIDTH - original_width
                    y = random.randint(0, HEIGHT - original_height)
                    vel_x = 0
                    vel_y = random.choice([-1, 1]) * random.uniform(1, 2)
                elif edge == 'bottom':
                    x = random.randint(0, WIDTH - original_width)
                    y = HEIGHT - original_height
                    vel_x = random.choice([-1, 1]) * random.uniform(1, 2)
                    vel_y = 0
                
                crawling_anim = {
                    'type': 'edge_crawl',
                    'edge': edge,
                    'frames': frames,
                    'frame_index': 0,
                    'frame_timer': 0,
                    'animation_speed': random.uniform(0.04, 0.08),
                    'x': x,
                    'y': y,
                    'vel_x': vel_x,
                    'vel_y': vel_y,
                    'width': original_width,
                    'height': original_height
                }
                self.crawling_animations.append(crawling_anim)
        except Exception as e:
            print(f"加载爬行动画失败: {e}")
    
    def update_crawling_animations(self):
        """更新爬行动画"""
        import random
        # 获取鼠标位置
        mouse_x, mouse_y = pygame.mouse.get_pos()
        
        for anim in self.crawling_animations:
            # 更新动画帧
            anim['frame_timer'] += 1/FPS
            if anim['frame_timer'] >= anim['animation_speed']:
                anim['frame_timer'] = 0
                anim['frame_index'] = (anim['frame_index'] + 1) % len(anim['frames'])
            
            # 根据动画类型更新位置
            if anim['type'] == 'follow_mouse':
                # 跟随鼠标的动画
                anim_center_x = anim['x'] + anim['width'] // 2
                anim_center_y = anim['y'] + anim['height'] // 2
                
                # 计算朝向鼠标的方向向量
                dx = mouse_x - anim_center_x
                dy = mouse_y - anim_center_y
                
                # 计算距离
                distance = (dx**2 + dy**2)**0.5
                
                # 如果距离不为0，标准化方向向量并设置速度
                if distance > 0:
                    speed = 2  # 移动速度
                    anim['vel_x'] = (dx / distance) * speed
                    anim['vel_y'] = (dy / distance) * speed
                
                # 更新位置
                anim['x'] += anim['vel_x']
                anim['y'] += anim['vel_y']
                
                # 边界检测，防止动画移出屏幕
                anim['x'] = max(0, min(WIDTH - anim['width'], anim['x']))
                anim['y'] = max(0, min(HEIGHT - anim['height'], anim['y']))
            
            elif anim['type'] == 'random_crawl':
                # 随机爬行的动画
                anim['direction_change_timer'] += 1
                
                # 定期改变方向
                if anim['direction_change_timer'] >= anim['direction_change_interval']:
                    anim['vel_x'] = random.uniform(-1.5, 1.5)
                    anim['vel_y'] = random.uniform(-1.5, 1.5)
                    anim['direction_change_timer'] = 0
                    anim['direction_change_interval'] = random.uniform(60, 180)
                
                # 更新位置
                anim['x'] += anim['vel_x']
                anim['y'] += anim['vel_y']
                
                # 边界反弹
                if anim['x'] <= 0 or anim['x'] >= WIDTH - anim['width']:
                    anim['vel_x'] = -anim['vel_x']
                    anim['x'] = max(0, min(WIDTH - anim['width'], anim['x']))
                
                if anim['y'] <= 0 or anim['y'] >= HEIGHT - anim['height']:
                    anim['vel_y'] = -anim['vel_y']
                    anim['y'] = max(0, min(HEIGHT - anim['height'], anim['y']))
            
            elif anim['type'] == 'edge_crawl':
                # 沿着边缘爬行的动画
                anim['x'] += anim['vel_x']
                anim['y'] += anim['vel_y']
                
                # 根据边缘类型处理边界
                if anim['edge'] == 'top':
                    anim['y'] = 0
                    if anim['x'] <= 0 or anim['x'] >= WIDTH - anim['width']:
                        anim['vel_x'] = -anim['vel_x']
                        anim['x'] = max(0, min(WIDTH - anim['width'], anim['x']))
                
                elif anim['edge'] == 'right':
                    anim['x'] = WIDTH - anim['width']
                    if anim['y'] <= 0 or anim['y'] >= HEIGHT - anim['height']:
                        anim['vel_y'] = -anim['vel_y']
                        anim['y'] = max(0, min(HEIGHT - anim['height'], anim['y']))
                
                elif anim['edge'] == 'bottom':
                    anim['y'] = HEIGHT - anim['height']
                    if anim['x'] <= 0 or anim['x'] >= WIDTH - anim['width']:
                        anim['vel_x'] = -anim['vel_x']
                        anim['x'] = max(0, min(WIDTH - anim['width'], anim['x']))
    
    def draw_crawling_animations(self):
        """绘制爬行动画"""
        for anim in self.crawling_animations:
            if anim['frames']:
                current_frame = anim['frames'][anim['frame_index']]
                
                # 根据动画类型决定是否翻转
                if anim['type'] == 'edge_crawl':
                    # 边缘爬行动画需要根据边缘位置翻转
                    if anim['edge'] == 'top':
                        # 在顶部边缘爬行，垂直翻转（上下翻转）
                        flipped_frame = pygame.transform.flip(current_frame, False, True)
                        self.screen.blit(flipped_frame, (int(anim['x']), int(anim['y'])))
                    elif anim['edge'] == 'left':
                        # 在左边缘爬行，旋转90度（竖起来）
                        rotated_frame = pygame.transform.rotate(current_frame, 90)
                        # 调整位置以适应旋转后的尺寸
                        rect = rotated_frame.get_rect()
                        rect.center = (int(anim['x']) + current_frame.get_width()//2, int(anim['y']) + current_frame.get_height()//2)
                        self.screen.blit(rotated_frame, rect)
                    elif anim['edge'] == 'right':
                        # 在右边缘爬行，旋转-90度（竖起来，朝另一个方向）
                        rotated_frame = pygame.transform.rotate(current_frame, -90)
                        # 调整位置以适应旋转后的尺寸
                        rect = rotated_frame.get_rect()
                        rect.center = (int(anim['x']) + current_frame.get_width()//2, int(anim['y']) + current_frame.get_height()//2)
                        self.screen.blit(rotated_frame, rect)
                    elif anim['edge'] == 'bottom':
                        # 在底部边缘爬行，根据移动方向决定是否水平翻转
                        if anim['vel_x'] < 0:  # 向左移动
                            flipped_frame = pygame.transform.flip(current_frame, True, False)
                            self.screen.blit(flipped_frame, (int(anim['x']), int(anim['y'])))
                        else:
                            self.screen.blit(current_frame, (int(anim['x']), int(anim['y'])))
                else:
                    # 其他类型动画不翻转
                    self.screen.blit(current_frame, (int(anim['x']), int(anim['y'])))
    
    def get_chinese_font(self, size):
        """获取支持中文的字体（带缓存）"""
        # 检查缓存
        if size in self.font_cache:
            return self.font_cache[size]
        
        # 优先尝试加载项目字体文件夹中的字体
        project_fonts = [
            'font/猫啃什锦黑.ttf',  # 项目字体文件 TTF
            'font/猫啃什锦黑.otf',  # 项目字体文件 OTF
        ]
        
        # 备用系统中文字体
        system_fonts = [
            '/System/Library/Fonts/PingFang.ttc',  # macOS 默认中文字体
            '/System/Library/Fonts/Hiragino Sans GB.ttc',  # macOS 中文字体
            '/System/Library/Fonts/STHeiti Light.ttc',  # macOS 中文字体
            'SimHei',  # Windows 中文字体
            'Microsoft YaHei',  # Windows 中文字体
            'WenQuanYi Micro Hei',  # Linux 中文字体
        ]
        
        font = None
        
        # 首先尝试项目字体
        for font_path in project_fonts:
            try:
                if os.path.exists(font_path):
                    font = pygame.font.Font(font_path, size)
                    print(f"成功加载项目字体: {font_path}")
                    break
            except Exception as e:
                print(f"加载项目字体失败 {font_path}: {e}")
                continue
        
        # 如果项目字体加载失败，尝试系统字体
        if font is None:
            for font_name in system_fonts:
                try:
                    if font_name.startswith('/'):
                        # 字体文件路径
                        if os.path.exists(font_name):
                            font = pygame.font.Font(font_name, size)
                            break
                    else:
                        # 系统字体名称
                        font = pygame.font.SysFont(font_name, size)
                        if font:
                            break
                except Exception as e:
                    continue
        
        # 如果都失败了，使用默认字体
        if font is None:
            font = pygame.font.Font(None, size)
            print("使用默认字体")
        
        # 缓存字体
        self.font_cache[size] = font
        return font
    
    def draw_decorative_patterns(self):
        """绘制装饰性花纹背景"""
        # 绘制对角线花纹
        pattern_color = (40, 35, 55)
        for i in range(0, WIDTH + HEIGHT, 80):
            # 左上到右下的对角线
            start_x = max(0, i - HEIGHT)
            start_y = max(0, HEIGHT - i)
            end_x = min(WIDTH, i)
            end_y = min(HEIGHT, HEIGHT - (i - WIDTH))
            if start_x < WIDTH and start_y < HEIGHT:
                pygame.draw.line(self.screen, pattern_color, (start_x, start_y), (end_x, end_y), 1)
        
        # 绘制装饰点
        for x in range(100, WIDTH, 150):
            for y in range(100, HEIGHT, 120):
                pygame.draw.circle(self.screen, (50, 45, 65), (x, y), 2)
                pygame.draw.circle(self.screen, (60, 55, 75), (x + 75, y + 60), 1)
    
    def draw_corner_ornaments(self, x, y, width, height, small=False):
        """绘制角落装饰花纹"""
        size = 15 if small else 25
        color = (180, 150, 80)
        
        # 左上角
        pygame.draw.lines(self.screen, color, False, [
            (x + 5, y + size), (x + 5, y + 5), (x + size, y + 5)
        ], 2)
        pygame.draw.lines(self.screen, color, False, [
            (x + 10, y + size//2), (x + 10, y + 10), (x + size//2, y + 10)
        ], 1)
        
        # 右上角
        pygame.draw.lines(self.screen, color, False, [
            (x + width - size, y + 5), (x + width - 5, y + 5), (x + width - 5, y + size)
        ], 2)
        pygame.draw.lines(self.screen, color, False, [
            (x + width - size//2, y + 10), (x + width - 10, y + 10), (x + width - 10, y + size//2)
        ], 1)
        
        # 左下角
        pygame.draw.lines(self.screen, color, False, [
            (x + 5, y + height - size), (x + 5, y + height - 5), (x + size, y + height - 5)
        ], 2)
        pygame.draw.lines(self.screen, color, False, [
            (x + 10, y + height - size//2), (x + 10, y + height - 10), (x + size//2, y + height - 10)
        ], 1)
        
        # 右下角
        pygame.draw.lines(self.screen, color, False, [
            (x + width - size, y + height - 5), (x + width - 5, y + height - 5), (x + width - 5, y + height - size)
        ], 2)
        pygame.draw.lines(self.screen, color, False, [
            (x + width - size//2, y + height - 10), (x + width - 10, y + height - 10), (x + width - 10, y + height - size//2)
        ], 1)
    
    def draw_ui(self):
        font = self.get_chinese_font(36)
        
        if self.state == PAUSED:
            # 暂停界面
            # 添加半透明背景
            overlay = pygame.Surface((WIDTH, HEIGHT))
            overlay.set_alpha(128)
            overlay.fill(BLACK)
            self.screen.blit(overlay, (0, 0))
            
            # 暂停标题
            pause_text = font.render("游戏暂停", True, WHITE)
            text_rect = pause_text.get_rect(center=(WIDTH//2, HEIGHT//2 - 80))
            self.screen.blit(pause_text, text_rect)
            
            # 按钮设置
            if self.game_mode == ONLINE:
                button_font = self.get_chinese_font(24)
                button_width = 200
                button_height = 50
                
                # 检查是否为房主
                is_host = (self.network_client and 
                          hasattr(self.network_client, 'is_host') and 
                          self.network_client.is_host)
                
                if is_host:
                    # 房主显示返回等待房间按钮
                    return_button = pygame.Rect(WIDTH//2 - button_width//2, HEIGHT//2 - 10, button_width, button_height)
                    pygame.draw.rect(self.screen, (100, 100, 100), return_button)
                    pygame.draw.rect(self.screen, WHITE, return_button, 2)
                    return_text = button_font.render("返回等待房间", True, WHITE)
                    return_text_rect = return_text.get_rect(center=return_button.center)
                    self.screen.blit(return_text, return_text_rect)
                    
                    # 继续游戏按钮
                    continue_button = pygame.Rect(WIDTH//2 - button_width//2, HEIGHT//2 + 60, button_width, button_height)
                    pygame.draw.rect(self.screen, (0, 100, 0), continue_button)
                    pygame.draw.rect(self.screen, WHITE, continue_button, 2)
                    continue_text = button_font.render("继续游戏", True, WHITE)
                    continue_text_rect = continue_text.get_rect(center=continue_button.center)
                    self.screen.blit(continue_text, continue_text_rect)
                else:
                    # 普通玩家只显示继续游戏按钮
                    continue_button = pygame.Rect(WIDTH//2 - button_width//2, HEIGHT//2 + 30, button_width, button_height)
                    pygame.draw.rect(self.screen, (0, 100, 0), continue_button)
                    pygame.draw.rect(self.screen, WHITE, continue_button, 2)
                    continue_text = button_font.render("继续游戏", True, WHITE)
                    continue_text_rect = continue_text.get_rect(center=continue_button.center)
                    self.screen.blit(continue_text, continue_text_rect)
                    
                    # 提示信息
                    hint_font = self.get_chinese_font(18)
                    hint_text = hint_font.render("只有房主可以返回等待房间", True, (200, 200, 200))
                    hint_rect = hint_text.get_rect(center=(WIDTH//2, HEIGHT//2 + 100))
                    self.screen.blit(hint_text, hint_rect)
            else:
                # 离线模式只显示继续游戏提示
                hint_font = self.get_chinese_font(20)
                hint_text = hint_font.render("按ESC键继续游戏", True, WHITE)
                hint_rect = hint_text.get_rect(center=(WIDTH//2, HEIGHT//2 + 30))
                self.screen.blit(hint_text, hint_rect)
        
        # 显示玩家信息面板
        if self.state == PLAYING and hasattr(self, 'player') and self.player:
            # 创建信息面板背景
            panel_width = 350
            panel_height = 120
            panel_x = 10
            panel_y = 10
            
            # 半透明背景
            panel_bg = pygame.Surface((panel_width, panel_height))
            panel_bg.set_alpha(200)
            panel_bg.fill((20, 20, 40))
            pygame.draw.rect(panel_bg, (255, 215, 0), panel_bg.get_rect(), 3)
            self.screen.blit(panel_bg, (panel_x, panel_y))
            
            # 字体设置
            font_medium = self.get_chinese_font(20)
            font_small = self.get_chinese_font(16)
            
            # 玩家信息
            player_info = f"玩家: {self.player_name}"
            if self.selected_character < len(self.character_options):
                player_info += f" ({self.character_options[self.selected_character]['name']})"
            
            player_text = font_medium.render(player_info, True, (255, 215, 0))
            self.screen.blit(player_text, (panel_x + 15, panel_y + 10))
            
            # 血量条
            health_y = panel_y + 40
            health_width = 200
            health_height = 18
            
            # 血量条背景
            health_bg = pygame.Rect(panel_x + 15, health_y, health_width, health_height)
            pygame.draw.rect(self.screen, (60, 60, 60), health_bg)
            pygame.draw.rect(self.screen, WHITE, health_bg, 2)
            
            # 血量条填充
            health_ratio = self.player.current_health / self.player.max_health
            health_fill_width = int(health_width * health_ratio)
            
            # 根据血量比例改变颜色
            if health_ratio > 0.6:
                health_color = (0, 255, 0)  # 绿色
            elif health_ratio > 0.3:
                health_color = (255, 255, 0)  # 黄色
            else:
                health_color = (255, 0, 0)  # 红色
            
            if health_fill_width > 0:
                health_fill = pygame.Rect(panel_x + 15, health_y, health_fill_width, health_height)
                pygame.draw.rect(self.screen, health_color, health_fill)
            
            # 血量文字
            health_text = f"血量: {self.player.current_health}/{self.player.max_health}"
            health_surface = font_small.render(health_text, True, WHITE)
            self.screen.blit(health_surface, (panel_x + 230, health_y + 2))
            
            # 角色属性
            attr_y = panel_y + 65
            attrs = [
                f"攻击: {self.player.attack_power}  防御: {self.player.defense}",
                f"速度: {self.player.speed_multiplier:.1f}x  跳跃: {self.player.jump_multiplier:.1f}x"
            ]
            
            for i, attr in enumerate(attrs):
                attr_text = font_small.render(attr, True, (200, 200, 255))
                self.screen.blit(attr_text, (panel_x + 15, attr_y + i * 20))
            
            # 显示游戏模式和网络状态
            if self.game_mode == OFFLINE:
                status_text = "本地联机模式"
                status_color = WHITE
            else:
                if self.network_client and self.network_client.connected:
                    player_count = len(self.network_client.other_players) + 1
                    status_text = f"线上联机 - 在线玩家: {player_count}"
                    status_color = GREEN
                else:
                    status_text = "线上联机 - 连接失败"
                    status_color = (255, 100, 100)
            
            status_surface = font_small.render(status_text, True, status_color)
            self.screen.blit(status_surface, (10, HEIGHT - 30))
    
    def create_local_server(self):
        """创建本地服务器"""
        try:
            import socket
            import threading
            from network import NetworkServer
            
            # 获取本机IP
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
            s.close()
            
            # 使用固定端口或随机端口
            port = 12345
            
            # 创建服务器
            self.local_server = NetworkServer(local_ip, port)
            server_thread = threading.Thread(target=self.local_server.start, daemon=True)
            server_thread.start()
            
            # 设置房间信息
            self.room_ip = local_ip
            self.room_port = str(port)
            self.mode = HOST_ROOM
            self.game_mode = ONLINE  # 设置为在线模式
            
            # 将房主自己加入玩家列表
            self.room_players = {'host': {'name': self.player_name or '房主', 'character': '未选择', 'ping': 0}}
            
            print(f"本地服务器已启动: {local_ip}:{port}")
            return True
            
        except Exception as e:
            print(f"创建服务器失败: {e}")
            return False
    
    def connect_to_room(self):
        """连接到房间"""
        try:
            # 检查是否已经连接，防止重复连接
            if self.network_client and self.network_client.connected:
                print("已经连接到房间，无需重复连接")
                return True
                
            if not self.room_ip or not self.room_port:
                return False
            
            port = int(self.room_port)
            
            # 创建网络客户端
            self.network_client = NetworkClient()
            if self.network_client.connect(self.room_ip, port):
                self.game_mode = ONLINE  # 设置为在线模式
                print(f"成功连接到房间: {self.room_ip}:{port}")
                return True
            else:
                print("连接失败")
                self.network_client = None  # 清理失败的连接
                return False
                
        except Exception as e:
            print(f"连接房间失败: {e}")
            self.network_client = None  # 清理失败的连接
            return False
    
    def leave_room(self):
        """离开房间"""
        # 停止本地服务器
        if self.local_server:
            print("房主主动离开房间，正在发送解散消息...")
            self.local_server.stop()
            self.local_server = None
        
        # 清理所有游戏和玩家数据
        self.cleanup_game()
        
        # 重置房间连接信息
        self.room_ip = "localhost"
        self.room_port = "12345"
        
        # 返回模式选择页面
        self.state = MODE_SELECT
    
    def try_connect_to_server(self):
        """尝试连接到服务器"""
        try:
            self.network_client = NetworkClient()
            # 不自动连接，等待用户按C键
        except Exception as e:
            print(f"网络客户端初始化失败: {e}")
    
    def draw_other_players(self):
        """绘制其他玩家"""
        if not self.network_client or not self.network_client.other_players:
            return
        
        # 创建字典副本以避免迭代时修改导致的错误
        other_players_copy = dict(self.network_client.other_players)
        for player_id, player_data in other_players_copy.items():
            # 获取玩家相对位置并转换为绝对坐标
            rel_x = player_data.get('rel_x', player_data.get('x', 0) / WIDTH if 'x' in player_data else 0)
            rel_y = player_data.get('rel_y', player_data.get('y', 0) / HEIGHT if 'y' in player_data else 0)
            x, y = self.relative_to_absolute(rel_x, rel_y)
            facing_right = player_data.get('facing_right', True)
            character_name = player_data.get('character_name', '哈基为')
            current_animation = player_data.get('current_animation', 'idle')
            frame_index = player_data.get('frame_index', 0)
            
            # 根据角色名称找到对应的角色选项
            character_folder = None
            for char_option in self.character_options:
                if char_option['name'] == character_name:
                    character_folder = char_option['gif_folder']
                    break
            
            # 如果找不到角色，使用默认角色
            if not character_folder:
                character_folder = self.character_options[0]['gif_folder']
            
            # 尝试加载角色的动画帧
            other_player_surface = None
            try:
                # 根据动画类型构建路径
                animation_files = {
                    'idle': 'noMoveAnimation.gif',
                    'move': 'MoveAnimation.gif',
                    'sprint': 'SprintAnimation.gif'
                }
                
                animation_file = animation_files.get(current_animation, 'noMoveAnimation.gif')
                animation_path = os.path.join(character_folder, animation_file)
                
                if os.path.exists(animation_path):
                    # 创建临时Player对象来加载动画帧
                    temp_player = Player(0, 0, character_folder, character_name)
                    if current_animation in temp_player.animation_frames and temp_player.animation_frames[current_animation]:
                        frames = temp_player.animation_frames[current_animation]
                        if len(frames) > 0:
                            # 确保帧索引在有效范围内
                            safe_frame_index = frame_index % len(frames)
                            other_player_surface = frames[safe_frame_index]
                            # 缩放到与本地玩家相同的大小
                            other_player_surface = pygame.transform.scale(other_player_surface, (96, 96))
            except Exception as e:
                print(f"加载其他玩家角色动画失败: {e}")
                import traceback
                traceback.print_exc()
            
            # 如果加载失败，使用默认的红色方块
            if other_player_surface is None:
                other_player_surface = pygame.Surface((96, 96))
                other_player_surface.fill((255, 100, 100))  # 红色表示其他玩家
                # 添加简单的眼睛
                pygame.draw.circle(other_player_surface, BLACK, (30, 30), 4)
                pygame.draw.circle(other_player_surface, BLACK, (66, 30), 4)
            
            # 根据朝向翻转
            if not facing_right:
                other_player_surface = pygame.transform.flip(other_player_surface, True, False)
            
            # 记录其他玩家位置作为脏矩形
            other_player_rect = pygame.Rect(x - 10, y - 30, 116, 126)  # 包含玩家和名称文本
            self.add_dirty_rect(other_player_rect)
            
            self.screen.blit(other_player_surface, (x, y))
            
            # 显示玩家信息
            font_small = pygame.font.Font(None, 20)
            # 优先显示玩家名称，如果没有则显示玩家ID
            display_name = player_data.get('player_name', f"P{player_id}")
            id_text = font_small.render(display_name, True, WHITE)
            self.screen.blit(id_text, (x, y - 20))
    
    def load_available_map_series(self):
        """加载可用的地图系列列表"""
        map_dir = "map"
        self.available_map_series = []
        
        if os.path.exists(map_dir):
            for series_name in os.listdir(map_dir):
                series_path = os.path.join(map_dir, series_name)
                if os.path.isdir(series_path):
                    series_info_path = os.path.join(series_path, "series_info.json")
                    if os.path.exists(series_info_path):
                        try:
                            with open(series_info_path, 'r', encoding='utf-8') as f:
                                series_data = json.load(f)
                                series_data['series_folder'] = series_name
                                
                                # 加载系列中的所有关卡
                                levels = []
                                for level_info in series_data['levels']:
                                    level_path = os.path.join(series_path, level_info['file'])
                                    if os.path.exists(level_path):
                                        with open(level_path, 'r', encoding='utf-8') as lf:
                                            level_data = json.load(lf)
                                            level_data['level_id'] = level_info['level_id']
                                            level_data['level_name'] = level_info['name']
                                            level_data['level_description'] = level_info['description']
                                            level_data['filename'] = level_info['file']
                                            levels.append(level_data)
                                
                                series_data['loaded_levels'] = levels
                                self.available_map_series.append(series_data)
                                print(f"加载地图系列: {series_data['series_name']} ({len(levels)}个关卡)")
                        except Exception as e:
                            print(f"加载地图系列 {series_name} 失败: {e}")
        
        # 如果没有找到地图系列，创建默认地图
        if not self.available_map_series:
            self.create_default_map_series()
    
    def create_default_map_series(self):
        """创建默认地图系列"""
        default_series = {
            "series_name": "默认系列",
            "description": "默认地图系列",
            "series_folder": "default_series",
            "levels": [
                {
                    "level_id": 1,
                    "name": "默认关卡",
                    "description": "默认关卡描述",
                    "file": "default.json"
                }
            ],
            "loaded_levels": [
                {
                    "name": "默认地图",
                    "description": "系统默认地图",
                    "background_color": [135, 206, 235],
                    "platforms": [
                        {"x": 0, "y": "HEIGHT - 50", "width": "WIDTH", "height": 50, "type": "ground"},
                        {"x": 300, "y": "HEIGHT - 150", "width": 200, "height": 32, "type": "platform"},
                        {"x": 600, "y": "HEIGHT - 250", "width": 200, "height": 32, "type": "platform"},
                        {"x": 900, "y": "HEIGHT - 180", "width": 200, "height": 32, "type": "platform"},
                        {"x": 150, "y": "HEIGHT - 300", "width": 150, "height": 32, "type": "platform"},
                        {"x": 750, "y": "HEIGHT - 350", "width": 150, "height": 32, "type": "platform"}
                    ],
                    "spawn_point": {"x": 100, "y": "HEIGHT - 200"},
                    "level_id": 1,
                    "level_name": "默认关卡",
                    "level_description": "默认关卡描述",
                    "filename": "default.json"
                }
            ]
        }
        self.available_map_series.append(default_series)
    
    def create_platforms_from_map(self, map_data):
        """根据地图数据创建平台"""
        platforms = []
        
        for platform_data in map_data['platforms']:
            # 解析坐标和尺寸，支持字符串表达式
            x = self.parse_coordinate(platform_data['x'])
            y = self.parse_coordinate(platform_data['y'])
            width = self.parse_coordinate(platform_data['width'])
            height = platform_data['height']
            
            platform = Platform(x, y, width, height)
            platforms.append(platform)
        
        return platforms
    
    def create_portals_from_map(self, map_data):
        """根据地图数据创建传送门"""
        portals = []
        
        portal_data_list = map_data.get('portals', [])
        for portal_data in portal_data_list:
            # 解析坐标和尺寸，支持字符串表达式
            x = self.parse_coordinate(portal_data['x'])
            y = self.parse_coordinate(portal_data['y'])
            width = portal_data['width']
            height = portal_data['height']
            target_map = portal_data['target_map']
            portal_type = portal_data.get('type', 'level_portal')
            
            portal = Portal(x, y, width, height, target_map, portal_type)
            portals.append(portal)
        
        return portals
    
    def create_enemies_from_map(self, map_data):
        """从地图数据创建敌怪（仅单机模式使用）"""
        enemies = []
        if 'enemies' in map_data:
            for i, enemy_data in enumerate(map_data['enemies']):
                try:
                    # 解析坐标
                    enemy_data['x'] = self.parse_coordinate(enemy_data['x'])
                    enemy_data['y'] = self.parse_coordinate(enemy_data['y'])
                    
                    # 创建敌怪
                    enemy = Enemy(enemy_data)
                    enemies.append(enemy)
                    print(f"单机模式创建敌怪: {enemy_data['type']} ({enemy_data['variant']}) 位置({enemy_data['x']}, {enemy_data['y']}) ID: {enemy.enemy_id}")
                except Exception as e:
                    print(f"创建敌怪失败: {e}, 数据: {enemy_data}")
        return enemies
    
    def check_portal_collisions(self):
        """检查玩家与传送门的碰撞"""
        if not self.player:
            return
            
        for portal in self.portals:
            if self.player.rect.colliderect(portal.rect):
                # 检查是否还有敌人存在
                if len(self.enemies) > 0:
                    # 显示需要清除所有敌人的提示
                    self.show_clear_enemies_message(portal)
                    continue
                
                # 在多人联机模式下，需要检查所有玩家是否都触碰到传送门
                if self.game_mode == ONLINE and self.network_client and self.network_client.connected:
                    if self.check_all_players_at_portal(portal):
                        # 只有房主可以触发传送
                        if self.network_client.is_host:
                            print("所有玩家都在传送门附近，房主发送传送门触发信号")
                            self.network_client.send_portal_trigger(portal.target_map)
                            # 房主也立即执行传送
                            self.teleport_to_map(portal.target_map)
                        break
                    else:
                        # 显示等待其他玩家的提示
                        self.show_portal_waiting_message(portal)
                        break
                else:
                    # 单人模式直接传送
                    self.teleport_to_map(portal.target_map)
                    break
    
    def check_all_players_at_portal(self, portal):
        """检查所有玩家是否都在传送门附近"""
        if not self.network_client or not self.network_client.other_players:
            # 如果没有其他玩家，只需要当前玩家在传送门即可
            return True
        
        # 扩大传送门检测范围，考虑角色大小和网络延迟
        portal_buffer = 32  # 额外的缓冲区域
        expanded_portal = pygame.Rect(
            portal.rect.x - portal_buffer,
            portal.rect.y - portal_buffer,
            portal.rect.width + portal_buffer * 2,
            portal.rect.height + portal_buffer * 2
        )
        
        # 检查所有其他玩家是否都在扩大的传送门区域内
        for player_id, player_data in self.network_client.other_players.items():
            # 获取其他玩家的位置
            rel_x = player_data.get('rel_x', 0)
            rel_y = player_data.get('rel_y', 0)
            x, y = self.relative_to_absolute(rel_x, rel_y)
            
            # 创建其他玩家的矩形（考虑角色大小）
            player_rect = pygame.Rect(x, y, 64, 64)  # 假设角色大小为64x64
            
            # 如果有玩家不在传送门区域内，返回False
            if not player_rect.colliderect(expanded_portal):
                return False
        
        return True
    
    def show_clear_enemies_message(self, portal):
        """显示需要清除所有敌人的消息"""
        font = self.get_chinese_font(28)
        enemy_count = len(self.enemies)
        message_text = f"需要清除所有敌人才能使用传送门 (剩余: {enemy_count})"
        text_surface = font.render(message_text, True, (255, 100, 100))
        
        # 在传送门上方显示消息
        text_rect = text_surface.get_rect(center=(portal.rect.centerx, portal.rect.y - 40))
        
        # 添加半透明背景
        bg_rect = text_rect.inflate(20, 10)
        bg_surface = pygame.Surface((bg_rect.width, bg_rect.height))
        bg_surface.set_alpha(150)
        bg_surface.fill((0, 0, 0))
        self.screen.blit(bg_surface, bg_rect)
        
        self.screen.blit(text_surface, text_rect)
    
    def show_portal_waiting_message(self, portal=None):
        """显示等待其他玩家的消息"""
        # 在屏幕中央显示等待消息
        font = self.get_chinese_font(32)
        message_text = "等待其他玩家到达传送门..."
        text_surface = font.render(message_text, True, (255, 255, 0))
        
        # 如果有传送门参数，在传送门上方显示；否则在屏幕中央显示
        if portal:
            text_rect = text_surface.get_rect(center=(portal.rect.centerx, portal.rect.y - 30))
        else:
            text_rect = text_surface.get_rect(center=(WIDTH // 2, HEIGHT // 2))
        
        # 添加半透明背景
        bg_rect = text_rect.inflate(20, 10)
        bg_surface = pygame.Surface((bg_rect.width, bg_rect.height))
        bg_surface.set_alpha(128)
        bg_surface.fill((0, 0, 0))
        self.screen.blit(bg_surface, bg_rect)
        
        self.screen.blit(text_surface, text_rect)
    
    def show_game_over(self):
        """显示游戏结束界面并返回房间"""
        # 显示游戏结束消息
        font_large = self.get_chinese_font(48)
        font_medium = self.get_chinese_font(32)
        
        # 创建半透明覆盖层
        overlay = pygame.Surface((WIDTH, HEIGHT))
        overlay.set_alpha(180)
        overlay.fill((0, 0, 0))
        self.screen.blit(overlay, (0, 0))
        
        # 游戏结束标题
        game_over_text = font_large.render("游戏结束", True, (255, 0, 0))
        game_over_rect = game_over_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 100))
        self.screen.blit(game_over_text, game_over_rect)
        
        # 提示信息
        info_text = font_medium.render("你的血量已归零", True, WHITE)
        info_rect = info_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 50))
        self.screen.blit(info_text, info_rect)
        
        # 返回提示
        return_text = font_medium.render("3秒后自动返回房间...", True, (255, 255, 0))
        return_rect = return_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 50))
        self.screen.blit(return_text, return_rect)
        
        # 更新显示
        pygame.display.flip()
        
        # 等待3秒
        pygame.time.wait(3000)
        
        # 返回房间逻辑
        self.return_to_room()
    
    def return_to_room(self):
        """返回房间的逻辑"""
        print("玩家死亡，返回房间")
        
        # 根据当前游戏模式决定返回位置
        if self.game_mode == OFFLINE:
            # 单机模式，返回主菜单
            self.cleanup_game()
            self.state = MAIN_MENU
            print("返回主菜单")
        elif self.game_mode == ONLINE:
            # 联机模式，返回等待房间
            if self.mode == HOST_ROOM:
                # 房主返回等待房间
                self.state = WAITING_ROOM
                # 切换回菜单音乐
                self.play_music('menu')
                # 清理游戏状态但保持网络连接
                self.player = None
                self.platforms = None
                self.enemies = []
                self.portals = []
                # 重置网络客户端的游戏开始标志，防止自动重新开始游戏
                if self.network_client:
                    self.network_client.game_started = False
                print("房主返回等待房间")
            else:
                # 普通玩家返回等待房间
                self.state = WAITING_ROOM
                # 切换回菜单音乐
                self.play_music('menu')
                # 清理游戏状态但保持网络连接
                self.player = None
                self.platforms = None
                self.enemies = []
                self.portals = []
                # 重置网络客户端的游戏开始标志，防止自动重新开始游戏
                if self.network_client:
                    self.network_client.game_started = False
                print("玩家返回等待房间")

    
    def teleport_to_map(self, target_map):
        """传送到目标地图或下一个关卡"""
        print(f"传送到地图: {target_map}")
        
        # 如果target_map是"next_level"，则传送到当前系列的下一个关卡
        if target_map == "next_level":
            if self.available_map_series and self.selected_series < len(self.available_map_series):
                current_series = self.available_map_series[self.selected_series]
                print(f"当前关卡索引: {self.selected_level}, 系列总关卡数: {len(current_series['loaded_levels'])}")
                next_level = self.selected_level + 1
                
                if next_level < len(current_series['loaded_levels']):
                    # 传送到下一个关卡
                    self.selected_level = next_level
                    map_data = current_series['loaded_levels'][self.selected_level]
                    
                    print(f"传送到下一关卡: {current_series['series_name']} - {map_data['level_name']} (索引: {self.selected_level})")
                    
                    # 更新当前地图
                    self.current_map_data = map_data
                    self.current_map_name = map_data.get('level_name', f"level_{self.selected_level}")
                    
                    # 重新创建平台、传送门和敌怪
                    self.platforms = self.create_platforms_from_map(map_data)
                    self.portals = self.create_portals_from_map(map_data)
                    self.enemies = self.create_enemies_from_map(map_data)
                    
                    # 重置玩家位置到新地图的出生点
                    spawn_x, spawn_y = self.get_spawn_point_from_map(map_data)
                    self.player.x = spawn_x
                    self.player.y = spawn_y
                    self.player.rect.x = self.player.x
                    self.player.rect.y = self.player.y
                    self.player.vel_x = 0
                    self.player.vel_y = 0
                    self.player.on_ground = False
                    
                    # 如果是联机模式，通知其他玩家关卡切换
                    if self.game_mode == ONLINE and self.network_client and self.network_client.connected:
                        # 发送地图选择更新
                        self.network_client.send_map_selection(self.selected_series * 100 + self.selected_level, 
                                                             f"{current_series['series_name']} - {map_data['level_name']}")
                        
                        # 发送更新后的玩家位置
                        rel_x, rel_y = self.absolute_to_relative(self.player.x, self.player.y)
                        player_data = {
                            'rel_x': rel_x,
                            'rel_y': rel_y,
                            'facing_right': self.player.facing_right,
                            'on_ground': self.player.on_ground,
                            'player_name': self.player_name,
                            'character_name': self.character_options[self.selected_character]['name'] if self.character_selected else "未选择"
                        }
                        self.network_client.send_player_data(player_data)
                    
                    return
                else:
                    print("已经是最后一个关卡了！")
                    return
            else:
                print("没有可用的地图系列！")
                return
        
        # 原有的地图文件加载逻辑（保持向后兼容）
        if isinstance(target_map, int):
            target_map_file = f"map{target_map}"
        else:
            target_map_file = target_map
        
        # 加载目标地图
        try:
            map_path = f'map/{target_map_file}.json'
            with open(map_path, 'r', encoding='utf-8') as f:
                map_data = json.load(f)
            
            # 更新当前地图
            self.current_map_data = map_data
            
            # 重新创建平台和传送门
            self.platforms = self.create_platforms_from_map(map_data)
            self.portals = self.create_portals_from_map(map_data)
            
            # 重置玩家位置到新地图的出生点
            spawn_x, spawn_y = self.get_spawn_point_from_map(map_data)
            self.player.x = spawn_x
            self.player.y = spawn_y
            self.player.rect.x = self.player.x
            self.player.rect.y = self.player.y
            self.player.vel_x = 0
            self.player.vel_y = 0
            self.player.on_ground = False
            
            # 如果是联机模式，通知其他玩家地图切换
            if self.game_mode == ONLINE and self.network_client and self.network_client.connected:
                # 发送地图切换消息
                map_change_data = {
                    'type': 'map_change',
                    'target_map': target_map_file
                }
                self.network_client.send_message(map_change_data)
                
                # 发送更新后的玩家位置
                rel_x, rel_y = self.absolute_to_relative(self.player.x, self.player.y)
                player_data = {
                    'rel_x': rel_x,
                    'rel_y': rel_y,
                    'facing_right': self.player.facing_right,
                    'on_ground': self.player.on_ground,
                    'player_name': self.player_name,
                    'character_name': self.character_options[self.selected_character]['name'] if self.character_selected else "未选择"
                }
                self.network_client.send_player_data(player_data)
            
            print(f"成功传送到地图: {map_data['name']}")
            
        except FileNotFoundError:
            print(f"错误: 找不到地图文件 {map_path}")
        except json.JSONDecodeError:
            print(f"错误: 地图文件 {map_path} 格式错误")
        except Exception as e:
            print(f"传送时发生错误: {e}")
    
    def parse_coordinate(self, coord):
        """解析坐标值，支持WIDTH和HEIGHT变量"""
        if isinstance(coord, str):
            # 替换WIDTH和HEIGHT变量
            coord = coord.replace('WIDTH', str(WIDTH))
            coord = coord.replace('HEIGHT', str(HEIGHT))
            try:
                return eval(coord)
            except:
                return 0
        return coord
    
    def absolute_to_relative(self, x, y):
        """将绝对坐标转换为相对坐标（0-1之间）"""
        rel_x = x / WIDTH if WIDTH > 0 else 0
        rel_y = y / HEIGHT if HEIGHT > 0 else 0
        return rel_x, rel_y
    
    def relative_to_absolute(self, rel_x, rel_y):
        """将相对坐标转换为当前分辨率下的绝对坐标"""
        x = rel_x * WIDTH
        y = rel_y * HEIGHT
        return x, y
    
    def get_spawn_point_from_map(self, map_data):
        """从地图数据获取出生点"""
        spawn_data = map_data.get('spawn_point', {'x': 100, 'y': 'HEIGHT - 200'})
        x = self.parse_coordinate(spawn_data['x'])
        y = self.parse_coordinate(spawn_data['y'])
        return x, y
    
    def draw_map_thumbnail(self, map_data, x, y, width, height):
        """绘制地图缩略图"""
        # 创建缩略图表面
        thumbnail_surface = pygame.Surface((width, height))
        
        # 获取背景颜色
        bg_color = map_data.get('background_color', [0, 0, 0])
        thumbnail_surface.fill(bg_color)
        
        # 使用标准分辨率作为基准计算缩放比例
        standard_width = 1200
        standard_height = 650
        scale_x = width / standard_width
        scale_y = height / standard_height
        
        # 绘制平台（使用标准分辨率计算坐标）
        for platform_data in map_data.get('platforms', []):
            # 临时设置全局变量为标准分辨率
            global WIDTH, HEIGHT
            original_width, original_height = WIDTH, HEIGHT
            WIDTH, HEIGHT = standard_width, standard_height
            
            platform_x = self.parse_coordinate(platform_data['x']) * scale_x
            platform_y = self.parse_coordinate(platform_data['y']) * scale_y
            platform_width = self.parse_coordinate(platform_data['width']) * scale_x
            platform_height = self.parse_coordinate(platform_data['height']) * scale_y
            
            # 恢复原始分辨率
            WIDTH, HEIGHT = original_width, original_height
            
            # 平台颜色
            platform_color = (139, 69, 19)  # 棕色
            pygame.draw.rect(thumbnail_surface, platform_color, 
                           (platform_x, platform_y, platform_width, platform_height))
        
        # 绘制出生点（使用标准分辨率）
        WIDTH, HEIGHT = standard_width, standard_height
        spawn_x, spawn_y = self.get_spawn_point_from_map(map_data)
        WIDTH, HEIGHT = original_width, original_height
        
        spawn_x *= scale_x
        spawn_y *= scale_y
        pygame.draw.circle(thumbnail_surface, (0, 255, 0), (int(spawn_x), int(spawn_y)), 3)
        
        # 绘制边框
        pygame.draw.rect(thumbnail_surface, WHITE, (0, 0, width, height), 2)
        
        # 将缩略图绘制到主屏幕
        self.screen.blit(thumbnail_surface, (x, y))
        
        return pygame.Rect(x, y, width, height)
    
    def restart_game(self):
        # 使用当前地图的spawn点重新创建玩家
        spawn_point = self.get_spawn_point_from_map(self.current_map)
        self.player = Player(spawn_point['x'], spawn_point['y'])
        self.state = PLAYING
    
    def run(self):
        running = True
        print("游戏开始运行...")
        
        try:
            while running:
                running = self.handle_events()
                if not running:
                    print("游戏循环结束，退出原因：用户关闭")
                    break
                self.update()
                self.draw()
                self.clock.tick(FPS)
        except Exception as e:
            print(f"游戏运行时发生错误: {e}")
            import traceback
            traceback.print_exc()
        finally:
            print("清理游戏资源...")
            # 清理网络连接
            if self.network_client and self.network_client.connected:
                self.network_client.disconnect()
            
            pygame.quit()
            sys.exit()

if __name__ == "__main__":
    game = Game()
    game.run()