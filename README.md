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

## Note:
As this program runs in the background, it's more likely than not that when the computer sleeps, the connection made by the app to the web is interrupted, and will therefore cause an exception. This is not a problem per se, but this means that any channels that went live during this interruption will have their notifications appear only after the computer wakes. The same goes for channels that have gone live during the computer's sleep.
