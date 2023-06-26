# Simple OPENCV VERSION 0.1

#IMPORT BASICS
import sys, os, pathlib
from typing import Union
import socket
from time import time
from datetime import datetime
from os.path import dirname, join
import cv2 as cv
import numpy as np
import glob
import webbrowser
#from root.ModelPrep import validate_params, change_koatuu, prep_params, load_regression

#IMPORT PANDAS
#import pandas as pd
#import sqlite3

#IMPORT SCIKITLEARN FOR MACHINE LEARNING
#import scikitlearn as sct

#IMPORT KIVY FOR GUI
import kivy
#from kivy.app import App
from kivymd.app import MDApp
from kivy.uix.widget import Widget
from kivymd.uix.widget import MDWidget
from kivymd.uix import *
from kivy.properties import ObjectProperty, NumericProperty, StringProperty, BooleanProperty,\
    ListProperty
from kivy.metrics import dp
from kivy.lang import Builder
#from kivymd.app import Builder
from kivy.core.window import Window
from kivy.uix.slider import Slider
#from kivy.uix.screenmanager import Screen, ScreenManager
from kivymd.uix.screen import MDScreen
from kivymd.uix.screenmanager import MDScreenManager
from kivymd.uix.screenmanager import ScreenManager
from kivymd.uix.toolbar import MDTopAppBar
from kivymd.uix.menu import MDDropdownMenu
from kivymd.uix.button import MDRaisedButton, MDIconButton, MDFlatButton
from kivymd.uix.floatlayout import MDFloatLayout
from kivy.uix.button import Button
from kivymd.uix.label import MDLabel
from kivymd.uix.boxlayout import MDBoxLayout
from optparse import Values
from kivy.core.window import Window
from kivy.uix.image import Image
from kivymd.uix.menu import MDDropdownMenu
from kivymd.uix.filemanager import MDFileManager
from kivy.uix.camera import Camera
from kivymd.toast import toast


class HomeScreen(MDScreen):
    sm = ScreenManager()
    layout = MDBoxLayout(orientation = 'vertical',
                         pos_hint=  {'center_x': 0.5,'center_y': 0.5})
    button = MDIconButton(icon = 'arrow-right-circle-outline',
                          text = "Next",
                          pos_hint = {"center_x": .5, "center_y": 0.5},
                          #md_bg_color = toolbar.md_bg_color,
                          on_release = sm.current == 'camera')
    layout.add_widget(button)


    

class CameraScreen(MDScreen):
    camera = Camera(index=2, resolution=(640,480))
    def capture(self):
        '''
        Function to capture the images and give them the names
        according to their captured time and date.
        '''
        camera = self.ids['camera']
        timestr = time.strftime("%Y%m%d_%H%M%S")
        camera.export_to_png("IMG_{}.png".format(timestr))
        print("Captured")


class SmotoApp(MDApp):
    title = 'Simple OpenCV'
    sm = ScreenManager()
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        Window.bind(on_keyboard=self.events)
        self.manager_open = False
        self.file_manager = MDFileManager(
            exit_manager=self.exit_manager, select_path=self.select_path
        )
    def build(self):
        
        self.theme_cls.theme_style = "Light"
        #self.theme_cls.primary_palette = "LightBlue"
        #self.theme_cls.material_style = "M3"
        return Builder.load_file('smoto.kv')
    #def on_start(self):
    #    self.fps_monitor_start()
        
    def on_save(self, instance, value):
        print(instance, value)

    def on_cancel(self, instance, value):
        print(instance, value)

    def homescreen(self): self.sm.switch_to(screen='home')

    def callback(self, button):
        self.menu.caller = button
        self.menu.open()

    def home_callback(self, text_item):
        self.menu.dismiss()
        Snackbar(text=text_item).open()

    def menu_callback(self, text_item):
        self.menu.dismiss()
        Snackbar(text=text_item).open()


    def on_pause(self):
        return True

    def on_resume(self):
        pass
    #HELP commands
    def help(self):
        webbrowser.open('https://docs.opencv.org/4.x/')
    #FILE MANAGER COMMANDS
    def file_manager_open(self):
        self.file_manager.show(os.path.expanduser("~"))  # output manager to the screen
        self.manager_open = True

    def select_path(self, path: str):
        '''
        It will be called when you click on the file name
        or the catalog selection button.

        :param path: path to the selected directory or file;
        '''

        self.exit_manager()
        toast(path)

    def exit_manager(self, *args):
        '''Called when the user reaches the root of the directory tree.'''

        self.manager_open = False
        self.file_manager.close()

    def events(self, instance, keyboard, keycode, text, modifiers):
        '''Called when buttons are pressed on the mobile device.'''

        if keyboard in (1001, 27):
            if self.manager_open:
                self.file_manager.back()
        return True

    #section of image menu commands

    imagemenus = {
            "Python": "language-python",
            "C++": "language-cpp",
            "Ruby": "language-ruby",
            "Kivy": "language-kivy"
        }
    def imgcallback(self, instance):
        """for keys,Values in data:
            if instance.icon == data(Values):
                lang = print("you pressed", instance.icon)
            else:
                pass"""

        if instance.icon == 'language-python':
            lang = "Python"
        elif instance.icon == 'language-cpp':
            lang = "C++"
        elif instance.icon == 'language-ruby':
            lang = "Ruby"
        elif instance.icon == 'language-kivy':
            lang = "Kivy"
        self.root.ids.images.text = f'you pressed {lang}'

        #self.root.ids.my_label.text = f'you pressed {instance.icon}'

    def imgopen(self):
        self.root.ids.images.text = f'Create Image'

    def imgclose(self):
        self.root.ids.images.text = f'Images'

    #templates commands
    templatecoms = {
            "Python": "language-python",
            "C++": "language-cpp",
            "Ruby": "language-ruby",
            "Kivy": "language-kivy"
        }
    def tmpcallback(self, instance):
        """for keys,Values in data:
            if instance.icon == data(Values):
                lang = print("you pressed", instance.icon)
            else:
                pass"""

        if instance.icon == 'language-python':
            lang = "Python"
        elif instance.icon == 'language-cpp':
            lang = "C++"
        elif instance.icon == 'language-ruby':
            lang = "Ruby"
        elif instance.icon == 'language-kivy':
            lang = "Kivy"
        self.root.ids.templates.text = f'you pressed {lang}'

        #self.root.ids.my_label.text = f'you pressed {instance.icon}'

    def tmpopen(self):
        self.root.ids.templates.text = f'Choose Template'

    def tmpclose(self):
        self.root.ids.templates.text = f'Template'

    #camera test




if __name__ == '__main__':
    SmotoApp().run()