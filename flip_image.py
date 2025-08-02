#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
图片翻转处理工具
用于对PNG图片进行水平翻转处理
"""

import os
from PIL import Image

def flip_image_horizontal(input_path, output_path=None):
    """
    对图片进行水平翻转
    
    Args:
        input_path (str): 输入图片路径
        output_path (str, optional): 输出图片路径，如果为None则覆盖原文件
    """
    try:
        # 检查输入文件是否存在
        if not os.path.exists(input_path):
            print(f"错误：文件 {input_path} 不存在")
            return False
            
        # 打开图片
        with Image.open(input_path) as img:
            # 水平翻转
            flipped_img = img.transpose(Image.FLIP_LEFT_RIGHT)
            
            # 确定输出路径
            if output_path is None:
                # 如果没有指定输出路径，在原文件名后添加_flipped
                name, ext = os.path.splitext(input_path)
                output_path = f"{name}_flipped{ext}"
            
            # 保存翻转后的图片
            flipped_img.save(output_path)
            print(f"成功翻转图片：{input_path} -> {output_path}")
            return True
            
    except Exception as e:
        print(f"处理图片时出错：{e}")
        return False

def flip_image_vertical(input_path, output_path=None):
    """
    对图片进行垂直翻转
    
    Args:
        input_path (str): 输入图片路径
        output_path (str, optional): 输出图片路径，如果为None则覆盖原文件
    """
    try:
        # 检查输入文件是否存在
        if not os.path.exists(input_path):
            print(f"错误：文件 {input_path} 不存在")
            return False
            
        # 打开图片
        with Image.open(input_path) as img:
            # 垂直翻转
            flipped_img = img.transpose(Image.FLIP_TOP_BOTTOM)
            
            # 确定输出路径
            if output_path is None:
                # 如果没有指定输出路径，在原文件名后添加_vflipped
                name, ext = os.path.splitext(input_path)
                output_path = f"{name}_vflipped{ext}"
            
            # 保存翻转后的图片
            flipped_img.save(output_path)
            print(f"成功垂直翻转图片：{input_path} -> {output_path}")
            return True
            
    except Exception as e:
        print(f"处理图片时出错：{e}")
        return False

def main():
    """
    主函数 - 处理指定的PNG文件
    """
    # 要处理的图片路径
    image_paths = [
        "d:/Project/Hajimi/boss/milkdragon/running.png",
        "d:/Project/Hajimi/boss/milkdragon/downing.png"
    ]
    
    print("开始处理图片翻转...")
    print("=" * 50)
    
    for img_path in image_paths:
        print(f"\n处理图片: {img_path}")
        
        # 水平翻转
        success_h = flip_image_horizontal(img_path)
        
        # 垂直翻转
        success_v = flip_image_vertical(img_path)
        
        if success_h and success_v:
            print(f"✓ {os.path.basename(img_path)} 处理完成")
        else:
            print(f"✗ {os.path.basename(img_path)} 处理失败")
    
    print("\n" + "=" * 50)
    print("图片翻转处理完成！")

if __name__ == "__main__":
    main()