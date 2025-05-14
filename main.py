#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
基于嵌入式AI的ROI区域视频传输系统启动脚本
使用YOLOv11模型进行物体检测和区域感兴趣编码

主入口文件，负责启动应用程序。
"""
import os
import sys
from src.python.cli.app import AIVideoApp


def main():
    """主函数，启动应用程序"""
    # 确保models目录存在
    models_dir = os.path.abspath('models')
    if not os.path.exists(models_dir):
        os.makedirs(models_dir)
        print(f"已创建models目录: {models_dir}")
    
    # 设置环境变量，指定模型下载路径
    os.environ['YOLO_CONFIG_DIR'] = models_dir
    
    # 直接设置Ultralytics模型权重目录
    try:
        from ultralytics import SETTINGS
        SETTINGS['weights_dir'] = models_dir
        print(f"已设置YOLOv11模型下载目录: {models_dir}")
    except ImportError:
        print("警告: 无法导入ultralytics模块，请确保已安装")
    
    print("============= 启动基于嵌入式AI的ROI区域视频传输系统 =============")
    print("使用YOLOv11模型进行物体检测和区域感兴趣编码")
    print("模型文件将自动下载到项目models目录")
    print("================================================================")
    
    # 创建并运行应用
    app = AIVideoApp()
    app.run()


if __name__ == "__main__":
    # 设置工作目录为脚本所在目录，确保生成的models目录在正确位置
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    print(f"工作目录设置为: {script_dir}")
    
    # 运行主函数
    main()
