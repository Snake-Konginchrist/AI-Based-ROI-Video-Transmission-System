import cv2


class CameraStream:
    def __init__(self, camera_id):
        self.cap = cv2.VideoCapture(camera_id)
        self.running = False

    def get_frame(self):
        if self.cap.isOpened():
            ret, frame = self.cap.read()
            if ret:
                return frame
        return None

    def release(self):
        self.cap.release()
