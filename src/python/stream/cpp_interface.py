"""
C++组件的Python接口

该模块提供了Python调用C++实现的RTMP推流和RTSP客户端功能的接口。
使用ctypes库来加载动态库并调用其函数。

作者: PycharmProjects
日期: 2023
"""

import os
import sys
import ctypes
import numpy as np
from typing import Callable, Optional, List, Tuple, Dict
import threading
import platform


# 确定动态库文件扩展名
def get_lib_ext():
    """根据操作系统获取动态库扩展名"""
    if platform.system() == 'Windows':
        return '.dll'
    elif platform.system() == 'Darwin':  # macOS
        return '.dylib'
    else:  # Linux和其他UNIX系统
        return '.so'


# 查找库文件的路径
def find_library(name: str) -> str:
    """
    查找动态库文件的路径
    
    Args:
        name: 库文件名（不包含扩展名）
    
    Returns:
        库文件的完整路径
    
    Raises:
        FileNotFoundError: 找不到库文件
    """
    # 可能的路径
    lib_ext = get_lib_ext()
    possible_paths = [
        os.path.join(os.path.dirname(__file__), '..', '..', '..', 'lib', f'lib{name}{lib_ext}'),
        os.path.join(os.path.dirname(__file__), '..', '..', '..', 'build', f'lib{name}{lib_ext}'),
        os.path.join(os.path.dirname(__file__), '..', '..', '..', 'lib', f'{name}{lib_ext}'),
        os.path.join(os.path.dirname(__file__), '..', '..', '..', 'build', f'{name}{lib_ext}'),
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            return os.path.abspath(path)
    
    # 如果未找到库，打印详细的错误信息
    error_msg = f"找不到库文件: {name}{lib_ext}\n"
    error_msg += "搜索路径:\n"
    for path in possible_paths:
        error_msg += f"  - {os.path.abspath(path)}\n"
    error_msg += "请确保已经编译C++库，并将库文件放在正确的位置。"
    
    raise FileNotFoundError(error_msg)


# 定义ROI区域类
class ROIRegion:
    """代表视频中的ROI（感兴趣区域）"""
    
    def __init__(self, x: int, y: int, width: int, height: int, qp: int = 15):
        """
        初始化ROI区域
        
        Args:
            x: 左上角x坐标
            y: 左上角y坐标
            width: 宽度
            height: 高度
            qp: QP值（量化参数，值越小质量越高）
        """
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.qp = qp
    
    def __repr__(self) -> str:
        return f"ROIRegion(x={self.x}, y={self.y}, width={self.width}, height={self.height}, qp={self.qp})"


# RTMP推流器类
class RTMPStreamer:
    """RTMP推流器，用于将视频流推送到流媒体服务器"""
    
    def __init__(self, url: str, width: int, height: int, fps: int = 30, 
                 bitrate: int = 1000000, gop: int = 30, qp: int = 23):
        """
        初始化RTMP推流器
        
        Args:
            url: RTMP服务器URL
            width: 视频宽度
            height: 视频高度
            fps: 帧率
            bitrate: 比特率（bps）
            gop: GOP大小
            qp: 默认QP值
        """
        try:
            # 加载动态库
            self.lib_path = find_library('rtmp_streamer')
            self.lib = ctypes.CDLL(self.lib_path)
            
            # 设置函数参数和返回类型
            self._setup_functions()
            
            # 创建推流器实例
            self.url_bytes = url.encode('utf-8')
            self.streamer = self.lib.create_rtmp_streamer(
                self.url_bytes, width, height, fps, bitrate, gop, qp
            )
            
            if not self.streamer:
                raise RuntimeError("创建RTMP推流器失败")
            
            # 保存参数
            self.width = width
            self.height = height
            self.channels = 3  # RGB格式
            self.is_initialized = False
            self.is_streaming = False
            
            # 创建帧数据
            self.frame_data = self.lib.create_frame_data(width, height, self.channels)
            if not self.frame_data:
                raise RuntimeError("创建帧数据失败")
            
            print(f"RTMP推流器创建成功，目标: {url}")
        
        except Exception as e:
            print(f"初始化RTMP推流器失败: {e}")
            self._cleanup()
            raise
    
    def _setup_functions(self):
        """设置C++函数的参数和返回类型"""
        # 创建和销毁推流器
        self.lib.create_rtmp_streamer.argtypes = [ctypes.c_char_p, ctypes.c_int, ctypes.c_int, 
                                               ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int]
        self.lib.create_rtmp_streamer.restype = ctypes.c_void_p
        
        self.lib.destroy_rtmp_streamer.argtypes = [ctypes.c_void_p]
        self.lib.destroy_rtmp_streamer.restype = None
        
        # 初始化和控制
        self.lib.initialize_streamer.argtypes = [ctypes.c_void_p]
        self.lib.initialize_streamer.restype = ctypes.c_bool
        
        self.lib.start_streaming.argtypes = [ctypes.c_void_p]
        self.lib.start_streaming.restype = ctypes.c_bool
        
        self.lib.stop_streaming.argtypes = [ctypes.c_void_p]
        self.lib.stop_streaming.restype = None
        
        # 帧数据操作
        self.lib.create_frame_data.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_int]
        self.lib.create_frame_data.restype = ctypes.c_void_p
        
        self.lib.destroy_frame_data.argtypes = [ctypes.c_void_p]
        self.lib.destroy_frame_data.restype = None
        
        self.lib.add_roi_region.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_int, 
                                         ctypes.c_int, ctypes.c_int, ctypes.c_int]
        self.lib.add_roi_region.restype = None
        
        self.lib.clear_roi_regions.argtypes = [ctypes.c_void_p]
        self.lib.clear_roi_regions.restype = None
        
        self.lib.set_frame_data.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_uint8), 
                                         ctypes.c_int, ctypes.c_int64]
        self.lib.set_frame_data.restype = ctypes.c_bool
        
        self.lib.push_frame.argtypes = [ctypes.c_void_p, ctypes.c_void_p]
        self.lib.push_frame.restype = ctypes.c_bool
    
    def initialize(self) -> bool:
        """
        初始化推流器
        
        Returns:
            是否成功初始化
        """
        if not self.streamer:
            return False
        
        success = self.lib.initialize_streamer(self.streamer)
        self.is_initialized = success
        return success
    
    def start(self) -> bool:
        """
        开始推流
        
        Returns:
            是否成功启动推流
        """
        if not self.streamer:
            return False
        
        if not self.is_initialized:
            if not self.initialize():
                return False
        
        success = self.lib.start_streaming(self.streamer)
        self.is_streaming = success
        return success
    
    def stop(self):
        """停止推流"""
        if self.streamer and self.is_streaming:
            self.lib.stop_streaming(self.streamer)
            self.is_streaming = False
    
    def push_frame(self, frame: np.ndarray, rois: Optional[List[ROIRegion]] = None) -> bool:
        """
        推送视频帧
        
        Args:
            frame: 视频帧（BGR格式的NumPy数组）
            rois: ROI区域列表
        
        Returns:
            是否成功推送
        """
        if not self.streamer or not self.is_streaming or not self.frame_data:
            return False
        
        if frame.shape[0] != self.height or frame.shape[1] != self.width:
            print(f"帧尺寸不匹配: 预期 {self.width}x{self.height}, 但收到 {frame.shape[1]}x{frame.shape[0]}")
            return False
        
        # 确保帧是连续的内存
        if not frame.flags['C_CONTIGUOUS']:
            frame = np.ascontiguousarray(frame)
        
        # 清除之前的ROI区域
        self.lib.clear_roi_regions(self.frame_data)
        
        # 添加新的ROI区域
        if rois:
            for roi in rois:
                self.lib.add_roi_region(
                    self.frame_data, roi.x, roi.y, roi.width, roi.height, roi.qp
                )
        
        # 设置帧数据
        timestamp = int(time.time() * 1000)  # 毫秒时间戳
        ptr = frame.ctypes.data_as(ctypes.POINTER(ctypes.c_uint8))
        size = frame.size
        
        success = self.lib.set_frame_data(self.frame_data, ptr, size, timestamp)
        if not success:
            return False
        
        # 推送帧
        return self.lib.push_frame(self.streamer, self.frame_data)
    
    def _cleanup(self):
        """清理资源"""
        if hasattr(self, 'frame_data') and self.frame_data:
            self.lib.destroy_frame_data(self.frame_data)
            self.frame_data = None
        
        if hasattr(self, 'streamer') and self.streamer:
            self.stop()
            self.lib.destroy_rtmp_streamer(self.streamer)
            self.streamer = None
    
    def __del__(self):
        """析构函数"""
        self._cleanup()


# RTSP客户端回调函数类型
RTSP_FRAME_CALLBACK = ctypes.CFUNCTYPE(
    None, ctypes.c_void_p, ctypes.POINTER(ctypes.c_uint8), 
    ctypes.c_int, ctypes.c_int, ctypes.c_int64
)


# RTSP客户端类
class RTSPClient:
    """RTSP客户端，用于从IP摄像头获取视频流"""
    
    def __init__(self, url: str, width: int = 0, height: int = 0):
        """
        初始化RTSP客户端
        
        Args:
            url: RTSP服务器URL
            width: 输出图像宽度（0表示使用原始宽度）
            height: 输出图像高度（0表示使用原始高度）
        """
        try:
            # 加载动态库
            self.lib_path = find_library('rtsp_client')
            self.lib = ctypes.CDLL(self.lib_path)
            
            # 设置函数参数和返回类型
            self._setup_functions()
            
            # 创建客户端实例
            self.url_bytes = url.encode('utf-8')
            self.client = self.lib.create_rtsp_client(self.url_bytes, width, height)
            
            if not self.client:
                raise RuntimeError("创建RTSP客户端失败")
            
            # 初始化回调相关
            self.callback = None
            self.user_callback = None
            self.callback_lock = threading.Lock()
            
            # 状态
            self.is_initialized = False
            self.is_running = False
            
            print(f"RTSP客户端创建成功，源: {url}")
        
        except Exception as e:
            print(f"初始化RTSP客户端失败: {e}")
            self._cleanup()
            raise
    
    def _setup_functions(self):
        """设置C++函数的参数和返回类型"""
        # 创建和销毁客户端
        self.lib.create_rtsp_client.argtypes = [ctypes.c_char_p, ctypes.c_int, ctypes.c_int]
        self.lib.create_rtsp_client.restype = ctypes.c_void_p
        
        self.lib.destroy_rtsp_client.argtypes = [ctypes.c_void_p]
        self.lib.destroy_rtsp_client.restype = None
        
        # 初始化和控制
        self.lib.initialize_client.argtypes = [ctypes.c_void_p]
        self.lib.initialize_client.restype = ctypes.c_bool
        
        self.lib.start_client.argtypes = [ctypes.c_void_p]
        self.lib.start_client.restype = ctypes.c_bool
        
        self.lib.stop_client.argtypes = [ctypes.c_void_p]
        self.lib.stop_client.restype = None
        
        # 获取信息
        self.lib.get_fps.argtypes = [ctypes.c_void_p]
        self.lib.get_fps.restype = ctypes.c_double
        
        self.lib.get_width.argtypes = [ctypes.c_void_p]
        self.lib.get_width.restype = ctypes.c_int
        
        self.lib.get_height.argtypes = [ctypes.c_void_p]
        self.lib.get_height.restype = ctypes.c_int
        
        # 设置回调
        self.lib.set_frame_callback.argtypes = [
            ctypes.c_void_p, RTSP_FRAME_CALLBACK, ctypes.c_void_p
        ]
        self.lib.set_frame_callback.restype = None
    
    def initialize(self) -> bool:
        """
        初始化客户端
        
        Returns:
            是否成功初始化
        """
        if not self.client:
            return False
        
        success = self.lib.initialize_client(self.client)
        self.is_initialized = success
        
        if success:
            # 获取尺寸
            self.width = self.lib.get_width(self.client)
            self.height = self.lib.get_height(self.client)
            print(f"RTSP客户端初始化成功，分辨率: {self.width}x{self.height}")
        
        return success
    
    def start(self) -> bool:
        """
        开始接收和处理RTSP流
        
        Returns:
            是否成功启动
        """
        if not self.client:
            return False
        
        if not self.is_initialized:
            if not self.initialize():
                return False
        
        success = self.lib.start_client(self.client)
        self.is_running = success
        return success
    
    def stop(self):
        """停止接收和处理RTSP流"""
        if self.client and self.is_running:
            self.lib.stop_client(self.client)
            self.is_running = False
    
    def set_frame_callback(self, callback: Callable[[np.ndarray, int], None]):
        """
        设置帧回调函数
        
        Args:
            callback: 回调函数，接受帧（NumPy数组）和时间戳参数
        """
        if not self.client:
            return
        
        with self.callback_lock:
            self.user_callback = callback
            
            # C++回调封装函数
            @RTSP_FRAME_CALLBACK
            def frame_callback(user_data, data, width, height, timestamp):
                if self.user_callback:
                    try:
                        # 将C++指针数据转换为NumPy数组
                        # 创建一个新的NumPy数组，有自己的内存，避免指针失效问题
                        size = width * height * 3  # RGB格式
                        buffer = (ctypes.c_uint8 * size).from_address(ctypes.addressof(data.contents))
                        frame = np.frombuffer(buffer, dtype=np.uint8, count=size).copy()
                        frame = frame.reshape((height, width, 3))
                        
                        # 调用用户提供的回调函数
                        self.user_callback(frame, timestamp)
                    
                    except Exception as e:
                        print(f"RTSP帧回调错误: {e}")
            
            # 保存回调引用，防止被垃圾回收
            self.callback = frame_callback
            
            # 设置C++端的回调
            self.lib.set_frame_callback(self.client, self.callback, None)
    
    def get_fps(self) -> float:
        """
        获取当前FPS（帧率）
        
        Returns:
            当前帧率
        """
        if not self.client:
            return 0.0
        
        return self.lib.get_fps(self.client)
    
    def _cleanup(self):
        """清理资源"""
        if hasattr(self, 'client') and self.client:
            self.stop()
            self.lib.destroy_rtsp_client(self.client)
            self.client = None
    
    def __del__(self):
        """析构函数"""
        self._cleanup()


# 简单测试
if __name__ == "__main__":
    import time
    import cv2
    
    print("RTSP/RTMP接口测试")
    
    try:
        # 测试RTSP客户端
        rtsp_url = "rtsp://admin:admin@192.168.1.100:554/stream"
        rtsp_client = RTSPClient(rtsp_url)
        
        # 设置帧回调
        def on_frame(frame, timestamp):
            print(f"收到RTSP帧: {frame.shape}, 时间戳: {timestamp}")
            cv2.imshow("RTSP Frame", frame)
            cv2.waitKey(1)
        
        rtsp_client.set_frame_callback(on_frame)
        
        # 初始化并启动
        if rtsp_client.initialize() and rtsp_client.start():
            print("RTSP客户端已启动")
            
            # 运行10秒
            for i in range(10):
                time.sleep(1)
                print(f"RTSP FPS: {rtsp_client.get_fps():.2f}")
            
            rtsp_client.stop()
        
        # 测试RTMP推流器
        rtmp_url = "rtmp://localhost/live/stream"
        rtmp_streamer = RTMPStreamer(rtmp_url, 640, 480)
        
        # 初始化并启动
        if rtmp_streamer.initialize() and rtmp_streamer.start():
            print("RTMP推流器已启动")
            
            # 创建测试帧
            test_frame = np.zeros((480, 640, 3), dtype=np.uint8)
            cv2.putText(test_frame, "RTMP Test", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            
            # 推送10帧
            for i in range(10):
                cv2.putText(test_frame, f"Frame {i}", (50, 100), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
                rtmp_streamer.push_frame(test_frame)
                time.sleep(1)
            
            rtmp_streamer.stop()
        
        print("测试完成")
    
    except Exception as e:
        print(f"测试错误: {e}")
    
    finally:
        cv2.destroyAllWindows() 