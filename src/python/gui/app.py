import tkinter as tk
from tkinter import messagebox, ttk
import os
import sys
import threading
from ..stream.camera import CameraStream
from ..stream.display import StreamDisplay
from ..yolo.processor import Processor
from ..stream.mode_handler import ClientHandler, ServerHandler, LocalHandler
from .mode_selection import ModeSelectionWindow
# from .utils import download_model_files


class AIVideoApp:
    """基于嵌入式AI的ROI区域视频传输系统的主应用类"""
    
    def __init__(self):
        """初始化应用"""
        self.root = None
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
                messagebox.showerror("错误", f"无法创建models目录: {e}")
                return False
                
        return True
        
    def setup_application(self, mode):
        """设置应用程序"""
        # 检查模型
        if not self.check_models():
            return False
        
        # 创建主窗口
        self.root = tk.Tk()
        self.root.title(f"AI增强视频流系统 - {mode.upper()}模式")
        
        # 初始化相机流
        self.camera_stream = CameraStream(0)
        
        # 初始化AI处理器
        try:
            # 使用YOLOv11模型（无需指定.pt后缀）
            self.ai_processor = Processor(model_weights="yolo11n")
        except Exception as e:
            messagebox.showerror("错误", f"加载AI模型失败: {e}")
            self.camera_stream.stop()
            self.root.destroy()
            return False
        
        # 根据模式选择处理器
        if mode == "client":
            self.handler = ClientHandler(self.root, self.camera_stream, self.ai_processor)
        elif mode == "server":
            self.handler = ServerHandler(self.root, self.camera_stream, self.ai_processor)
        else:  # local
            self.handler = LocalHandler(self.root, self.camera_stream, self.ai_processor)
        
        # 启动处理
        self.handler.start()
        
        # 关闭时清理资源
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        return True
    
    def on_closing(self):
        """关闭应用程序时的清理操作"""
        if self.handler:
            self.handler.stop()
        
        if self.camera_stream:
            self.camera_stream.stop()
        
        if self.root:
            self.root.destroy()
    
    def run(self):
        """运行应用程序"""
        # 创建模式选择窗口
        mode_selector = ModeSelectionWindow()
        selected_mode = mode_selector.get_selected_mode()
        
        # 如果用户取消了选择，直接退出
        if not selected_mode:
            return
        
        # 设置应用程序
        if self.setup_application(selected_mode):
            # 运行主循环
            if self.root:
                self.root.mainloop()


# 用于测试
if __name__ == "__main__":
    app = AIVideoApp()
    app.run() 