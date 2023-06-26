import cv2
from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen
from kivy.lang import Builder
from kivy.clock import Clock
#from kivy.core.window import Window

Builder.load_file('camera_screen.kv')

class CameraScreen(MDScreen):
    def start_camera(self):
        # Start the camera
        self.cap = cv2.VideoCapture(2)
        #Clock.schedule_interval(self.update_frame, 1/30)
        if not self.cap.isOpened():
            print("Cannot open camera")
            exit()
        while self.cap.isOpened():
            ret, frame = self.cap.read()
            if not ret: 
                break
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
    def stop_camera(self):
        # Stop the camera
        self.cap.release()
        #Clock.unschedule(self.update_frame)

    #def update_frame(self):
        # Update the frame from the camera
        #img = self.ids.camera
        #while True:
         #   ret, frame = self.cap.read()
            #if not ret:
            #    break
                # Convert the frame to texture and display it
            #buf1 = cv2.flip(frame, 0)
            #buf = buf1.tostring()
            #texture = frame.create(size=(frame.shape[1], frame.shape[0]), colorfmt='bgr')
            #texture.blit_buffer(buf, colorfmt='bgr', bufferfmt='ubyte')
            #self.ids.camera.texture = texture
            #gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            #self.ids.camera.source = gray
class MainApp(MDApp):
    def build(self):
        #Window.fullscreen = 'auto'
        return CameraScreen()

if __name__ == '__main__':
    MainApp().run()
