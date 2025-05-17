import requests as req
import tkinter as tk
import google_auth_oauthlib.flow, googleapiclient.errors, googleapiclient.discovery
import webbrowser, os, time, threading, events, random, asyncio
import sqlite3 as sql
from dotenv import load_dotenv, find_dotenv
from notifypy import Notify
from PIL import Image
from bs4 import BeautifulSoup

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
            events.search_error.notify('Already tracking that channel')
            return None

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
        uniq_id = channel['id']
        # thumbnail is channel pfp
        thumbnail = channel['snippet']['thumbnails']['default']['url']
        save_channel_icon(icon_url=thumbnail, handle=url)
    #TODO: handle possible errors
    except (KeyError, UnboundLocalError):
        events.search_error.notify('Channel not found or nonexistent')
        return None

    state = is_streaming(url)
    i = {'url': 'https://www.youtube.com/' + url, 'title': title, 'handle': url, 
         'status': True if state else False, 'id': uniq_id}
    if state:
        notify_on_live(channel=i)
    channels.append(i)

    # insert into db
    with sql.connect(DATABASE_PATH) as con:
        cur = con.cursor()
        cur.execute('INSERT INTO channels (title, handle, uniq_id) VALUES (?, ?, ?)', (title, url, uniq_id))
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
    except (FileExistsError, UnboundLocalError):
        pass
    # convert to PNG
    img = Image.open('i.jpg')
    try:
        new_file_path = ICONS_DIR_PATH + handle + '.png'
        img.save(new_file_path)
        os.remove('i.jpg')
    #TODO: handle possible errors
    except (FileNotFoundError, FileExistsError) as e:
        pass

def load_from_db():
    global channels
    with sql.connect(DATABASE_PATH) as con:
        cur = con.cursor()
        d = list(cur.execute('SELECT title, handle, uniq_id FROM channels'))
        for item in d:
            channels = [{'url': 'https://www.youtube.com/' + item[1], 'title': item[0], 'handle': item[1], 
                         'status': True if is_streaming(item[1]) else False, 'id': item[2]}] + channels


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

# function that runs in the background of the program, constantly checking all channels whether they are live or not
# interval is random from 1-2 minutes
def background_checking():
    global channels
    while True:
        seconds = 60 * random.uniform(0.8, 1.5)
        for channel in channels:
            status = is_streaming(channel['handle'])
            if channel['status'] == False and status:
                print(channel['title'] + ' is streaming!')
                channel['status'] = True
                events.channel_went_live.notify()
                notify_on_live(channel=channel)
            
            # channel goes offline
            elif channel['status'] == True and not status:
                channel['status'] = False
                events.channel_went_offline.notify()
        
        print('CHANNELS CHECKED')
        time.sleep(seconds)


def run_bg_threads():
    threads = []
    # bg checking thread
    i = threading.Thread(target=background_checking, daemon=True)
    i.start()

def sort_channels_by_status():
    global channels
    channels = sorted(channels, key=lambda x: x['status'], reverse=True)

# display a desktop notification when a channel goes live
# will only notify if user enables setting to notify
def notify_on_live(channel: dict):
    if not setting_1_state:
        return
    handle = channel['handle']
    title = '🔴 ' + channel['title'] + ' is now live!'
    message = handle + ' has started streaming, check it out!'
    
    notification = Notify()
    notification.name = 'Channel Tracker'
    notification.message = get_live_title(channel['id'])
    notification.title = title
    notification.icon = ICONS_DIR_PATH + handle + '.png'
    notification.audio = 'static/notification-ping.wav'

    notification.send()
    # direct to channel (optional)
    if setting_2_state:
        webbrowser.open_new('https://www.youtube.com/' + handle)

# returns the title of the current channel livestream
def get_live_title(uniq_id: str):
    live_url = r'https://www.youtube.com/channel/' + uniq_id + '/live'

    try:
        res = req.get(live_url).text
        soup = BeautifulSoup(res, 'html.parser')
        meta_tag = soup.find('meta', attrs={'name': 'title'})
        return meta_tag['content']
    except TypeError:
        return 'Check them out!'

    #TODO: handle possible errors

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
            except (NotADirectoryError, FileNotFoundError):
                pass

            break