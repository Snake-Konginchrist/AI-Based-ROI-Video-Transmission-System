import cv2
import time
import threading
import re
import urllib.parse


class CameraStream:
    """
    摄像头流处理类，支持本地摄像头和RTSP视频流
    """
    
    def __init__(self, source, resolution=(640, 480)):
        """
        初始化摄像头流
        
        Args:
            source: 视频源，可以是整数（本地摄像头索引）或字符串（RTSP URL）
            resolution: 视频分辨率，格式为(宽, 高)
        """
        self.source = source
        self.resolution = resolution
        self.cap = None
        self.running = False
        self.reconnect_thread = None
        self.lock = threading.Lock()  # 用于线程安全访问
        self.last_frame = None        # 缓存最近一帧，防止获取失败时返回None
        self.frame_count = 0          # 已处理的帧数
        self.fps = 0                  # 估计的FPS
        self.last_time = time.time()  # 上次FPS计算时间
        
        # 开启摄像头
        self.open_camera()
    
    def open_camera(self):
        """打开摄像头或视频流"""
        try:
            # 如果已经有活跃的摄像头，先关闭它
            if self.cap is not None:
                self.cap.release()
            
            # 根据source类型打开相应的视频流
            if isinstance(self.source, int):
                # 本地摄像头
                self.cap = cv2.VideoCapture(self.source)
                print(f"已打开本地摄像头 {self.source}")
                
            elif isinstance(self.source, str):
                # 检查是否是RTSP URL
                if self.source.lower().startswith(('rtsp://', 'rtmp://')):
                    # 使用RTSP流
                    # 设置RTSP流的参数
                    self.cap = cv2.VideoCapture(self.source)
                    self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 2)  # 设置小的缓冲区以减少延迟
                    print(f"已打开网络流: {self._sanitize_url(self.source)}")
                    
                elif self.source.lower().startswith(('http://', 'https://')):
                    # 普通的HTTP流
                    self.cap = cv2.VideoCapture(self.source)
                    print(f"已打开HTTP流: {self._sanitize_url(self.source)}")
                    
                else:
                    # 尝试作为视频文件打开
                    self.cap = cv2.VideoCapture(self.source)
                    print(f"已打开视频文件: {self.source}")
            else:
                raise ValueError(f"不支持的视频源类型: {type(self.source)}")
            
            # 设置分辨率
            if self.resolution:
                self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.resolution[0])
                self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.resolution[1])
            
            # 检查是否成功打开
            if not self.cap.isOpened():
                raise IOError(f"无法打开视频源: {self.source}")
            
            # 读取一帧测试是否正常工作
            ret, _ = self.cap.read()
            if not ret:
                raise IOError(f"无法从视频源读取: {self.source}")
            
            self.running = True
            return True
            
        except Exception as e:
            print(f"打开视频源失败: {e}")
            if self.cap is not None:
                self.cap.release()
                self.cap = None
            return False
    
    def _sanitize_url(self, url):
        """移除URL中的敏感信息（如用户名和密码）用于打印"""
        try:
            # 解析URL
            parsed = urllib.parse.urlparse(url)
            
            # 检查是否有用户名和密码
            if '@' in parsed.netloc:
                # 替换敏感信息
                netloc = re.sub(r'[^@]+@', '***:***@', parsed.netloc)
                # 重建URL
                sanitized = urllib.parse.urlunparse(
                    (parsed.scheme, netloc, parsed.path, parsed.params, parsed.query, parsed.fragment)
                )
                return sanitized
            return url
        except:
            # 如果解析失败，返回原始URL的概要
            return url[:8] + "..." + url[-8:] if len(url) > 20 else url
    
    def get_frame(self):
        """
        获取一帧视频
        
        Returns:
            视频帧或None（如果获取失败）
        """
        if not self.running or self.cap is None or not self.cap.isOpened():
            # 如果摄像头未运行，尝试自动重新连接
            if not self.reconnect_thread or not self.reconnect_thread.is_alive():
                self.reconnect_thread = threading.Thread(target=self.auto_reconnect)
                self.reconnect_thread.daemon = True
                self.reconnect_thread.start()
            return self.last_frame  # 返回最后一帧或None
        
        try:
            with self.lock:
                ret, frame = self.cap.read()
            
            if ret:
                # 更新统计信息
                self.frame_count += 1
                current_time = time.time()
                time_diff = current_time - self.last_time
                
                # 每秒更新一次FPS
                if time_diff >= 1.0:
                    self.fps = self.frame_count / time_diff
                    self.frame_count = 0
                    self.last_time = current_time
                
                # 添加FPS信息到帧上
                cv2.putText(
                    frame, 
                    f"FPS: {self.fps:.1f}", 
                    (10, frame.shape[0] - 10), 
                    cv2.FONT_HERSHEY_SIMPLEX, 
                    0.5, 
                    (0, 255, 0), 
                    1
                )
                
                # 缓存帧
                self.last_frame = frame
                return frame
            else:
                # 读取失败，尝试重新连接
                if not self.reconnect_thread or not self.reconnect_thread.is_alive():
                    self.reconnect_thread = threading.Thread(target=self.auto_reconnect)
                    self.reconnect_thread.daemon = True
                    self.reconnect_thread.start()
                return self.last_frame
        except Exception as e:
            print(f"获取视频帧失败: {e}")
            return self.last_frame
    
    def auto_reconnect(self, max_attempts=5, delay=2.0):
        """
        自动尝试重新连接视频源
        
        Args:
            max_attempts: 最大重试次数
            delay: 每次重试之间的延迟（秒）
        """
        attempts = 0
        
        while attempts < max_attempts:
            print(f"尝试重新连接视频源 (尝试 {attempts+1}/{max_attempts})...")
            
            # 休眠一段时间后再尝试
            time.sleep(delay)
            
            # 尝试重新打开视频源
            if self.open_camera():
                print("成功重新连接到视频源")
                return True
                
            attempts += 1
        
        print(f"无法重新连接到视频源，已达到最大尝试次数 ({max_attempts})")
        return False
    
    def stop(self):
        """停止视频流"""
        self.running = False
        
        if self.cap:
            with self.lock:
                self.cap.release()
                self.cap = None
        
        # 等待重新连接线程结束
        if self.reconnect_thread and self.reconnect_thread.is_alive():
            self.reconnect_thread.join(timeout=1.0)
    
    def change_source(self, new_source):
        """
        更改视频源
        
        Args:
            new_source: 新的视频源
        
        Returns:
            是否成功更改
        """
        self.source = new_source
        
        # 停止当前流
        self.stop()
        
        # 打开新的视频源
        return self.open_camera()
