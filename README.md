# 基于AI的视频流处理系统

## 项目介绍
这个项目实现了一个基于人工智能的视频流处理系统，它使用计算机的摄像头捕获实时视频，应用YOLO算法进行对象检测，并同时在用户界面上展示原始视频流和处理后的视频流。
## 项目要求
本课题以嵌入式AI开发平台为基础，在算能SE5盒子上实现对摄像头的视频流解码后，通过AI识别到关键区域如人和车辆后，对关键的ROI区域采用高码率（低QP），对非关键区域采用低码率（高QP）编码。并将编码后的视频流通过RTMP协议推送到服务器。
1. 基于国产嵌入式AI开发平台：算能SE5盒子；
2. 支持通过RTSP协议拉取摄像头视频流；
3. 支持对视频流进行解码；
4. 通过YOLO算法对视频流进行AI识别人员、车辆；
5. 根据YOLO识别后的结果找出重点区域，对重点区域采用高码率（低QP），对非关键区域采用低码率（高QP）编码；
6. 将识别后的结果通过RTMP协议推送到流媒体服务器。

## 功能特点
- 实时捕获电脑摄像头的视频流。
- 使用YOLO算法进行实时对象检测。
- 显示原始视频和AI处理后的视频。
- 界面友好，操作简单。
## 安装指南
### 环境要求
- Python 3.12.1（推荐使用虚拟环境）
- pip 24.0 （Python包管理器）
### 安装步骤
1. 克隆仓库到本地：
   ```bash
   git clone https://gitee.com/Snake-Konginchrist/AI-Based-ROI-Video-Transmission-System.git
   ```
2. 安装所需的依赖包：
   ```bash
   pip install -r requirements.txt
   ```
## 使用方法
运行主程序：
```bash
python main.py
```
## 文件结构
- `main.py`: 主程序入口。
- `camera_stream.py`: 负责视频流捕获。
- `ai_processor.py`: 包含YOLO算法，进行视频流处理。
- `stream_display.py`: 负责在GUI中显示视频。
- `requirements.txt`: 项目依赖列表。
## 贡献指南
欢迎任何形式的贡献。请确保您的代码符合项目的代码规范，并通过所有测试。
## 许可证
此项目在MIT许可证下发布。
## 联系方式
- GitHub: [Snake-Konginchrist](https://github.com/Snake-Konginchrist)
- Gitee: [Snake-Konginchrist](https://gitee.com/Snake-Konginchrist)
- Email: developer@skstudio.cn（优先）
## 致谢
- 感谢所有为该项目做出贡献的开发者。
- 特别感谢YOLO算法的开发者和贡献者。
---