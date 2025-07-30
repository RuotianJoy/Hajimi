import json
import os

class CharacterLoader:
    def __init__(self, character_dir="character/"):
        self.character_dir = character_dir
        self.characters = {}
        self.character_index = []
        self.load_characters()
    
    def load_characters(self):
        """从character目录加载所有角色配置"""
        try:
            # 加载角色索引文件
            index_path = os.path.join(self.character_dir, "characters.json")
            if os.path.exists(index_path):
                with open(index_path, 'r', encoding='utf-8') as f:
                    index_data = json.load(f)
                    self.character_index = index_data.get("characters", [])
            
            # 加载每个角色的配置文件
            for char_info in self.character_index:
                if char_info.get("enabled", True):
                    char_file = char_info.get("file")
                    if char_file:
                        char_path = os.path.join(self.character_dir, char_file)
                        if os.path.exists(char_path):
                            with open(char_path, 'r', encoding='utf-8') as f:
                                char_data = json.load(f)
                                self.characters[char_data["id"]] = char_data
                        else:
                            print(f"警告: 角色文件 {char_path} 不存在")
            
            print(f"成功加载 {len(self.characters)} 个角色")
            
        except Exception as e:
            print(f"加载角色配置时出错: {e}")
            # 如果加载失败，使用默认角色配置
            self._load_default_characters()
    
    def _load_default_characters(self):
        """加载默认角色配置（作为备用）"""
        self.characters = {
            "hajiwei": {
                "id": "hajiwei",
                "name": "哈基为",
                "description": "哈基米史上最高的山!!!",
                "color": [65, 105, 225],
                "stats": {
                    "attack_power": 3,
                    "speed_multiplier": 1.0,
                    "defense": 2,
                    "jump_multiplier": 1.0,
                    "max_health": 100
                },
                "animations": {
                    "gif_folder": "gif/CharacterOne/"
                }
            },
            "hajiyang": {
                "id": "hajiyang",
                "name": "哈基阳",
                "description": "哈基米史上最臭的石!!!",
                "color": [255, 100, 100],
                "stats": {
                    "attack_power": 2,
                    "speed_multiplier": 1.3,
                    "defense": 1,
                    "jump_multiplier": 1.2,
                    "max_health": 80
                },
                "animations": {
                    "gif_folder": "gif/CharacterThree/"
                }
            }
        }
        self.character_index = [
            {"id": "hajiwei", "file": "hajiwei.json", "enabled": True, "default": True},
            {"id": "hajiyang", "file": "hajiyang.json", "enabled": True, "default": False}
        ]
    
    def get_character_options(self):
        """获取角色选项列表，用于游戏界面显示"""
        options = []
        for char_info in self.character_index:
            if char_info.get("enabled", True):
                char_id = char_info["id"]
                if char_id in self.characters:
                    char_data = self.characters[char_id]
                    options.append({
                        "name": char_data["name"],
                        "color": tuple(char_data["color"]),
                        "description": char_data["description"],
                        "gif_folder": char_data["animations"]["gif_folder"]
                    })
        return options
    
    def get_character_by_index(self, index):
        """根据索引获取角色数据"""
        enabled_chars = [char for char in self.character_index if char.get("enabled", True)]
        if 0 <= index < len(enabled_chars):
            char_id = enabled_chars[index]["id"]
            return self.characters.get(char_id)
        return None
    
    def get_character_by_id(self, char_id):
        """根据ID获取角色数据"""
        return self.characters.get(char_id)
    
    def get_character_stats(self, char_id):
        """获取角色属性"""
        char_data = self.characters.get(char_id)
        if char_data:
            return char_data.get("stats", {})
        return {}
    
    def get_default_character_index(self):
        """获取默认角色的索引"""
        for i, char_info in enumerate(self.character_index):
            if char_info.get("enabled", True) and char_info.get("default", False):
                return i
        return 0  # 如果没有默认角色，返回第一个
    
    def reload_characters(self):
        """重新加载角色配置"""
        self.characters.clear()
        self.character_index.clear()
        self.load_characters()