# 开发指南

## 项目背景

随着视频监控和智能安防需求的不断增长，如何在有限的网络带宽下实现高质量的视频传输成为一个重要课题。本项目通过结合嵌入式AI技术和智能编码策略，实现了对视频关键区域的智能识别和差异化编码，有效提升了视频传输效率。

## 项目要求

本课题以嵌入式AI开发平台为基础，在算能SE5盒子上实现对摄像头的视频流解码后，通过AI识别到关键区域如人和车辆后，对关键的ROI区域采用高码率（低QP），对非关键区域采用低码率（高QP）编码。并将编码后的视频流通过RTMP协议推送到服务器。

### 具体实现要求：
1. 基于国产嵌入式AI开发平台：算能SE5盒子；
2. 支持通过RTSP协议拉取摄像头视频流；
3. 支持对视频流进行解码；
4. 通过YOLO算法对视频流进行AI识别人员、车辆；
5. 根据YOLO识别后的结果找出重点区域，对重点区域采用高码率（低QP），对非关键区域采用低码率（高QP）编码；
6. 将识别后的结果通过RTMP协议推送到流媒体服务器。

## 技术架构

### 系统架构图
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   摄像头设备     │    │   本地处理       │    │   网络传输       │
│   (RTSP)        │───▶│   (YOLOv11)     │───▶│   (RTMP)        │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │
                              ▼
                       ┌─────────────────┐
                       │   用户界面       │
                       │   (Tkinter)     │
                       └─────────────────┘
```

### 核心模块

1. **视频流处理模块** (`src/python/stream/`)
   - `camera.py`: 摄像头接口，支持RTSP流接入
   - `encoder.py`: 视频编码器，实现差异化编码
   - `decoder.py`: 视频解码器
   - `display.py`: 视频显示组件

2. **AI处理模块** (`src/python/yolo/`)
   - `processor.py`: YOLOv11目标检测处理器

3. **用户界面模块** (`src/python/gui/`)
   - `app.py`: 主界面应用
   - `mode_selection.py`: 模式选择界面
   - `utils.py`: 界面工具函数

4. **C++接口模块** (`src/cpp/`)
   - `rtmp/`: RTMP推流实现
   - `rtsp/`: RTSP客户端实现

## 开发环境配置

### 1. 环境要求
- Python 3.8+
- C++编译器 (GCC 7+ 或 MSVC 2019+)
- FFmpeg 4.0+ 开发库
- OpenCV 4.2+

### 2. 开发环境搭建
```bash
# 克隆项目
git clone https://gitee.com/Snake-Konginchrist/AI-Based-ROI-Video-Transmission-System.git
cd AI-Based-ROI-Video-Transmission-System

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或 venv\Scripts\activate  # Windows

# 安装开发依赖
pip install -r requirements.txt
pip install -r requirements-dev.txt  # 开发依赖

# 编译C++组件
cd src/cpp && make && cd ../..
```

### 3. IDE配置
推荐使用PyCharm或VS Code进行开发：

**PyCharm配置：**
- 设置Python解释器为虚拟环境
- 配置代码风格为PEP 8
- 启用类型检查

**VS Code配置：**
- 安装Python扩展
- 配置Python路径
- 启用代码格式化

## 代码规范

### 1. Python代码规范
- 遵循PEP 8编码规范
- 使用类型注解
- 添加详细的文档字符串
- 函数和类名使用snake_case
- 常量使用UPPER_CASE

### 2. C++代码规范
- 遵循Google C++ Style Guide
- 使用有意义的变量名
- 添加必要的注释
- 函数名使用camelCase
- 类名使用PascalCase

### 3. 注释规范
```python
def process_video_frame(frame: np.ndarray, roi_regions: List[Dict]) -> np.ndarray:
    """
    处理视频帧，对ROI区域进行差异化编码
    
    Args:
        frame (np.ndarray): 输入视频帧，形状为(H, W, C)
        roi_regions (List[Dict]): ROI区域列表，每个区域包含坐标和类型信息
        
    Returns:
        np.ndarray: 处理后的视频帧
        
    Example:
        >>> frame = cv2.imread('test.jpg')
        >>> roi_regions = [{'x': 100, 'y': 100, 'w': 200, 'h': 200, 'type': 'person'}]
        >>> processed_frame = process_video_frame(frame, roi_regions)
    """
    # 实现代码...
```

## 测试规范

### 1. 单元测试
- 测试覆盖率要求>80%
- 使用pytest框架
- 测试文件命名：`test_*.py`

```python
# test_processor.py
import pytest
import numpy as np
from src.python.yolo.processor import YOLOProcessor

class TestYOLOProcessor:
    def test_model_loading(self):
        """测试模型加载功能"""
        processor = YOLOProcessor()
        assert processor.model is not None
    
    def test_detection(self):
        """测试目标检测功能"""
        processor = YOLOProcessor()
        # 创建测试图像
        test_image = np.random.randint(0, 255, (640, 640, 3), dtype=np.uint8)
        results = processor.detect(test_image)
        assert isinstance(results, list)
```

### 2. 集成测试
- 测试完整功能流程
- 验证模块间接口
- 性能测试

### 3. 性能测试
- 帧率测试：确保实时处理能力
- 内存使用测试：监控内存泄漏
- CPU使用率测试：优化资源消耗

## 版本管理

### 1. Git工作流
- 使用feature分支开发新功能
- 提交前进行代码审查
- 使用语义化版本号

### 2. 提交规范
遵循Angular提交规范：
```
<type>(<scope>): <subject>

<body>

<footer>
```

类型说明：
- `feat`: 新功能
- `fix`: 修复bug
- `docs`: 文档更新
- `style`: 代码格式调整
- `refactor`: 代码重构
- `test`: 测试相关
- `chore`: 构建过程或辅助工具的变动

## 部署指南

### 1. 开发环境部署
```bash
# 安装依赖
pip install -r requirements.txt

# 编译C++组件
cd src/cpp && make && cd ../..

# 运行测试
pytest tests/

# 启动开发服务器
python main.py
```

### 2. 生产环境部署
```bash
# 创建生产环境
python -m venv venv_prod
source venv_prod/bin/activate

# 安装生产依赖
pip install -r requirements.txt

# 编译优化版本
cd src/cpp && make release && cd ../..

# 配置系统服务
sudo cp systemd/roi-video.service /etc/systemd/system/
sudo systemctl enable roi-video.service
sudo systemctl start roi-video.service
```

## 性能优化

### 1. 算法优化
- 使用更高效的YOLO模型
- 优化ROI检测算法
- 实现并行处理

### 2. 内存优化
- 使用内存池
- 及时释放不需要的资源
- 优化数据结构

### 3. 网络优化
- 使用连接池
- 实现断线重连
- 优化数据传输格式

## 故障排查

### 1. 日志系统
```python
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)
```

### 2. 调试工具
- 使用pdb进行调试
- 添加性能监控
- 使用内存分析工具

## 贡献指南

### 1. 提交Issue
- 使用模板描述问题
- 提供复现步骤
- 附加日志和截图

### 2. 提交PR
- 遵循代码规范
- 添加测试用例
- 更新相关文档

### 3. 代码审查
- 检查代码质量
- 验证功能正确性
- 确认性能影响

## 联系方式

- **技术支持**：developer@skstudio.cn
- **项目主页**：[Gitee](https://gitee.com/Snake-Konginchrist/AI-Based-ROI-Video-Transmission-System)
- **文档更新**：请关注项目最新文档 