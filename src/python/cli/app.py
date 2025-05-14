#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
基于嵌入式AI的ROI区域视频传输系统的命令行界面应用
提供命令行交互界面，替代GUI界面
"""
import os
import threading
import time
import sys
from ..stream.camera import CameraStream
from ..yolo.processor import Processor
from ..stream.mode_handler import ClientHandler, ServerHandler, LocalHandler
from .mode_handler import CLIClientHandler, CLIServerHandler, CLILocalHandler


class AIVideoApp:
    """基于嵌入式AI的ROI区域视频传输系统的命令行应用类"""
    
    def __init__(self):
        """初始化应用"""
        self.camera_stream = None
        self.ai_processor = None
        self.handler = None
        
    def check_models(self):
        """检查模型文件是否可以使用
        
        注意：使用YOLOv11不需要预先下载模型文件，会自动下载到models目录
        """
        print("正在准备加载YOLOv11模型...")
        
        # 确保models目录存在
        if not os.path.exists('models'):
            try:
                os.makedirs('models')
                print("已创建models目录")
            except Exception as e:
                print(f"错误: 无法创建models目录: {e}")
                return False
        
        # 注意：环境变量已在main.py中设置
        # os.environ['YOLO_CONFIG_DIR'] = os.path.abspath('models')
                
        return True
        
    def setup_application(self, mode):
        """设置应用程序"""
        # 检查模型
        if not self.check_models():
            return False
        
        # 初始化相机流
        self.camera_stream = CameraStream(0)
        
        # 初始化AI处理器
        try:
            # 使用YOLOv11模型（无需指定.pt后缀）
            models_dir = os.path.abspath('models')
            model_path = os.path.join(models_dir, "yolo11n.pt")
            
            # 如果模型文件已存在，则直接使用本地文件
            if os.path.exists(model_path):
                print(f"使用本地模型: {model_path}")
                self.ai_processor = Processor(model_weights=model_path)
            else:
                # 否则使用名称，由Processor去处理下载
                print(f"模型未找到，将尝试下载到: {models_dir}")
                self.ai_processor = Processor(model_weights="yolo11n")
        except Exception as e:
            print(f"错误: 加载AI模型失败: {e}")
            self.camera_stream.stop()
            return False
        
        # 根据模式选择处理器
        if mode == "client":
            self.handler = CLIClientHandler(self.camera_stream, self.ai_processor)
        elif mode == "server":
            self.handler = CLIServerHandler(self.camera_stream, self.ai_processor)
        else:  # local
            self.handler = CLILocalHandler(self.camera_stream, self.ai_processor)
        
        # 启动处理
        self.handler.start()
        
        return True
    
    def run(self):
        """运行应用程序"""
        print("\n选择运行模式:")
        print("1. 本地处理模式 - 无需网络传输")
        print("2. 客户端模式 - 推送视频流")
        print("3. 服务端模式 - 接收并处理视频流")
        
        while True:
            choice = input("\n请输入模式序号 (1-3): ")
            
            if choice == '1':
                selected_mode = "local"
                break
            elif choice == '2':
                selected_mode = "client"
                break
            elif choice == '3':
                selected_mode = "server"
                break
            else:
                print("无效选择，请重新输入!")
        
        print(f"\n已选择 {selected_mode} 模式")
        
        # 设置应用程序
        if self.setup_application(selected_mode):
            # 显示使用指南
            print("\n============= 使用指南 =============")
            print("程序已启动")
            print("- Window titles will be in English to avoid encoding issues")
            print("- Each mode will display two video windows: Original and Processed")
            print("- If windows don't appear automatically, check taskbar or other desktop areas")
            print("- If GUI support is missing, install OpenCV with GUI:")
            print("  pip install opencv-contrib-python")
            print("- Processed video frames will be saved to 'output' directory")
            print("- Press ESC key in video windows to exit")
            print("- Or press Ctrl+C in command line to exit")
            print("====================================\n")
            
            try:
                # 等待用户输入以退出程序
                print("程序正在运行中，按 Ctrl+C 退出...")
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                print("\n正在退出程序...")
                if self.handler:
                    self.handler.stop()
                if self.camera_stream:
                    self.camera_stream.stop()


# 用于测试
if __name__ == "__main__":
    app = AIVideoApp()
    app.run() 