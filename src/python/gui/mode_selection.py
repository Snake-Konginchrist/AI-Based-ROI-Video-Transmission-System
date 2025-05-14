import tkinter as tk
from tkinter import ttk


class ModeSelectionWindow:
    """模式选择窗口类"""
    
    def __init__(self):
        """初始化模式选择窗口"""
        self.selected_mode = None
    
    def get_selected_mode(self):
        """显示模式选择窗口并获取用户选择的模式
        
        Returns:
            str: 选择的模式（"client", "server", "local"）
                 如果用户取消选择，返回None
        """
        # 创建窗口
        root = tk.Tk()
        root.title("选择运行模式")
        root.geometry("400x300")
        
        # 创建变量存储选择的模式
        mode_var = tk.StringVar()
        
        # 创建标题
        title_label = tk.Label(root, text="基于嵌入式AI的ROI区域视频传输系统", font=("Arial", 14))
        title_label.pack(pady=20)
        
        # 创建模式选择框架
        frame = tk.Frame(root)
        frame.pack(pady=10)
        
        # 模式选择单选按钮
        modes = [
            ("客户端模式 - 推送视频流", "client"),
            ("服务端模式 - 接收并处理视频流", "server"),
            ("本地处理模式 - 无需网络传输", "local")
        ]
        
        for text, mode in modes:
            rb = tk.Radiobutton(frame, text=text, variable=mode_var, value=mode)
            rb.pack(anchor=tk.W, pady=5)
        
        # 默认选择本地模式
        mode_var.set("local")
        
        # 确认按钮回调函数
        def on_confirm():
            self.selected_mode = mode_var.get()
            root.destroy()
        
        # 取消按钮回调函数
        def on_cancel():
            self.selected_mode = None
            root.destroy()
        
        # 创建按钮框架
        button_frame = tk.Frame(root)
        button_frame.pack(pady=20)
        
        # 确认按钮
        confirm_button = tk.Button(button_frame, text="确认", command=on_confirm, width=10)
        confirm_button.pack(side=tk.LEFT, padx=10)
        
        # 取消按钮
        cancel_button = tk.Button(button_frame, text="取消", command=on_cancel, width=10)
        cancel_button.pack(side=tk.LEFT, padx=10)
        
        # 启动主循环
        root.mainloop()
        
        # 返回选择的模式
        return self.selected_mode


# 用于测试
if __name__ == "__main__":
    selector = ModeSelectionWindow()
    mode = selector.get_selected_mode()
    print(f"选择的模式: {mode}") 