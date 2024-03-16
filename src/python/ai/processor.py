import cv2
import numpy as np


class Processor:
    # def __init__(self, model_weights, model_cfg, class_names):
    #     self.net = cv2.dnn.readNet(model_weights, model_cfg)
    #     self.classes = open(class_names).read().strip().split('\n')
    def __init__(self, model_weights, model_cfg, class_names):
        self.net = cv2.dnn.readNetFromDarknet(model_cfg, model_weights)
        self.classes = []
        with open(class_names, 'r') as f:
            self.classes = [line.strip() for line in f.readlines()]

    def process_frame(self, frame):

        # 将图像转换为 YOLOv3 需要的格式
        height, width, _ = frame.shape
        blob = cv2.dnn.blobFromImage(frame, 1/255.0, (416, 416), (0, 0, 0), True, crop=False)

        # 将 blob 输入到网络中进行预测
        self.net.setInput(blob)
        outs = self.net.forward(self.get_output_layers())

        class_ids = []
        confidences = []
        boxes = []
        conf_threshold = 0.5
        nms_threshold = 0.4

        # 解析预测结果
        for out in outs:
            for detection in out:
                scores = detection[5:]
                class_id = np.argmax(scores)
                confidence = scores[class_id]

                # 绘制目标检测结果
                if confidence > conf_threshold:
                    center_x = int(detection[0] * width)
                    center_y = int(detection[1] * height)
                    w = int(detection[2] * width)
                    h = int(detection[3] * height)
                    x = center_x - w / 2
                    y = center_y - h / 2
                    class_ids.append(class_id)
                    confidences.append(float(confidence))
                    boxes.append([x, y, w, h])

                    # x, y, w, h = detection[0:4]
                    # left = int(x - w / 2)
                    # top = int(y - h / 2)
                    # right = int(x + w / 2)
                    # bottom = int(y + h / 2)
                    # cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
                    # cv2.putText(frame, self.classes[class_id], (left, top - 10), cv2

        indices = cv2.dnn.NMSBoxes(boxes, confidences, conf_threshold, nms_threshold)

        for i in indices:
            i = i[0]
            box = boxes[i]
            x, y, w, h = box[0], box[1], box[2], box[3]

            self.draw_prediction(frame, class_ids[i], confidences[i], round(x), round(y), round(x + w), round(y + h))

        return frame

    def get_output_layers(self):
        layer_names = self.net.getLayerNames()
        output_layers = [layer_names[i[0] - 1] for i in self.net.getUnconnectedOutLayers()]
        return output_layers

    def draw_prediction(self, img, class_id, confidence, x, y, x_plus_w, y_plus_h):
        label = str(self.classes[class_id])
        color = (0, 255, 0)
        cv2.rectangle(img, (x, y), (x_plus_w, y_plus_h), color, 2)
        cv2.putText(img, label, (x - 10, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

# 使用示例
# ai_processor = Processor('yolov3.weights', 'yolov3.cfg', 'coco.names')
