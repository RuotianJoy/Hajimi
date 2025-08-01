#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
图片处理工具
用于对游戏中的武器图片进行预处理，包括旋转、缩放等操作
"""

import os
import sys
import pygame
from PIL import Image

def get_resource_path(relative_path):
    """获取资源文件的绝对路径，兼容开发环境和PyInstaller打包环境"""
    try:
        # PyInstaller创建临时文件夹，并将路径存储在_MEIPASS中
        base_path = sys._MEIPASS
    except Exception:
        # 开发环境下使用当前脚本所在目录
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)

def rotate_image_pil(input_path, output_path, angle):
    """
    使用PIL库旋转图片
    
    Args:
        input_path (str): 输入图片路径
        output_path (str): 输出图片路径
        angle (float): 旋转角度（正数为逆时针，负数为顺时针）
    """
    try:
        # 打开图片
        with Image.open(input_path) as img:
            # 保持透明度
            if img.mode != 'RGBA':
                img = img.convert('RGBA')
            
            # 旋转图片（PIL中正数为逆时针，所以用负数实现顺时针）
            rotated_img = img.rotate(-angle, expand=True, fillcolor=(0, 0, 0, 0))
            
            # 保存图片
            rotated_img.save(output_path, 'PNG')
            print(f"图片旋转成功: {input_path} -> {output_path} (旋转角度: {angle}度)")
            
    except Exception as e:
        print(f"旋转图片失败: {e}")

def rotate_image_pygame(input_path, output_path, angle):
    """
    使用pygame库旋转图片
    
    Args:
        input_path (str): 输入图片路径
        output_path (str): 输出图片路径
        angle (float): 旋转角度（正数为逆时针，负数为顺时针）
    """
    try:
        # 初始化pygame（仅用于图像处理）
        pygame.init()
        
        # 加载图片
        image = pygame.image.load(input_path).convert_alpha()
        
        # 旋转图片
        rotated_image = pygame.transform.rotate(image, angle)
        
        # 保存图片
        pygame.image.save(rotated_image, output_path)
        print(f"图片旋转成功: {input_path} -> {output_path} (旋转角度: {angle}度)")
        
        pygame.quit()
        
    except Exception as e:
        print(f"旋转图片失败: {e}")

def process_nadir_weapon():
    """
    处理nadir武器图片，将其顺时针旋转45度
    """
    # 原始图片路径
    input_path = get_resource_path(os.path.join("weapon", "nadir", "nadir.png"))
    
    # 输出图片路径（添加_rotated后缀）
    output_dir = os.path.dirname(input_path)
    output_path = os.path.join(output_dir, "nadir_rotated_45.png")
    
    # 检查输入文件是否存在
    if not os.path.exists(input_path):
        print(f"错误: 找不到nadir武器图片文件: {input_path}")
        return False
    
    print(f"开始处理nadir武器图片...")
    print(f"输入文件: {input_path}")
    print(f"输出文件: {output_path}")
    
    # 使用PIL进行旋转（推荐，质量更好）
    try:
        rotate_image_pil(input_path, output_path, 45)  # 顺时针45度
        return True
    except ImportError:
        print("PIL库未安装，尝试使用pygame...")
        # 如果PIL不可用，使用pygame
        rotate_image_pygame(input_path, output_path, -45)  # pygame中负数为顺时针
        return True
    except Exception as e:
        print(f"处理失败: {e}")
        return False

def batch_process_weapons():
    """
    批量处理所有武器图片
    """
    weapons = [
        {
            "name": "nadir",
            "input": os.path.join("weapon", "nadir", "nadir.png"),
            "output": os.path.join("weapon", "nadir", "nadir_rotated_45.png"),
            "angle": 45
        },
        # 可以在这里添加更多武器的处理配置
    ]
    
    success_count = 0
    total_count = len(weapons)
    
    for weapon in weapons:
        input_path = get_resource_path(weapon["input"])
        output_path = get_resource_path(weapon["output"])
        
        if os.path.exists(input_path):
            try:
                rotate_image_pil(input_path, output_path, weapon["angle"])
                success_count += 1
            except Exception as e:
                print(f"处理 {weapon['name']} 失败: {e}")
        else:
            print(f"跳过 {weapon['name']}: 文件不存在 {input_path}")
    
    print(f"\n批量处理完成: {success_count}/{total_count} 个文件处理成功")

def main():
    """
    主函数
    """
    print("=== 武器图片处理工具 ===")
    print("1. 处理nadir武器 (旋转45度)")
    print("2. 批量处理所有武器")
    print("3. 退出")
    
    while True:
        try:
            choice = input("\n请选择操作 (1-3): ").strip()
            
            if choice == "1":
                process_nadir_weapon()
            elif choice == "2":
                batch_process_weapons()
            elif choice == "3":
                print("退出程序")
                break
            else:
                print("无效选择，请输入1-3")
                
        except KeyboardInterrupt:
            print("\n程序被用户中断")
            break
        except Exception as e:
            print(f"发生错误: {e}")

if __name__ == "__main__":
    main()