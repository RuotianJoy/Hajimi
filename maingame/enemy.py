import pygame
import math
import os
import sys

from maingame import GRAVITY

def get_resource_path(relative_path):
    """获取资源文件的绝对路径，兼容开发环境和PyInstaller打包环境"""
    try:
        # PyInstaller创建临时文件夹，并将路径存储在_MEIPASS中
        base_path = sys._MEIPASS
    except Exception:
        # 开发环境中使用脚本所在目录
        base_path = os.path.abspath(".")
    
    return os.path.join(base_path, relative_path)


class Enemy:
    def __init__(self, enemy_data):
        self.type = enemy_data['type']
        self.variant = enemy_data['variant']
        self.x = enemy_data['x']
        self.y = enemy_data['y']
        # 根据敌人类型设置不同的碰撞大小
        if self.type == 'spider':
            if self.variant == 'wall_crawling':
                # 墙上蜘蛛
                self.width = 120
                self.height = 120
            else:
                # 普通蜘蛛
                self.width = 156
                self.height = 48
        elif self.type == 'vulture':
            # 秃鹫：宽度2倍，高度1.4倍
            self.width = 140  # 128
            self.height = 116  # 90
        else:
            # 史莱姆等其他敌人保持原始大小
            self.width = 64
            self.height = 48
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
        self.attack_cooldown = 2.0  # 攻击冷却时间

        # 特殊属性
        if self.type == 'slime':
            self.jump_strength = enemy_data.get('jump_strength', 50)  # 跳跃高度三倍
            self.jump_timer = 0
            self.jump_interval = 2.0  # 史莱姆跳跃间隔
        elif self.type == 'spider':
            self.wall_crawl = enemy_data.get('wall_crawl', False)
            self.jump_strength = enemy_data.get('jump_strength', 25)  # 蜘蛛跳跃高度为史莱姆的一半
            self.jump_timer = 0
            self.jump_interval = 3.0  # 蜘蛛跳跃间隔稍长
        elif self.type == 'vulture':
            self.flight_height_min = enemy_data.get('flight_height_min', 'HEIGHT - 600')
            self.flight_height_max = enemy_data.get('flight_height_max', 'HEIGHT - 300')
            self.flying = True

        # 动画相关
        self.animation_frames = {}
        self.current_animation = 'move'
        self.frame_index = 0
        self.animation_speed = 0.15  # 调整动画速度，使动画更连贯
        self.frame_timer = 0
        self.facing_right = True
        
        # 巡逻相关
        self.patrol_start_x = self.x

        # 秃鹫旋转角度
        self.rotation = 0

        # 加载动画
        self.load_animations()

        self.rect = pygame.Rect(self.x, self.y, self.width, self.height)

    def load_animations(self):
        """加载敌怪动画"""
        try:
            if self.type == 'slime':
                gif_path = get_resource_path(f'enemy/slime/{self.variant.title()}_Slime.gif')
                frames = self.load_gif_frames(gif_path)
                if frames:
                    self.animation_frames['idle'] = frames
                    self.animation_frames['move'] = frames
                    self.animation_frames['jump'] = frames
            elif self.type == 'spider':
                if self.variant == 'ground_static':
                    gif_path = get_resource_path('enemy/spider/Black_Recluse_(ground).gif')
                elif self.variant == 'ground_crawling':
                    gif_path = get_resource_path('enemy/spider/Black_Recluse_(ground).gif')
                else:  # wall_crawling
                    gif_path = get_resource_path('enemy/spider/Black_Recluse.gif')
                frames = self.load_gif_frames(gif_path)
                if frames:
                    self.animation_frames['idle'] = frames
                    self.animation_frames['move'] = frames
            elif self.type == 'vulture':
                # 加载两个方向的动画
                gif_path_left = get_resource_path('enemy/vulture/Vulture_(flying).gif')  # 向左飞行（原始）
                gif_path_right = get_resource_path('enemy/vulture/Vulture_(flying)_flipped.gif')  # 向右飞行（翻转）

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
                # 墙爬蜘蛛也需要基本的边界检测
                self.check_collisions(platforms)
        elif self.type == 'vulture':
            # 飞行敌人保持当前移动
            self.x += self.vel_x * dt * 60
            self.y += self.vel_y * dt * 60
            # 秃鹫需要边界检测，防止飞出地图
            self.check_vulture_boundaries()

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
        elif min_distance > self.aggro_range * 2.5:  # 脱离仇恨范围
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
        if self.state == 'patrol':
            # 巡逻移动
            if self.facing_right:
                self.x += 50 * dt
            else:
                self.x -= 50 * dt
                
            # 简单的边界检测，到达边界时转向
            if self.x <= self.patrol_start_x - 100 or self.x >= self.patrol_start_x + 100:
                self.facing_right = not self.facing_right
                
        elif self.state == 'chase' and self.target_player:
            # 追击移动
            if self.target_player.x > self.x:
                self.x += 80 * dt
                self.facing_right = True
            else:
                self.x -= 80 * dt
                self.facing_right = False

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

    def check_vulture_boundaries(self):
        """检查秃鹫的边界，防止飞出地图"""
        # 水平边界检测
        if self.x < 0:
            self.x = 0
            self.vel_x = abs(self.vel_x)  # 反弹
            if hasattr(self, 'patrol_direction'):
                self.patrol_direction = 1  # 向右
        elif self.x > 1952:  # 地图宽度 - 敌人宽度
            self.x = 1952
            self.vel_x = -abs(self.vel_x)  # 反弹
            if hasattr(self, 'patrol_direction'):
                self.patrol_direction = -1  # 向左
        
        # 垂直边界检测
        if self.y < 0:
            self.y = 0
            self.vel_y = abs(self.vel_y)  # 反弹
        elif self.y > 952:  # 地图高度 - 敌人高度
            self.y = 952
            self.vel_y = -abs(self.vel_y)  # 反弹

    def update_animation(self, dt):
        """更新动画"""
        if not self.animation_frames:
            return
        if self.current_animation not in self.animation_frames:
            return

        self.frame_timer += self.animation_speed
        if self.frame_timer >= 1.0:
            self.frame_timer = 0
            frames = self.animation_frames[self.current_animation]
            self.frame_index = (self.frame_index + 1) % len(frames)

    def get_current_frame(self):
        """获取当前动画帧"""
        # 对于秃鹫，根据facing_right选择正确的动画方向
        if self.type == 'vulture':
            if hasattr(self, 'facing_right'):
                if self.facing_right and 'fly_right' in self.animation_frames:
                    frames = self.animation_frames['fly_right']
                elif not self.facing_right and 'fly_left' in self.animation_frames:
                    frames = self.animation_frames['fly_left']
                else:
                    # 回退到默认动画
                    if self.current_animation in self.animation_frames:
                        frames = self.animation_frames[self.current_animation]
                    else:
                        return None
            else:
                # 没有facing_right属性时使用默认动画
                if self.current_animation in self.animation_frames:
                    frames = self.animation_frames[self.current_animation]
                else:
                    return None
            
            if frames:
                return frames[self.frame_index % len(frames)]
            return None
        
        # 其他敌人的正常动画逻辑
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
                    frame = pygame.transform.scale(frame, (int(frame.get_width()), int(frame.get_height())))
                else:
                    # 普通蜘蛛宽度增加30%
                    frame = pygame.transform.scale(frame, (int(frame.get_width()), frame.get_height()))
                
                # 蜘蛛绘制
                if self.variant == 'wall_crawling':
                    # 墙爬蜘蛛：根据移动方向旋转动画
                    if hasattr(self, 'rotation') and self.rotation != 0:
                        # 应用旋转
                        frame = pygame.transform.rotate(frame, -self.rotation)
                        # 计算旋转后的绘制位置（居中）
                        frame_rect = frame.get_rect()
                        draw_x = self.x - (frame_rect.width - self.width) // 2
                        draw_y = self.y - (frame_rect.height - self.height) // 2
                        screen.blit(frame, (draw_x, draw_y))
                    else:
                        # 没有旋转时的普通绘制
                        if self.facing_right:
                            frame = pygame.transform.flip(frame, True, False)
                        screen.blit(frame, (self.x, self.y))
                else:
                    # 普通蜘蛛：只进行水平翻转
                    if self.facing_right:
                        frame = pygame.transform.flip(frame, True, False)
                    screen.blit(frame, (self.x, self.y))
            elif self.type == 'vulture':
                # 秃鹫放大1.4倍
                frame = pygame.transform.scale(frame, (int(frame.get_width()), int(frame.get_height())))

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
            elif self.type == 'slime':
                # 史莱姆绘制
                if not self.facing_right:
                    frame = pygame.transform.flip(frame, True, False)
                screen.blit(frame, (self.x, self.y))
            else:
                # 其他敌怪的正常处理
                # 根据朝向翻转
                if not self.facing_right:
                    frame = pygame.transform.flip(frame, True, False)
                screen.blit(frame, (self.x, self.y))
        else:
            # 绘制默认矩形
            color = (255, 0, 0) if self.type == 'slime' else (100, 100, 100)
            pygame.draw.rect(screen, color, self.rect)

        # 绘制血条（始终显示）
        bar_width = 64
        bar_height = 8
        bar_x = self.x
        bar_y = self.y - 12

        # 秃鹫特殊处理：调整血条位置以适应缩放
        if self.type == 'vulture':
            bar_width = 64  # 匹配秃鹫的缩放
            bar_x = self.x - (bar_width - self.width) // 2  # 居中对齐
            bar_y = self.y - 20  # 向上偏移更多以避免重叠

        # 背景
        pygame.draw.rect(screen, (60, 60, 60), (bar_x, bar_y, bar_width, bar_height))
        pygame.draw.rect(screen, (200, 200, 200), (bar_x, bar_y, bar_width, bar_height), 1)
        # 血量
        health_ratio = max(0, self.current_health / self.max_health) if self.max_health > 0 else 0
        health_width = int(bar_width * health_ratio)
        health_color = (255, 0, 0) if health_ratio < 0.3 else (255, 255, 0) if health_ratio < 0.7 else (0, 255, 0)
        if health_width > 0:
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
