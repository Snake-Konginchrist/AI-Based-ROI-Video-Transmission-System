import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import threading
import cv2
import time
import socket
import struct
import pickle
import numpy as np
from PIL import Image, ImageTk
from src.python.stream.display import StreamDisplay


class BaseHandler:
    """处理器基类"""
    def __init__(self, root, camera_stream, ai_processor):
        self.root = root
        self.camera_stream = camera_stream
        self.ai_processor = ai_processor
        self.running = False
        self.thread = None
        
        # 创建UI元素
        self.setup_ui()
    
    def setup_ui(self):
        """设置基本UI界面"""
        # 主框架
        self.main_frame = ttk.Frame(self.root)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 视频显示区域
        self.video_frame = ttk.Frame(self.main_frame)
        self.video_frame.pack(fill=tk.BOTH, expand=True)
        
        # 原始视频标签
        self.original_frame = ttk.LabelFrame(self.video_frame, text="原始视频")
        self.original_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
        self.original_label = ttk.Label(self.original_frame)
        self.original_label.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 处理后视频标签
        self.processed_frame = ttk.LabelFrame(self.video_frame, text="处理后视频")
        self.processed_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5)
        self.processed_label = ttk.Label(self.processed_frame)
        self.processed_label.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 控制区域
        self.control_frame = ttk.Frame(self.main_frame)
        self.control_frame.pack(fill=tk.X, pady=10)
        
        # 状态标签
        self.status_var = tk.StringVar(value="就绪")
        self.status_label = ttk.Label(self.control_frame, textvariable=self.status_var)
        self.status_label.pack(side=tk.LEFT, padx=5)
        
        # 添加进度条
        self.progress_var = tk.DoubleVar(value=0)
        self.progress = ttk.Progressbar(
            self.control_frame, 
            variable=self.progress_var,
            orient=tk.HORIZONTAL,
            length=200,
            mode='determinate'
        )
        self.progress.pack(side=tk.LEFT, padx=10)
    
    def update_status(self, message):
        """更新状态信息"""
        self.status_var.set(message)
    
    def update_progress(self, value):
        """更新进度条值"""
        self.progress_var.set(value)
    
    def display_frame(self, label, frame):
        """在标签上显示视频帧"""
        if frame is None:
            return
        
        # 调整图像大小以适应标签
        h, w = frame.shape[:2]
        max_size = (400, 300)  # 最大显示尺寸
        
        # 计算缩放比例
        scale = min(max_size[0]/w, max_size[1]/h)
        new_size = (int(w*scale), int(h*scale))
        
        # 缩放图像
        resized = cv2.resize(frame, new_size)
        
        # 转换颜色格式
        cv2_image = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)
        pil_image = Image.fromarray(cv2_image)
        tk_image = ImageTk.PhotoImage(image=pil_image)
        
        # 更新标签图像
        label.imgtk = tk_image
        label.config(image=tk_image)
    
    def start(self):
        """启动处理线程"""
        self.running = True
        self.thread = threading.Thread(target=self.process_loop)
        self.thread.daemon = True
        self.thread.start()
    
    def stop(self):
        """停止处理线程"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=1.0)
    
    def process_loop(self):
        """处理循环，子类需要实现"""
        raise NotImplementedError("子类必须实现process_loop方法")


class LocalHandler(BaseHandler):
    """本地处理模式处理器"""
    def __init__(self, root, camera_stream, ai_processor):
        super().__init__(root, camera_stream, ai_processor)
        
        # 添加本地模式特有的UI元素
        self.add_local_controls()
    
    def add_local_controls(self):
        """添加本地模式控制按钮"""
        # 添加QP值调整滑块
        self.qp_frame = ttk.LabelFrame(self.control_frame, text="编码质量控制")
        self.qp_frame.pack(side=tk.RIGHT, padx=10)
        
        # ROI区域QP值
        ttk.Label(self.qp_frame, text="ROI区域QP值:").grid(row=0, column=0, padx=5, pady=3)
        self.roi_qp_var = tk.IntVar(value=15)  # 低QP = 高质量
        self.roi_qp_scale = ttk.Scale(
            self.qp_frame, 
            from_=5, 
            to=40, 
            orient=tk.HORIZONTAL, 
            variable=self.roi_qp_var,
            length=100
        )
        self.roi_qp_scale.grid(row=0, column=1, padx=5, pady=3)
        ttk.Label(self.qp_frame, textvariable=self.roi_qp_var).grid(row=0, column=2, padx=5)
        
        # 非ROI区域QP值
        ttk.Label(self.qp_frame, text="非ROI区域QP值:").grid(row=1, column=0, padx=5, pady=3)
        self.non_roi_qp_var = tk.IntVar(value=35)  # 高QP = 低质量
        self.non_roi_qp_scale = ttk.Scale(
            self.qp_frame, 
            from_=5, 
            to=40, 
            orient=tk.HORIZONTAL, 
            variable=self.non_roi_qp_var,
            length=100
        )
        self.non_roi_qp_scale.grid(row=1, column=1, padx=5, pady=3)
        ttk.Label(self.qp_frame, textvariable=self.non_roi_qp_var).grid(row=1, column=2, padx=5)
    
    def process_loop(self):
        """本地处理循环"""
        self.update_status("本地处理中...")
        
        while self.running:
            # 获取帧
            frame = self.camera_stream.get_frame()
            if frame is None:
                time.sleep(0.01)
                continue
            
            # 显示原始帧
            self.display_frame(self.original_label, frame.copy())
            
            # AI处理帧
            try:
                # AI检测，获取ROI区域
                processed_frame, rois = self.ai_processor.process_frame(
                    frame.copy(), 
                    return_rois=True, 
                    roi_qp=self.roi_qp_var.get(), 
                    non_roi_qp=self.non_roi_qp_var.get()
                )
                
                # 显示处理后的帧
                self.display_frame(self.processed_label, processed_frame)
                
                # 更新ROI信息
                if rois:
                    self.update_status(f"检测到 {len(rois)} 个目标")
                
            except Exception as e:
                self.update_status(f"处理错误: {e}")
            
            # 控制帧率
            time.sleep(0.01)


class ClientHandler(BaseHandler):
    """客户端模式处理器"""
    def __init__(self, root, camera_stream, ai_processor):
        super().__init__(root, camera_stream, ai_processor)
        
        # 客户端特有属性
        self.server_address = None
        self.server_port = None
        self.client_socket = None
        self.connected = False
        
        # 添加客户端模式特有的UI元素
        self.add_client_controls()
    
    def add_client_controls(self):
        """添加客户端模式控制按钮"""
        # 连接控制区域
        self.conn_frame = ttk.LabelFrame(self.control_frame, text="服务器连接")
        self.conn_frame.pack(side=tk.RIGHT, padx=10)
        
        # 连接按钮
        self.connect_btn = ttk.Button(self.conn_frame, text="连接服务器", command=self.connect_to_server)
        self.connect_btn.grid(row=0, column=0, padx=5, pady=5)
        
        # 断开按钮
        self.disconnect_btn = ttk.Button(self.conn_frame, text="断开连接", command=self.disconnect_from_server, state=tk.DISABLED)
        self.disconnect_btn.grid(row=0, column=1, padx=5, pady=5)
        
        # 连接状态
        self.connection_var = tk.StringVar(value="未连接")
        self.connection_label = ttk.Label(self.conn_frame, textvariable=self.connection_var)
        self.connection_label.grid(row=0, column=2, padx=5, pady=5)
    
    def connect_to_server(self):
        """连接到服务器"""
        # 获取服务器地址和端口
        self.server_address = simpledialog.askstring("服务器地址", "请输入服务器IP地址:", initialvalue="127.0.0.1")
        if not self.server_address:
            return
        
        self.server_port = simpledialog.askinteger("服务器端口", "请输入服务器端口:", initialvalue=8089, minvalue=1024, maxvalue=65535)
        if not self.server_port:
            return
        
        # 尝试连接
        try:
            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client_socket.connect((self.server_address, self.server_port))
            self.connected = True
            
            # 更新UI
            self.connection_var.set(f"已连接: {self.server_address}:{self.server_port}")
            self.connect_btn.config(state=tk.DISABLED)
            self.disconnect_btn.config(state=tk.NORMAL)
            self.update_status("已连接到服务器")
            
        except Exception as e:
            messagebox.showerror("连接错误", f"无法连接到服务器: {e}")
            self.connection_var.set("连接失败")
            self.client_socket = None
    
    def disconnect_from_server(self):
        """断开服务器连接"""
        if self.client_socket:
            try:
                self.client_socket.close()
            except:
                pass
            
            self.client_socket = None
            self.connected = False
            
            # 更新UI
            self.connection_var.set("未连接")
            self.connect_btn.config(state=tk.NORMAL)
            self.disconnect_btn.config(state=tk.DISABLED)
            self.update_status("已断开连接")
    
    def process_loop(self):
        """客户端处理循环"""
        self.update_status("客户端就绪")
        
        while self.running:
            # 获取帧
            frame = self.camera_stream.get_frame()
            if frame is None:
                time.sleep(0.01)
                continue
            
            # 显示原始帧
            self.display_frame(self.original_label, frame)
            
            # 如果已连接，发送帧到服务器
            if self.connected and self.client_socket:
                try:
                    # 编码帧
                    _, encoded_frame = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
                    data = pickle.dumps(encoded_frame)
                    
                    # 发送大小和数据
                    message_size = struct.pack("<L", len(data))
                    self.client_socket.sendall(message_size + data)
                    
                    # 接收处理后的帧
                    try:
                        # 接收消息大小 (4字节)
                        packed_msg_size = self.client_socket.recv(4)
                        if not packed_msg_size:
                            continue
                        
                        msg_size = struct.unpack("<L", packed_msg_size)[0]
                        
                        # 接收完整数据
                        data = b""
                        while len(data) < msg_size:
                            remaining = msg_size - len(data)
                            data += self.client_socket.recv(
                                4096 if remaining > 4096 else remaining
                            )
                        
                        # 解码图像
                        frame_data = pickle.loads(data)
                        processed_frame = cv2.imdecode(frame_data, cv2.IMREAD_COLOR)
                        
                        # 显示处理后的帧
                        self.display_frame(self.processed_label, processed_frame)
                        
                    except Exception as e:
                        self.update_status(f"接收错误: {e}")
                
                except (socket.error, socket.timeout) as e:
                    self.update_status(f"连接错误: {e}")
                    self.disconnect_from_server()
                
                except Exception as e:
                    self.update_status(f"发送错误: {e}")
            
            # 控制帧率
            time.sleep(0.01)
    
    def stop(self):
        """停止客户端"""
        # 断开连接
        self.disconnect_from_server()
        super().stop()


class ServerHandler(BaseHandler):
    """服务端模式处理器"""
    def __init__(self, root, camera_stream, ai_processor):
        super().__init__(root, camera_stream, ai_processor)
        
        # 服务端特有属性
        self.server_socket = None
        self.client_socket = None
        self.client_address = None
        self.server_running = False
        self.server_thread = None
        
        # 默认端口
        self.port = 8089
        
        # 添加服务端模式特有的UI元素
        self.add_server_controls()
    
    def add_server_controls(self):
        """添加服务端模式控制按钮"""
        # 服务器控制区域
        self.server_frame = ttk.LabelFrame(self.control_frame, text="服务器控制")
        self.server_frame.pack(side=tk.RIGHT, padx=10)
        
        # 端口输入
        ttk.Label(self.server_frame, text="端口:").grid(row=0, column=0, padx=5, pady=5)
        self.port_var = tk.StringVar(value=str(self.port))
        port_entry = ttk.Entry(self.server_frame, textvariable=self.port_var, width=6)
        port_entry.grid(row=0, column=1, padx=5, pady=5)
        
        # 启动服务器按钮
        self.start_server_btn = ttk.Button(self.server_frame, text="启动服务器", command=self.start_server)
        self.start_server_btn.grid(row=0, column=2, padx=5, pady=5)
        
        # 停止服务器按钮
        self.stop_server_btn = ttk.Button(self.server_frame, text="停止服务器", command=self.stop_server, state=tk.DISABLED)
        self.stop_server_btn.grid(row=0, column=3, padx=5, pady=5)
        
        # 服务器状态
        self.server_status_var = tk.StringVar(value="已停止")
        self.server_status_label = ttk.Label(self.server_frame, textvariable=self.server_status_var)
        self.server_status_label.grid(row=0, column=4, padx=5, pady=5)
        
        # 添加QP值调整滑块
        self.qp_frame = ttk.LabelFrame(self.main_frame, text="编码质量控制")
        self.qp_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # ROI区域QP值
        ttk.Label(self.qp_frame, text="ROI区域QP值:").grid(row=0, column=0, padx=5, pady=3)
        self.roi_qp_var = tk.IntVar(value=15)  # 低QP = 高质量
        self.roi_qp_scale = ttk.Scale(
            self.qp_frame, 
            from_=5, 
            to=40, 
            orient=tk.HORIZONTAL, 
            variable=self.roi_qp_var,
            length=100
        )
        self.roi_qp_scale.grid(row=0, column=1, padx=5, pady=3)
        ttk.Label(self.qp_frame, textvariable=self.roi_qp_var).grid(row=0, column=2, padx=5)
        
        # 非ROI区域QP值
        ttk.Label(self.qp_frame, text="非ROI区域QP值:").grid(row=0, column=3, padx=5, pady=3)
        self.non_roi_qp_var = tk.IntVar(value=35)  # 高QP = 低质量
        self.non_roi_qp_scale = ttk.Scale(
            self.qp_frame, 
            from_=5, 
            to=40, 
            orient=tk.HORIZONTAL, 
            variable=self.non_roi_qp_var,
            length=100
        )
        self.non_roi_qp_scale.grid(row=0, column=4, padx=5, pady=3)
        ttk.Label(self.qp_frame, textvariable=self.non_roi_qp_var).grid(row=0, column=5, padx=5)
    
    def start_server(self):
        """启动服务器"""
        # 获取端口
        try:
            self.port = int(self.port_var.get())
            if not (1024 <= self.port <= 65535):
                raise ValueError("端口必须在1024-65535之间")
        except ValueError as e:
            messagebox.showerror("端口错误", f"无效的端口: {e}")
            return
        
        # 创建服务器套接字
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind(('0.0.0.0', self.port))
            self.server_socket.listen(5)
            self.server_socket.settimeout(0.5)  # 设置超时以允许线程终止
            
            # 更新UI
            self.server_status_var.set(f"监听 {self.port}")
            self.start_server_btn.config(state=tk.DISABLED)
            self.stop_server_btn.config(state=tk.NORMAL)
            self.update_status(f"服务器已启动，监听端口 {self.port}")
            
            # 启动服务器线程
            self.server_running = True
            self.server_thread = threading.Thread(target=self.server_loop)
            self.server_thread.daemon = True
            self.server_thread.start()
            
        except Exception as e:
            if self.server_socket:
                self.server_socket.close()
                self.server_socket = None
            messagebox.showerror("服务器错误", f"无法启动服务器: {e}")
            self.server_status_var.set("启动失败")
    
    def stop_server(self):
        """停止服务器"""
        self.server_running = False
        
        # 关闭客户端连接
        if self.client_socket:
            try:
                self.client_socket.close()
            except:
                pass
            self.client_socket = None
            self.client_address = None
        
        # 关闭服务器套接字
        if self.server_socket:
            try:
                self.server_socket.close()
            except:
                pass
            self.server_socket = None
        
        # 等待服务器线程结束
        if self.server_thread:
            self.server_thread.join(timeout=2.0)
            self.server_thread = None
        
        # 更新UI
        self.server_status_var.set("已停止")
        self.start_server_btn.config(state=tk.NORMAL)
        self.stop_server_btn.config(state=tk.DISABLED)
        self.update_status("服务器已停止")
    
    def server_loop(self):
        """服务器接收客户端连接的循环"""
        while self.server_running:
            try:
                # 等待客户端连接
                client_sock, client_addr = self.server_socket.accept()
                
                # 保存客户端连接
                self.client_socket = client_sock
                self.client_address = client_addr
                
                # 更新UI
                self.root.after(0, lambda: self.update_status(f"客户端已连接: {client_addr[0]}:{client_addr[1]}"))
                
                # 处理客户端通信
                self.handle_client(client_sock, client_addr)
                
            except socket.timeout:
                # 超时是正常的，用于检查是否需要退出循环
                continue
            except Exception as e:
                # 其他错误
                self.root.after(0, lambda e=e: self.update_status(f"服务器错误: {e}"))
    
    def handle_client(self, client_socket, client_address):
        """处理与单个客户端的通信"""
        while self.server_running and client_socket:
            try:
                # 接收消息大小 (4字节)
                packed_msg_size = client_socket.recv(4)
                if not packed_msg_size:
                    break
                
                msg_size = struct.unpack("<L", packed_msg_size)[0]
                
                # 接收完整数据
                data = b""
                while len(data) < msg_size:
                    remaining = msg_size - len(data)
                    data += client_socket.recv(
                        4096 if remaining > 4096 else remaining
                    )
                
                # 解码图像
                frame_data = pickle.loads(data)
                frame = cv2.imdecode(frame_data, cv2.IMREAD_COLOR)
                
                # 在UI线程中安全地更新显示
                self.root.after(0, lambda f=frame: self.display_frame(self.original_label, f))
                
                # AI处理帧
                try:
                    # AI检测，获取ROI区域
                    processed_frame, _ = self.ai_processor.process_frame(
                        frame, 
                        return_rois=True, 
                        roi_qp=self.roi_qp_var.get(), 
                        non_roi_qp=self.non_roi_qp_var.get()
                    )
                    
                    # 在UI线程中安全地更新显示
                    self.root.after(0, lambda f=processed_frame: self.display_frame(self.processed_label, f))
                    
                    # 发送处理后的帧回客户端
                    _, encoded_frame = cv2.imencode('.jpg', processed_frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
                    reply_data = pickle.dumps(encoded_frame)
                    
                    # 发送大小和数据
                    reply_size = struct.pack("<L", len(reply_data))
                    client_socket.sendall(reply_size + reply_data)
                    
                except Exception as e:
                    self.root.after(0, lambda e=e: self.update_status(f"处理错误: {e}"))
                
            except (socket.error, socket.timeout):
                break
            
            except Exception as e:
                self.root.after(0, lambda e=e: self.update_status(f"客户端处理错误: {e}"))
        
        # 连接已关闭
        try:
            client_socket.close()
        except:
            pass
        
        # 清理状态
        if self.client_socket == client_socket:
            self.client_socket = None
            self.client_address = None
            self.root.after(0, lambda: self.update_status("客户端已断开连接"))
    
    def process_loop(self):
        """服务端模式的主处理循环"""
        self.update_status("服务端就绪")
        
        while self.running:
            # 在本地模式下，可以显示本地摄像头的画面
            frame = self.camera_stream.get_frame()
            if frame is not None and not self.client_socket:
                self.display_frame(self.original_label, frame)
                
                # 处理本地画面（仅供演示）
                try:
                    processed_frame, _ = self.ai_processor.process_frame(
                        frame, 
                        return_rois=True,
                        roi_qp=self.roi_qp_var.get(), 
                        non_roi_qp=self.non_roi_qp_var.get()
                    )
                    self.display_frame(self.processed_label, processed_frame)
                except Exception as e:
                    self.update_status(f"本地处理错误: {e}")
            
            # 控制帧率
            time.sleep(0.01)
    
    def stop(self):
        """停止服务端"""
        # 停止服务器
        self.stop_server()
        super().stop() 