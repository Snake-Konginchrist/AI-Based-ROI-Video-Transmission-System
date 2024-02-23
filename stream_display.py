import cv2
import tkinter as tk
from PIL import Image, ImageTk
import threading


class StreamDisplay:
    def __init__(self, root, camera_stream, ai_processor):
        self.root = root
        self.camera_stream = camera_stream
        self.ai_processor = ai_processor
        self.original_label = tk.Label(root)
        self.original_label.pack(side=tk.LEFT)
        self.processed_label = tk.Label(root)
        self.processed_label.pack(side=tk.RIGHT)

    def update_frames(self):
        while self.camera_stream.running:
            frame = self.camera_stream.get_frame()
            if frame is not None:
                # 显示原始帧
                self.display_frame(self.original_label, frame)
                # 处理帧
                processed_frame = self.ai_processor.process_frame(frame)
                # 显示处理后的帧
                self.display_frame(self.processed_label, processed_frame)

    def start_stream(self):
        self.camera_stream.running = True
        thread = threading.Thread(target=self.update_frames)
        thread.daemon = True
        thread.start()

    @staticmethod
    def display_frame(self, label, frame):
        # OpenCV捕获的图像是BGR格式，需要转换为RGB格式
        cv2image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        pil_image = Image.fromarray(cv2image)
        imgtk = ImageTk.PhotoImage(image=pil_image)

        # 如果label已经有图像，则更新图像，否则使用label的config方法附加图像
        if label.imgtk:
            label.imgtk = imgtk
            label.configure(image=imgtk)
        else:
            label.imgtk = imgtk
            label.image = imgtk  # 保留引用
            label.configure(image=imgtk)
