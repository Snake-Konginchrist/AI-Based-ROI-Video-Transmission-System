# 常见问题解答 (FAQ)

## 模型加载错误

### 问题：无法加载YOLO模型
**可能原因及解决方案：**

1. **模型文件不存在或损坏**
   - 解决方案：程序会自动下载缺失的模型文件，请确保网络连接正常
   - 手动下载：可以从 [Ultralytics官方仓库](https://github.com/ultralytics/ultralytics) 下载模型文件

2. **OpenCV版本兼容性问题**
   - 解决方案：尝试使用4.5.4或以下版本的OpenCV
   - 命令：`pip install opencv-python==4.5.4.60`

3. **显存不足**
   - 解决方案：调整模型配置降低资源消耗
   - 使用更小的模型：如 `yolo11n.pt` 替代 `yolo11s.pt`

## 推流失败

### 问题：RTMP推流失败
**检查步骤：**

1. **FFmpeg库是否正确安装**
   ```bash
   # 检查FFmpeg版本
   ffmpeg -version
   
   # 如果未安装，请安装FFmpeg开发库
   # Ubuntu/Debian
   sudo apt-get install libavcodec-dev libavformat-dev libavutil-dev libswscale-dev
   
   # CentOS/RHEL
   sudo yum install ffmpeg-devel
   ```

2. **RTMP服务器地址是否可访问**
   - 检查网络连接
   - 验证RTMP服务器地址和端口
   - 确认服务器支持RTMP协议

3. **C++库是否正确编译并放置在lib目录**
   ```bash
   # 检查库文件是否存在
   ls -la lib/
   
   # 重新编译C++库
   cd src/cpp && make clean && make
   ```

## 视频卡顿

### 问题：视频处理卡顿
**优化建议：**

1. **降低输入视频分辨率**
   - 在配置中设置较低的分辨率
   - 推荐：720p或更低

2. **减小处理帧率**
   - 降低FPS设置
   - 推荐：15-30 FPS

3. **启用GPU加速（需CUDA支持）**
   ```bash
   # 检查CUDA是否可用
   python -c "import torch; print(torch.cuda.is_available())"
   
   # 安装CUDA版本的PyTorch
   pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
   ```

4. **优化系统资源**
   - 关闭不必要的后台程序
   - 增加系统内存
   - 使用SSD存储

## 编译错误

### 问题：C++组件编译失败
**常见解决方案：**

1. **缺少依赖库**
   ```bash
   # Ubuntu/Debian
   sudo apt-get install build-essential pkg-config
   sudo apt-get install libavcodec-dev libavformat-dev libavutil-dev libswscale-dev
   
   # CentOS/RHEL
   sudo yum groupinstall "Development Tools"
   sudo yum install ffmpeg-devel
   ```

2. **Makefile路径问题**
   - 确保在正确的目录下执行make命令
   - 检查Makefile是否存在

3. **编译器版本问题**
   - 确保使用兼容的编译器版本
   - GCC 7+ 或 MSVC 2019+

## 网络连接问题

### 问题：客户端无法连接到服务器
**排查步骤：**

1. **检查网络配置**
   - 确认服务器IP地址和端口
   - 检查防火墙设置
   - 验证网络连通性

2. **端口占用问题**
   ```bash
   # 检查端口是否被占用
   netstat -tulpn | grep :8080
   
   # 或使用lsof
   lsof -i :8080
   ```

3. **服务端未启动**
   - 确保服务端程序正在运行
   - 检查服务端日志输出

## 性能优化

### 问题：系统性能不佳
**优化建议：**

1. **硬件优化**
   - 使用更快的CPU
   - 增加内存容量
   - 使用GPU加速

2. **软件优化**
   - 使用更高效的模型
   - 调整编码参数
   - 优化算法实现

3. **系统优化**
   - 更新驱动程序
   - 优化操作系统设置
   - 使用专用硬件

## 开发相关

### 代码规范
- 遵循PEP 8编码规范
- 使用类型注解
- 添加必要的注释和文档字符串

### 测试要求
- 单元测试覆盖率>80%
- 集成测试确保功能完整性
- 性能测试满足实时性要求

## 联系支持

如果以上解决方案无法解决您的问题，请通过以下方式联系技术支持：

- **技术支持邮箱**：developer@skstudio.cn
- **项目Issues**：[Gitee Issues](https://gitee.com/Snake-Konginchrist/AI-Based-ROI-Video-Transmission-System/issues)
- **文档更新**：请关注项目最新文档更新 