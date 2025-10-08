# 基于嵌入式AI的ROI区域视频传输系统设计与实现

### 声明
> **本项目为开源演示版本，仅包含基础功能实现。**
> 
> **如需获取完整商业版本（含高级特性及技术支持），请通过邮箱contact@skstudio.cn联系我们。**
> 
> **开源版本用户可获得有限的技术支持与问题解答。**
> 
> **彩旗开源交流QQ群：1022820973**

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
- 基于YOLOv11算法的目标检测（支持人、车等目标识别）
- 智能ROI（感兴趣区域）识别与处理
- 自适应编码策略（关键区域高码率，非关键区域低码率）
- 支持三种运行模式：客户端模式、服务端模式、本地处理模式
- 支持RTMP推流和RTSP流接入
- 实时视频流显示与监控

## 技术特点
- 基于算能SE5嵌入式AI开发平台
- 支持RTSP协议视频流接入
- 采用YOLOv11深度学习算法进行目标检测
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

## 快速开始

### 1. 克隆项目仓库
```bash
git clone https://gitee.com/Snake-Konginchrist/AI-Based-ROI-Video-Transmission-System.git
cd AI-Based-ROI-Video-Transmission-System
```

### 2. 安装依赖
```bash
# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或 venv\Scripts\activate  # Windows

# 安装Python依赖
pip install -r requirements.txt
```

### 3. 编译C++组件
```bash
# Linux/Mac
sudo apt-get install libavcodec-dev libavformat-dev libavutil-dev libswscale-dev pkg-config
cd src/cpp && make && cd ../..

# Windows (需要FFmpeg开发库)
cd src\cpp && make && cd ..\..
```

### 4. 运行系统
```bash
python main.py
```

## 使用说明
程序启动后会提示选择运行模式：
- **本地处理模式**：同时进行捕获和处理，无需网络传输
- **客户端模式**：捕获本地摄像头视频，推送至服务端处理
- **服务端模式**：接收客户端推送的视频流，进行AI处理后返回结果

可通过界面上的滑块实时调整ROI编码参数：
- **ROI区域QP值**：调整目标区域的编码质量（较低QP值=较高质量）
- **非ROI区域QP值**：调整背景区域的编码质量（较高QP值=较低质量）

## 项目结构
```
.
├── main.py                      # 主程序入口
├── src/                         # 源代码
│   ├── python/                  # Python代码
│   │   ├── gui/                 # 图形用户界面
│   │   ├── stream/              # 视频流处理
│   │   ├── yolo/                # YOLOv11 AI处理器
│   │   └── cli/                 # 命令行接口
│   └── cpp/                     # C++代码
│       ├── rtmp/                # RTMP推流实现
│       ├── rtsp/                # RTSP客户端实现
│       └── Makefile             # 编译脚本
├── lib/                         # 编译后的C++库文件
├── requirements.txt             # Python依赖列表
└── README.md                    # 项目文档
```

## 技术栈
- Python 3.8+
- OpenCV
- Ultralytics YOLOv11
- Tkinter (GUI)
- C++/FFmpeg (RTMP推流)

## 联系方式
- 项目主页：[GitHub](https://github.com/Snake-Konginchrist/AI-Based-ROI-Video-Transmission-System)
- 技术支持：developer@skstudio.cn
- 商务合作：contact@skstudio.cn

## 版权声明
本项目采用MIT开源协议，详情请参见LICENSE文件。

## 相关文档
- [常见问题解答 (FAQ)](FAQ.md) - 使用过程中遇到的问题及解决方案
- [开发指南 (DEVELOPMENT.md)](DEVELOPMENT.md) - 详细的开发文档和技术架构说明

## 星标历史
[![Star History Chart](https://api.star-history.com/svg?repos=Snake-Konginchrist/AI-Based-ROI-Video-Transmission-System&type=Date)](https://www.star-history.com/#Snake-Konginchrist/AI-Based-ROI-Video-Transmission-System&Date)