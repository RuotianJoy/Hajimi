import socket
import threading
import json
import time
import math
import uuid
from typing import Dict, Any, Optional

class NetworkClient:
    def __init__(self, host='localhost', port=12345):
        self.host = host
        self.port = port
        self.socket = None
        self.connected = False
        self.player_id = None
        self.other_players = {}
        self.running = False
        self.game_started = False
        self.is_host = False
        self.host_disconnected = False  # 房主断开连接标志
        self.return_to_waiting_room = False  # 返回等待房间标志
        self.room_disbanded = False  # 房间解散标志
        self.map_updated = False  # 地图更新标志
        self.selected_map_index = 0  # 选择的地图索引
        self.selected_map_name = ''  # 选择的地图名称
        self.portal_triggered = False  # 传送门触发标志
        self.portal_target_map = ''  # 传送门目标地图
        self.dead_enemies = set()  # 死亡敌人ID集合
        self.enemy_updates = {}  # 敌人状态更新字典
        self.enemies_sync_data = []  # 服务端同步的敌人数据
        self.map_ready = False  # 服务端地图是否准备完成
        self.server_enemies_count = 0  # 服务端敌人数量
        
    def connect(self, host=None, port=None):
        # 如果提供了参数，则更新host和port
        if host is not None:
            self.host = host
        if port is not None:
            self.port = port
            
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.host, self.port))
            self.connected = True
            self.running = True
            
            # 启动接收线程
            receive_thread = threading.Thread(target=self._receive_messages)
            receive_thread.daemon = True
            receive_thread.start()
            
            print(f"已连接到服务器 {self.host}:{self.port}")
            return True
        except Exception as e:
            print(f"连接失败: {e}")
            return False
    
    def disconnect(self):
        self.running = False
        self.connected = False
        if self.socket:
            try:
                self.socket.close()
            except:
                pass
        print("已断开连接")
    
    def send_player_data(self, player_data):
        if not self.connected:
            return
        
        # 兼容旧的参数格式和新的字典格式
        if isinstance(player_data, dict):
            data = {
                'type': 'player_update',
                'timestamp': time.time()
            }
            data.update(player_data)
        else:
            # 兼容旧的参数格式 (x, y, facing_right, on_ground)
            x, y, facing_right, on_ground = player_data if isinstance(player_data, tuple) else (player_data, None, None, None)
            data = {
                'type': 'player_update',
                'x': x,
                'y': y,
                'facing_right': facing_right,
                'on_ground': on_ground,
                'timestamp': time.time()
            }
        
        try:
            message = json.dumps(data) + '\n'
            self.socket.send(message.encode('utf-8'))
        except Exception as e:
            print(f"发送数据失败: {e}")
            self.connected = False
    
    def send_character_selection(self, character_name, player_name):
        """发送角色选择信息到服务器"""
        if not self.connected:
            return
        
        data = {
            'type': 'character_selection',
            'character_name': character_name,
            'player_name': player_name,
            'timestamp': time.time()
        }
        
        try:
            message = json.dumps(data) + '\n'
            self.socket.send(message.encode('utf-8'))
            print(f"已发送角色选择: {character_name}")
        except Exception as e:
            print(f"发送角色选择失败: {e}")
            self.connected = False
    
    def send_game_start(self):
        """发送游戏开始信号到服务器"""
        if not self.connected:
            return
        
        data = {
            'type': 'game_start',
            'timestamp': time.time()
        }
        
        try:
            message = json.dumps(data) + '\n'
            self.socket.send(message.encode('utf-8'))
            print("已发送游戏开始信号")
        except Exception as e:
            print(f"发送游戏开始信号失败: {e}")
            self.connected = False
    
    def send_return_to_waiting_room(self):
        """发送返回等待房间信号到服务器"""
        if not self.connected:
            return
        
        data = {
            'type': 'return_to_waiting_room',
            'timestamp': time.time()
        }
        
        try:
            message = json.dumps(data) + '\n'
            self.socket.send(message.encode('utf-8'))
            print("已发送返回等待房间信号")
        except Exception as e:
            print(f"发送返回等待房间信号失败: {e}")
            self.connected = False
    
    def send_map_selection(self, map_index, map_name):
        """发送地图选择信息到服务器"""
        if not self.connected:
            return
        
        data = {
            'type': 'map_selection',
            'map_index': map_index,
            'map_name': map_name,
            'timestamp': time.time()
        }
        
        try:
            message = json.dumps(data) + '\n'
            self.socket.send(message.encode('utf-8'))
            print(f"已发送地图选择: {map_name}")
        except Exception as e:
            print(f"发送地图选择失败: {e}")
            self.connected = False
    
    def send_portal_trigger(self, target_map):
        """发送传送门触发信息到服务器"""
        if not self.connected:
            return
        
        data = {
            'type': 'portal_trigger',
            'target_map': target_map,
            'timestamp': time.time()
        }
        
        try:
            message = json.dumps(data) + '\n'
            self.socket.send(message.encode('utf-8'))
            print(f"发送传送门触发信号: {target_map}")
        except Exception as e:
            print(f"发送传送门触发失败: {e}")
            self.connected = False
    
    def send_player_death(self, player_name):
        """发送玩家死亡信息到服务器"""
        if not self.connected:
            return
        
        data = {
            'type': 'player_death',
            'player_name': player_name,
            'timestamp': time.time()
        }
        
        try:
            message = json.dumps(data) + '\n'
            self.socket.send(message.encode('utf-8'))
            print(f"已发送玩家死亡信号: {player_name}")
        except Exception as e:
            print(f"发送玩家死亡信号失败: {e}")
            self.connected = False
    
    def send_enemy_death(self, enemy_id):
        """发送敌人死亡信息到服务器"""
        if not self.connected:
            return
        
        data = {
            'type': 'enemy_death',
            'enemy_id': enemy_id,
            'timestamp': time.time()
        }
        
        try:
            message = json.dumps(data) + '\n'
            self.socket.send(message.encode('utf-8'))
            print(f"已发送敌人死亡信号: (ID: {enemy_id})")
        except Exception as e:
            print(f"发送敌人死亡信号失败: {e}")
            self.connected = False
    
    def send_player_damage(self, target_player_id, damage):
        """发送玩家受伤信息到服务器"""
        if not self.connected:
            return
        
        data = {
            'type': 'player_damage',
            'target_player_id': target_player_id,
            'damage': damage,
            'timestamp': time.time()
        }
        
        try:
            message = json.dumps(data) + '\n'
            self.socket.send(message.encode('utf-8'))
            print(f"已发送玩家伤害信号: 玩家{target_player_id} 受到{damage}点伤害")
        except Exception as e:
            print(f"发送玩家伤害信号失败: {e}")
            self.connected = False
    
    def send_enemy_update(self, enemy_data):
        """发送敌人状态更新"""
        if not self.connected:
            return
        
        data = {
            'type': 'enemy_update',
            'timestamp': time.time()
        }
        data.update(enemy_data)
        
        try:
            message = json.dumps(data) + '\n'
            self.socket.send(message.encode('utf-8'))
        except Exception as e:
            print(f"发送敌人状态更新失败: {e}")
    
    def send_enemies_batch_update(self, enemies_data):
        """批量发送敌人状态更新"""
        if not self.connected:
            return
        
        data = {
            'type': 'enemies_batch_update',
            'enemies': enemies_data,
            'timestamp': time.time()
        }
        
        try:
            message = json.dumps(data) + '\n'
            self.socket.send(message.encode('utf-8'))
        except Exception as e:
            print(f"批量发送敌人状态更新失败: {e}")
    
    def send_enemy_creation(self, enemy_data):
        """发送敌人创建请求到服务器"""
        if not self.connected:
            return
        
        data = {
            'type': 'enemy_creation',
            'enemy_data': enemy_data,
            'timestamp': time.time()
        }
        
        try:
            message = json.dumps(data) + '\n'
            self.socket.send(message.encode('utf-8'))
        except Exception as e:
            print(f"发送敌人创建请求失败: {e}")
    
    def send_enemy_damage(self, enemy_id, damage, current_health):
        """发送敌人受伤信息到服务器"""
        if not self.connected:
            return
        
        data = {
            'type': 'enemy_damage',
            'enemy_id': enemy_id,
            'damage': damage,
            'current_health': current_health,
            'timestamp': time.time()
        }
        
        try:
            message = json.dumps(data) + '\n'
            self.socket.send(message.encode('utf-8'))
            print(f"已发送敌人伤害信号: 敌人{enemy_id} 受到{damage}点伤害，剩余血量{current_health}")
        except Exception as e:
            print(f"发送敌人伤害信号失败: {e}")
            self.connected = False
            self.connected = False
    
    def send_map_data(self, map_data):
        """发送地图数据到服务端"""
        if not self.connected:
            return
        
        data = {
            'type': 'map_data',
            'map_data': map_data,
            'timestamp': time.time()
        }
        
        try:
            message = json.dumps(data) + '\n'
            self.socket.send(message.encode('utf-8'))
            print(f"已发送地图数据: {map_data.get('name', '未知地图')}")
        except Exception as e:
            print(f"发送地图数据失败: {e}")
            self.connected = False
    
    def _receive_messages(self):
        buffer = ""
        
        while self.running and self.connected:
            try:
                data = self.socket.recv(1024).decode('utf-8')
                if not data:
                    break
                
                buffer += data
                while '\n' in buffer:
                    line, buffer = buffer.split('\n', 1)
                    if line.strip():
                        self._handle_message(json.loads(line))
                        
            except Exception as e:
                print(f"接收消息失败: {e}")
                break
        
        self.connected = False
    
    def _handle_message(self, message):
        msg_type = message.get('type')
        
        if msg_type == 'player_id':
            self.player_id = message['id']
            self.is_host = message.get('is_host', False)
            print(f"获得玩家ID: {self.player_id}, 房主状态: {self.is_host}")
        
        elif msg_type == 'player_update':
            player_id = message['player_id']
            if player_id != self.player_id:
                # 如果玩家不存在，创建新的玩家记录
                if player_id not in self.other_players:
                    self.other_players[player_id] = {}
                
                # 更新玩家数据，只更新存在的字段
                player_data = self.other_players[player_id]
                
                # 游戏中的位置数据（支持相对坐标和绝对坐标）
                if 'rel_x' in message:
                    player_data['rel_x'] = message['rel_x']
                elif 'x' in message:
                    player_data['x'] = message['x']
                if 'rel_y' in message:
                    player_data['rel_y'] = message['rel_y']
                elif 'y' in message:
                    player_data['y'] = message['y']
                if 'facing_right' in message:
                    player_data['facing_right'] = message['facing_right']
                if 'on_ground' in message:
                    player_data['on_ground'] = message['on_ground']
                
                # 等待房间的玩家信息
                if 'player_name' in message:
                    player_data['player_name'] = message['player_name']
                if 'character_name' in message:
                    player_data['character_name'] = message['character_name']
                if 'character_index' in message:
                    player_data['character_index'] = message['character_index']
                
                # 动画信息
                if 'current_animation' in message:
                    player_data['current_animation'] = message['current_animation']
                if 'frame_index' in message:
                    player_data['frame_index'] = message['frame_index']
                
                player_data['timestamp'] = message.get('timestamp', time.time())
                
                # 添加调试信息（可选）
                if 'x' in message and 'y' in message:
                    animation = message.get('current_animation', 'unknown')
                    frame = message.get('frame_index', 'unknown')
   # 添加调试信息（可选）
                # print(f"接收到玩家 {player_id} 数据: x={message['x']}, y={message['y']}, 动画={animation}, 帧={frame}")
        
        elif msg_type == 'player_disconnect':
            player_id = message['player_id']
            if player_id in self.other_players:
                del self.other_players[player_id]
                print(f"玩家 {player_id} 已断开连接")
        
        elif msg_type == 'host_disconnect':
            player_id = message['player_id']
            print(f"房主 {player_id} 已断开连接，返回模式选择页面")
            self.host_disconnected = True
            # 清空其他玩家数据
            self.other_players.clear()
        
        elif msg_type == 'room_disbanded':
            print("房间已解散")
            self.room_disbanded = True
        
        elif msg_type == 'map_selection':
            # 接收房主的地图选择
            map_index = message.get('map_index', 0)
            map_name = message.get('map_name', '未知地图')
            print(f"房主选择了地图: {map_name}")
            # 设置标志，让游戏主循环处理地图更新
            self.map_updated = True
            self.selected_map_index = map_index
            self.selected_map_name = map_name
            # 清空其他玩家数据
            self.other_players.clear()
        
        elif msg_type == 'character_selection':
            player_id = message['player_id']
            character_name = message['character_name']
            player_name = message['player_name']
            
            if player_id in self.other_players:
                self.other_players[player_id]['character_name'] = character_name
                self.other_players[player_id]['player_name'] = player_name
            else:
                self.other_players[player_id] = {
                    'character_name': character_name,
                    'player_name': player_name,
                    'x': 0,
                    'y': 0,
                    'facing_right': True,
                    'on_ground': True,
                    'timestamp': time.time()
                }
            print(f"玩家 {player_id} 选择了角色: {character_name}")
        
        elif msg_type == 'game_start':
            # 设置游戏开始标志
            self.game_started = True
            print("收到游戏开始信号，准备进入游戏")
        
        elif msg_type == 'return_to_waiting_room':
            # 设置返回等待房间标志
            self.return_to_waiting_room = True
            print("收到返回等待房间信号")
        
        elif msg_type == 'portal_trigger':
            # 设置传送门触发标志
            self.portal_triggered = True
            self.portal_target_map = message.get('target_map', '')
            print(f"收到传送门触发信号: {self.portal_target_map}")
        
        elif msg_type == 'map_change':
            # 接收房主的地图切换信号
            target_map = message.get('target_map', '')
            print(f"收到地图切换信号: {target_map}")
            # 设置传送门触发标志，让游戏主循环处理地图切换
            self.portal_triggered = True
            self.portal_target_map = target_map
        
        elif msg_type == 'player_death':
            # 接收其他玩家死亡信号
            player_name = message.get('player_name', '未知玩家')
            player_id = message.get('player_id', '')
            print(f"玩家 {player_name} 已死亡")
            # 可以在这里添加显示其他玩家死亡的UI提示
        
        elif msg_type == 'enemy_death':
            # 接收敌人死亡信号，用于同步敌人状态
            enemy_id = message.get('enemy_id', '')
            enemy_type = message.get('enemy_type', '未知敌人')
            print(f"敌人 {enemy_type} (ID: {enemy_id}) 已被击败")
            # 设置标志让游戏主循环处理敌人移除
            if not hasattr(self, 'dead_enemies'):
                self.dead_enemies = set()
            self.dead_enemies.add(enemy_id)
        
        elif msg_type == 'enemy_update':
            # 接收敌人状态更新
            enemy_id = message.get('enemy_id', '')
            if not hasattr(self, 'enemy_updates'):
                self.enemy_updates = {}
            self.enemy_updates[enemy_id] = message
        
        elif msg_type == 'enemies_batch_update':
            # 接收批量敌人状态更新
            enemies_data = message.get('enemies', [])
            if not hasattr(self, 'enemy_updates'):
                self.enemy_updates = {}
            for enemy_data in enemies_data:
                 enemy_id = enemy_data.get('enemy_id', '')
                 if enemy_id:
                     self.enemy_updates[enemy_id] = enemy_data
        
        elif msg_type == 'enemies_sync':
            # 接收服务端同步的敌人数据
            enemies_data = message.get('enemies', [])
            if not hasattr(self, 'enemies_sync_data'):
                self.enemies_sync_data = []
            self.enemies_sync_data = enemies_data
        
        elif msg_type == 'player_damage_received':
            # 接收玩家受伤信息
            damage = message.get('damage', 0)
            from_player_id = message.get('from_player_id', '')
            
            # 设置受伤标志，让游戏主循环处理伤害
            if not hasattr(self, 'pending_damage'):
                self.pending_damage = 0
            self.pending_damage += damage
            print(f"收到伤害信息: {damage}点伤害 (来自玩家 {from_player_id})")
        
        elif msg_type == 'map_ready':
            # 处理地图准备完成消息
            self.map_ready = True
            self.server_enemies_count = message.get('enemies_count', 0)
            print(f"服务端地图准备完成: {message.get('map_name', '未知地图')}，敌人数量: {self.server_enemies_count}")

class GameObjectPool:
    """服务端统一游戏对象池，管理所有玩家和敌怪"""
    def __init__(self):
        self.players = {}  # 玩家对象池 {player_id: player_data}
        self.enemies = {}  # 敌怪对象池 {enemy_id: enemy_data}
        self.platforms = []  # 平台数据
        self.current_map_data = None  # 当前地图信息
        self.last_update_time = time.time()
        
        # 游戏常量
        self.GRAVITY = 1.2
        self.FPS = 60
        
        # 地图相关
        self.map_enemies_spawned = False  # 标记是否已生成地图敌人
        
    def add_player(self, player_id, player_data):
        """添加玩家到对象池"""
        self.players[player_id] = {
            'id': player_id,
            'x': player_data.get('x', 100),
            'y': player_data.get('y', 100),
            'vel_x': 0,
            'vel_y': 0,
            'facing_right': True,
            'on_ground': False,
            'character_name': player_data.get('character_name', '哈基为'),
            'player_name': player_data.get('player_name', '玩家'),
            'health': 100,
            'max_health': 100,
            'last_update': time.time()
        }
        
    def remove_player(self, player_id):
        """从对象池移除玩家"""
        if player_id in self.players:
            del self.players[player_id]
            
    def add_enemy(self, enemy_id, enemy_data):
        """添加敌怪到对象池"""
        self.enemies[enemy_id] = {
            'id': enemy_id,
            'type': enemy_data.get('type', 'slime'),
            'variant': enemy_data.get('variant', 'blue'),
            'x': enemy_data.get('x', 0),
            'y': enemy_data.get('y', 0),
            'vel_x': 0,
            'vel_y': 0,
            'facing_right': True,
            'on_ground': False,
            'health': enemy_data.get('health', 50),
            'max_health': enemy_data.get('health', 50),
            'attack_power': enemy_data.get('attack_power', 10),
            'speed': enemy_data.get('speed', 1.2),  # 降低默认移动速度，从2改为1.2
            'patrol_range': enemy_data.get('patrol_range', 200),
            'aggro_range': enemy_data.get('aggro_range', 150),
            'state': 'patrol',  # patrol, chase, attack, idle
            'target_player_id': None,
            'patrol_start_x': enemy_data.get('x', 0),
            'patrol_direction': 1,
            'last_attack_time': 0,
            'attack_cooldown': 1.0,
            'current_animation': 'idle',
            'frame_index': 0,
            'last_update': time.time()
        }
        
        # 设置初始巡逻速度和特殊属性
        if enemy_data.get('type') == 'slime':
            self.enemies[enemy_id]['jump_timer'] = 0
            self.enemies[enemy_id]['jump_interval'] = 2.0
            self.enemies[enemy_id]['jump_strength'] = 35
        elif enemy_data.get('type') == 'spider':
            if enemy_data.get('variant') in ['ground_static', 'ground_crawling']:
                self.enemies[enemy_id]['vel_x'] = enemy_data.get('speed', 2) * self.enemies[enemy_id]['patrol_direction']
        elif enemy_data.get('type') == 'vulture':
            self.enemies[enemy_id]['flying'] = True
            self.enemies[enemy_id]['flight_height_min'] = enemy_data.get('flight_height_min', 300)
            self.enemies[enemy_id]['flight_height_max'] = enemy_data.get('flight_height_max', 600)
            self.enemies[enemy_id]['rotation'] = 0
            
    def remove_enemy(self, enemy_id):
        """从对象池移除敌怪"""
        if enemy_id in self.enemies:
            del self.enemies[enemy_id]
            
    def set_map_data(self, map_data):
        """设置当前地图数据并生成敌人"""
        self.current_map_data = map_data
        self.map_enemies_spawned = False
        
        # 解析平台数据
        self.platforms = []
        if 'platforms' in map_data:
            for platform in map_data['platforms']:
                parsed_platform = {
                    'x': self.parse_coordinate(platform['x']),
                    'y': self.parse_coordinate(platform['y']),
                    'width': self.parse_coordinate(platform['width']),
                    'height': platform['height'],
                    'type': platform.get('type', 'platform')
                }
                self.platforms.append(parsed_platform)
            
            # 平台数据解析完成
        
        # 清除现有敌人
        self.enemies.clear()
        
        # 从地图数据生成敌人
        self.spawn_enemies_from_map()
        
    def spawn_enemies_from_map(self):
        """从地图数据生成敌人到对象池"""
        if not self.current_map_data or self.map_enemies_spawned:
            return
            
        if 'enemies' in self.current_map_data:
            for i, enemy_data in enumerate(self.current_map_data['enemies']):
                try:
                    # 解析坐标
                    x = self.parse_coordinate(enemy_data['x'])
                    y = self.parse_coordinate(enemy_data['y'])
                    
                    # 生成确定性ID
                    map_name = self.current_map_data.get('level_name', self.current_map_data.get('name', 'unknown'))
                    enemy_id = f"{map_name}_{i}_{enemy_data['type']}_{enemy_data['variant']}"
                    
                    # 创建敌人数据
                    server_enemy_data = {
                        'type': enemy_data['type'],
                        'variant': enemy_data['variant'],
                        'x': x,
                        'y': y,
                        'health': enemy_data.get('health', 50),
                        'attack_power': enemy_data.get('attack_power', 10),
                        'speed': enemy_data.get('speed', 2),
                        'patrol_range': enemy_data.get('patrol_range', 200),
                        'aggro_range': enemy_data.get('aggro_range', 150)
                    }
                    
                    # 为秃鹫添加飞行高度参数
                    if enemy_data['type'] == 'vulture':
                        server_enemy_data['flight_height_min'] = self.parse_coordinate(enemy_data.get('flight_height_min', 'HEIGHT - 600'))
                        server_enemy_data['flight_height_max'] = self.parse_coordinate(enemy_data.get('flight_height_max', 'HEIGHT - 300'))
                    
                    # 添加到对象池
                    self.add_enemy(enemy_id, server_enemy_data)
                    print(f"服务端生成敌人: {enemy_data['type']} ({enemy_data['variant']}) 位置({x}, {y}) ID: {enemy_id}")
                    
                except Exception as e:
                    print(f"服务端生成敌人失败: {e}, 数据: {enemy_data}")
                    
        self.map_enemies_spawned = True
        
    def parse_coordinate(self, coord):
        """解析坐标表达式"""
        if isinstance(coord, str):
            # 简单的表达式解析，支持基本的数学运算
            try:
                # 替换常见的屏幕尺寸变量
                coord = coord.replace('WIDTH', '1920')
                coord = coord.replace('HEIGHT', '1080')
                coord = coord.replace('SCREEN_WIDTH', '1920')
                coord = coord.replace('SCREEN_HEIGHT', '1080')
                return eval(coord)
            except:
                return 0
        return coord
            
    def update_player(self, player_id, player_data):
        """更新玩家数据"""
        if player_id in self.players:
            self.players[player_id].update(player_data)
            self.players[player_id]['last_update'] = time.time()
            
    def update_game_objects(self):
        """更新所有游戏对象（服务端游戏逻辑）"""
        current_time = time.time()
        dt = current_time - self.last_update_time
        self.last_update_time = current_time
        
        # 更新所有敌怪
        
        # 更新所有敌怪
        for enemy_id, enemy in self.enemies.items():
            self._update_enemy_ai(enemy, dt)
            self._update_enemy_physics(enemy, dt)
            
    def _update_enemy_ai(self, enemy, dt):
        """更新敌怪AI逻辑"""
        # 寻找最近的玩家作为目标
        target_player = None
        min_distance = float('inf')
        
        for player_id, player in self.players.items():
            distance = math.sqrt((enemy['x'] - player['x'])**2 + (enemy['y'] - player['y'])**2)
            if distance < min_distance:
                min_distance = distance
                target_player = player
        
        if not target_player:
            return
        
        # 根据距离更新AI状态
        if min_distance <= enemy['aggro_range']:
            enemy['state'] = 'chase'
            enemy['target_player_id'] = target_player.get('player_id')
        elif min_distance > enemy['aggro_range'] * 1.5:  # 脱离仇恨范围
            enemy['state'] = 'patrol'
            enemy['target_player_id'] = None
        
        # 根据敌人类型调用对应的移动逻辑
        if enemy['type'] == 'slime':
            self._update_slime_movement(enemy, dt, target_player)
        elif enemy['type'] == 'spider':
            self._update_spider_movement(enemy, dt, target_player)
        elif enemy['type'] == 'vulture':
            self._update_vulture_movement(enemy, dt, target_player)
            
    def _update_slime_movement(self, enemy, dt, target_player):
        """更新史莱姆移动逻辑"""
        # 更新跳跃计时器
        enemy['jump_timer'] += dt
        
        if enemy['state'] == 'patrol':
            # 巡逻状态：在巡逻范围内跳跃移动
            patrol_distance = abs(enemy['x'] - enemy['patrol_start_x'])
            
            # 如果超出巡逻范围，改变方向
            if patrol_distance >= enemy['patrol_range']:
                enemy['patrol_direction'] *= -1
            
            # 定期跳跃
            if enemy['jump_timer'] >= enemy['jump_interval'] and enemy['on_ground']:
                enemy['vel_y'] = -enemy['jump_strength']
                enemy['vel_x'] = enemy['speed'] * 0.8 * enemy['patrol_direction']
                enemy['jump_timer'] = 0
                enemy['facing_right'] = enemy['patrol_direction'] > 0
                enemy['current_animation'] = 'jump'
                
        elif enemy['state'] == 'chase' and target_player:
            # 追击状态：向玩家方向跳跃
            direction_x = target_player['x'] - enemy['x']
            
            # 更频繁的跳跃
            if enemy['jump_timer'] >= enemy['jump_interval'] * 0.6 and enemy['on_ground']:
                enemy['vel_y'] = -enemy['jump_strength']
                enemy['vel_x'] = enemy['speed'] * 0.8 * (1 if direction_x > 0 else -1)  # 降低追击速度倍数，从1.0改为0.8
                enemy['jump_timer'] = 0
                enemy['facing_right'] = direction_x > 0
                enemy['current_animation'] = 'jump'

            
    def _update_spider_movement(self, enemy, dt, target_player):
        """更新蜘蛛移动逻辑"""
        if enemy['variant'] in ['ground_static', 'ground_crawling']:
            # 地面蜘蛛
            if enemy['state'] == 'patrol':
                # 巡逻状态：左右移动
                patrol_distance = abs(enemy['x'] - enemy['patrol_start_x'])
                
                # 如果超出巡逻范围，改变方向
                if patrol_distance >= enemy['patrol_range']:
                    enemy['patrol_direction'] *= -1
                
                enemy['vel_x'] = enemy['speed'] * enemy['patrol_direction']
                enemy['facing_right'] = enemy['patrol_direction'] > 0
                enemy['current_animation'] = 'move'
                
            elif enemy['state'] == 'chase' and target_player:
                # 追击状态：向玩家方向移动
                direction_x = target_player['x'] - enemy['x']
                
                if abs(direction_x) > 10:  # 避免抖动
                    enemy['vel_x'] = enemy['speed'] * 1.2 * (1 if direction_x > 0 else -1)  # 降低追击速度倍数，从1.5改为1.2
                    enemy['facing_right'] = direction_x > 0
                    enemy['current_animation'] = 'move'
                else:
                    enemy['vel_x'] = 0
                    enemy['current_animation'] = 'idle'
                    
        elif enemy['variant'] == 'wall_crawling':
            # 墙爬蜘蛛：可以在墙面和天花板移动
            if enemy['state'] == 'patrol':
                # 简单的圆形巡逻
                angle = time.time() * enemy['speed'] * 0.5
                radius = enemy['patrol_range'] * 0.3
                enemy['vel_x'] = math.cos(angle) * enemy['speed']
                enemy['vel_y'] = math.sin(angle) * enemy['speed'] * 0.5
                enemy['facing_right'] = enemy['vel_x'] > 0
                
            elif enemy['state'] == 'chase' and target_player:
                # 直接向玩家移动
                direction_x = target_player['x'] - enemy['x']
                direction_y = target_player['y'] - enemy['y']
                distance = math.sqrt(direction_x**2 + direction_y**2)
                
                if distance > 10:
                    enemy['vel_x'] = (direction_x / distance) * enemy['speed'] * 1.2  # 降低追击速度倍数，从1.5改为1.2
                    enemy['vel_y'] = (direction_y / distance) * enemy['speed'] * 1.2  # 降低追击速度倍数，从1.5改为1.2
                    enemy['facing_right'] = direction_x > 0
                else:
                    enemy['vel_x'] = 0
                    enemy['vel_y'] = 0
                
    def _update_vulture_movement(self, enemy, dt, target_player):
        """更新秃鹫移动逻辑"""
        if enemy['state'] == 'patrol':
            # 巡逻状态：在指定高度范围内飞行
            patrol_distance = abs(enemy['x'] - enemy['patrol_start_x'])
            
            # 如果超出巡逻范围，改变方向
            if patrol_distance >= enemy['patrol_range']:
                enemy['patrol_direction'] *= -1
            
            # 水平移动
            enemy['vel_x'] = enemy['speed'] * enemy['patrol_direction']
            enemy['facing_right'] = enemy['patrol_direction'] > 0
            
            # 垂直波动飞行
            flight_center = (enemy['flight_height_min'] + enemy['flight_height_max']) / 2
            wave_amplitude = (enemy['flight_height_max'] - enemy['flight_height_min']) / 4
            target_y = flight_center + math.sin(time.time() * 2) * wave_amplitude
            
            # 向目标高度移动
            y_diff = target_y - enemy['y']
            if abs(y_diff) > 5:
                enemy['vel_y'] = (y_diff / abs(y_diff)) * enemy['speed'] * 0.5
            else:
                enemy['vel_y'] = 0
                
            enemy['current_animation'] = 'move'
            
        elif enemy['state'] == 'chase' and target_player:
            # 追击状态：直接向玩家飞行
            direction_x = target_player['x'] - enemy['x']
            direction_y = target_player['y'] - enemy['y']
            distance = math.sqrt(direction_x**2 + direction_y**2)
            
            if distance > 20:  # 避免过度接近
                # 计算移动向量
                enemy['vel_x'] = (direction_x / distance) * enemy['speed'] * 1.5
                enemy['vel_y'] = (direction_y / distance) * enemy['speed'] * 1.5
                enemy['facing_right'] = direction_x > 0
                
                # 计算旋转角度（斜向飞行）
                angle = math.atan2(direction_y, direction_x)
                enemy['rotation'] = math.degrees(angle)
                
                enemy['current_animation'] = 'move'
            else:
                # 接近目标时悬停
                enemy['vel_x'] *= 0.5
                enemy['vel_y'] *= 0.5
                enemy['rotation'] = 0
                enemy['current_animation'] = 'idle'
            
    def _update_enemy_physics(self, enemy, dt):
        """更新敌怪物理状态"""
        # 应用重力（除了飞行敌人）
        if enemy['type'] != 'vulture':
            enemy['vel_y'] += self.GRAVITY * dt * 60
        
        # 更新位置
        enemy['x'] += enemy['vel_x'] * dt * 60
        enemy['y'] += enemy['vel_y'] * dt * 60
        
        # 简单的平台碰撞检测（基于地图数据）
        if enemy['type'] != 'vulture':  # 飞行敌人不需要地面碰撞
            self._check_enemy_platform_collision(enemy)
        
        # 边界检测
        if enemy['x'] < 0:
            enemy['x'] = 0
            enemy['vel_x'] = 0
            if enemy['type'] == 'slime':
                enemy['patrol_direction'] *= -1
        elif enemy['x'] > 2000:  # 假设地图宽度
            enemy['x'] = 2000
            enemy['vel_x'] = 0
            if enemy['type'] == 'slime':
                enemy['patrol_direction'] *= -1
        
        # 防止敌人掉出地图
        if enemy['y'] > 1000:  # 假设地图高度
            enemy['y'] = 1000
            enemy['vel_y'] = 0
            enemy['on_ground'] = True
    
    def _check_enemy_platform_collision(self, enemy):
        """检查敌人与平台的碰撞"""
        enemy['on_ground'] = False
        enemy_width = 48  # 敌人宽度
        enemy_height = 48  # 敌人高度
        
        # 碰撞检测已正常工作，移除调试信息
        
        # 检查与所有平台的碰撞
        for platform in self.platforms:
            # 检查水平重叠
            if (enemy['x'] + enemy_width > platform['x'] and 
                enemy['x'] < platform['x'] + platform['width']):
                
                # 检查垂直碰撞（从上方落下）
                if (enemy['vel_y'] >= 0 and 
                    enemy['y'] < platform['y'] and 
                    enemy['y'] + enemy_height > platform['y'] - 5):
                    
                    enemy['y'] = platform['y'] - enemy_height
                    enemy['vel_y'] = 0
                    enemy['on_ground'] = True
                    break
                
                # 检查从下方撞击平台
                elif (enemy['vel_y'] < 0 and 
                      enemy['y'] >= platform['y'] + platform['height'] - 10 and 
                      enemy['y'] <= platform['y'] + platform['height'] + 10):
                    
                    enemy['y'] = platform['y'] + platform['height']
                    enemy['vel_y'] = 0
                    break
            
            # 检查水平碰撞（左右撞墙）
            if (enemy['y'] + enemy_height > platform['y'] and 
                enemy['y'] < platform['y'] + platform['height']):
                
                # 从左侧撞击
                if (enemy['vel_x'] > 0 and 
                    enemy['x'] + enemy_width <= platform['x'] + 10 and 
                    enemy['x'] + enemy_width >= platform['x'] - 10):
                    
                    enemy['x'] = platform['x'] - enemy_width
                    enemy['vel_x'] = 0
                    if enemy['type'] == 'slime':
                        enemy['patrol_direction'] *= -1
                    break
                
                # 从右侧撞击
                elif (enemy['vel_x'] < 0 and 
                      enemy['x'] >= platform['x'] + platform['width'] - 10 and 
                      enemy['x'] <= platform['x'] + platform['width'] + 10):
                    
                    enemy['x'] = platform['x'] + platform['width']
                    enemy['vel_x'] = 0
                    if enemy['type'] == 'slime':
                        enemy['patrol_direction'] *= -1
                    break
            
    def get_all_enemies_data(self):
        """获取所有敌怪的同步数据"""
        enemies_data = []
        for enemy_id, enemy in self.enemies.items():
            enemy_sync_data = {
                'enemy_id': enemy_id,
                'type': enemy['type'],
                'variant': enemy['variant'],
                'x': enemy['x'],
                'y': enemy['y'],
                'vel_x': enemy['vel_x'],
                'vel_y': enemy['vel_y'],
                'facing_right': enemy['facing_right'],
                'state': enemy['state'],
                'current_animation': enemy['current_animation'],
                'frame_index': enemy['frame_index'],
                'health': enemy['health'],
                'attack_power': enemy['attack_power'],
                'speed': enemy['speed'],
                'patrol_range': enemy['patrol_range'],
                'aggro_range': enemy['aggro_range']
            }
            
            # 添加特殊属性
            if enemy['type'] == 'vulture' and 'rotation' in enemy:
                enemy_sync_data['rotation'] = enemy['rotation']
            
            enemies_data.append(enemy_sync_data)
        return enemies_data
        
    def get_all_players_data(self):
        """获取所有玩家的同步数据"""
        players_data = []
        for player_id, player in self.players.items():
            players_data.append({
                'player_id': player_id,
                'x': player['x'],
                'y': player['y'],
                'vel_x': player.get('vel_x', 0),
                'vel_y': player.get('vel_y', 0),
                'facing_right': player['facing_right'],
                'on_ground': player['on_ground'],
                'character_name': player['character_name'],
                'player_name': player['player_name'],
                'health': player['health']
            })
        return players_data

class NetworkServer:
    def __init__(self, host='localhost', port=12345):
        self.host = host
        self.port = port
        self.socket = None
        self.clients = {}
        self.running = False
        self.connected_addresses = set()  # 跟踪已连接的地址，防止重复连接
        self.host_player_id = None  # 房主玩家ID
        
        # 游戏对象池
        self.game_pool = GameObjectPool()
        self.last_sync_time = time.time()
        self.sync_interval = 1.0 / 60  # 60 FPS同步
    
    def start(self):
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.socket.bind((self.host, self.port))
            self.socket.listen(5)
            self.running = True
            
            print(f"服务器启动在 {self.host}:{self.port}")
            
            # 启动游戏循环线程
            game_loop_thread = threading.Thread(target=self._game_loop)
            game_loop_thread.daemon = True
            game_loop_thread.start()
            
            while self.running:
                try:
                    client_socket, address = self.socket.accept()
                    
                    # 检查是否是重复连接（同一个IP和端口）
                    if address in self.connected_addresses:
                        print(f"拒绝重复连接: {address}")
                        client_socket.close()
                        continue
                    
                    # 生成唯一的玩家ID
                    player_id = str(uuid.uuid4())[:8]  # 使用UUID的前8位作为玩家ID
                    
                    # 确保ID唯一性
                    while player_id in self.clients:
                        player_id = str(uuid.uuid4())[:8]
                    
                    # 如果这是第一个连接的玩家，设为房主
                    is_host = len(self.clients) == 0
                    if is_host:
                        self.host_player_id = player_id
                    
                    self.clients[player_id] = {
                        'socket': client_socket,
                        'address': address,
                        'last_update': time.time(),
                        'is_host': is_host
                    }
                    
                    # 记录已连接的地址
                    self.connected_addresses.add(address)
                    
                    # 添加玩家到游戏对象池
                    self.game_pool.add_player(player_id, {'player_name': f'玩家{len(self.clients)}'})
                    
                    # 发送玩家ID和房主状态
                    welcome_msg = json.dumps({
                        'type': 'player_id', 
                        'id': player_id,
                        'is_host': is_host
                    }) + '\n'
                    client_socket.send(welcome_msg.encode('utf-8'))
                    
                    # 向新客户端发送当前所有玩家的信息
                    for existing_player_id, existing_client_info in self.clients.items():
                        if existing_player_id != player_id and 'player_name' in existing_client_info:
                            existing_player_msg = {
                                'type': 'player_update',
                                'player_id': existing_player_id,
                                'player_name': existing_client_info.get('player_name', '未命名'),
                                'character_name': existing_client_info.get('character_name', '未选择'),
                                'timestamp': time.time()
                            }
                            try:
                                client_socket.send((json.dumps(existing_player_msg) + '\n').encode('utf-8'))
                            except:
                                pass
                    
                    # 启动客户端处理线程
                    client_thread = threading.Thread(
                        target=self._handle_client, 
                        args=(player_id, client_socket)
                    )
                    client_thread.daemon = True
                    client_thread.start()
                    
                    print(f"玩家 {player_id} 从 {address} 连接")
                    
                except Exception as e:
                    if self.running:
                        print(f"接受连接失败: {e}")
        
        except Exception as e:
            print(f"服务器启动失败: {e}")
    
    def send_room_disbanded_message(self):
        """主动发送房间解散消息给所有客户端"""
        if not self.clients:
            print("没有客户端连接，无需发送解散消息")
            return
            
        # 获取所有客户端列表
        all_clients = list(self.clients.items())
        successful_sends = 0
        
        print(f"准备向 {len(all_clients)} 个客户端发送房间解散消息")
        
        for player_id, client_info in all_clients:
            try:
                client_socket = client_info['socket']
                if client_socket and not client_socket._closed:
                    message = json.dumps({
                        'type': 'room_disbanded',
                        'message': '房主离开，房间已解散'
                    }) + '\n'
                    client_socket.send(message.encode('utf-8'))
                    successful_sends += 1
                    print(f"成功向客户端 {player_id} 发送解散消息")
                else:
                    print(f"客户端 {player_id} 的socket已失效")
            except Exception as e:
                print(f"向客户端 {player_id} 发送解散消息失败: {e}")
        
        print(f"房间解散消息发送完成，成功发送给 {successful_sends} 个客户端")
        
        # 等待一段时间确保消息发送完成
        time.sleep(1)
    
    def stop(self):
        self.running = False
        
        # 先发送房间解散消息
        self.send_room_disbanded_message()
        
        # 关闭所有客户端连接
        # 先复制键列表，避免在迭代过程中修改字典
        client_ids = list(self.clients.keys())
        for player_id in client_ids:
            try:
                if player_id in self.clients:
                    self.clients[player_id]['socket'].close()
            except:
                pass
        
        # 清理所有连接记录
        self.clients.clear()
        self.connected_addresses.clear()
        
        if self.socket:
            try:
                self.socket.close()
            except:
                pass
        
        print("服务器已停止")
    
    def _game_loop(self):
        """游戏主循环，定期更新游戏对象池并同步数据"""
        while self.running:
            try:
                current_time = time.time()
                
                # 更新游戏对象池
                self.game_pool.update_game_objects()
                
                # 定期同步敌人数据
                if current_time - self.last_sync_time >= self.sync_interval:
                    self._sync_enemies_data()
                    self.last_sync_time = current_time
                
                # 控制循环频率
                time.sleep(1.0 / 60)  # 60 FPS
                
            except Exception as e:
                print(f"游戏循环错误: {e}")
                time.sleep(0.1)
    
    def _sync_enemies_data(self):
        """同步敌人数据给所有客户端"""
        if not self.clients:
            return
            
        enemies_data = self.game_pool.get_all_enemies_data()
        if enemies_data:
            sync_message = {
                'type': 'enemies_sync',
                'enemies': enemies_data,
                'timestamp': time.time()
            }
            self._broadcast_to_all(sync_message)
    
    def _handle_client(self, player_id, client_socket):
        buffer = ""
        
        try:
            while self.running:
                data = client_socket.recv(1024).decode('utf-8')
                if not data:
                    break
                
                buffer += data
                while '\n' in buffer:
                    line, buffer = buffer.split('\n', 1)
                    if line.strip():
                        message = json.loads(line)
                        self._process_message(player_id, message)
        
        except Exception as e:
            print(f"处理客户端 {player_id} 失败: {e}")
        
        finally:
            self._disconnect_client(player_id)
    
    def add_enemy_to_pool(self, enemy_data):
        """添加敌人到游戏对象池"""
        enemy_id = str(uuid.uuid4())[:8]
        self.game_pool.add_enemy(enemy_id, enemy_data)
        return enemy_id
    
    def remove_enemy_from_pool(self, enemy_id):
        """从游戏对象池移除敌人"""
        self.game_pool.remove_enemy(enemy_id)
    
    def _process_message(self, player_id, message):
        if message['type'] == 'player_update':
            # 更新客户端信息
            if player_id in self.clients:
                self.clients[player_id]['last_update'] = time.time()
            
            # 更新服务端游戏对象池中的玩家数据
            player_data = {
                'x': message.get('x', 0),
                'y': message.get('y', 0),
                'vel_x': message.get('vel_x', 0),
                'vel_y': message.get('vel_y', 0),
                'facing_right': message.get('facing_right', True),
                'on_ground': message.get('on_ground', False),
                'character_name': message.get('character_name', '哈基为'),
                'player_name': message.get('player_name', '玩家'),
                'health': message.get('health', 100)
            }
            self.game_pool.update_player(player_id, player_data)
            
            # 转发给其他玩家
            forward_msg = message.copy()
            forward_msg['player_id'] = player_id
            
            self._broadcast_to_others(player_id, forward_msg)
        
        elif message['type'] == 'character_selection':
            # 更新客户端角色信息
            if player_id in self.clients:
                self.clients[player_id]['character_name'] = message['character_name']
                self.clients[player_id]['player_name'] = message['player_name']
                self.clients[player_id]['last_update'] = time.time()
            
            # 转发给其他玩家
            forward_msg = message.copy()
            forward_msg['player_id'] = player_id
            
            self._broadcast_to_others(player_id, forward_msg)
            print(f"服务器: 玩家 {player_id} 选择了角色 {message['character_name']}")
        
        elif message['type'] == 'game_start':
            # 广播游戏开始消息给所有玩家
            forward_msg = message.copy()
            forward_msg['player_id'] = player_id
            
            self._broadcast_to_all(forward_msg)
            print(f"服务器: 玩家 {player_id} 开始了游戏，通知所有玩家")
        
        elif message['type'] == 'return_to_waiting_room':
            # 广播返回等待房间消息给所有玩家
            forward_msg = message.copy()
            forward_msg['player_id'] = player_id
            
            self._broadcast_to_all(forward_msg)
            print(f"服务器: 玩家 {player_id} 返回等待房间，通知所有玩家")
        
        elif message['type'] == 'map_selection':
            # 广播地图选择消息给其他玩家（不包括发送者）
            forward_msg = message.copy()
            forward_msg['player_id'] = player_id
            
            self._broadcast_to_others(player_id, forward_msg)
        
        elif message['type'] == 'portal_trigger':
            # 广播传送门触发消息给所有玩家
            forward_msg = message.copy()
            forward_msg['player_id'] = player_id
            
            self._broadcast_to_all(forward_msg)
            print(f"服务器: 玩家 {player_id} 触发传送门到 {message.get('target_map', '未知地图')}，通知所有玩家")
        
        elif message['type'] == 'map_change':
            # 广播地图切换消息给其他玩家
            forward_msg = message.copy()
            forward_msg['player_id'] = player_id
            
            self._broadcast_to_others(player_id, forward_msg)
            print(f"服务器: 房主 {player_id} 切换地图到 {message.get('target_map', '未知地图')}，通知其他玩家")
        
        elif message['type'] == 'player_death':
            # 广播玩家死亡消息给所有玩家
            forward_msg = message.copy()
            forward_msg['player_id'] = player_id
            
            self._broadcast_to_all(forward_msg)
            print(f"服务器: 玩家 {player_id} ({message.get('player_name', '未知')}) 死亡，通知所有玩家")
        
        elif message['type'] == 'enemy_death':
            # 广播敌人死亡消息给所有玩家
            forward_msg = message.copy()
            forward_msg['player_id'] = player_id
            
            self._broadcast_to_all(forward_msg)
            print(f"服务器: 玩家 {player_id} 击败了敌人 {message.get('enemy_type', '未知')}，通知所有玩家")
        
        elif message['type'] == 'player_damage':
            # 转发玩家伤害信息给目标玩家
            target_player_id = message.get('target_player_id', '')
            damage = message.get('damage', 0)
            
            if target_player_id in self.clients:
                damage_msg = {
                    'type': 'player_damage_received',
                    'damage': damage,
                    'from_player_id': player_id,
                    'timestamp': time.time()
                }
                
                try:
                    target_socket = self.clients[target_player_id]['socket']
                    target_socket.send((json.dumps(damage_msg) + '\n').encode('utf-8'))
                    print(f"服务器: 转发伤害信息给玩家 {target_player_id}，伤害值: {damage}")
                except Exception as e:
                    print(f"转发伤害信息失败: {e}")
            else:
                print(f"服务器: 目标玩家 {target_player_id} 不存在，无法转发伤害信息")
        
        elif message['type'] == 'enemy_update':
            # 广播敌人状态更新给其他玩家
            forward_msg = message.copy()
            forward_msg['player_id'] = player_id
            
            self._broadcast_to_others(player_id, forward_msg)
        
        elif message['type'] == 'enemies_batch_update':
            # 广播批量敌人状态更新给其他玩家
            forward_msg = message.copy()
            forward_msg['player_id'] = player_id
            
            # 同时更新服务端游戏对象池中的敌人数据
            enemies_data = message.get('enemies', [])
            for enemy_data in enemies_data:
                enemy_id = enemy_data.get('enemy_id', '')
                if enemy_id in self.game_pool.enemies:
                    self.game_pool.enemies[enemy_id].update({
                        'x': enemy_data.get('x', self.game_pool.enemies[enemy_id]['x']),
                        'y': enemy_data.get('y', self.game_pool.enemies[enemy_id]['y']),
                        'vel_x': enemy_data.get('vel_x', self.game_pool.enemies[enemy_id]['vel_x']),
                        'vel_y': enemy_data.get('vel_y', self.game_pool.enemies[enemy_id]['vel_y']),
                        'facing_right': enemy_data.get('facing_right', self.game_pool.enemies[enemy_id]['facing_right']),
                        'state': enemy_data.get('state', self.game_pool.enemies[enemy_id]['state']),
                        'health': enemy_data.get('health', self.game_pool.enemies[enemy_id]['health']),
                        'last_update': time.time()
                    })
            
            self._broadcast_to_others(player_id, forward_msg)
        
        elif message['type'] == 'enemy_creation':
            # 处理敌人创建请求
            enemy_data = message.get('enemy_data', {})
            enemy_id = self.add_enemy_to_pool(enemy_data)
            print(f"服务器: 玩家 {player_id} 创建了敌人 {enemy_data.get('enemy_type', '未知')}，ID: {enemy_id}")
        
        elif message['type'] == 'enemy_damage':
            # 处理敌人受伤信息
            enemy_id = message.get('enemy_id', '')
            damage = message.get('damage', 0)
            current_health = message.get('current_health', 0)
            
            # 更新服务端游戏对象池中的敌人血量
            if enemy_id in self.game_pool.enemies:
                self.game_pool.enemies[enemy_id]['health'] = current_health
                print(f"服务器: 敌人 {enemy_id} 受到 {damage} 点伤害，剩余血量: {current_health}")
                
                # 检查敌人是否死亡
                if current_health <= 0:
                    # 广播敌人死亡消息
                    death_msg = {
                        'type': 'enemy_death',
                        'enemy_id': enemy_id,
                        'enemy_type': self.game_pool.enemies[enemy_id].get('type', '未知敌人'),
                        'player_id': player_id,
                        'timestamp': time.time()
                    }
                    self._broadcast_to_all(death_msg)
                    
                    # 从游戏对象池中移除死亡的敌人
                    self.remove_enemy_from_pool(enemy_id)
                    print(f"服务器: 敌人 {enemy_id} 已死亡，从游戏对象池中移除")
            else:
                print(f"服务器: 敌人 {enemy_id} 不存在，无法应用伤害")
            
        elif message['type'] == 'map_data':
            # 处理地图数据设置请求
            map_data = message.get('map_data', {})
            self.game_pool.set_map_data(map_data)
            print(f"服务器: 设置地图数据 {map_data.get('name', '未知地图')}，生成了 {len(self.game_pool.enemies)} 个敌人")
            
            # 广播地图设置完成消息给所有客户端
            map_ready_message = {
                'type': 'map_ready',
                'map_name': map_data.get('name', '未知地图'),
                'enemies_count': len(self.game_pool.enemies)
            }
            self._broadcast_to_all(map_ready_message)
    
    def _broadcast_to_others(self, sender_id, message):
        message_str = json.dumps(message) + '\n'
        
        for player_id, client_info in list(self.clients.items()):
            if player_id != sender_id:
                try:
                    client_info['socket'].send(message_str.encode('utf-8'))
                except:
                    self._disconnect_client(player_id)
    
    def _broadcast_to_all(self, message):
        """向所有连接的客户端广播消息"""
        message_str = json.dumps(message) + '\n'
        
        # 创建客户端字典的副本以避免并发修改问题
        clients_copy = dict(self.clients)
        successful_sends = 0
        for client_id, client_info in clients_copy.items():
            try:
                # 检查socket是否仍然有效
                socket_obj = client_info['socket']
                if socket_obj.fileno() != -1:  # socket仍然有效
                    socket_obj.send(message_str.encode('utf-8'))
                    successful_sends += 1
                    if message.get('type') == 'room_disbanded':
                        print(f"成功向客户端 {client_id} 发送房间解散消息")
            except Exception as e:
                print(f"向客户端 {client_id} 发送消息失败: {e}")
        
        if message.get('type') == 'room_disbanded':
            print(f"房间解散消息发送完成，成功发送给 {successful_sends} 个客户端")
    
    def _disconnect_client(self, player_id):
        if player_id in self.clients:
            client_info = self.clients[player_id]
            address = client_info['address']
            is_host = client_info.get('is_host', False)
            
            # 如果房主断开连接，先处理房间解散逻辑
            if is_host and player_id == self.host_player_id:
                print(f"房主 {player_id} 已断开连接，准备解散房间")
                
                # 立即发送解散消息给所有其他客户端（在删除任何客户端之前）
                disbanded_msg = {
                    'type': 'room_disbanded',
                    'reason': 'host_left',
                    'message': '房主离开，房间已解散'
                }
                
                # 获取所有非房主客户端
                other_clients = [(pid, client) for pid, client in self.clients.items() if pid != player_id]
                print(f"向 {len(other_clients)} 个剩余客户端发送解散消息")
                
                # 向每个其他客户端发送消息
                successful_sends = 0
                for client_id, client_data in other_clients:
                    try:
                        client_socket = client_data['socket']
                        if client_socket.fileno() != -1:  # 检查socket是否有效
                            message_str = json.dumps(disbanded_msg) + '\n'  # 添加换行符
                            client_socket.send(message_str.encode('utf-8'))
                            successful_sends += 1
                            print(f"成功向客户端 {client_id} 发送解散消息")
                        else:
                            print(f"客户端 {client_id} 的socket已失效")
                    except Exception as e:
                        print(f"向客户端 {client_id} 发送解散消息失败: {e}")
                
                print(f"房间解散消息发送完成，成功发送给 {successful_sends} 个客户端")
                
                # 重置房主ID
                self.host_player_id = None
                
                # 延迟停止服务器，给客户端时间处理消息
                import threading
                def delayed_stop():
                    import time
                    time.sleep(3)  # 增加到3秒确保消息处理完成
                    print("延迟停止服务器")
                    self.stop()
                
                stop_thread = threading.Thread(target=delayed_stop, daemon=True)
                stop_thread.start()
            
            # 关闭socket
            try:
                client_info['socket'].close()
            except:
                pass
            
            # 从客户端列表中移除（如果还存在的话）
            if player_id in self.clients:
                del self.clients[player_id]
            
            # 从已连接地址集合中移除
            self.connected_addresses.discard(address)
            
            # 如果不是房主断开连接，通知其他玩家
            if not (is_host and player_id == self.host_player_id):
                # 普通玩家断开连接
                disconnect_msg = {
                    'type': 'player_disconnect',
                    'player_id': player_id
                }
                self._broadcast_to_all(disconnect_msg)
            
            print(f"玩家 {player_id} 已断开连接")

def start_server():
    """启动服务器的便捷函数"""
    server = NetworkServer()
    try:
        server.start()
    except KeyboardInterrupt:
        print("\n正在关闭服务器...")
        server.stop()

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "server":
        start_server()
    else:
        print("使用方法:")
        print("  python network.py server  # 启动服务器")
        print("  在main.py中使用NetworkClient连接")