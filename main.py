import tkinter as tk
from src.python.stream.camera import CameraStream
from src.python.stream.display import StreamDisplay
from src.python.ai.processor import Processor


def main():
    root = tk.Tk()
    root.title("AI Enhanced Video Stream")

    # 初始化模块
    camera_stream = CameraStream(0)

    # 提供正确的模型权重文件、配置文件和类名文件路径
    model_weights = 'model/yolov3.weights'
    model_cfg = 'model/yolov3-face.cfg'
    class_names = 'model/face.names'
    ai_processor = Processor(model_weights, model_cfg, class_names)

    display = StreamDisplay(root, camera_stream, ai_processor)

    # 开始视频流处理
    display.start_stream()
    root.mainloop()


if __name__ == "__main__":
    main()
