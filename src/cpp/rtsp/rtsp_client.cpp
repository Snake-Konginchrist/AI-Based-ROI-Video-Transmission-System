/**
 * RTSP客户端实现
 * 
 * 本文件实现了一个基于FFmpeg的RTSP客户端，用于从IP摄像头获取视频流
 * 
 * 作者: PycharmProjects
 * 日期: 2023
 */

extern "C" {
#include <libavcodec/avcodec.h>
#include <libavformat/avformat.h>
#include <libavutil/imgutils.h>
#include <libavutil/time.h>
#include <libswscale/swscale.h>
}

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <iostream>
#include <vector>
#include <thread>
#include <atomic>
#include <mutex>
#include <condition_variable>
#include <queue>
#include <functional>

// 最大帧缓冲队列大小
#define MAX_QUEUE_SIZE 30

// 帧回调函数类型
typedef std::function<void(uint8_t*, int, int, int64_t)> FrameCallback;

class RTSPClient {
private:
    // FFmpeg上下文
    AVFormatContext* formatContext;
    AVCodecContext* codecContext;
    AVFrame* frame;
    AVFrame* rgbFrame;
    AVPacket* packet;
    SwsContext* swsContext;
    
    // RTSP URL
    std::string rtspUrl;
    
    // 视频流索引
    int videoStreamIndex;
    
    // 线程控制
    std::atomic<bool> isRunning;
    std::thread readThread;
    std::mutex callbackMutex;
    
    // 帧回调函数
    FrameCallback frameCallback;
    
    // 输出参数
    int outputWidth;
    int outputHeight;
    
    // 性能统计
    int64_t lastFrameTime;
    int frameCount;
    double fps;
    
public:
    /**
     * 构造函数
     * 
     * @param url RTSP服务器URL
     * @param width 输出图像宽度（0表示使用原始宽度）
     * @param height 输出图像高度（0表示使用原始高度）
     */
    RTSPClient(const std::string& url, int width = 0, int height = 0)
        : rtspUrl(url), outputWidth(width), outputHeight(height),
          isRunning(false), videoStreamIndex(-1), lastFrameTime(0), frameCount(0), fps(0) {
        
        // 初始化FFmpeg（仅在新版本需要）
        #if LIBAVFORMAT_VERSION_INT < AV_VERSION_INT(58, 9, 100)
            av_register_all();
        #endif
        avformat_network_init();
        
        // 初始化为空指针
        formatContext = nullptr;
        codecContext = nullptr;
        frame = nullptr;
        rgbFrame = nullptr;
        packet = nullptr;
        swsContext = nullptr;
    }
    
    /**
     * 析构函数 - 释放资源
     */
    ~RTSPClient() {
        stop();
        cleanup();
    }
    
    /**
     * 设置帧回调函数
     * 
     * @param callback 帧处理回调函数
     */
    void setFrameCallback(const FrameCallback& callback) {
        std::lock_guard<std::mutex> lock(callbackMutex);
        frameCallback = callback;
    }
    
    /**
     * 初始化RTSP客户端
     * 
     * @return 是否成功初始化
     */
    bool initialize() {
        // 如果已初始化，先清理
        cleanup();
        
        // 创建格式上下文
        formatContext = avformat_alloc_context();
        if (!formatContext) {
            std::cerr << "无法分配格式上下文" << std::endl;
            return false;
        }
        
        // 设置RTSP选项
        AVDictionary* options = nullptr;
        // 设置较低延迟的RTSP选项
        av_dict_set(&options, "rtsp_transport", "tcp", 0);  // 使用TCP传输RTSP
        av_dict_set(&options, "max_delay", "500000", 0);    // 最大延迟500ms
        av_dict_set(&options, "stimeout", "2000000", 0);    // 连接超时2秒
        
        // 打开RTSP流
        int ret = avformat_open_input(&formatContext, rtspUrl.c_str(), nullptr, &options);
        if (ret < 0) {
            char errBuf[AV_ERROR_MAX_STRING_SIZE];
            av_strerror(ret, errBuf, AV_ERROR_MAX_STRING_SIZE);
            std::cerr << "无法打开RTSP流: " << errBuf << std::endl;
            cleanup();
            return false;
        }
        
        // 释放选项字典
        av_dict_free(&options);
        
        // 获取流信息
        ret = avformat_find_stream_info(formatContext, nullptr);
        if (ret < 0) {
            std::cerr << "无法获取流信息" << std::endl;
            cleanup();
            return false;
        }
        
        // 查找视频流
        videoStreamIndex = -1;
        for (unsigned int i = 0; i < formatContext->nb_streams; i++) {
            if (formatContext->streams[i]->codecpar->codec_type == AVMEDIA_TYPE_VIDEO) {
                videoStreamIndex = i;
                break;
            }
        }
        
        if (videoStreamIndex == -1) {
            std::cerr << "找不到视频流" << std::endl;
            cleanup();
            return false;
        }
        
        // 获取视频流参数
        AVCodecParameters* codecParams = formatContext->streams[videoStreamIndex]->codecpar;
        
        // 查找解码器
        const AVCodec* codec = avcodec_find_decoder(codecParams->codec_id);
        if (!codec) {
            std::cerr << "找不到解码器" << std::endl;
            cleanup();
            return false;
        }
        
        // 创建解码器上下文
        codecContext = avcodec_alloc_context3(codec);
        if (!codecContext) {
            std::cerr << "无法分配解码器上下文" << std::endl;
            cleanup();
            return false;
        }
        
        // 复制编解码器参数到解码器上下文
        ret = avcodec_parameters_to_context(codecContext, codecParams);
        if (ret < 0) {
            std::cerr << "无法复制解码器参数" << std::endl;
            cleanup();
            return false;
        }
        
        // 打开解码器
        ret = avcodec_open2(codecContext, codec, nullptr);
        if (ret < 0) {
            std::cerr << "无法打开解码器" << std::endl;
            cleanup();
            return false;
        }
        
        // 设置输出尺寸
        if (outputWidth <= 0) outputWidth = codecContext->width;
        if (outputHeight <= 0) outputHeight = codecContext->height;
        
        // 创建转换上下文
        swsContext = sws_getContext(
            codecContext->width, codecContext->height, codecContext->pix_fmt,  // 源格式
            outputWidth, outputHeight, AV_PIX_FMT_RGB24,  // 目标格式
            SWS_BILINEAR, nullptr, nullptr, nullptr
        );
        if (!swsContext) {
            std::cerr << "无法创建像素格式转换上下文" << std::endl;
            cleanup();
            return false;
        }
        
        // 分配帧
        frame = av_frame_alloc();
        rgbFrame = av_frame_alloc();
        if (!frame || !rgbFrame) {
            std::cerr << "无法分配帧" << std::endl;
            cleanup();
            return false;
        }
        
        // 分配RGB帧数据缓冲区
        ret = av_image_alloc(
            rgbFrame->data, rgbFrame->linesize,
            outputWidth, outputHeight,
            AV_PIX_FMT_RGB24, 1
        );
        if (ret < 0) {
            std::cerr << "无法分配RGB帧缓冲区" << std::endl;
            cleanup();
            return false;
        }
        
        // 设置RGB帧参数
        rgbFrame->width = outputWidth;
        rgbFrame->height = outputHeight;
        rgbFrame->format = AV_PIX_FMT_RGB24;
        
        // 分配数据包
        packet = av_packet_alloc();
        if (!packet) {
            std::cerr << "无法分配数据包" << std::endl;
            cleanup();
            return false;
        }
        
        std::cout << "RTSP客户端初始化完成，分辨率: " << outputWidth << "x" << outputHeight << std::endl;
        return true;
    }
    
    /**
     * 开始接收和处理RTSP流
     * 
     * @return 是否成功启动
     */
    bool start() {
        if (isRunning.load()) {
            return true;  // 已经在运行
        }
        
        // 如果尚未初始化，则初始化
        if (!formatContext) {
            if (!initialize()) {
                return false;
            }
        }
        
        // 设置运行标志
        isRunning.store(true);
        
        // 启动读取线程
        readThread = std::thread(&RTSPClient::readLoop, this);
        
        return true;
    }
    
    /**
     * 停止接收和处理RTSP流
     */
    void stop() {
        if (!isRunning.load()) {
            return;  // 已经停止
        }
        
        // 设置停止标志
        isRunning.store(false);
        
        // 等待读取线程结束
        if (readThread.joinable()) {
            readThread.join();
        }
    }
    
    /**
     * 获取当前FPS（帧率）
     * 
     * @return 当前帧率
     */
    double getFPS() const {
        return fps;
    }
    
    /**
     * 获取输出宽度
     * 
     * @return 输出图像宽度
     */
    int getWidth() const {
        return outputWidth;
    }
    
    /**
     * 获取输出高度
     * 
     * @return 输出图像高度
     */
    int getHeight() const {
        return outputHeight;
    }
    
private:
    /**
     * 清理资源
     */
    void cleanup() {
        if (packet) {
            av_packet_free(&packet);
            packet = nullptr;
        }
        
        if (rgbFrame) {
            if (rgbFrame->data[0]) {
                av_freep(&rgbFrame->data[0]);
            }
            av_frame_free(&rgbFrame);
            rgbFrame = nullptr;
        }
        
        if (frame) {
            av_frame_free(&frame);
            frame = nullptr;
        }
        
        if (codecContext) {
            avcodec_free_context(&codecContext);
            codecContext = nullptr;
        }
        
        if (formatContext) {
            avformat_close_input(&formatContext);
            formatContext = nullptr;
        }
        
        if (swsContext) {
            sws_freeContext(swsContext);
            swsContext = nullptr;
        }
        
        videoStreamIndex = -1;
    }
    
    /**
     * 处理视频帧
     * 
     * @param avFrame 原始AVFrame
     * @param timestamp 时间戳
     */
    void processFrame(const AVFrame* avFrame, int64_t timestamp) {
        // 转换为RGB格式
        sws_scale(
            swsContext,
            avFrame->data, avFrame->linesize, 0, avFrame->height,
            rgbFrame->data, rgbFrame->linesize
        );
        
        // 更新FPS计算
        int64_t currentTime = av_gettime();
        frameCount++;
        
        if (lastFrameTime == 0) {
            lastFrameTime = currentTime;
        } else if (currentTime - lastFrameTime > 1000000) {  // 每秒更新一次
            fps = (double)frameCount * 1000000 / (currentTime - lastFrameTime);
            frameCount = 0;
            lastFrameTime = currentTime;
        }
        
        // 调用回调函数
        std::lock_guard<std::mutex> lock(callbackMutex);
        if (frameCallback) {
            // 计算RGB图像数据大小
            int rgbDataSize = rgbFrame->linesize[0] * rgbFrame->height;
            
            // 调用回调函数处理帧
            frameCallback(rgbFrame->data[0], outputWidth, outputHeight, timestamp);
        }
    }
    
    /**
     * RTSP流读取循环
     */
    void readLoop() {
        int ret;
        
        while (isRunning.load()) {
            // 读取数据包
            ret = av_read_frame(formatContext, packet);
            if (ret < 0) {
                // 错误处理
                if (ret == AVERROR_EOF) {
                    std::cout << "已到达流结尾" << std::endl;
                    break;  // 流结束
                } else if (ret == AVERROR(EAGAIN)) {
                    // 暂时没有数据，继续尝试
                    std::this_thread::sleep_for(std::chrono::milliseconds(10));
                    continue;
                } else {
                    char errBuf[AV_ERROR_MAX_STRING_SIZE];
                    av_strerror(ret, errBuf, AV_ERROR_MAX_STRING_SIZE);
                    std::cerr << "读取帧错误: " << errBuf << std::endl;
                    
                    // 等待一段时间后重试
                    std::this_thread::sleep_for(std::chrono::milliseconds(100));
                    continue;
                }
            }
            
            // 检查是否是视频包
            if (packet->stream_index == videoStreamIndex) {
                // 发送数据包到解码器
                ret = avcodec_send_packet(codecContext, packet);
                if (ret < 0) {
                    std::cerr << "发送数据包到解码器失败" << std::endl;
                } else {
                    // 接收解码后的帧
                    while (ret >= 0) {
                        ret = avcodec_receive_frame(codecContext, frame);
                        if (ret == AVERROR(EAGAIN) || ret == AVERROR_EOF) {
                            break;
                        } else if (ret < 0) {
                            std::cerr << "从解码器接收帧失败" << std::endl;
                            break;
                        }
                        
                        // 处理解码后的帧
                        int64_t timestamp = frame->pts;
                        if (timestamp == AV_NOPTS_VALUE) {
                            timestamp = 0;
                        }
                        
                        // 根据流的时间基准转换时间戳
                        timestamp = av_rescale_q(
                            timestamp,
                            formatContext->streams[videoStreamIndex]->time_base,
                            AVRational{1, 1000}  // 转换为毫秒
                        );
                        
                        processFrame(frame, timestamp);
                    }
                }
            }
            
            // 释放数据包
            av_packet_unref(packet);
            
            // 控制处理速度，避免CPU占用过高
            std::this_thread::sleep_for(std::chrono::milliseconds(1));
        }
    }
};

// 暴露给Python的C接口
extern "C" {
    /**
     * 创建RTSP客户端
     * 
     * @param url RTSP服务器URL
     * @param width 输出图像宽度（0表示使用原始宽度）
     * @param height 输出图像高度（0表示使用原始高度）
     * @return 客户端指针
     */
    RTSPClient* create_rtsp_client(const char* url, int width, int height) {
        return new RTSPClient(url, width, height);
    }
    
    /**
     * 释放RTSP客户端
     * 
     * @param client 客户端指针
     */
    void destroy_rtsp_client(RTSPClient* client) {
        if (client) {
            delete client;
        }
    }
    
    /**
     * 初始化RTSP客户端
     * 
     * @param client 客户端指针
     * @return 是否成功初始化
     */
    bool initialize_client(RTSPClient* client) {
        return client ? client->initialize() : false;
    }
    
    /**
     * 开始接收和处理RTSP流
     * 
     * @param client 客户端指针
     * @return 是否成功启动
     */
    bool start_client(RTSPClient* client) {
        return client ? client->start() : false;
    }
    
    /**
     * 停止接收和处理RTSP流
     * 
     * @param client 客户端指针
     */
    void stop_client(RTSPClient* client) {
        if (client) {
            client->stop();
        }
    }
    
    /**
     * 获取当前FPS（帧率）
     * 
     * @param client 客户端指针
     * @return 当前帧率
     */
    double get_fps(RTSPClient* client) {
        return client ? client->getFPS() : 0.0;
    }
    
    /**
     * 获取输出宽度
     * 
     * @param client 客户端指针
     * @return 输出图像宽度
     */
    int get_width(RTSPClient* client) {
        return client ? client->getWidth() : 0;
    }
    
    /**
     * 获取输出高度
     * 
     * @param client 客户端指针
     * @return 输出图像高度
     */
    int get_height(RTSPClient* client) {
        return client ? client->getHeight() : 0;
    }
    
    // 回调函数指针类型
    typedef void (*FrameCallbackFunc)(void* userData, uint8_t* data, int width, int height, int64_t timestamp);
    
    /**
     * 设置帧回调函数
     * 
     * @param client 客户端指针
     * @param callback 回调函数指针
     * @param userData 用户数据指针
     */
    void set_frame_callback(RTSPClient* client, FrameCallbackFunc callback, void* userData) {
        if (client && callback) {
            client->setFrameCallback([callback, userData](uint8_t* data, int width, int height, int64_t timestamp) {
                callback(userData, data, width, height, timestamp);
            });
        }
    }
}
