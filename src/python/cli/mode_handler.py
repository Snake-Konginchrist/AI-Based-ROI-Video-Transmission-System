#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
命令行界面的模式处理器模块
提供命令行界面下的本地/客户端/服务端模式处理
"""
import threading
import time
import cv2
import socket
import struct
import pickle
import numpy as np
import os


class CLIBaseHandler:
    """命令行界面处理器基类"""
    def __init__(self, camera_stream, ai_processor):
        self.camera_stream = camera_stream
        self.ai_processor = ai_processor
        self.running = False
        self.thread = None
    
    def update_status(self, message):
        """更新状态信息"""
        print(f"状态: {message}")
    
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


class CLILocalHandler(CLIBaseHandler):
    """命令行界面本地处理模式处理器"""
    def __init__(self, camera_stream, ai_processor):
        super().__init__(camera_stream, ai_processor)
        
        # 默认QP值
        self.roi_qp = 15
        self.non_roi_qp = 35
        
        # 创建本地模式的配置线程
        self.config_thread = threading.Thread(target=self.config_loop)
        self.config_thread.daemon = True
        self.config_thread.start()
    
    def config_loop(self):
        """配置循环，允许用户修改参数"""
        print("\n=== 本地处理模式配置 ===")
        print("您可以通过修改以下参数来调整视频质量:")
        print(f"- ROI区域QP值: {self.roi_qp} (低值=高质量)")
        print(f"- 非ROI区域QP值: {self.non_roi_qp} (高值=低质量)")
        
        while self.running:
            try:
                print("\n输入参数编号进行修改:")
                print("1. 修改ROI区域QP值")
                print("2. 修改非ROI区域QP值")
                print("3. 显示当前设置")
                print("0. 返回 (继续处理)")
                
                choice = input("\n请选择 (0-3): ")
                
                if choice == '1':
                    try:
                        value = int(input("输入新的ROI区域QP值 (5-40): "))
                        if 5 <= value <= 40:
                            self.roi_qp = value
                            print(f"ROI区域QP值已更新为: {self.roi_qp}")
                        else:
                            print("无效值，请输入5-40之间的整数")
                    except ValueError:
                        print("请输入有效的整数")
                        
                elif choice == '2':
                    try:
                        value = int(input("输入新的非ROI区域QP值 (5-40): "))
                        if 5 <= value <= 40:
                            self.non_roi_qp = value
                            print(f"非ROI区域QP值已更新为: {self.non_roi_qp}")
                        else:
                            print("无效值，请输入5-40之间的整数")
                    except ValueError:
                        print("请输入有效的整数")
                
                elif choice == '3':
                    print(f"\n当前设置:")
                    print(f"- ROI区域QP值: {self.roi_qp} (低值=高质量)")
                    print(f"- 非ROI区域QP值: {self.non_roi_qp} (高值=低质量)")
                
                elif choice == '0':
                    print("返回处理...")
                    break
                
                else:
                    print("无效选择，请重新输入!")
                    
            except KeyboardInterrupt:
                break
    
    def process_loop(self):
        """本地处理循环"""
        self.update_status("本地处理中...")
        
        # 创建输出目录
        output_dir = "output"
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        # 检查是否支持GUI
        has_gui_support = True
        try:
            # 尝试创建两个显示窗口，分别显示原始视频和处理后的视频
            original_window = "Original Video - AI ROI System"
            processed_window = "Processed Video - AI ROI System"
            
            cv2.namedWindow(original_window, cv2.WINDOW_NORMAL)
            cv2.resizeWindow(original_window, 640, 480)  # 设置合适的窗口大小
            
            cv2.namedWindow(processed_window, cv2.WINDOW_NORMAL)
            cv2.resizeWindow(processed_window, 640, 480)  # 设置合适的窗口大小
            
            # 移动窗口位置，使它们不重叠
            cv2.moveWindow(original_window, 50, 100)
            cv2.moveWindow(processed_window, 700, 100)
            
            print("已创建视频显示窗口")
        except cv2.error as e:
            has_gui_support = False
            print("警告: 无法创建视频窗口，可能是因为OpenCV没有GUI支持")
            print("错误详情:", str(e))
            print("您可以安装带GUI支持的OpenCV: pip install opencv-contrib-python")
            print("处理将继续，但不会显示视频窗口")
            
        frame_count = 0
        last_fps_time = time.time()
        fps = 0
        
        # 视频显示检查标志
        showed_video = False
        
        while self.running:
            # 获取帧
            frame = self.camera_stream.get_frame()
            if frame is None:
                time.sleep(0.01)
                continue
            
            # 计算FPS
            frame_count += 1
            current_time = time.time()
            elapsed = current_time - last_fps_time
            
            if elapsed >= 1.0:
                fps = frame_count / elapsed
                frame_count = 0
                last_fps_time = current_time
                print(f"FPS: {fps:.1f}")
            
            # 在原始帧上添加信息
            original_display = frame.copy()
            cv2.putText(
                original_display, 
                f"Original Video - FPS: {fps:.1f}", 
                (10, 30), 
                cv2.FONT_HERSHEY_SIMPLEX, 
                0.7, 
                (0, 255, 0), 
                2
            )
            
            # AI处理帧
            try:
                # AI检测，获取ROI区域
                processed_frame, rois = self.ai_processor.process_frame(
                    frame.copy(), 
                    return_rois=True, 
                    roi_qp=self.roi_qp, 
                    non_roi_qp=self.non_roi_qp
                )
                
                # 在处理后的图像上添加FPS和QP信息
                cv2.putText(
                    processed_frame, 
                    f"Processed Video - FPS: {fps:.1f}", 
                    (10, 30), 
                    cv2.FONT_HERSHEY_SIMPLEX, 
                    0.7, 
                    (0, 255, 255), 
                    2
                )
                
                cv2.putText(
                    processed_frame, 
                    f"ROI QP: {self.roi_qp} / Non-ROI QP: {self.non_roi_qp}", 
                    (10, 70), 
                    cv2.FONT_HERSHEY_SIMPLEX, 
                    0.7, 
                    (0, 255, 255), 
                    2
                )
                
                # 如果支持GUI，显示视频帧
                if has_gui_support:
                    try:
                        # 显示原始视频
                        cv2.imshow(original_window, original_display)
                        
                        # 显示处理后的视频
                        cv2.imshow(processed_window, processed_frame)
                        
                        # 检测是否已经显示视频
                        if not showed_video:
                            showed_video = True
                            print("Video windows are now displayed")
                            print("Original video window title:", original_window)
                            print("Processed video window title:", processed_window)
                        
                        # 检测键盘输入，按ESC键退出
                        key = cv2.waitKey(1) & 0xFF
                        if key == 27:  # ESC键
                            print("用户按ESC键退出")
                            self.running = False
                            break
                    except Exception as e:
                        print(f"显示视频帧时出错: {e}")
                        has_gui_support = False
                
                # 保存处理后的图像 (每10帧保存一次，避免产生太多文件)
                if frame_count % 10 == 0:
                    filename = os.path.join(output_dir, f"frame_{int(time.time())}.jpg")
                    cv2.imwrite(filename, processed_frame)
                    if not has_gui_support:
                        print(f"已保存处理后的图像到: {filename}")
                
                # 更新ROI信息
                if rois:
                    objects = [f"{roi['class']}({roi['confidence']:.2f})" for roi in rois]
                    self.update_status(f"检测到 {len(rois)} 个目标: {', '.join(objects)}")
                
            except Exception as e:
                self.update_status(f"处理错误: {e}")
            
            # 控制帧率
            time.sleep(0.01)
        
        # 如果支持GUI，关闭窗口
        if has_gui_support:
            try:
                cv2.destroyWindow(original_window)
                cv2.destroyWindow(processed_window)
                cv2.destroyAllWindows()  # 确保所有窗口都被关闭
            except:
                pass


class CLIClientHandler(CLIBaseHandler):
    """命令行界面客户端模式处理器"""
    def __init__(self, camera_stream, ai_processor):
        super().__init__(camera_stream, ai_processor)
        
        # 网络设置
        self.server_ip = "127.0.0.1"  # 默认服务器IP
        self.server_port = 8000       # 默认服务器端口
        self.client_socket = None     # 客户端套接字
        self.connected = False        # 连接状态
        
        # 默认QP值
        self.roi_qp = 15
        self.non_roi_qp = 35
        
        # 创建配置线程
        self.config_thread = threading.Thread(target=self.config_loop)
        self.config_thread.daemon = True
        self.config_thread.start()
    
    def config_loop(self):
        """配置循环，允许用户修改参数"""
        print("\n=== 客户端模式配置 ===")
        
        while self.running:
            try:
                print("\n输入参数编号进行修改:")
                print("1. 设置服务器IP地址")
                print("2. 设置服务器端口") 
                print("3. 连接到服务器" if not self.connected else "3. 断开连接")
                print("4. 修改ROI区域QP值")
                print("5. 修改非ROI区域QP值")
                print("6. 显示当前设置")
                print("0. 返回 (继续处理)")
                
                choice = input("\n请选择 (0-6): ")
                
                if choice == '1':
                    if self.connected:
                        print("请先断开连接再修改服务器IP")
                        continue
                    ip = input(f"输入服务器IP地址 (当前: {self.server_ip}): ")
                    self.server_ip = ip
                    print(f"服务器IP已设置为: {self.server_ip}")
                    
                elif choice == '2':
                    if self.connected:
                        print("请先断开连接再修改服务器端口")
                        continue
                    try:
                        port = int(input(f"输入服务器端口 (当前: {self.server_port}): "))
                        if 1 <= port <= 65535:
                            self.server_port = port
                            print(f"服务器端口已设置为: {self.server_port}")
                        else:
                            print("无效端口，请输入1-65535之间的整数")
                    except ValueError:
                        print("请输入有效的整数")
                
                elif choice == '3':
                    if not self.connected:
                        self.connect_to_server()
                    else:
                        self.disconnect_from_server()
                
                elif choice == '4':
                    try:
                        value = int(input("输入新的ROI区域QP值 (5-40): "))
                        if 5 <= value <= 40:
                            self.roi_qp = value
                            print(f"ROI区域QP值已更新为: {self.roi_qp}")
                        else:
                            print("无效值，请输入5-40之间的整数")
                    except ValueError:
                        print("请输入有效的整数")
                
                elif choice == '5':
                    try:
                        value = int(input("输入新的非ROI区域QP值 (5-40): "))
                        if 5 <= value <= 40:
                            self.non_roi_qp = value
                            print(f"非ROI区域QP值已更新为: {self.non_roi_qp}")
                        else:
                            print("无效值，请输入5-40之间的整数")
                    except ValueError:
                        print("请输入有效的整数")
                
                elif choice == '6':
                    print(f"\n当前设置:")
                    print(f"- 服务器IP: {self.server_ip}")
                    print(f"- 服务器端口: {self.server_port}")
                    print(f"- 连接状态: {'已连接' if self.connected else '未连接'}")
                    print(f"- ROI区域QP值: {self.roi_qp} (低值=高质量)")
                    print(f"- 非ROI区域QP值: {self.non_roi_qp} (高值=低质量)")
                
                elif choice == '0':
                    print("返回处理...")
                    break
                
                else:
                    print("无效选择，请重新输入!")
                    
            except KeyboardInterrupt:
                break
    
    def connect_to_server(self):
        """连接到服务器"""
        if self.connected:
            print("已经连接到服务器")
            return
        
        try:
            # 创建TCP套接字
            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client_socket.connect((self.server_ip, self.server_port))
            self.connected = True
            print(f"已连接到服务器: {self.server_ip}:{self.server_port}")
        except Exception as e:
            print(f"连接服务器失败: {e}")
            self.client_socket = None
    
    def disconnect_from_server(self):
        """断开服务器连接"""
        if not self.connected:
            print("未连接到服务器")
            return
        
        try:
            if self.client_socket:
                self.client_socket.close()
                self.client_socket = None
            self.connected = False
            print("已断开服务器连接")
        except Exception as e:
            print(f"断开连接时出错: {e}")
            self.client_socket = None
            self.connected = False
    
    def process_loop(self):
        """客户端处理循环"""
        self.update_status("客户端处理中...")
        
        # 检查是否支持GUI
        has_gui_support = True
        try:
            # 尝试创建两个显示窗口，分别显示原始视频和处理后的视频
            original_window = "Client - Original Video"
            processed_window = "Client - Processed Video"
            
            cv2.namedWindow(original_window, cv2.WINDOW_NORMAL)
            cv2.resizeWindow(original_window, 640, 480)  # 设置合适的窗口大小
            
            cv2.namedWindow(processed_window, cv2.WINDOW_NORMAL)
            cv2.resizeWindow(processed_window, 640, 480)  # 设置合适的窗口大小
            
            # 移动窗口位置，使它们不重叠
            cv2.moveWindow(original_window, 50, 100)
            cv2.moveWindow(processed_window, 700, 100)
            
            print("已创建视频显示窗口")
        except cv2.error as e:
            has_gui_support = False
            print("警告: 无法创建视频窗口，可能是因为OpenCV没有GUI支持")
            print("错误详情:", str(e))
            print("您可以安装带GUI支持的OpenCV: pip install opencv-contrib-python")
            print("处理将继续，但不会显示视频窗口")
        
        # 创建输出目录（用于保存图像）
        output_dir = "output"
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            
        frame_count = 0
        last_fps_time = time.time()
        fps = 0
        
        # 视频显示检查标志
        showed_video = False
        
        while self.running:
            # 获取帧
            frame = self.camera_stream.get_frame()
            if frame is None:
                time.sleep(0.01)
                continue
            
            # 计算FPS
            frame_count += 1
            current_time = time.time()
            elapsed = current_time - last_fps_time
            
            if elapsed >= 1.0:
                fps = frame_count / elapsed
                frame_count = 0
                last_fps_time = current_time
                print(f"FPS: {fps:.1f}")
            
            # 在原始帧上添加信息
            original_display = frame.copy()
            cv2.putText(
                original_display, 
                f"Original Video - FPS: {fps:.1f}", 
                (10, 30), 
                cv2.FONT_HERSHEY_SIMPLEX, 
                0.7, 
                (0, 255, 0), 
                2
            )
            
            # 如果已连接到服务器，发送处理后的数据
            if self.connected and self.client_socket:
                try:
                    # AI检测，获取ROI区域
                    processed_frame, rois = self.ai_processor.process_frame(
                        frame.copy(), 
                        return_rois=True, 
                        roi_qp=self.roi_qp, 
                        non_roi_qp=self.non_roi_qp
                    )
                    
                    # 在处理后的图像上添加FPS和连接状态信息
                    cv2.putText(
                        processed_frame, 
                        f"Processed Video - FPS: {fps:.1f}", 
                        (10, 30), 
                        cv2.FONT_HERSHEY_SIMPLEX, 
                        0.7, 
                        (0, 255, 255), 
                        2
                    )
                    
                    cv2.putText(
                        processed_frame, 
                        f"ROI QP: {self.roi_qp} / Non-ROI QP: {self.non_roi_qp}", 
                        (10, 70), 
                        cv2.FONT_HERSHEY_SIMPLEX, 
                        0.7, 
                        (0, 255, 255), 
                        2
                    )
                    
                    cv2.putText(
                        processed_frame, 
                        f"Connected to: {self.server_ip}:{self.server_port}", 
                        (10, 110), 
                        cv2.FONT_HERSHEY_SIMPLEX, 
                        0.7, 
                        (0, 255, 255), 
                        2
                    )
                    
                    # 如果支持GUI，显示视频帧
                    if has_gui_support:
                        try:
                            # 显示原始视频
                            cv2.imshow(original_window, original_display)
                            
                            # 显示处理后的视频
                            cv2.imshow(processed_window, processed_frame)
                            
                            # 检测是否已经显示视频
                            if not showed_video:
                                showed_video = True
                                print("Video windows are now displayed")
                                print("Original video window title:", original_window)
                                print("Processed video window title:", processed_window)
                            
                            # 检测键盘输入，按ESC键退出
                            key = cv2.waitKey(1) & 0xFF
                            if key == 27:  # ESC键
                                print("用户按ESC键退出")
                                self.running = False
                                break
                        except Exception as e:
                            print(f"显示视频帧时出错: {e}")
                            has_gui_support = False
                    
                    # 保存处理后的图像（每10帧保存一次）
                    if frame_count % 10 == 0:
                        filename = os.path.join(output_dir, f"client_frame_{int(time.time())}.jpg")
                        cv2.imwrite(filename, processed_frame)
                        if not has_gui_support:
                            print(f"已保存处理后的图像到: {filename}")
                    
                    # 准备发送数据
                    data = {
                        'frame': processed_frame,
                        'rois': rois
                    }
                    
                    # 序列化数据
                    data_bytes = pickle.dumps(data)
                    
                    # 发送数据大小
                    size = len(data_bytes)
                    size_bytes = struct.pack("!I", size)
                    self.client_socket.sendall(size_bytes)
                    
                    # 发送数据
                    self.client_socket.sendall(data_bytes)
                    
                    # 更新ROI信息
                    if rois:
                        objects = [f"{roi['class']}({roi['confidence']:.2f})" for roi in rois]
                        self.update_status(f"发送: 检测到 {len(rois)} 个目标: {', '.join(objects)}")
                    
                except (socket.error, BrokenPipeError) as e:
                    print(f"发送数据时出错, 断开连接: {e}")
                    self.disconnect_from_server()
                except Exception as e:
                    print(f"处理错误: {e}")
            else:
                # 未连接状态，只显示原始视频
                # 在图像上添加未连接状态
                display_frame = frame.copy()
                cv2.putText(
                    display_frame, 
                    "Processed Video - Not Connected - FPS: {:.1f}".format(fps), 
                    (10, 30), 
                    cv2.FONT_HERSHEY_SIMPLEX, 
                    0.7, 
                    (0, 0, 255), 
                    2
                )
                
                # 如果支持GUI，显示视频帧
                if has_gui_support:
                    try:
                        # 显示原始视频
                        cv2.imshow(original_window, original_display)
                        
                        # 显示处理前的视频（未连接状态）
                        cv2.imshow(processed_window, display_frame)
                        
                        # 检测是否已经显示视频
                        if not showed_video:
                            showed_video = True
                            print("Video windows are now displayed")
                            print("Original video window title:", original_window)
                            print("Processed video window title:", processed_window)
                        
                        # 检测键盘输入，按ESC键退出
                        key = cv2.waitKey(1) & 0xFF
                        if key == 27:  # ESC键
                            print("用户按ESC键退出")
                            self.running = False
                            break
                    except Exception as e:
                        print(f"显示视频帧时出错: {e}")
                        has_gui_support = False
                
                # 保存原始图像（每10帧保存一次）
                if frame_count % 10 == 0:
                    filename = os.path.join(output_dir, f"client_original_{int(time.time())}.jpg")
                    cv2.imwrite(filename, display_frame)
                    if not has_gui_support:
                        print(f"已保存原始图像到: {filename}")
            
            # 控制帧率
            time.sleep(0.01)
        
        # 如果支持GUI，关闭窗口
        if has_gui_support:
            try:
                cv2.destroyWindow(original_window)
                cv2.destroyWindow(processed_window)
                cv2.destroyAllWindows()  # 确保所有窗口都被关闭
            except:
                pass
    
    def stop(self):
        """停止处理"""
        self.disconnect_from_server()
        super().stop()


class CLIServerHandler(CLIBaseHandler):
    """命令行界面服务端模式处理器"""
    def __init__(self, camera_stream, ai_processor):
        super().__init__(camera_stream, ai_processor)
        
        # 网络设置
        self.server_ip = "0.0.0.0"  # 监听所有网络接口
        self.server_port = 8000     # 默认服务器端口
        self.server_socket = None   # 服务器套接字
        self.running_server = False # 服务器运行状态
        
        # 客户端连接
        self.clients = []  # 客户端列表
        self.clients_lock = threading.Lock()  # 线程锁
        
        # 创建配置线程
        self.config_thread = threading.Thread(target=self.config_loop)
        self.config_thread.daemon = True
        self.config_thread.start()
    
    def config_loop(self):
        """配置循环，允许用户修改参数"""
        print("\n=== 服务端模式配置 ===")
        
        while self.running:
            try:
                print("\n输入参数编号进行修改:")
                print("1. 设置监听端口")
                print("2. 启动服务器" if not self.running_server else "2. 停止服务器")
                print("3. 显示客户端连接")
                print("4. 显示当前设置")
                print("0. 返回 (继续处理)")
                
                choice = input("\n请选择 (0-4): ")
                
                if choice == '1':
                    if self.running_server:
                        print("请先停止服务器再修改端口")
                        continue
                    try:
                        port = int(input(f"输入监听端口 (当前: {self.server_port}): "))
                        if 1 <= port <= 65535:
                            self.server_port = port
                            print(f"监听端口已设置为: {self.server_port}")
                        else:
                            print("无效端口，请输入1-65535之间的整数")
                    except ValueError:
                        print("请输入有效的整数")
                
                elif choice == '2':
                    if not self.running_server:
                        self.start_server()
                    else:
                        self.stop_server()
                
                elif choice == '3':
                    with self.clients_lock:
                        if not self.clients:
                            print("当前没有客户端连接")
                        else:
                            print(f"当前连接的客户端 ({len(self.clients)}):")
                            for i, (client, addr) in enumerate(self.clients, 1):
                                print(f"  {i}. {addr[0]}:{addr[1]}")
                
                elif choice == '4':
                    print(f"\n当前设置:")
                    print(f"- 监听地址: {self.server_ip}")
                    print(f"- 监听端口: {self.server_port}")
                    print(f"- 服务器状态: {'运行中' if self.running_server else '已停止'}")
                    with self.clients_lock:
                        print(f"- 连接的客户端数量: {len(self.clients)}")
                
                elif choice == '0':
                    print("返回处理...")
                    break
                
                else:
                    print("无效选择，请重新输入!")
                    
            except KeyboardInterrupt:
                break
    
    def start_server(self):
        """启动服务器"""
        if self.running_server:
            print("服务器已在运行")
            return
        
        try:
            # 创建TCP套接字
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind((self.server_ip, self.server_port))
            self.server_socket.listen(5)
            self.server_socket.settimeout(0.5)  # 设置超时，便于服务器停止
            
            # 启动服务器线程
            self.running_server = True
            self.server_thread = threading.Thread(target=self.server_loop)
            self.server_thread.daemon = True
            self.server_thread.start()
            
            print(f"服务器已启动，监听 {self.server_ip}:{self.server_port}")
        except Exception as e:
            print(f"启动服务器失败: {e}")
            if self.server_socket:
                self.server_socket.close()
                self.server_socket = None
            self.running_server = False
    
    def stop_server(self):
        """停止服务器"""
        if not self.running_server:
            print("服务器未运行")
            return
        
        self.running_server = False
        
        # 关闭所有客户端连接
        with self.clients_lock:
            for client, _ in self.clients:
                try:
                    client.close()
                except:
                    pass
            self.clients.clear()
        
        # 关闭服务器套接字
        if self.server_socket:
            try:
                self.server_socket.close()
            except:
                pass
            self.server_socket = None
        
        if hasattr(self, 'server_thread'):
            self.server_thread.join(timeout=1.0)
        
        print("服务器已停止")
    
    def server_loop(self):
        """服务器线程主循环"""
        print("等待客户端连接...")
        
        while self.running_server and self.server_socket:
            try:
                # 接受客户端连接
                client_socket, client_address = self.server_socket.accept()
                
                # 添加到客户端列表
                with self.clients_lock:
                    self.clients.append((client_socket, client_address))
                
                print(f"客户端已连接: {client_address[0]}:{client_address[1]}")
                
                # 为每个客户端创建处理线程
                client_thread = threading.Thread(
                    target=self.handle_client,
                    args=(client_socket, client_address)
                )
                client_thread.daemon = True
                client_thread.start()
                
            except socket.timeout:
                continue  # 超时，继续等待
            except Exception as e:
                if self.running_server:
                    print(f"接受连接时出错: {e}")
                break
    
    def handle_client(self, client_socket, client_address):
        """处理客户端连接"""
        print(f"开始处理客户端 {client_address[0]}:{client_address[1]} 的数据")
        
        # 检查是否支持GUI
        has_gui_support = True
        try:
            # 尝试创建显示窗口
            window_name = f"Server - Received Video from {client_address[0]}:{client_address[1]}"
            cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
            cv2.resizeWindow(window_name, 960, 540)  # 设置合适的窗口大小
            # 移动窗口到合适位置
            cv2.moveWindow(window_name, 400, 100)
            print(f"已创建视频显示窗口: {window_name}")
        except cv2.error as e:
            has_gui_support = False
            print("警告: 无法创建视频窗口，可能是因为OpenCV没有GUI支持")
            print("错误详情:", str(e))
            print("您可以安装带GUI支持的OpenCV: pip install opencv-contrib-python")
            print("处理将继续，但不会显示视频窗口")
        
        # 创建输出目录
        output_dir = "output"
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        # 视频显示检查标志
        showed_video = False
        
        try:
            while self.running_server:
                # 接收数据大小
                size_bytes = client_socket.recv(4)
                if not size_bytes:
                    break  # 连接已关闭
                
                size = struct.unpack("!I", size_bytes)[0]
                
                # 接收数据
                data_bytes = b""
                remaining = size
                
                while remaining > 0:
                    chunk = client_socket.recv(min(remaining, 4096))
                    if not chunk:
                        raise Exception("连接中断")
                    data_bytes += chunk
                    remaining -= len(chunk)
                
                # 反序列化数据
                data = pickle.loads(data_bytes)
                frame = data.get('frame')
                rois = data.get('rois', [])
                
                if frame is not None:
                    # 处理接收到的帧
                    if rois:
                        objects = [f"{roi['class']}({roi['confidence']:.2f})" for roi in rois]
                        print(f"接收: 检测到 {len(rois)} 个目标: {', '.join(objects)}")
                    
                    # 在图像上添加信息
                    cv2.putText(
                        frame, 
                        f"Server Received - From {client_address[0]}:{client_address[1]}", 
                        (10, 30), 
                        cv2.FONT_HERSHEY_SIMPLEX, 
                        0.7, 
                        (0, 255, 255), 
                        2
                    )
                    
                    cv2.putText(
                        frame, 
                        f"Detected Objects: {len(rois)}", 
                        (10, 70), 
                        cv2.FONT_HERSHEY_SIMPLEX, 
                        0.7, 
                        (0, 255, 255), 
                        2
                    )
                    
                    # 如果支持GUI，显示接收的视频帧
                    if has_gui_support:
                        try:
                            cv2.imshow(window_name, frame)
                            
                            # 检测是否已经显示视频
                            if not showed_video:
                                showed_video = True
                                print("Video windows are now displayed")
                                print("Video window title:", window_name)
                            
                            # 检测键盘输入，按ESC键退出
                            key = cv2.waitKey(1) & 0xFF
                            if key == 27:  # ESC键
                                print("用户按ESC键退出")
                                break
                        except Exception as e:
                            print(f"显示视频帧时出错: {e}")
                            has_gui_support = False
                    
                    # 保存接收到的图像 (每10帧保存一次)
                    if time.time() % 10 < 0.1:
                        filename = os.path.join(output_dir, f"received_{int(time.time())}.jpg")
                        cv2.imwrite(filename, frame)
                        if not has_gui_support:
                            print(f"已保存接收的图像到: {filename}")
                
        except (socket.error, BrokenPipeError) as e:
            print(f"客户端 {client_address[0]}:{client_address[1]} 断开连接: {e}")
        except Exception as e:
            print(f"处理客户端数据时出错: {e}")
        finally:
            # 关闭客户端连接
            try:
                client_socket.close()
            except:
                pass
            
            # 从客户端列表中移除
            with self.clients_lock:
                self.clients = [(c, a) for c, a in self.clients if c != client_socket]
            
            # 如果支持GUI，关闭窗口
            if has_gui_support:
                try:
                    cv2.destroyWindow(window_name)
                    cv2.destroyAllWindows()  # 确保所有窗口都被关闭
                except:
                    pass
            
            print(f"客户端 {client_address[0]}:{client_address[1]} 已断开连接")
    
    def process_loop(self):
        """服务端处理循环"""
        self.update_status("服务端处理中...")
        
        # 运行直到停止
        while self.running:
            time.sleep(0.5)
    
    def stop(self):
        """停止处理"""
        self.stop_server()
        super().stop() 