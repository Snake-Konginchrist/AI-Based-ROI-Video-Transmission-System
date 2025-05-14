# 基于嵌入式AI的ROI区域视频传输系统设计与实现

### 声明
> **本项目为开源演示版本，仅包含基础功能实现。**
> 
> **如需获取完整商业版本（含高级特性及技术支持），请通过邮箱contact@skstudio.cn联系我们。**
> 
> **开源版本用户可获得有限的技术支持与问题解答。**

## 项目简介
本项目是一个基于人工智能的视频流处理系统，采用计算机视觉和深度学习技术，实现了实时视频流的智能处理与传输。系统通过摄像头捕获实时视频，利用YOLO算法进行目标检测，并在用户界面上同步展示原始视频流和处理后的视频流。

## 项目背景
随着视频监控和智能安防需求的不断增长，如何在有限的网络带宽下实现高质量的视频传输成为一个重要课题。本项目通过结合嵌入式AI技术和智能编码策略，实现了对视频关键区域的智能识别和差异化编码，有效提升了视频传输效率。

## 项目要求
本课题以嵌入式AI开发平台为基础，在算能SE5盒子上实现对摄像头的视频流解码后，通过AI识别到关键区域如人和车辆后，对关键的ROI区域采用高码率（低QP），对非关键区域采用低码率（高QP）编码。并将编码后的视频流通过RTMP协议推送到服务器。

具体实现要求：
1. 基于国产嵌入式AI开发平台：算能SE5盒子；
2. 支持通过RTSP协议拉取摄像头视频流；
3. 支持对视频流进行解码；
4. 通过YOLO算法对视频流进行AI识别人员、车辆；
5. 根据YOLO识别后的结果找出重点区域，对重点区域采用高码率（低QP），对非关键区域采用低码率（高QP）编码；
6. 将识别后的结果通过RTMP协议推送到流媒体服务器。

## 核心功能
- 实时视频流捕获与处理
- 基于YOLO算法的目标检测（支持人、车等目标识别）
- 智能ROI（感兴趣区域）识别与处理
- 自适应编码策略（关键区域高码率，非关键区域低码率）
- 支持三种运行模式：客户端模式、服务端模式、本地处理模式
- 支持RTMP推流和RTSP流接入
- 实时视频流显示与监控

## 技术特点
- 基于算能SE5嵌入式AI开发平台
- 支持RTSP协议视频流接入
- 采用YOLO深度学习算法进行目标检测
- 智能QP值调整实现差异化编码
- 支持RTMP协议视频流推送
- 友好的图形用户界面
- Python与C++混合编程实现高性能

## 系统要求
### 硬件要求
- 算能SE5 AI开发平台或同等性能的计算机
- 支持RTSP协议的摄像头设备（可选，用于实际部署）
- 网络连接设备（用于RTMP推流和RTSP接入）

### 软件要求
- Python 3.8+（推荐使用虚拟环境）
- FFmpeg 4.0+ 及开发库（用于编译C++部分）
- C++编译环境（GCC/MSVC）
- OpenCV 4.2+
- CUDA支持（可选，用于GPU加速）

## 安装部署
### 1. 克隆项目仓库
```bash
git clone https://gitee.com/Snake-Konginchrist/AI-Based-ROI-Video-Transmission-System.git
cd AI-Based-ROI-Video-Transmission-System
```

### 2. 创建并激活虚拟环境（推荐）
```bash
# Linux/Mac
python -m venv venv
source venv/bin/activate

# Windows
python -m venv venv
venv\Scripts\activate
```

### 3. 安装Python依赖
```bash
pip install -r requirements.txt
```

### 4. 编译C++组件
#### Linux/Mac
```bash
# 安装FFmpeg开发库
sudo apt-get install libavcodec-dev libavformat-dev libavutil-dev libswscale-dev pkg-config

# 编译C++库
cd src/cpp
make
cd ../..
```

#### Windows
```bash
# 请确保已安装FFmpeg开发库和pkg-config（可使用vcpkg或MSYS2）
# 使用MinGW或MSVC编译
cd src\cpp
make
cd ..\..
```

### 5. 验证安装
```bash
python -c "import cv2; print(f'OpenCV version: {cv2.__version__}')"
ls -la lib/  # 查看编译生成的库文件
```

## 使用说明
### 1. 启动系统
```bash
python main.py
```

### 2. 选择运行模式
程序启动后会提示选择运行模式：
- **客户端模式**：捕获本地摄像头视频，推送至服务端处理
- **服务端模式**：接收客户端推送的视频流，进行AI处理后返回结果
- **本地处理模式**：同时进行捕获和处理，无需网络传输

### 3. 配置参数
根据选择的模式不同，需要配置不同的参数：
- **客户端模式**：设置服务器地址和端口
- **服务端模式**：设置监听端口
- **本地处理模式**：配置摄像头设备

### 4. ROI编码参数调整
可通过界面上的滑块实时调整：
- **ROI区域QP值**：调整目标区域的编码质量（较低QP值=较高质量）
- **非ROI区域QP值**：调整背景区域的编码质量（较高QP值=较低质量）

## 项目结构
```
.
├── main.py                      # 主程序入口
├── models/                      # YOLO模型文件
│   ├── yolov3.weights           # YOLOv3权重文件
│   ├── yolov3.cfg               # YOLOv3配置文件
│   └── coco.names               # COCO数据集类别名称
├── lib/                         # 编译后的C++库文件
│   ├── librtmp_streamer.so      # RTMP推流库
│   └── librtsp_client.so        # RTSP客户端库
├── src/                         # 源代码
│   ├── python/                  # Python代码
│   │   ├── ai/                  # AI处理模块
│   │   │   └── processor.py     # YOLO处理器
│   │   └── stream/              # 视频流处理
│   │       ├── camera.py        # 摄像头接口
│   │       ├── display.py       # 视频显示
│   │       ├── mode_handler.py  # 模式处理器
│   │       └── cpp_interface.py # C++接口
│   └── cpp/                     # C++代码
│       ├── rtmp/                # RTMP推流实现
│       ├── rtsp/                # RTSP客户端实现
│       └── Makefile             # 编译脚本
├── requirements.txt             # Python依赖列表
└── README.md                    # 项目文档
```

## 常见问题解答
### 模型加载错误
如果遇到"无法加载YOLO模型"错误，可能是以下原因：
1. 模型文件不存在或损坏 - 程序会自动下载缺失的模型文件
2. OpenCV版本兼容性问题 - 尝试使用4.5.4或以下版本的OpenCV
3. 显存不足 - 调整模型配置降低资源消耗

### 推流失败
如果RTMP推流失败，请检查：
1. FFmpeg库是否正确安装
2. RTMP服务器地址是否可访问
3. C++库是否正确编译并放置在lib目录

### 视频卡顿
如果视频处理卡顿，可尝试：
1. 降低输入视频分辨率
2. 减小处理帧率
3. 启用GPU加速（需CUDA支持）

## 开发指南
1. 代码规范
   - 遵循PEP 8编码规范
   - 使用类型注解
   - 添加必要的注释和文档字符串

2. 测试要求
   - 单元测试覆盖率>80%
   - 集成测试确保功能完整性
   - 性能测试满足实时性要求

## 版本说明
- 当前版本：1.0.0
- 发布日期：2024-03-21

## 联系方式
- 项目主页：[Gitee](https://gitee.com/Snake-Konginchrist/AI-Based-ROI-Video-Transmission-System)
- 技术支持：developer@skstudio.cn
- 商务合作：contact@skstudio.cn

## 版权声明
本项目采用MIT开源协议，详情请参见LICENSE文件。

## 致谢
- 感谢算能科技提供的SE5开发平台支持
- 感谢YOLO算法开发团队的开源贡献
- 感谢所有为本项目提供帮助的开发者

## 最新更新：集成YOLOv11模型

我们升级了系统的AI处理器，从OpenCV DNN实现的YOLOv3迁移到ultralytics的YOLOv11模型。这带来了以下优势：

1. **更高的检测精度**：YOLOv11相比YOLOv3有显著的精度提升，在COCO数据集上mAP提高了约20%。
2. **更快的推理速度**：YOLOv11经过优化，具有更高的推理效率。
3. **更简单的集成**：无需手动下载和管理模型文件，ultralytics库会自动下载并缓存模型。
4. **更好的可扩展性**：可以轻松切换到YOLOv11系列的其他模型（如yolo11s.pt, yolo11m.pt等）或用于分割和姿态估计的专用模型。

## 如何使用

1. 安装依赖：
   ```
   pip install ultralytics opencv-python
   ```

2. 运行应用：
   ```
   python main.py
   ```

3. 在启动菜单中选择运行模式：
   - 本地处理模式：在本地处理视频流
   - 客户端模式：将视频流发送到服务器处理
   - 服务端模式：接收并处理客户端发送的视频流

## 关键特性

- 使用YOLOv11实时检测视频中的物体
- 对检测到的区域（ROI）使用高质量编码，对其他区域使用低质量编码
- 支持本地处理和网络分布式处理
- 可视化编码质量差异

## 目录结构

```
.
├── main.py                 # 主入口文件
├── src/
│   ├── python/             # Python实现部分
│   │   ├── gui/            # 图形用户界面
│   │   ├── stream/         # 视频流处理
│   │   ├── yolo/           # YOLOv11 AI处理器
│   │   └── __init__.py
│   └── cpp/                # C++实现部分（RTMP推流）
│       └── rtmp/           # RTMP推流模块
└── README.md
```

## 技术栈

- Python 3.8+
- OpenCV
- Ultralytics YOLOv11
- Tkinter (GUI)
- C++/FFmpeg (RTMP推流)

---