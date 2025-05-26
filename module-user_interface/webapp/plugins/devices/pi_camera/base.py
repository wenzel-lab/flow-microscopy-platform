from abc import ABC, abstractmethod

class BaseCamera(ABC):
    
    def __init__(self):
        pass

    @abstractmethod
    def get_camera_by_id(self, camera_id):
        pass

    @abstractmethod
    def get_all_cameras(self):
        pass

    @abstractmethod
    def setup_camera(self, cam):
        pass

    @abstractmethod
    def generate_frames(self, camera):
        pass

    @abstractmethod

    def get_camera_by_id(self, camera_id):
        pass