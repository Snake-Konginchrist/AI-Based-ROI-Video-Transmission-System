import cv2
import numpy as np
import os
from ultralytics import YOLO


class Processor:
    """AI处理器类，负责视频帧的智能处理"""
    
    def __init__(self, model_weights="yolo11n", model_cfg=None, class_names=None):
        """
        初始化AI处理器
        
        Args:
            model_weights: YOLO模型名称（无需后缀，如'yolo11n'）或自定义模型路径
            model_cfg: 不再使用，保留为向后兼容
            class_names: 不再使用，保留为向后兼容
        """
        try:
            # 确保models目录存在
            models_dir = os.path.abspath('models')
            if not os.path.exists(models_dir):
                os.makedirs(models_dir)
                print("已创建models目录")
            
            # 注意：环境变量已在main.py中设置
            # os.environ['YOLO_CONFIG_DIR'] = os.path.abspath('models')
            
            # 检查是否需要下载模型或使用本地模型
            model_path = model_weights
            if not os.path.exists(model_weights) and not model_weights.startswith(models_dir):
                # 如果不是绝对路径，则尝试在models目录中查找
                potential_model_path = os.path.join(models_dir, f"{model_weights}.pt")
                if os.path.exists(potential_model_path):
                    model_path = potential_model_path
                    print(f"使用本地模型: {model_path}")
            
            # 使用ultralytics加载模型
            # 优先自动选择最适合系统的模型版本
            self.net = YOLO(model_path)
            print(f"已成功加载YOLOv11模型: {model_weights}")
            
            # 获取模型支持的类别列表
            self.classes = self.net.names
            print(f"模型支持的类别数量: {len(self.classes)}")
            
        except Exception as e:
            raise Exception(f"无法加载模型: {e}")
        
        # 设置检测参数
        self.conf_threshold = 0.5  # 置信度阈值
        self.nms_threshold = 0.4   # 非极大值抑制阈值

    def process_frame(self, frame, return_rois=False, roi_qp=15, non_roi_qp=35):
        """
        处理视频帧，进行目标检测并应用差异化编码
        
        Args:
            frame: 输入的视频帧
            return_rois: 是否返回检测到的ROI区域信息
            roi_qp: ROI区域的QP值（低值=高质量）
            non_roi_qp: 非ROI区域的QP值（高值=低质量）
            
        Returns:
            处理后的帧，以及ROI区域信息（如果return_rois=True）
        """
        if frame is None:
            if return_rois:
                return None, []
            return None
        
        # 保存原始帧的副本
        original_frame = frame.copy()
        
        # 获取图像尺寸
        height, width, _ = frame.shape
        
        # 使用YOLOv11进行目标检测
        results = self.net(frame, conf=self.conf_threshold, iou=self.nms_threshold, verbose=False)
        
        # 创建掩码图像，用于标记ROI区域
        mask = np.zeros((height, width), dtype=np.uint8)
        
        # 解析检测结果
        rois = []  # ROI区域列表
        
        # 处理每个检测结果
        for result in results:
            boxes = result.boxes  # 获取边界框
            
            # 处理每个检测到的对象
            for i in range(len(boxes)):
                # 获取边界框坐标
                box = boxes[i].xyxy[0].cpu().numpy()  # 转换为numpy数组
                x1, y1, x2, y2 = box
                x, y = int(x1), int(y1)
                w, h = int(x2 - x1), int(y2 - y1)
                
                # 获取类别和置信度
                cls_id = int(boxes[i].cls[0].item())
                conf = float(boxes[i].conf[0].item())
                
                # 确保坐标不超出图像边界
                x = max(0, x)
                y = max(0, y)
                right = min(width, x + w)
                bottom = min(height, y + h)
                
                # 将检测到的对象区域标记为ROI
                cv2.rectangle(mask, (x, y), (right, bottom), 255, -1)  # 填充ROI区域
                
                # 在原始帧上绘制边界框和标签
                self.draw_prediction(frame, cls_id, conf, x, y, right, bottom)
                
                # 添加到ROI列表
                roi_info = {
                    'class': self.classes[cls_id],
                    'confidence': conf,
                    'box': [x, y, w, h]
                }
                rois.append(roi_info)
        
        # 应用差异化编码（模拟不同QP值的编码效果）
        # 在实际应用中，这里应该调用编码器API设置不同区域的QP值
        # 这里我们使用JPEG压缩模拟不同质量的编码效果
        roi_encoded = self.simulate_encoding(original_frame, mask, roi_qp, non_roi_qp)
        
        if return_rois:
            return roi_encoded, rois
        return roi_encoded

    def draw_prediction(self, img, class_id, confidence, x, y, x_plus_w, y_plus_h):
        """
        在图像上绘制检测结果
        
        Args:
            img: 要绘制的图像
            class_id: 类别ID
            confidence: 置信度
            x, y: 左上角坐标
            x_plus_w, y_plus_h: 右下角坐标
        """
        # 获取类别名称
        label = self.classes[class_id] if class_id in self.classes else f"未知类别-{class_id}"
        
        # 格式化置信度
        conf_text = f"{confidence:.2f}"
        
        # 绘制边界框
        color = self.get_color_for_class(class_id)
        cv2.rectangle(img, (x, y), (x_plus_w, y_plus_h), color, 2)
        
        # 绘制类别标签背景
        text_size, _ = cv2.getTextSize(f"{label} {conf_text}", cv2.FONT_HERSHEY_SIMPLEX, 0.5, 2)
        cv2.rectangle(img, (x, y - text_size[1] - 5), (x + text_size[0], y), color, -1)
        
        # 绘制类别标签文本
        cv2.putText(img, f"{label} {conf_text}", (x, y - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1)

    def get_color_for_class(self, class_id):
        """
        为不同类别生成不同的颜色
        
        Args:
            class_id: 类别ID
            
        Returns:
            BGR颜色值
        """
        colors = [
            (0, 255, 0),    # 绿色
            (255, 0, 0),    # 蓝色
            (0, 0, 255),    # 红色
            (255, 255, 0),  # 青色
            (0, 255, 255),  # 黄色
            (255, 0, 255),  # 洋红
            (127, 255, 0),  # 黄绿色
            (255, 127, 0),  # 蓝紫色
            (127, 0, 255),  # 红紫色
            (255, 255, 255) # 白色
        ]
        return colors[class_id % len(colors)]

    def simulate_encoding(self, original_frame, mask, roi_qp, non_roi_qp):
        """
        模拟不同区域使用不同QP值编码的效果
        
        Args:
            original_frame: 原始视频帧
            mask: ROI区域掩码
            roi_qp: ROI区域的QP值（低值=高质量）
            non_roi_qp: 非ROI区域的QP值（高值=低质量）
            
        Returns:
            差异化编码后的帧
        """
        # 转换QP值到JPEG质量参数（0-100，与QP值相反，值越大质量越高）
        roi_quality = max(5, min(100, int(100 - (roi_qp * 2.5))))
        non_roi_quality = max(5, min(100, int(100 - (non_roi_qp * 2.5))))
        
        # 处理ROI区域（高质量）
        roi_frame = original_frame.copy()
        # 编码ROI区域（使用高质量）
        _, roi_encoded = cv2.imencode('.jpg', roi_frame, [cv2.IMWRITE_JPEG_QUALITY, roi_quality])
        roi_decoded = cv2.imdecode(roi_encoded, cv2.IMREAD_COLOR)
        
        # 处理非ROI区域（低质量）
        non_roi_frame = original_frame.copy()
        # 编码非ROI区域（使用低质量）
        _, non_roi_encoded = cv2.imencode('.jpg', non_roi_frame, [cv2.IMWRITE_JPEG_QUALITY, non_roi_quality])
        non_roi_decoded = cv2.imdecode(non_roi_encoded, cv2.IMREAD_COLOR)
        
        # 合并两个区域
        # 将mask转换为适合合并的形式
        mask_3ch = cv2.merge([mask, mask, mask])
        
        # 使用mask合并两个不同质量的帧
        result = np.where(mask_3ch > 0, roi_decoded, non_roi_decoded)
        
        # 添加文本说明
        cv2.putText(result, f"ROI QP: {roi_qp}", (10, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
        cv2.putText(result, f"非ROI QP: {non_roi_qp}", (10, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)
        
        return result.astype(np.uint8)

# 使用示例
# ai_processor = Processor('yolov3.weights', 'yolov3.cfg', 'coco.names')
