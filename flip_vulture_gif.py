#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
秃鹫GIF翻转工具
用于翻转秃鹫飞行动画GIF，保持帧率相同，避免重影
"""

import os
from PIL import Image, ImageSequence

def flip_gif(input_path, output_path):
    """
    翻转GIF动画
    
    Args:
        input_path: 输入GIF文件路径
        output_path: 输出GIF文件路径
    """
    try:
        # 打开原始GIF
        with Image.open(input_path) as img:
            # 获取GIF信息
            duration = img.info.get('duration', 100)  # 默认100ms每帧
            loop = img.info.get('loop', 0)  # 循环次数
            
            # 处理每一帧
            frames = []
            durations = []
            
            for frame in ImageSequence.Iterator(img):
                # 水平翻转帧
                flipped_frame = frame.transpose(Image.FLIP_LEFT_RIGHT)
                
                # 转换为RGBA模式以保持透明度
                if flipped_frame.mode != 'RGBA':
                    flipped_frame = flipped_frame.convert('RGBA')
                
                frames.append(flipped_frame)
                
                # 获取当前帧的持续时间
                frame_duration = frame.info.get('duration', duration)
                durations.append(frame_duration)
            
            # 保存翻转后的GIF
            if frames:
                frames[0].save(
                    output_path,
                    save_all=True,
                    append_images=frames[1:],
                    duration=durations,
                    loop=loop,
                    optimize=True,
                    disposal=2  # 清除前一帧，避免重影
                )
                print(f"成功翻转GIF: {input_path} -> {output_path}")
                print(f"帧数: {len(frames)}, 平均帧率: {1000/sum(durations)*len(durations):.1f} FPS")
            else:
                print(f"错误: 无法读取GIF帧 {input_path}")
                
    except Exception as e:
        print(f"翻转GIF时出错: {e}")

def main():
    """主函数"""
    # 秃鹫GIF文件路径
    vulture_dir = "enemy/vulture"
    
    # 检查目录是否存在
    if not os.path.exists(vulture_dir):
        print(f"错误: 目录不存在 {vulture_dir}")
        return
    
    # 查找所有GIF文件
    gif_files = [f for f in os.listdir(vulture_dir) if f.lower().endswith('.gif')]
    
    if not gif_files:
        print(f"在 {vulture_dir} 中未找到GIF文件")
        return
    
    print(f"找到 {len(gif_files)} 个GIF文件:")
    for gif_file in gif_files:
        print(f"  - {gif_file}")
    
    # 处理每个GIF文件
    for gif_file in gif_files:
        input_path = os.path.join(vulture_dir, gif_file)
        
        # 生成输出文件名（添加_flipped后缀）
        name, ext = os.path.splitext(gif_file)
        output_filename = f"{name}_flipped{ext}"
        output_path = os.path.join(vulture_dir, output_filename)
        
        print(f"\n正在处理: {gif_file}")
        flip_gif(input_path, output_path)
    
    print("\n所有GIF文件处理完成！")
    print("\n接下来需要手动替换原文件或修改代码中的文件名引用。")

if __name__ == "__main__":
    main()