import cv2
import tkinter as tk
from PIL import Image, ImageTk
import threading
import time
import numpy as np


class StreamDisplay:
    """视频流显示类，负责在GUI中显示视频流"""
    
    def __init__(self, root, camera_stream, ai_processor):
        """
        初始化视频流显示
        
        Args:
            root: Tkinter根窗口
            camera_stream: 摄像头流对象
            ai_processor: AI处理器对象
        """
        self.root = root
        self.camera_stream = camera_stream
        self.ai_processor = ai_processor
        self.running = False
        self.thread = None
        
        # 创建显示标签
        self.original_label = tk.Label(root)
        self.original_label.pack(side=tk.LEFT, padx=10, pady=10)
        self.original_label.imgtk = None
        
        self.processed_label = tk.Label(root)
        self.processed_label.pack(side=tk.RIGHT, padx=10, pady=10)
        self.processed_label.imgtk = None
        
        # 状态变量
        self.fps = 0
        self.frame_count = 0
        self.last_time = time.time()
        
        # 状态显示
        self.status_frame = tk.Frame(root)
        self.status_frame.pack(side=tk.BOTTOM, fill=tk.X)
        
        self.status_var = tk.StringVar(value="就绪")
        self.status_label = tk.Label(self.status_frame, textvariable=self.status_var)
        self.status_label.pack(side=tk.LEFT, padx=10)
        
        self.fps_var = tk.StringVar(value="FPS: 0.0")
        self.fps_label = tk.Label(self.status_frame, textvariable=self.fps_var)
        self.fps_label.pack(side=tk.RIGHT, padx=10)

    def update_frames(self):
        """更新视频帧的循环"""
        while self.running:
            try:
                # 获取原始帧
                frame = self.camera_stream.get_frame()
                
                if frame is not None:
                    # 显示原始帧
                    self.display_frame(self.original_label, frame.copy())
                    
                    # 处理帧
                    try:
                        processed_frame = self.ai_processor.process_frame(frame.copy())
                        
                        # 显示处理后的帧
                        if processed_frame is not None:
                            self.display_frame(self.processed_label, processed_frame)
                    except Exception as e:
                        self.status_var.set(f"处理错误: {e}")
                    
                    # 更新FPS计数
                    self.frame_count += 1
                    current_time = time.time()
                    time_diff = current_time - self.last_time
                    
                    # 每秒更新一次FPS显示
                    if time_diff >= 1.0:
                        self.fps = self.frame_count / time_diff
                        self.fps_var.set(f"FPS: {self.fps:.1f}")
                        self.frame_count = 0
                        self.last_time = current_time
                        
            except Exception as e:
                self.status_var.set(f"显示错误: {e}")
            
            # 降低CPU使用率
            time.sleep(0.01)

    def start_stream(self):
        """启动视频流显示"""
        if self.running:
            return
            
        self.running = True
        self.camera_stream.running = True
        self.thread = threading.Thread(target=self.update_frames)
        self.thread.daemon = True
        self.thread.start()
        self.status_var.set("视频流运行中")

    def stop_stream(self):
        """停止视频流显示"""
        self.running = False
        
        if self.thread:
            self.thread.join(timeout=1.0)
            self.thread = None
            
        self.status_var.set("视频流已停止")

    def display_frame(self, label, frame):
        """
        在标签上显示视频帧
        
        Args:
            label: 要显示帧的Tkinter标签
            frame: 要显示的视频帧
        """
        if frame is None:
            return
            
        try:
            # 调整图像大小
            h, w = frame.shape[:2]
            max_size = (640, 480)  # 最大显示尺寸
            
            # 计算缩放比例，保持宽高比
            scale = min(max_size[0]/w, max_size[1]/h)
            new_size = (int(w*scale), int(h*scale))
            
            # 缩放图像
            if scale != 1.0:
                frame = cv2.resize(frame, new_size)
            
            # 转换颜色格式 BGR -> RGB
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # 转换为PIL图像
            pil_image = Image.fromarray(rgb_frame)
            
            # 转换为Tkinter可用的图像
            imgtk = ImageTk.PhotoImage(image=pil_image)
            
            # 更新标签
            label.imgtk = imgtk
            label.config(image=imgtk)
            
        except Exception as e:
            print(f"显示帧错误: {e}")
            
    def update_status(self, message):
        """更新状态显示"""
        self.status_var.set(message)
