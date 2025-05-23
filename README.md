# onLive
A desktop application that notifies you when your favorite YouTube channel/s go live.

![onLive's GUI](https://i.imgur.com/8tZWlf5.png)

## Made using:
__Python__

onLive was made purely in Python, relying on themed tkinter for its front-end design.

The program uses a third-party tkinter theme, [azure](https://github.com/rdbende/Azure-ttk-theme) by [rbdende](https://github.com/rdbende).

## How to run:
Before trying to track a channel, make sure that you first insert __your own YouTube API key__ within the .env file. You can do this by simply pasting: `GOOGLE_API_KEY = '{your-key-here}'`. You will not be able to use the application without a proper API key.

If unfamiliar with YouTube's API, you can follow these two separate guides by Google in creating a project then obtaining an API key:

[YouTube API Overview](https://developers.google.com/youtube/v3/getting-started)

[Obtaining authorization credentials](https://developers.google.com/youtube/registering_an_application)
