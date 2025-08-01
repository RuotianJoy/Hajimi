import pygame
import os
import sys
from maingame import WIDTH, HEIGHT, GRAVITY, JUMP_STRENGTH, PLAYER_SPEED, BLUE
from maingame.weapon import Weapon

def get_resource_path(relative_path):
    """获取资源文件的绝对路径，兼容开发环境和PyInstaller打包环境"""
    try:
        # PyInstaller创建临时文件夹，并将路径存储在_MEIPASS中
        base_path = sys._MEIPASS
    except Exception:
        # 开发环境中使用当前工作目录
        base_path = os.path.abspath(".")
    
    return os.path.join(base_path, relative_path)


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

        # 武器系统
        if character_name == "哈基为":
            self.weapon = Weapon("meowmere")
        elif character_name == "哈基阳":
            self.weapon = Weapon("nadir")
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
            self.animation_frames['idle'] = self.load_gif_frames(get_resource_path(self.character_folder + 'noMoveAnimation.gif'))
            self.animation_frames['move'] = self.load_gif_frames(get_resource_path(self.character_folder + 'MoveAnimation.gif'))
            self.animation_frames['sprint'] = self.load_gif_frames(get_resource_path(self.character_folder + 'SprintAnimation.gif'))
            # print(f"玩家动画加载成功: {self.character_folder}")
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
