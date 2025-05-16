import requests as req
import tkinter as tk
import google_auth_oauthlib.flow, googleapiclient.errors, googleapiclient.discovery
import webbrowser, os, time
import sqlite3 as sql
from dotenv import load_dotenv, find_dotenv
from notifypy import Notify
from PIL import Image

channels = []

DATABASE_PATH = r'src/database.db'
ICONS_DIR_PATH = r'static/channel-icons/'

setting_1_state: bool = True
setting_2_state: bool = False

dotenv_path = find_dotenv()
load_dotenv()
load_dotenv(find_dotenv(usecwd=True))

# TODO: error handling

def search_youtube_channel(handle: str):
    global channels
    # check for duplicate
    handle.lower().strip
    for channel in channels:
        if handle == channel['handle']:
            print('Duplicate')
            return

    DEVELOPER_KEY = os.getenv('UTUBE_API_KEY')
    api_service_name = "youtube"
    api_version = "v3"

    youtube = googleapiclient.discovery.build(
    api_service_name, api_version, developerKey=DEVELOPER_KEY)

    request = youtube.channels().list(
        part="snippet,contentDetails,statistics",
        forHandle=handle
    )
    if not request:
        return None

    response = request.execute()
    # extract relevant data
    try:
        channel = response['items'][0]
        title = channel['snippet']['title']
        url = channel['snippet']['customUrl']
        # thumbnail is channel pfp
        thumbnail = channel['snippet']['thumbnails']['default']['url']
    #TODO: handle possible errors
    except KeyError:
        pass

    save_channel_icon(thumbnail, url)

    if is_streaming(url):
        i = {'url': 'https://www.youtube.com/' + url, 'title': title, 'handle': url, 'status': True,
            'icon': thumbnail}
        channels = [i] + channels
        notify_on_live(title, ICONS_DIR_PATH + url + '.png', url)
    else:
        i = {'url': 'https://www.youtube.com/' + url, 'title': title, 'handle': url, 'status': False,
            'icon': thumbnail}
        channels.append(i)

    # insert into db
    with sql.connect(DATABASE_PATH) as con:
        cur = con.cursor()
        cur.execute('INSERT INTO channels (title, handle, icon) VALUES (?, ?, ?)', (title, url, thumbnail))
        con.commit()

    return i

# saves a channel's YouTube pfp as a PNG into static/channel-icons
def save_channel_icon(icon_url: str, handle: str):
    img_data = req.get(icon_url).content
    file_name = ICONS_DIR_PATH + handle
    # temp jpeg file
    try:
        with open('i.jpg', 'wb') as handler:
            handler.write(img_data)
    #TODO: handle possible errors
    except IsADirectoryError:
        pass
    # convert to PNG
    img = Image.open('i.jpg')
    try:
        new_file_path = ICONS_DIR_PATH + handle + '.png'
        img.save(new_file_path)
        os.remove('i.jpg')
    #TODO: handle possible errors
    except Exception as e:
        pass

def load_from_db():
    global channels
    with sql.connect(DATABASE_PATH) as con:
        cur = con.cursor()
        d = list(cur.execute('SELECT title, handle, icon FROM channels'))
        for item in d:
            if is_streaming(item[1]):
                channels = [{'url': 'https://www.youtube.com/' + item[1], 'title': item[0], 'handle': item[1], 'status': True,
                              'icon': item[2]}] + channels
                
                notify_on_live(item[0], ICONS_DIR_PATH + item[1] + '.png', item[1])
            else:
                channels.append({'url': 'https://www.youtube.com/' + item[1], 'title': item[0], 'handle': item[1], 'status': False,
                              'icon': item[2]})


# TODO: html response is too large, find more efficient way
def is_streaming(handle: str) -> bool:
    # this indicator will only appear on a channel's source code when they are streaming
    indicator = r'{"text":" watching"}'
    url = r'https://www.youtube.com/' + handle
    res = req.get(url)
    if res:
        if indicator in res.text:
            return True
        
    return False

# display a desktop notification when a channel goes live
# will only notify if user enables setting to notify
def notify_on_live(channel_name: str, icon_path: str, handle: str):
    if not setting_1_state:
        return
    title = '🔴 ' + channel_name + ' is now live!'
    message = handle + ' has started streaming, check it out!'
    
    notification = Notify()
    notification.name = 'Channel Tracker'
    notification.message = message
    notification.title = title
    notification.icon = icon_path
    notification.audio = 'static/notification-ping.wav'

    notification.send()
    # direct to channel (optional)
    if setting_2_state:
        webbrowser.open_new('https://www.youtube.com/' + handle)

def callback(url: str):
    return lambda e: webbrowser.open(url)

def untrack_channel(handle: str):
    for channel in channels:
        if channel['handle'] == handle:
            channels.remove(channel)
            # delete from db
            with sql.connect(DATABASE_PATH) as con:
                cur = con.cursor()
                cur.execute('DELETE FROM channels WHERE handle = ?', (handle,))
                con.commit()
            # delete channel pfp from storage
            try:
                os.remove(ICONS_DIR_PATH + channel['handle'] + '.png')
            #TODO: handle possible errors
            except NotADirectoryError:
                pass

            break