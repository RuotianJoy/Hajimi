# -*- coding: utf-8 -*-
"""
武器图片裁剪工具
专门用于处理nadir武器图片，去除多余部分并减少高度
"""

import os
from PIL import Image

def crop_nadir_weapon(input_path, output_path=None):
    """
    裁剪nadir武器图片，去除多余部分并减少高度
    
    Args:
        input_path (str): 输入图片路径
        output_path (str): 输出图片路径，如果为None则覆盖原文件
    """
    try:
        # 打开图片
        with Image.open(input_path) as img:
            # 转换为RGBA模式以保持透明度
            if img.mode != 'RGBA':
                img = img.convert('RGBA')
            
            # 获取图片尺寸
            width, height = img.size
            print(f"原始图片尺寸: {width} x {height}")
            
            # 获取图片数据
            pixels = img.load()
            
            # 找到非透明像素的边界
            min_x, min_y = width, height
            max_x, max_y = 0, 0
            
            for y in range(height):
                for x in range(width):
                    # 检查像素是否非透明（alpha > 0）
                    if len(pixels[x, y]) >= 4 and pixels[x, y][3] > 0:
                        min_x = min(min_x, x)
                        max_x = max(max_x, x)
                        min_y = min(min_y, y)
                        max_y = max(max_y, y)
            
            # 如果没有找到非透明像素，返回错误
            if min_x >= width or min_y >= height:
                print("错误：图片中没有找到非透明像素")
                return False
            
            # 添加一些边距
            padding = 5
            crop_left = max(0, min_x - padding)
            crop_top = max(0, min_y - padding)
            crop_right = min(width, max_x + padding + 1)
            crop_bottom = min(height, max_y + padding + 1)
            
            # 计算裁剪后的尺寸
            crop_width = crop_right - crop_left
            crop_height = crop_bottom - crop_top
            
            print(f"检测到的内容区域: ({min_x}, {min_y}) 到 ({max_x}, {max_y})")
            print(f"裁剪区域: ({crop_left}, {crop_top}) 到 ({crop_right}, {crop_bottom})")
            print(f"裁剪后尺寸: {crop_width} x {crop_height}")
            
            # 裁剪图片
            cropped_img = img.crop((crop_left, crop_top, crop_right, crop_bottom))
            
            # 进一步减少高度（如果高度仍然较大）
            if crop_height > 100:  # 如果高度超过100像素
                # 计算新的高度（减少20%）
                new_height = int(crop_height * 0.8)
                new_width = crop_width  # 保持宽度不变
                
                # 使用高质量重采样缩放
                cropped_img = cropped_img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                print(f"进一步缩减高度到: {new_width} x {new_height}")
            
            # 确定输出路径
            if output_path is None:
                output_path = input_path
            
            # 保存处理后的图片
            cropped_img.save(output_path, 'PNG')
            print(f"图片处理完成: {output_path}")
            
            return True
            
    except Exception as e:
        print(f"处理图片时出错: {e}")
        return False

def main():
    """主函数"""
    # 目标文件路径
    input_file = "d:/Project/Hajimi/weapon/nadir/nadir_rotated_45_backup.png"
    
    # 检查文件是否存在
    if not os.path.exists(input_file):
        print(f"错误：文件不存在 {input_file}")
        return
    
    print(f"开始处理文件: {input_file}")
    
    # 创建备份
    backup_file = input_file.replace(".png", "_backup.png")
    try:
        with Image.open(input_file) as img:
            img.save(backup_file, 'PNG')
        print(f"已创建备份文件: {backup_file}")
    except Exception as e:
        print(f"创建备份失败: {e}")
        return
    
    # 处理图片
    success = crop_nadir_weapon(input_file)
    
    if success:
        print("\n处理完成！")
        print(f"原文件已更新: {input_file}")
        print(f"备份文件: {backup_file}")
    else:
        print("\n处理失败！")

if __name__ == "__main__":
    main()