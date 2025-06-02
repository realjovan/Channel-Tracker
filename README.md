# onLive
A desktop application that notifies you when your favorite YouTube channel/s go live.

![onLive's GUI](https://i.imgur.com/8tZWlf5.png)

## Made using:
__Python__

onLive was made purely in Python, relying on themed tkinter for its front-end design.

The program uses a third-party tkinter theme, [azure](https://github.com/rdbende/Azure-ttk-theme) by [rbdende](https://github.com/rdbende).

## Why?:
I just wanted a simple way to be notified on my computer when a streamer I watch goes live. And I thought that a project like this one would make a good learning experience for a beginner like me, which it definitely was (and still is as I continue to fix some bugs).

## How?:
Before trying to track a channel, make sure that you first insert __your own YouTube API key__ within the .env file. You can do this by simply pasting: `GOOGLE_API_KEY = '{your-key-here}'` into the .env file. If there is no .env file, you can create it manually as a new Notepad note, specifically named __.env__. You will not be able to use the application without a proper API key.

If unfamiliar with YouTube's API, you can follow these two separate guides by Google in creating a project then obtaining an API key:

[YouTube API Overview](https://developers.google.com/youtube/v3/getting-started)

[Obtaining authorization credentials](https://developers.google.com/youtube/registering_an_application)

This program runs through [gui.py](gui.py)

## Known bugs:
~> At some point, whenever I have this program running in the background, there's a possibility that it will just stop updating the channels statuses. Unclear whether it just won't update the UI or the background logic just stopped working but it's probably the latter. Additionally, while these are two different bugs, the program sometimes sends a notification twice pertaining to the same livestream. This happens when I wake up my computer from idle state after leaving it idle for a while. I have a feeling that having the computer on idle also causes the first bug. Will have to fix this somehow.
