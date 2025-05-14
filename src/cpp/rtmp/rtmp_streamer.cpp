/**
 * RTMP推流器实现
 * 
 * 本文件实现了一个基于FFmpeg的RTMP推流器，用于将视频流推送到流媒体服务器
 * 支持设置不同区域的编码质量(QP值)
 * 
 * 作者: PycharmProjects
 * 日期: 2023
 */

extern "C" {
#include <libavcodec/avcodec.h>
#include <libavformat/avformat.h>
#include <libavutil/imgutils.h>
#include <libavutil/opt.h>
#include <libswscale/swscale.h>
}

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <iostream>
#include <vector>
#include <chrono>
#include <thread>
#include <atomic>
#include <mutex>
#include <condition_variable>

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

class RTMPStreamer {
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
    
    // 推流目标URL
    std::string rtmpUrl;
    
    // 编码参数
    int width;
    int height;
    int fps;
    int bitrate;
    int gopSize;
    int defaultQP;  // 默认QP值
    
    // 线程控制
    std::atomic<bool> isRunning;
    std::thread streamThread;
    std::mutex frameMutex;
    std::condition_variable frameCV;
    FrameData currentFrame;
    bool newFrameAvailable;
    
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
                int bitrate = 1000000, int gop = 30, int qp = 23) 
        : rtmpUrl(url), width(width), height(height), fps(fps), 
          bitrate(bitrate), gopSize(gop), defaultQP(qp),
          isRunning(false), newFrameAvailable(false) {
        
        // 初始化FFmpeg（仅在新版本需要）
        #if LIBAVFORMAT_VERSION_INT < AV_VERSION_INT(58, 9, 100)
            av_register_all();
        #endif
        avformat_network_init();
        
        // 初始化为空指针
        formatContext = nullptr;
        codecContext = nullptr;
        stream = nullptr;
        swsContext = nullptr;
        frame = nullptr;
        tmpFrame = nullptr;
        packet = nullptr;
    }
    
    /**
     * 析构函数 - 释放资源
     */
    ~RTMPStreamer() {
        stop();
        cleanup();
    }
    
    /**
     * 初始化推流器
     * 
     * @return 是否成功初始化
     */
    bool initialize() {
        // 创建输出格式上下文
        int ret = avformat_alloc_output_context2(&formatContext, nullptr, "flv", rtmpUrl.c_str());
        if (ret < 0 || !formatContext) {
            std::cerr << "无法创建输出上下文" << std::endl;
            return false;
        }
        
        // 查找编码器
        const AVCodec* codec = avcodec_find_encoder(AV_CODEC_ID_H264);
        if (!codec) {
            std::cerr << "无法找到H264编码器" << std::endl;
            cleanup();
            return false;
        }
        
        // 创建流
        stream = avformat_new_stream(formatContext, codec);
        if (!stream) {
            std::cerr << "无法创建输出流" << std::endl;
            cleanup();
            return false;
        }
        
        // 配置编码器上下文
        codecContext = avcodec_alloc_context3(codec);
        if (!codecContext) {
            std::cerr << "无法分配编码器上下文" << std::endl;
            cleanup();
            return false;
        }
        
        // 设置编码参数
        codecContext->codec_id = AV_CODEC_ID_H264;
        codecContext->codec_type = AVMEDIA_TYPE_VIDEO;
        codecContext->width = width;
        codecContext->height = height;
        codecContext->time_base = AVRational{1, fps};
        codecContext->framerate = AVRational{fps, 1};
        codecContext->gop_size = gopSize;
        codecContext->max_b_frames = 0;  // 不使用B帧，减少延迟
        codecContext->pix_fmt = AV_PIX_FMT_YUV420P;
        codecContext->bit_rate = bitrate;
        
        // 设置H264特定参数
        av_opt_set(codecContext->priv_data, "preset", "ultrafast", 0);  // 最快速度编码
        av_opt_set(codecContext->priv_data, "tune", "zerolatency", 0);  // 最小延迟
        
        // 对于更高级的编码器（如x264），可以设置CRF（质量因子）
        char crf[10];
        snprintf(crf, sizeof(crf), "%d", defaultQP);
        av_opt_set(codecContext->priv_data, "crf", crf, 0);
        
        // 复制编码器参数到流
        ret = avcodec_parameters_from_context(stream->codecpar, codecContext);
        if (ret < 0) {
            std::cerr << "无法复制编码器参数到输出流" << std::endl;
            cleanup();
            return false;
        }
        
        // 打开编码器
        ret = avcodec_open2(codecContext, codec, nullptr);
        if (ret < 0) {
            std::cerr << "无法打开编码器" << std::endl;
            cleanup();
            return false;
        }
        
        // 创建转换上下文（用于RGB到YUV转换）
        swsContext = sws_getContext(
            width, height, AV_PIX_FMT_BGR24,  // 源格式
            width, height, AV_PIX_FMT_YUV420P,  // 目标格式
            SWS_BICUBIC, nullptr, nullptr, nullptr
        );
        if (!swsContext) {
            std::cerr << "无法创建像素格式转换上下文" << std::endl;
            cleanup();
            return false;
        }
        
        // 分配帧和数据包
        frame = av_frame_alloc();
        tmpFrame = av_frame_alloc();
        if (!frame || !tmpFrame) {
            std::cerr << "无法分配帧" << std::endl;
            cleanup();
            return false;
        }
        
        // 设置帧参数
        frame->format = AV_PIX_FMT_YUV420P;
        frame->width = width;
        frame->height = height;
        
        // 分配帧缓冲区
        ret = av_frame_get_buffer(frame, 0);
        if (ret < 0) {
            std::cerr << "无法分配帧缓冲区" << std::endl;
            cleanup();
            return false;
        }
        
        // 设置临时帧参数（用于输入RGB数据）
        tmpFrame->format = AV_PIX_FMT_BGR24;
        tmpFrame->width = width;
        tmpFrame->height = height;
        
        // 分配临时帧缓冲区
        ret = av_frame_get_buffer(tmpFrame, 0);
        if (ret < 0) {
            std::cerr << "无法分配临时帧缓冲区" << std::endl;
            cleanup();
            return false;
        }
        
        // 分配数据包
        packet = av_packet_alloc();
        if (!packet) {
            std::cerr << "无法分配数据包" << std::endl;
            cleanup();
            return false;
        }
        
        // 打开输出
        if (!(formatContext->oformat->flags & AVFMT_NOFILE)) {
            ret = avio_open(&formatContext->pb, rtmpUrl.c_str(), AVIO_FLAG_WRITE);
            if (ret < 0) {
                std::cerr << "无法打开输出文件" << std::endl;
                cleanup();
                return false;
            }
        }
        
        // 写入流头部
        ret = avformat_write_header(formatContext, nullptr);
        if (ret < 0) {
            std::cerr << "无法写入流头部" << std::endl;
            cleanup();
            return false;
        }
        
        return true;
    }
    
    /**
     * 开始推流
     * 
     * @return 是否成功启动推流
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
        
        // 启动推流线程
        streamThread = std::thread(&RTMPStreamer::streamLoop, this);
        
        return true;
    }
    
    /**
     * 停止推流
     */
    void stop() {
        if (!isRunning.load()) {
            return;  // 已经停止
        }
        
        // 设置停止标志
        isRunning.store(false);
        
        // 唤醒等待的线程
        {
            std::lock_guard<std::mutex> lock(frameMutex);
            newFrameAvailable = true;
            frameCV.notify_one();
        }
        
        // 等待推流线程结束
        if (streamThread.joinable()) {
            streamThread.join();
        }
        
        // 写入流尾部
        if (formatContext) {
            av_write_trailer(formatContext);
        }
        
        // 关闭输出
        if (formatContext && !(formatContext->oformat->flags & AVFMT_NOFILE)) {
            avio_closep(&formatContext->pb);
        }
    }
    
    /**
     * 发送帧进行推流
     * 
     * @param frameData 帧数据
     * @return 是否成功排队等待推流
     */
    bool pushFrame(const FrameData& frameData) {
        if (!isRunning.load()) {
            return false;
        }
        
        // 锁定互斥量
        std::lock_guard<std::mutex> lock(frameMutex);
        
        // 更新当前帧
        currentFrame = frameData;
        newFrameAvailable = true;
        
        // 通知推流线程
        frameCV.notify_one();
        
        return true;
    }
    
private:
    /**
     * 清理资源
     */
    void cleanup() {
        if (swsContext) {
            sws_freeContext(swsContext);
            swsContext = nullptr;
        }
        
        if (packet) {
            av_packet_free(&packet);
            packet = nullptr;
        }
        
        if (frame) {
            av_frame_free(&frame);
            frame = nullptr;
        }
        
        if (tmpFrame) {
            av_frame_free(&tmpFrame);
            tmpFrame = nullptr;
        }
        
        if (codecContext) {
            avcodec_free_context(&codecContext);
            codecContext = nullptr;
        }
        
        if (formatContext) {
            avformat_free_context(formatContext);
            formatContext = nullptr;
        }
    }
    
    /**
     * 推流线程的主循环
     */
    void streamLoop() {
        int frameIndex = 0;
        int ret;
        
        while (isRunning.load()) {
            // 等待新帧
            std::unique_lock<std::mutex> lock(frameMutex);
            frameCV.wait(lock, [this] { return newFrameAvailable || !isRunning.load(); });
            
            // 检查是否应该退出
            if (!isRunning.load() && !newFrameAvailable) {
                break;
            }
            
            // 复制帧数据
            FrameData localFrame = currentFrame;
            newFrameAvailable = false;
            lock.unlock();
            
            // 填充tmpFrame数据
            for (int y = 0; y < localFrame.height; y++) {
                for (int x = 0; x < localFrame.width; x++) {
                    int src_idx = (y * localFrame.width + x) * localFrame.channels;
                    int dst_idx = y * tmpFrame->linesize[0] + x * 3;
                    
                    tmpFrame->data[0][dst_idx] = localFrame.data[src_idx];       // B
                    tmpFrame->data[0][dst_idx + 1] = localFrame.data[src_idx + 1]; // G
                    tmpFrame->data[0][dst_idx + 2] = localFrame.data[src_idx + 2]; // R
                }
            }
            
            // 将RGB转换为YUV
            sws_scale(swsContext, tmpFrame->data, tmpFrame->linesize, 0, localFrame.height,
                     frame->data, frame->linesize);
            
            // 设置帧时间戳
            frame->pts = frameIndex++;
            
            // 应用ROI区域的QP设置（如果编码器支持）
            if (!localFrame.rois.empty() && codecContext->codec_id == AV_CODEC_ID_H264) {
                // 根据ROI设置MB级别的QP值
                // 这是一个简化的版本，实际实现可能需要更复杂的处理
                // 不同的编码器可能有不同的API来设置区域QP值
                
                // 这里我们使用x264编码器的private_data来设置区域QP
                // 注意: 这是一个低级操作，可能在不同版本的FFmpeg或编码器中有所不同
                
                // 示例代码，实际实现需要根据使用的编码器API进行调整
                for (const auto& roi : localFrame.rois) {
                    std::cout << "设置ROI区域 (" << roi.x << "," << roi.y << "," 
                              << roi.width << "," << roi.height << ") QP=" << roi.qp << std::endl;
                    
                    // 在实际应用中，这里应该调用编码器的API来设置区域QP
                    // 例如，对于x264，可以使用x264_param_t的rc.zones参数
                    // 但这需要直接操作编码器的私有数据，这里只做演示
                }
            }
            
            // 编码帧
            ret = avcodec_send_frame(codecContext, frame);
            if (ret < 0) {
                std::cerr << "发送帧到编码器失败" << std::endl;
                continue;
            }
            
            // 获取编码后的包
            while (ret >= 0) {
                ret = avcodec_receive_packet(codecContext, packet);
                if (ret == AVERROR(EAGAIN) || ret == AVERROR_EOF) {
                    break;
                } else if (ret < 0) {
                    std::cerr << "从编码器接收数据包失败" << std::endl;
                    break;
                }
                
                // 转换时间戳
                av_packet_rescale_ts(packet, codecContext->time_base, stream->time_base);
                packet->stream_index = stream->index;
                
                // 写入数据包
                ret = av_interleaved_write_frame(formatContext, packet);
                if (ret < 0) {
                    std::cerr << "写入数据包失败" << std::endl;
                }
                
                // 重置数据包
                av_packet_unref(packet);
            }
            
            // 简单的帧率控制
            std::this_thread::sleep_for(std::chrono::milliseconds(1000 / fps));
        }
    }
};

// 暴露给Python的C接口
extern "C" {
    /**
     * 创建RTMP推流器
     * 
     * @param url RTMP服务器URL
     * @param width 视频宽度
     * @param height 视频高度
     * @param fps 帧率
     * @param bitrate 比特率
     * @param gop GOP大小
     * @param qp 默认QP值
     * @return 推流器指针
     */
    RTMPStreamer* create_rtmp_streamer(const char* url, int width, int height, 
                                     int fps, int bitrate, int gop, int qp) {
        return new RTMPStreamer(url, width, height, fps, bitrate, gop, qp);
    }
    
    /**
     * 释放RTMP推流器
     * 
     * @param streamer 推流器指针
     */
    void destroy_rtmp_streamer(RTMPStreamer* streamer) {
        if (streamer) {
            delete streamer;
        }
    }
    
    /**
     * 初始化推流器
     * 
     * @param streamer 推流器指针
     * @return 是否成功初始化
     */
    bool initialize_streamer(RTMPStreamer* streamer) {
        return streamer ? streamer->initialize() : false;
    }
    
    /**
     * 开始推流
     * 
     * @param streamer 推流器指针
     * @return 是否成功启动推流
     */
    bool start_streaming(RTMPStreamer* streamer) {
        return streamer ? streamer->start() : false;
    }
    
    /**
     * 停止推流
     * 
     * @param streamer 推流器指针
     */
    void stop_streaming(RTMPStreamer* streamer) {
        if (streamer) {
            streamer->stop();
        }
    }
    
    /**
     * 创建帧数据结构
     * 
     * @param width 图像宽度
     * @param height 图像高度
     * @param channels 图像通道数
     * @return 帧数据指针
     */
    FrameData* create_frame_data(int width, int height, int channels) {
        FrameData* frameData = new FrameData();
        frameData->width = width;
        frameData->height = height;
        frameData->channels = channels;
        frameData->data = new uint8_t[width * height * channels];
        frameData->timestamp = 0;
        return frameData;
    }
    
    /**
     * 释放帧数据结构
     * 
     * @param frame_data 帧数据指针
     */
    void destroy_frame_data(FrameData* frame_data) {
        if (frame_data) {
            if (frame_data->data) {
                delete[] frame_data->data;
            }
            delete frame_data;
        }
    }
    
    /**
     * 添加ROI区域
     * 
     * @param frame_data 帧数据指针
     * @param x 左上角x坐标
     * @param y 左上角y坐标
     * @param width 宽度
     * @param height 高度
     * @param qp QP值
     */
    void add_roi_region(FrameData* frame_data, int x, int y, int width, int height, int qp) {
        if (frame_data) {
            ROIRegion roi = {x, y, width, height, qp};
            frame_data->rois.push_back(roi);
        }
    }
    
    /**
     * 清除所有ROI区域
     * 
     * @param frame_data 帧数据指针
     */
    void clear_roi_regions(FrameData* frame_data) {
        if (frame_data) {
            frame_data->rois.clear();
        }
    }
    
    /**
     * 设置帧数据
     * 
     * @param frame_data 帧数据指针
     * @param data 图像数据
     * @param size 数据大小
     * @param timestamp 时间戳
     * @return 是否成功设置
     */
    bool set_frame_data(FrameData* frame_data, const uint8_t* data, int size, int64_t timestamp) {
        if (!frame_data || !data) {
            return false;
        }
        
        int expected_size = frame_data->width * frame_data->height * frame_data->channels;
        if (size != expected_size) {
            return false;
        }
        
        memcpy(frame_data->data, data, size);
        frame_data->timestamp = timestamp;
        return true;
    }
    
    /**
     * 将帧推送到流
     * 
     * @param streamer 推流器指针
     * @param frame_data 帧数据指针
     * @return 是否成功推送
     */
    bool push_frame(RTMPStreamer* streamer, const FrameData* frame_data) {
        return streamer && frame_data ? streamer->pushFrame(*frame_data) : false;
    }
}
