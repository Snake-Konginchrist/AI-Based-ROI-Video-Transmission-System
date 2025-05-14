/**
 * RTMP推流器头文件
 * 
 * 定义了RTMP推流器的接口，用于将视频流推送到流媒体服务器
 * 支持设置不同区域的编码质量(QP值)
 * 
 * 作者: PycharmProjects
 * 日期: 2023
 */

#ifndef RTMP_STREAMER_H
#define RTMP_STREAMER_H

#include <string>
#include <vector>
#include <atomic>
#include <mutex>
#include <thread>
#include <condition_variable>

// 前向声明
struct AVFormatContext;
struct AVCodecContext;
struct AVStream;
struct SwsContext;
struct AVFrame;
struct AVPacket;

// 定义ROI区域结构
struct ROIRegion {
    int x;      // 左上角x坐标
    int y;      // 左上角y坐标
    int width;  // 宽度
    int height; // 高度
    int qp;     // 该区域的QP值
};

// 定义帧数据结构
struct FrameData {
    uint8_t* data;          // 图像数据
    int width;              // 图像宽度
    int height;             // 图像高度
    int channels;           // 图像通道数
    std::vector<ROIRegion> rois; // ROI区域列表
    int64_t timestamp;      // 时间戳
};

/**
 * RTMP推流器类
 * 
 * 负责将视频帧编码并推送到RTMP服务器
 */
class RTMPStreamer {
public:
    /**
     * 构造函数
     * 
     * @param url RTMP服务器URL
     * @param width 视频宽度
     * @param height 视频高度
     * @param fps 帧率
     * @param bitrate 比特率（bps）
     * @param gop GOP大小
     * @param qp 默认QP值
     */
    RTMPStreamer(const std::string& url, int width, int height, int fps = 30, 
                int bitrate = 1000000, int gop = 30, int qp = 23);
    
    /**
     * 析构函数 - 释放资源
     */
    ~RTMPStreamer();
    
    /**
     * 初始化推流器
     * 
     * @return 是否成功初始化
     */
    bool initialize();
    
    /**
     * 开始推流
     * 
     * @return 是否成功启动推流
     */
    bool start();
    
    /**
     * 停止推流
     */
    void stop();
    
    /**
     * 发送帧进行推流
     * 
     * @param frameData 帧数据
     * @return 是否成功排队等待推流
     */
    bool pushFrame(const FrameData& frameData);

private:
    // FFmpeg上下文
    AVFormatContext* formatContext;
    AVCodecContext* codecContext;
    AVStream* stream;
    SwsContext* swsContext;
    
    // 帧缓冲
    AVFrame* frame;
    AVFrame* tmpFrame;
    AVPacket* packet;
    
    // 推流参数
    std::string rtmpUrl;
    int width;
    int height;
    int fps;
    int bitrate;
    int gopSize;
    int defaultQP;
    
    // 线程控制
    std::atomic<bool> isRunning;
    std::thread streamThread;
    std::mutex frameMutex;
    std::condition_variable frameCV;
    FrameData currentFrame;
    bool newFrameAvailable;
    
    /**
     * 清理资源
     */
    void cleanup();
    
    /**
     * 推流线程的主循环
     */
    void streamLoop();
};

#endif // RTMP_STREAMER_H 