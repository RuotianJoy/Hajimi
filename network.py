import socket
import threading
import json
import time
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

class NetworkServer:
    def __init__(self, host='localhost', port=12345):
        self.host = host
        self.port = port
        self.socket = None
        self.clients = {}
        self.running = False
        self.connected_addresses = set()  # 跟踪已连接的地址，防止重复连接
        self.host_player_id = None  # 房主玩家ID
    
    def start(self):
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.socket.bind((self.host, self.port))
            self.socket.listen(5)
            self.running = True
            
            print(f"服务器启动在 {self.host}:{self.port}")
            
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
    
    def _process_message(self, player_id, message):
        if message['type'] == 'player_update':
            # 更新客户端信息
            if player_id in self.clients:
                self.clients[player_id]['last_update'] = time.time()
            
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
            print(f"服务器: 房主 {player_id} 选择了地图 {message.get('map_name', '未知')}，通知其他玩家")
    
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