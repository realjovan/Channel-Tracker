from tkinter import *
from tkinter import font
from plyer import notification
from PIL import Image
import requests as req
import os, sys

img_address = r'https://pbs.twimg.com/profile_images/1805470826520567808/oXxgfwjC_400x400.jpg'

img_data = req.get(img_address).content

with open('test.jpg', 'wb') as handler:
    handler.write(img_data)

if not os.path.exists('test.jpg'):
    print('File doesn\'t exist.')
    sys.exit(1)

print('File exists')

# convert to ICO
sizes = (88,88)
img = Image.open('test.jpg')
try:
    img.save('imgtest/new.ico')
except Exception as e:
    pass

notification.notify(title='Test', message='Test', timeout=2, app_icon='imgtest/new.ico')


