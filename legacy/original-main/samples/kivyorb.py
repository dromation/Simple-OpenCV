import cv2
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.image import Image as KivyImage
from kivymd.app import MDApp
from kivymd.uix.button import MDFlatButton
from kivymd.uix.slider import MDSlider


class MainLayout(BoxLayout):
    def __init__(self, **kwargs):
        super(MainLayout, self).__init__(**kwargs)
        self.orientation = 'vertical'
        
        self.image = KivyImage(source='input_image.jpg')
        self.add_widget(self.image)
        
        self.slider = MDSlider(min=1, max=100, value=50)
        self.add_widget(self.slider)
        
        self.button = MDFlatButton(text='Detect Keypoints')
        self.button.bind(on_press=self.detect_keypoints)
        self.add_widget(self.button)
    
    def detect_keypoints(self, *args):
        orb = cv2.ORB_create(nfeatures=int(self.slider.value))
        
        image = cv2.imread('input_image.jpg', cv2.IMREAD_GRAYSCALE)
        keypoints, descriptors = orb.detectAndCompute(image, None)
        image_with_keypoints = cv2.drawKeypoints(image, keypoints, None)
        
        cv2.imshow('Image with Keypoints', image_with_keypoints)
        cv2.waitKey(0)
        cv2.destroyAllWindows()
        

class OrbApp(App):
    def build(self):
        return MainLayout()


if __name__ == '__main__':
    OrbApp().run()
