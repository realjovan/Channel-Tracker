import requests as req
import tkinter as tk
import google_auth_oauthlib.flow, googleapiclient.errors, googleapiclient.discovery
import google.auth.exceptions
import webbrowser, os, time, threading, events, random, asyncio
import sqlite3 as sql
from dotenv import load_dotenv, find_dotenv
from notifypy import Notify
from PIL import Image
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

channels = []

DATABASE_PATH = r'src/database.db'
ICONS_DIR_PATH = r'static/channel-icons/'

window_hidden: bool = False
setting_1_state: bool = True
setting_2_state: bool = False

dotenv_path = find_dotenv()
load_dotenv()
load_dotenv(find_dotenv(usecwd=True))

# Google YouTube API key (should be provided by user)
developer_key: str

session = req.Session()
retry = Retry(connect=3, backoff_factor=0.5)
adapter = HTTPAdapter(max_retries=retry)
session.mount('http://', adapter)
session.mount('https://', adapter)

# TODO: error handling

def search_youtube_channel(handle: str):
    global channels
    # check for duplicate
    handle.lower().strip
    for channel in channels:
        if handle == channel['handle']:
            events.search_error.notify('Already tracking that channel')
            return None
        
    if not developer_key:
        get_api_key()

    api_service_name = "youtube"
    api_version = "v3"

    try:
        youtube = googleapiclient.discovery.build(
        api_service_name, api_version, developerKey=developer_key)

        request = youtube.channels().list(
            part="snippet,contentDetails,statistics",
            forHandle=handle
        )
        if not request:
            return None

        response = request.execute()
    except google.auth.exceptions.DefaultCredentialsError:
        events.search_error.notify('No API key. Please follow README.md')
        return None

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
        new = threading.Thread(target=notify_on_live, args=(i,)).start()
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
    # check if a database exists
    if not os.path.isfile(DATABASE_PATH):
        new_database()

    with sql.connect(DATABASE_PATH) as con:
        cur = con.cursor()
        d = list(cur.execute('SELECT title, handle, uniq_id FROM channels'))
        for item in d:
            channels = [{'url': 'https://www.youtube.com/' + item[1], 'title': item[0], 'handle': item[1], 
                         'status': True if is_streaming(item[1]) else False, 'id': item[2]}] + channels

# create a fresh database
def new_database():
    print('CREATING NEW TABLE')
    table_scheme = """CREATE TABLE channels(
    title TEXT NOT NULL,
    handle TEXT PRIMARY KEY NOT NULL,
    uniq_id TEXT NOT NULL
    );"""
    
    with sql.connect(DATABASE_PATH) as con:
        cur = con.cursor()
        cur.execute(table_scheme)
        con.commit()

# TODO: html response is too large, find more efficient way
def is_streaming(handle: str) -> bool:
    # this indicator will only appear on a channel's source code when they are streaming
    indicator = r'{"text":" watching"}'
    url = r'https://www.youtube.com/' + handle
    try:
        res = req.get(url)
        if indicator in res.text:
            return True
        return False
    # max retries exceeded
    except req.exceptions.ConnectionError:
        time.sleep(1.5)
        return is_streaming(handle)

# function that runs in the background of the program, constantly checking all channels whether they are live or not
# interval is random from 1-2 minutes
def background_checking():
    global channels
    count = 0
    while True:
        count += 1
        seconds = 60 * random.uniform(0.8, 1.5)
        for channel in channels:
            status = is_streaming(channel['handle'])
            if channel['status'] == False and status:
                print(channel['title'] + ' is streaming!')
                channel['status'] = True
                temp_thread = threading.Thread(target=notify_on_live, args=(channel,)).start()
                if not window_hidden:
                    events.channel_went_live.notify()
            
            # channel goes offline
            elif channel['status'] == True and not status:
                channel['status'] = False
                if not window_hidden:
                    events.channel_went_offline.notify()

            time.sleep(1)
        
        print('CHANNELS CHECKED - {num}'.format(num=count))
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

def on_window_hidden():
    global window_hidden
    print('--WINDOW IS HIDDEN')
    window_hidden = True

def on_window_shown():
    global window_hidden
    print('--WINDOW IS SHOWN')
    window_hidden = False

events.gui_hidden.subscribe(on_window_hidden)
events.gui_shown.subscribe(on_window_shown)

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

def get_api_key():
    global developer_key
    developer_key = os.getenv('GOOGLE_API_KEY')

events.app_launched.subscribe(load_from_db)
events.app_launched.subscribe(run_bg_threads)
events.app_launched.subscribe(get_api_key)