# AI-Based ROI Video Transmission System Design and Implementation

### Disclaimer
> **This project is an open-source demonstration version containing only basic functionality.**
> 
> **For the complete commercial version (with advanced features and technical support), please contact us at contact@skstudio.cn.**
> 
> **Open-source version users can receive limited technical support and issue resolution.**
> 
> **SK Open Source QQ Group: 1022820973**
> 
> **SK Open Source Discord Community: [Join our Discord](https://discord.gg/thWGWq7CwA)**

## Project Overview
This project is an AI-based video streaming processing system that utilizes computer vision and deep learning technologies to achieve intelligent processing and transmission of real-time video streams. The system captures real-time video through cameras, performs object detection using YOLO algorithms, and simultaneously displays both original and processed video streams on the user interface.

## Project Background
With the continuous growth of video surveillance and intelligent security demands, achieving high-quality video transmission under limited network bandwidth has become an important challenge. This project effectively improves video transmission efficiency by combining embedded AI technology with intelligent encoding strategies, enabling intelligent identification and differential encoding of key video regions.

## Project Requirements
This project is based on an embedded AI development platform, implementing video stream decoding from cameras on the Sophgo SE5 box. After AI recognition of key regions such as people and vehicles, it applies high bitrate (low QP) encoding for key ROI regions and low bitrate (high QP) encoding for non-key regions. The encoded video stream is then pushed to the server via the RTMP protocol.

Specific implementation requirements:
1. Based on domestic embedded AI development platform: Sophgo SE5 box;
2. Support pulling camera video streams through RTSP protocol;
3. Support video stream decoding;
4. Perform AI recognition of people and vehicles on video streams through YOLO algorithms;
5. Identify key regions based on YOLO recognition results, apply high bitrate (low QP) for key regions and low bitrate (high QP) for non-key regions;
6. Push recognition results to streaming media server through RTMP protocol.

## Core Features
- Real-time video stream capture and processing
- Object detection based on YOLOv11 algorithm (supports people, vehicles, and other target recognition)
- Intelligent ROI (Region of Interest) identification and processing
- Adaptive encoding strategy (high bitrate for key regions, low bitrate for non-key regions)
- Support for three operation modes: client mode, server mode, local processing mode
- Support for RTMP push streaming and RTSP stream access
- Real-time video stream display and monitoring

## Technical Features
- Based on Sophgo SE5 embedded AI development platform
- Support for RTSP protocol video stream access
- Adoption of YOLOv11 deep learning algorithm for object detection
- Intelligent QP value adjustment for differential encoding
- Support for RTMP protocol video stream pushing
- Friendly graphical user interface
- High-performance implementation through Python and C++ mixed programming

## System Requirements
### Hardware Requirements
- Sophgo SE5 AI development platform or computer with equivalent performance
- Camera device supporting RTSP protocol (optional, for actual deployment)
- Network connection device (for RTMP push streaming and RTSP access)

### Software Requirements
- Python 3.8+ (virtual environment recommended)
- FFmpeg 4.0+ and development libraries (for compiling C++ components)
- C++ compilation environment (GCC/MSVC)
- OpenCV 4.2+
- CUDA support (optional, for GPU acceleration)

## Quick Start

### 1. Clone Project Repository
```bash
git clone https://gitee.com/Snake-Konginchrist/AI-Based-ROI-Video-Transmission-System.git
cd AI-Based-ROI-Video-Transmission-System
```

### 2. Install Dependencies
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or venv\Scripts\activate  # Windows

# Install Python dependencies
pip install -r requirements.txt
```

### 3. Compile C++ Components
```bash
# Linux/Mac
sudo apt-get install libavcodec-dev libavformat-dev libavutil-dev libswscale-dev pkg-config
cd src/cpp && make && cd ../..

# Windows (requires FFmpeg development libraries)
cd src\cpp && make && cd ..\..
```

### 4. Run System
```bash
python main.py
```

## Usage Instructions
After program startup, you will be prompted to select operation mode:
- **Local Processing Mode**: Simultaneous capture and processing without network transmission
- **Client Mode**: Capture local camera video and push to server for processing
- **Server Mode**: Receive video streams pushed by clients, perform AI processing and return results

You can adjust ROI encoding parameters in real-time through interface sliders:
- **ROI Region QP Value**: Adjust encoding quality for target regions (lower QP value = higher quality)
- **Non-ROI Region QP Value**: Adjust encoding quality for background regions (higher QP value = lower quality)

## Project Structure
```
.
├── main.py                      # Main program entry
├── src/                         # Source code
│   ├── python/                  # Python code
│   │   ├── gui/                 # Graphical user interface
│   │   ├── stream/              # Video stream processing
│   │   ├── yolo/                # YOLOv11 AI processor
│   │   └── cli/                 # Command line interface
│   └── cpp/                     # C++ code
│       ├── rtmp/                # RTMP push streaming implementation
│       ├── rtsp/                # RTSP client implementation
│       └── Makefile             # Compilation script
├── lib/                         # Compiled C++ library files
├── requirements.txt             # Python dependency list
└── README.md                    # Project documentation
```

## Technology Stack
- Python 3.8+
- OpenCV
- Ultralytics YOLOv11
- Tkinter (GUI)
- C++/FFmpeg (RTMP streaming)

## Contact Information
- Project Homepage: [GitHub](https://github.com/Snake-Konginchrist/AI-Based-ROI-Video-Transmission-System)
- Technical Support: developer@skstudio.cn
- Business Cooperation: contact@skstudio.cn

## Copyright Notice
This project adopts the MIT open-source license, please refer to the LICENSE file for details.

## Related Documentation
- [Frequently Asked Questions (FAQ)](FAQ.md) - Problems encountered during use and solutions
- [Development Guide (DEVELOPMENT.md)](DEVELOPMENT.md) - Detailed development documentation and technical architecture description

## Star History
[![Star History Chart](https://api.star-history.com/svg?repos=Snake-Konginchrist/AI-Based-ROI-Video-Transmission-System&type=Date)](https://www.star-history.com/#Snake-Konginchrist/AI-Based-ROI-Video-Transmission-System&Date)