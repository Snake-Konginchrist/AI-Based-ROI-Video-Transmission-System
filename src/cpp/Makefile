# 基于嵌入式AI的ROI区域视频传输系统 C++部分 Makefile
# 作者: PycharmProjects
# 日期: 2023

# 编译器设置
CXX = g++
CXXFLAGS = -Wall -std=c++11 -fPIC -O2 -g

# FFmpeg设置
FFMPEG_INCLUDE = $(shell pkg-config --cflags libavcodec libavformat libavutil libswscale)
FFMPEG_LIBS = $(shell pkg-config --libs libavcodec libavformat libavutil libswscale)

# 输出目录
BUILD_DIR = ../../build
LIB_DIR = ../../lib

# 源码目录
RTMP_SRC_DIR = rtmp
RTSP_SRC_DIR = rtsp

# 目标库文件
RTMP_LIB = $(LIB_DIR)/librtmp_streamer.so
RTSP_LIB = $(LIB_DIR)/librtsp_client.so

# 源码文件
RTMP_SRC = $(RTMP_SRC_DIR)/rtmp_streamer.cpp
RTSP_SRC = $(RTSP_SRC_DIR)/rtsp_client.cpp

# 目标对象文件
RTMP_OBJ = $(BUILD_DIR)/rtmp_streamer.o
RTSP_OBJ = $(BUILD_DIR)/rtsp_client.o

# 默认目标
all: directories $(RTMP_LIB) $(RTSP_LIB)

# 创建必要的目录
directories:
	@mkdir -p $(BUILD_DIR)
	@mkdir -p $(LIB_DIR)

# 编译RTMP推流器
$(RTMP_OBJ): $(RTMP_SRC)
	$(CXX) $(CXXFLAGS) $(FFMPEG_INCLUDE) -c $< -o $@

$(RTMP_LIB): $(RTMP_OBJ)
	$(CXX) -shared -o $@ $^ $(FFMPEG_LIBS)

# 编译RTSP客户端
$(RTSP_OBJ): $(RTSP_SRC)
	$(CXX) $(CXXFLAGS) $(FFMPEG_INCLUDE) -c $< -o $@

$(RTSP_LIB): $(RTSP_OBJ)
	$(CXX) -shared -o $@ $^ $(FFMPEG_LIBS)

# 清理
clean:
	rm -rf $(BUILD_DIR)/* $(LIB_DIR)/*

# 安装依赖项
deps:
	@echo "安装FFmpeg开发库..."
	@if [ -x "$(command -v apt-get)" ]; then \
		apt-get update && apt-get install -y libavcodec-dev libavformat-dev libavutil-dev libswscale-dev pkg-config; \
	elif [ -x "$(command -v yum)" ]; then \
		yum install -y ffmpeg-devel pkgconfig; \
	elif [ -x "$(command -v dnf)" ]; then \
		dnf install -y ffmpeg-devel pkgconfig; \
	elif [ -x "$(command -v pacman)" ]; then \
		pacman -S --noconfirm ffmpeg pkg-config; \
	elif [ -x "$(command -v brew)" ]; then \
		brew install ffmpeg pkg-config; \
	else \
		echo "无法识别的包管理器，请手动安装FFmpeg开发库和pkg-config"; \
		exit 1; \
	fi

# 帮助
help:
	@echo "使用方法:"
	@echo "make            - 构建RTMP推流器和RTSP客户端库"
	@echo "make rtmp       - 仅构建RTMP推流器库"
	@echo "make rtsp       - 仅构建RTSP客户端库"
	@echo "make clean      - 清理构建文件"
	@echo "make deps       - 安装依赖项"
	@echo "make help       - 显示此帮助信息"

# 单独目标
rtmp: directories $(RTMP_LIB)
rtsp: directories $(RTSP_LIB)

.PHONY: all clean help deps directories rtmp rtsp
