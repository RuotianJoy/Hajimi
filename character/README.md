# 角色系统说明

## 概述

角色系统已完全数据化，所有角色配置都存储在JSON文件中，便于管理和扩展。

## 文件结构

```
character/
├── characters.json     # 角色索引配置文件
├── hajimi.json        # 哈基为角色配置
├── hajiyang.json      # 哈基阳角色配置
├── warrior.json       # 战士角色配置
└── README.md          # 本说明文件
```

## 配置文件说明

### characters.json (角色索引)

主配置文件，管理所有角色的启用状态和加载顺序：

- `characters`: 角色列表
  - `id`: 角色唯一标识符
  - `file`: 对应的JSON配置文件名
  - `enabled`: 是否启用该角色
  - `default`: 是否为默认角色

### 角色配置文件格式

每个角色的JSON文件包含以下字段：

```json
{
  "id": "角色ID",
  "name": "角色名称",
  "description": "角色描述",
  "type": "角色类型",
  "color": [R, G, B],
  "stats": {
    "attack_power": 攻击力,
    "speed_multiplier": 速度倍数,
    "defense": 防御力,
    "jump_multiplier": 跳跃倍数,
    "max_health": 最大生命值,
    "star_ratings": {
      "attack": 攻击星级(1-5),
      "speed": 速度星级(1-5),
      "defense": 防御星级(1-5),
      "jump": 跳跃星级(1-5)
    }
  },
  "animations": {
    "gif_folder": "动画文件夹路径",
    "files": {
      "idle": "待机动画文件",
      "move": "移动动画文件",
      "sprint": "冲刺动画文件"
    }
  },
  "gameplay": {
    "character_class": "角色职业",
    "special_abilities": ["特殊能力列表"],
    "unlock_requirements": {
      "default": 是否默认解锁,
      "level_required": 解锁所需等级
    }
  }
}
```

## 角色类型

- **平衡型**: 各项属性均衡
- **敏捷型**: 速度和跳跃力突出
- **坦克型**: 攻击力和防御力突出

## 属性说明

- **attack_power**: 攻击力 (1-5)
- **speed_multiplier**: 速度倍数 (0.5-2.0)
- **defense**: 防御力 (1-5)
- **jump_multiplier**: 跳跃倍数 (0.5-2.0)
- **max_health**: 最大生命值 (50-200)

## 添加新角色

1. 在 `character/` 目录下创建新的JSON配置文件
2. 按照上述格式填写角色数据
3. 在 `characters.json` 中添加角色索引信息
4. 重启游戏即可加载新角色

## 注意事项

- 所有JSON文件必须使用UTF-8编码
- 角色ID必须唯一
- 动画文件夹路径相对于游戏根目录
- 修改配置后需要重启游戏才能生效
- 如果JSON文件格式错误，系统会自动使用默认角色配置