/**
 * RTMP推流器C接口头文件
 * 
 * 提供了RTMP推流器的C语言接口，用于其他语言调用
 * 
 * 作者: PycharmProjects
 * 日期: 2023
 */

#ifndef RTMP_C_API_H
#define RTMP_C_API_H

#ifdef __cplusplus
extern "C" {
#endif

// 导出标记
#if defined(_WIN32) || defined(_WIN64)
    #ifdef RTMP_EXPORTS
        #define RTMP_API __declspec(dllexport)
    #else
        #define RTMP_API __declspec(dllimport)
    #endif
#else
    #define RTMP_API
#endif

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
RTMP_API void* create_rtmp_streamer(const char* url, int width, int height, 
                                int fps, int bitrate, int gop, int qp);

/**
 * 释放RTMP推流器
 * 
 * @param streamer 推流器指针
 */
RTMP_API void destroy_rtmp_streamer(void* streamer);

/**
 * 初始化推流器
 * 
 * @param streamer 推流器指针
 * @return 是否成功初始化
 */
RTMP_API int initialize_streamer(void* streamer);

/**
 * 开始推流
 * 
 * @param streamer 推流器指针
 * @return 是否成功启动推流
 */
RTMP_API int start_streaming(void* streamer);

/**
 * 停止推流
 * 
 * @param streamer 推流器指针
 */
RTMP_API void stop_streaming(void* streamer);

/**
 * 创建帧数据结构
 * 
 * @param width 图像宽度
 * @param height 图像高度
 * @param channels 图像通道数
 * @return 帧数据指针
 */
RTMP_API void* create_frame_data(int width, int height, int channels);

/**
 * 释放帧数据结构
 * 
 * @param frame_data 帧数据指针
 */
RTMP_API void destroy_frame_data(void* frame_data);

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
RTMP_API void add_roi_region(void* frame_data, int x, int y, int width, int height, int qp);

/**
 * 清除所有ROI区域
 * 
 * @param frame_data 帧数据指针
 */
RTMP_API void clear_roi_regions(void* frame_data);

/**
 * 设置帧数据
 * 
 * @param frame_data 帧数据指针
 * @param data 图像数据
 * @param size 数据大小
 * @param timestamp 时间戳
 * @return 是否成功设置
 */
RTMP_API int set_frame_data(void* frame_data, const unsigned char* data, int size, long long timestamp);

/**
 * 将帧推送到流
 * 
 * @param streamer 推流器指针
 * @param frame_data 帧数据指针
 * @return 是否成功推送
 */
RTMP_API int push_frame(void* streamer, void* frame_data);

#ifdef __cplusplus
}
#endif

#endif // RTMP_C_API_H 