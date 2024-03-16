import cv2


class CameraStream:
    # def __init__(self, camera_id):
    #     self.cap = cv2.VideoCapture(camera_id)
    #     self.running = False

    def __init__(self, source_id, resolution=(640, 480)):
        self.cap = cv2.VideoCapture(source_id)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, resolution[0])
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, resolution[1])

    def get_frame(self):
        if self.cap.isOpened():
            ret, frame = self.cap.read()
            if ret:
                return frame
        return None

    def stop(self):
        self.cap.release()
