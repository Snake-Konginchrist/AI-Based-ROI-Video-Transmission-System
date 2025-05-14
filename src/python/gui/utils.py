"""
GUI工具模块，提供各种辅助功能
"""
import os
import sys
import tkinter as tk
from tkinter import ttk, messagebox


def create_tooltip(widget, text):
    """为控件创建悬停提示
    
    Args:
        widget: 需要添加提示的控件
        text: 提示文本
    """
    tooltip = None
    
    def enter(event):
        nonlocal tooltip
        x, y, _, _ = widget.bbox("insert")
        x += widget.winfo_rootx() + 25
        y += widget.winfo_rooty() + 20
        
        # 创建提示窗口
        tooltip = tk.Toplevel(widget)
        tooltip.wm_overrideredirect(True)
        tooltip.wm_geometry(f"+{x}+{y}")
        
        label = tk.Label(tooltip, text=text, background="#FFFFDD", relief="solid", borderwidth=1)
        label.pack()
    
    def leave(event):
        nonlocal tooltip
        if tooltip:
            tooltip.destroy()
            tooltip = None
    
    widget.bind("<Enter>", enter)
    widget.bind("<Leave>", leave)


# 用于测试
if __name__ == "__main__":
    # 测试创建tooltip
    root = tk.Tk()
    button = tk.Button(root, text="测试按钮")
    button.pack(pady=20)
    create_tooltip(button, "这是一个测试按钮")
    root.mainloop() 