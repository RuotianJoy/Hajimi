import math
import pygame
import time
from maingame.enemy import Enemy
from maingame import GRAVITY

class Boss(Enemy):
    def __init__(self, boss_data, player_count=1):
        # 基础boss数据
        base_data = {
            'type': 'boss',
            'variant': 'milkdragon',
            'x': boss_data.get('x', 960),  # 屏幕中央
            'y': boss_data.get('y', 400),
            'health': 2000,  # 基础血量
            'attack_power': 30,
            'speed': 150,
            'patrol_range': 200,
            'aggro_range': 800,
            'enemy_id': boss_data.get('enemy_id', 'boss_milkdragon')
        }
        
        # 根据玩家数量调整血量和伤害
        health_multiplier = 1 + (player_count - 1) * 0.5  # 每多一个玩家增加50%
        base_data['health'] = int(2000 * health_multiplier)
        
        super().__init__(base_data)
        
        # Boss特有属性
        self.player_count = player_count
        self.health_multiplier = health_multiplier
        self.width = 400  # Boss更大的碰撞体积，放大两倍
        self.height = 300  # 放大两倍
        
        # 攻击形态
        self.attack_mode = 'running'  # running, jumping, skilling
        self.attack_timer = 0
        self.attack_cooldown = 3.0
        self.mode_switch_timer = 0
        self.mode_duration = 8.0  # 每种形态持续8秒
        
        # 冲撞攻击
        self.charge_target = None
        self.charge_speed = 200
        self.charge_damage = int(30 * health_multiplier)
        
        # 跳跃攻击
        self.jump_target_pos = None
        self.is_jumping = False
        self.jump_phase = 'preparing'  # preparing, jumping, falling, landing
        self.jump_damage = int(40 * health_multiplier)
        self.jump_speed = 300
        
        # 技能攻击（弹幕）
        self.skill_active = False
        self.skill_timer = 0
        self.skill_duration = 5.0
        self.projectiles = []  # 弹幕列表
        self.projectile_spawn_timer = 0
        self.projectile_spawn_interval = 0.2  # 每0.2秒发射一波弹幕
        self.skill_damage = int(25 * health_multiplier)
        
        # 攻击冷却机制
        self.attack_cooldown = 1.0  # 攻击冷却时间（秒）
        self.last_attack_time = 0  # 上次攻击时间
        
        # 动画相关
        self.load_boss_animations()
        
        # 更新矩形
        self.rect = pygame.Rect(self.x, self.y, self.width, self.height)
        
    def load_boss_animations(self):
        """加载Boss动画"""
        try:
            import os
            import sys
            
            def get_resource_path(relative_path):
                try:
                    base_path = sys._MEIPASS
                except Exception:
                    base_path = os.path.abspath(".")
                return os.path.join(base_path, relative_path)
            
            # 加载三种形态的图片
            running_path = get_resource_path('boss/milkdragon/running_flipped.png')
            downing_path = get_resource_path('boss/milkdragon/downing_flipped.png')
            skilling_path = get_resource_path('boss/milkdragon/skilling.png')
            
            running_img = pygame.image.load(running_path).convert_alpha()
            downing_img = pygame.image.load(downing_path).convert_alpha()
            skilling_img = pygame.image.load(skilling_path).convert_alpha()
            
            # 缩放到合适大小
            running_img = pygame.transform.scale(running_img, (self.width, self.height))
            downing_img = pygame.transform.scale(downing_img, (self.width, self.height))
            skilling_img = pygame.transform.scale(skilling_img, (self.width, self.height))
            
            self.animation_frames = {
                'running': [running_img],
                'jumping': [running_img],  # 跳跃准备阶段用running
                'falling': [downing_img],  # 下落阶段用downing
                'skilling': [skilling_img],
                'idle': [running_img]
            }
            
        except Exception as e:
            print(f"加载Boss动画失败: {e}")
            # 创建默认动画
            surface = pygame.Surface((self.width, self.height))
            surface.fill((150, 0, 150))  # 紫色
            self.animation_frames = {
                'running': [surface],
                'jumping': [surface],
                'falling': [surface],
                'skilling': [surface],
                'idle': [surface]
            }
    
    def update(self, dt, player, platforms, other_players=None):
        """更新Boss状态"""
        if self.current_health <= 0:
            return
        
        # 收集所有玩家
        all_players = [player]
        if other_players:
            all_players.extend(other_players)
        
        # 更新攻击模式切换
        self.update_attack_mode(dt)
        
        # 根据当前攻击模式执行不同的AI
        if self.attack_mode == 'running':
            self.update_running_mode(dt, all_players)
        elif self.attack_mode == 'jumping':
            self.update_jumping_mode(dt, all_players, platforms)
        elif self.attack_mode == 'skilling':
            self.update_skilling_mode(dt, all_players)
        
        # 更新弹幕
        self.update_projectiles(dt)
        
        # 边界检测，防止Boss移动到地图外
        self.check_boundaries()
        
        # 攻击冷却机制已移至check_player_collision中处理
        
        # 更新动画
        self.update_animation(dt)
        
        # 更新矩形位置
        self.rect.x = int(self.x)
        self.rect.y = int(self.y)
    
    def update_attack_mode(self, dt):
        """更新攻击模式切换"""
        self.mode_switch_timer += dt
        
        if self.mode_switch_timer >= self.mode_duration:
            self.mode_switch_timer = 0
            
            # 循环切换攻击模式
            if self.attack_mode == 'running':
                self.attack_mode = 'jumping'
                self.current_animation = 'jumping'
            elif self.attack_mode == 'jumping':
                self.attack_mode = 'skilling'
                self.current_animation = 'skilling'
                self.skill_active = True
                self.skill_timer = 0
            else:  # skilling
                self.attack_mode = 'running'
                self.current_animation = 'running'
                self.skill_active = False
                self.projectiles.clear()
    
    def update_running_mode(self, dt, players):
        """更新冲撞模式"""
        # 寻找最近的玩家
        target_player = self.find_nearest_player(players)
        if not target_player:
            return
        
        # 向目标玩家冲撞
        dx = target_player.x - self.x
        dy = target_player.y - self.y
        distance = math.sqrt(dx*dx + dy*dy)
        
        if distance > 0:
            # 标准化方向向量
            dx /= distance
            dy /= distance
            
            # 移动
            self.x += dx * self.charge_speed * dt
            self.y += dy * self.charge_speed * dt
            
            # 设置朝向
            self.facing_right = dx > 0
    
    def update_jumping_mode(self, dt, players, platforms):
        """更新跳跃攻击模式"""
        if not self.is_jumping:
            # 选择随机玩家位置作为目标
            if players:
                import random
                target_player = random.choice(players)
                self.jump_target_pos = (target_player.x, target_player.y)
                self.is_jumping = True
                self.jump_phase = 'jumping'
                self.vel_y = -1280  # 向上跳跃
                self.current_animation = 'jumping'
        else:
            if self.jump_phase == 'jumping':
                # 向目标位置移动
                if self.jump_target_pos:
                    dx = self.jump_target_pos[0] - self.x
                    if abs(dx) > 5:
                        self.x += (dx / abs(dx)) * self.jump_speed * dt
                        # 设置朝向
                        self.facing_right = dx > 0
                
                # 应用重力
                self.vel_y += GRAVITY * dt * 60
                self.y += self.vel_y * dt
                
                # 检查是否开始下落
                if self.vel_y > 0:
                    self.jump_phase = 'falling'
                    self.current_animation = 'falling'
            
            elif self.jump_phase == 'falling':
                # 继续下落
                self.vel_y += GRAVITY * dt * 60
                self.y += self.vel_y * dt
                
                # 检查是否到达地面（地图底部边界）
                if self.y + self.height >= 1080:  # 地图高度
                    self.y = 1080 - self.height
                    self.vel_y = 0
                    self.is_jumping = False
                    self.jump_phase = 'preparing'
                    self.current_animation = 'running'
    
    def update_skilling_mode(self, dt, players):
        """更新技能攻击模式"""
        if not self.skill_active:
            return
        
        self.skill_timer += dt
        self.projectile_spawn_timer += dt
        
        # 发射弹幕
        if self.projectile_spawn_timer >= self.projectile_spawn_interval:
            self.projectile_spawn_timer = 0
            self.spawn_projectiles()
        
        # 技能持续时间结束
        if self.skill_timer >= self.skill_duration:
            self.skill_active = False
            self.projectiles.clear()
    
    def spawn_projectiles(self):
        """生成弹幕"""
        # 计算屏幕80%半径
        screen_radius = min(1920, 1080) * 0.4  # 80%屏幕的半径
        
        # 在boss周围生成环形弹幕
        projectile_count = 12  # 每波12个弹幕
        for i in range(projectile_count):
            angle = (2 * math.pi * i) / projectile_count
            
            # 弹幕初始位置（boss周围）
            start_x = self.x + self.width/2 + math.cos(angle) * 100
            start_y = self.y + self.height/2 + math.sin(angle) * 100
            
            # 弹幕移动方向
            vel_x = math.cos(angle) * 200
            vel_y = math.sin(angle) * 200
            
            projectile = {
                'x': start_x,
                'y': start_y,
                'vel_x': vel_x,
                'vel_y': vel_y,
                'damage': self.skill_damage,
                'lifetime': 3.0,  # 弹幕存在3秒
                'radius': 16  # 弹幕放大两倍
            }
            
            self.projectiles.append(projectile)
    
    def update_projectiles(self, dt):
        """更新弹幕"""
        for projectile in self.projectiles[:]:
            # 移动弹幕
            projectile['x'] += projectile['vel_x'] * dt
            projectile['y'] += projectile['vel_y'] * dt
            
            # 减少生命时间
            projectile['lifetime'] -= dt
            
            # 移除过期弹幕
            if projectile['lifetime'] <= 0:
                self.projectiles.remove(projectile)
            
            # 边界检查
            elif (projectile['x'] < -50 or projectile['x'] > 1970 or 
                  projectile['y'] < -50 or projectile['y'] > 1130):
                self.projectiles.remove(projectile)
    
    def find_nearest_player(self, players):
        """寻找最近的玩家"""
        if not players:
            return None
        
        nearest_player = None
        min_distance = float('inf')
        
        for player in players:
            if player and hasattr(player, 'x') and hasattr(player, 'y'):
                distance = math.sqrt((self.x - player.x)**2 + (self.y - player.y)**2)
                if distance < min_distance:
                    min_distance = distance
                    nearest_player = player
        
        return nearest_player
    
    def can_attack(self):
        """检查是否可以攻击（基于时间的冷却）"""
        current_time = time.time()
        return current_time - self.last_attack_time >= self.attack_cooldown
    
    def attack(self, player):
        """攻击玩家并返回伤害值"""
        if not self.can_attack():
            return 0
            
        player_rect = pygame.Rect(player.x, player.y, player.width, player.height)
        damage = 0
        
        # Boss本体碰撞
        if self.rect.colliderect(player_rect):
            if self.attack_mode == 'running':
                damage = self.charge_damage
            elif self.attack_mode == 'jumping' and self.jump_phase == 'falling':
                damage = self.jump_damage
                
        # 弹幕碰撞
        for projectile in self.projectiles[:]:
            proj_rect = pygame.Rect(projectile['x'] - projectile['radius'], 
                                  projectile['y'] - projectile['radius'],
                                  projectile['radius'] * 2, 
                                  projectile['radius'] * 2)
            if proj_rect.colliderect(player_rect):
                self.projectiles.remove(projectile)
                damage = max(damage, projectile['damage'])
        
        if damage > 0:
            self.last_attack_time = time.time()
            
        return damage
    
    def check_player_collision(self, player):
        """检查与玩家的碰撞"""
        if not player:
            return False
        
        # 检查玩家是否在伤害免疫期间
        if hasattr(player, 'damage_immunity_time') and player.damage_immunity_time > 0:
            return False
        
        damage = self.attack(player)
        if damage > 0:
            return {'damage': damage, 'type': 'boss_attack'}
        return False
    
    def draw(self, screen):
        """绘制Boss"""
        # 绘制Boss本体
        frame = self.get_current_frame()
        if frame:
            if not self.facing_right:
                frame = pygame.transform.flip(frame, True, False)
            screen.blit(frame, (int(self.x), int(self.y)))
        
        # 绘制血量条
        self.draw_health_bar(screen)
        
        # 绘制弹幕
        for projectile in self.projectiles:
            pygame.draw.circle(screen, (255, 100, 100), 
                             (int(projectile['x']), int(projectile['y'])), 
                             projectile['radius'])
    
    def draw_health_bar(self, screen):
        """绘制血量条"""
        bar_width = 300
        bar_height = 20
        from maingame import WIDTH
        bar_x = (WIDTH - bar_width) // 2  # 屏幕顶部中央
        bar_y = 50
        
        # 背景
        pygame.draw.rect(screen, (100, 100, 100), (bar_x, bar_y, bar_width, bar_height))
        
        # 血量
        health_ratio = self.current_health / self.max_health
        health_width = int(bar_width * health_ratio)
        
        # 血量颜色根据剩余血量变化
        if health_ratio > 0.6:
            health_color = (0, 255, 0)  # 绿色
        elif health_ratio > 0.3:
            health_color = (255, 255, 0)  # 黄色
        else:
            health_color = (255, 0, 0)  # 红色
        
        pygame.draw.rect(screen, health_color, (bar_x, bar_y, health_width, bar_height))
        
        # 边框
        pygame.draw.rect(screen, (255, 255, 255), (bar_x, bar_y, bar_width, bar_height), 2)
        
        # 血量文字
        font = pygame.font.Font(None, 24)
        health_text = font.render(f"Boss: {self.current_health}/{self.max_health}", True, (255, 255, 255))
        text_rect = health_text.get_rect(center=(bar_x + bar_width//2, bar_y - 15))
        screen.blit(health_text, text_rect)
    
    def take_damage(self, damage):
        """受到伤害"""
        self.current_health -= damage
        if self.current_health < 0:
            self.current_health = 0
        return self.current_health <= 0  # 返回是否死亡
    
    def check_boundaries(self):
        """检查边界，防止Boss移动到地图外"""
        # 水平边界检测
        if self.x < 0:
            self.x = 0
        elif self.x + self.width > 1920:  # 地图宽度
            self.x = 1920 - self.width
        
        # 垂直边界检测
        if self.y < 0:
            self.y = 0
        elif self.y + self.height > 1080:  # 地图高度
            self.y = 1080 - self.height