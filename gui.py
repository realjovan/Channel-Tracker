import tkinter as tk
from tkinter import *
from tkinter import ttk
import app, webbrowser, os, time, events, threading
import tkinter.font as tkFont
from pystray import Menu, MenuItem, Icon
from PIL import Image

APP_ICON_PATH = r'static/app_icon.png'

class StreamTrackerGUI():
    def __init__(self, window):
        events.channel_went_live.subscribe(self.propagate_channels)
        events.channel_went_offline.subscribe(self.propagate_channels)
        events.gui_shown.subscribe(self.propagate_channels)
        events.search_error.subscribe(self.display_error)
        self.window = window
        self.displayed_channel_labels = []
        '''
        MISC VARIABLES
        '''
        # Color:
        self.clr_main = '#f0f0f0'
        self.clr_secondary = "#f0f0f0"
        self.clr_accent = '#2e7fe8'
        self.clr_secondary_accent = '#ff5151'

        # Fonts:
        self.fnt_main = 'Cascadia Code'
        self.fnt_size_main = 8

        # Icons:
        self.icn_app = PhotoImage(file=APP_ICON_PATH)

        # Settings states:
        self.setting_1_state = IntVar(value=1)
        self.setting_2_state = IntVar(value=0)

        # Theme
        self.window.call('source', 'azure/azure.tcl')
        self.window.call('set_theme', 'light')

        # Styles
        s = ttk.Style()
        self.default_font = tkFont.Font(root=window, family='Bahnschrift', size=9)
        self.default_font_bold = tkFont.Font(root=window, family='Bahnschrift', size=9, weight='bold')

        s.configure('SecondaryFrame.TFrame', background=self.clr_secondary)
        s.configure('SecondaryLabel.TLabel', background=self.clr_secondary)
        s.configure('TButton', background=self.clr_secondary)
        s.configure('TEntry', background=self.clr_secondary)
        s.configure('ErrorLabel.TLabel', background=self.clr_secondary, foreground='#ba3d3d')
        s.configure('LiveLabel.TLabel', background=self.clr_secondary, foreground='red')
        s.configure('SecondaryChannelLink.TLabel', background=self.clr_secondary)
        s.configure('.', font=self.default_font)
        '''
        WINDOW CONFIG
        '''
        self.window_base_width, window_base_height = 420, 740

        self.window.title('Streamer Notifier')
        self.window.iconphoto(True, self.icn_app)
        self.window.minsize(window_base_height, self.window_base_width)
        self.window.maxsize(window_base_height + 100, self.window_base_width + 100)

        '''
        FRAMES
        '''
        self.search_youtuber_frame = ttk.Frame(window)
        self.search_youtuber_frame.rowconfigure((0, 1), weight=1)
        self.search_youtuber_frame.rowconfigure(2, weight=0)
        self.search_youtuber_frame.columnconfigure((0, 2), weight=1)
        self.search_youtuber_frame.columnconfigure(1, weight=0)

        self.channels_list_frame = ttk.Frame(window)
        self.channels_list_frame.columnconfigure((0, 1), weight=0)
        self.channels_list_frame.columnconfigure((2, 3), weight=1)
        self.channels_list_frame.columnconfigure(4, weight=0)

        self.optionals_settings = ttk.Frame(window)
        self.optionals_settings.columnconfigure((0, 3), weight=0)
        self.optionals_settings.columnconfigure((1, 2), weight=1)
        self.optionals_settings.rowconfigure((0, 1), weight=1)

        # pack frames
        self.search_youtuber_frame.pack(fill='x', padx=1)
        self.optionals_settings.pack(fill='x', side='bottom')
        '''
        WIDGETS
        '''
        self.channel_handle_label = ttk.Label(self.search_youtuber_frame, text='Channel Handle:', font=self.default_font)
        self.channel_handle_entry = ttk.Entry(self.search_youtuber_frame, font=self.default_font)
        self.channel_handle_submit = ttk.Button(self.search_youtuber_frame, text='Track', command=self.search_for_channel)

        self.header_title_label = ttk.Label(self.channels_list_frame, text='Channel', padding=(10, 0), font=self.default_font_bold)
        self.header_handle_label = ttk.Label(self.channels_list_frame, text='Handle', font=self.default_font_bold)
        self.header_status_label = ttk.Label(self.channels_list_frame, text='Status', font=self.default_font_bold)
        self.header_remove_label = ttk.Label(self.channels_list_frame, text='Remove', padding=(10, 0), font=self.default_font_bold)

        self.setting_1 = ttk.Checkbutton(self.optionals_settings, text='Enable desktop notification',
                                     variable=self.setting_1_state, command=self.upd_setting_1_state)
        self.setting_1.selected = True

        self.setting_2 = ttk.Checkbutton(self.optionals_settings, text='Direct to channel when live',
                                     variable=self.setting_2_state, command=self.upd_setting_2_state)

        self.error_label = ttk.Label(self.search_youtuber_frame, text='', anchor=CENTER)
        self.error_label.configure(font=self.default_font, foreground='#ba3d3d')

        # place widgets
        self.channel_handle_label.grid(row=1, column=0, pady=(50, 3), sticky=E)
        self.channel_handle_entry.grid(row=1, column=1, padx=7, pady=(50, 3))
        self.channel_handle_submit.grid(row=1, column=2, pady=(50, 3), sticky=W)

        self.header_title_label.grid(row=0, column=1)
        self.header_handle_label.grid(row=0, column=2)
        self.header_status_label.grid(row=0, column=3)

        self.setting_1.grid(row=0, column=1, ipady=2, columnspan=1)
        self.setting_2.grid(row=0, column=2, ipady=2, columnspan=1)

        self.error_label.grid(row=2, column=0, pady=(5, 35), columnspan=3, sticky='nsew')


    def search_for_channel(self):
        handle = self.channel_handle_entry.get()
        try:
            if handle[0] != '@':
                handle = '@' + handle
            if len(handle) <= 1:
                raise IndexError()
        except IndexError:
            events.search_error.notify('No input received or too short (example: @niminightmare, niminightmare)')
            return

        data = app.search_youtube_channel(handle)
        if not data:
            return
        self.channel_handle_entry.delete(0, END)
        self.propagate_channels()

    # displays the list of channels on overview
    # NOTE: initial is only True when the program *initially* opens
    def propagate_channels(self, initial = False):
        app.sort_channels_by_status()
        if len(app.channels) == 0:
            self.channels_list_frame.pack_forget()
        else:
            self.channels_list_frame.pack(fill='x', pady=8)
        for i, channel in enumerate(app.channels):
            for j, key in enumerate(channel):
                lab = ttk.Label(self.channels_list_frame, text='', style='SecondaryLabel.TLabel' if i % 2 == 0 else '')
                lab.configure(padding=(0, 5), anchor=CENTER, font=self.default_font)
                
                if j == 0:
                    lab.configure(text='🔗', cursor='hand2', style='SecondaryChannelLink.TLabel' if i % 2 == 0 else
                                  '', foreground='blue')
                    lab.bind('<Button-1>', app.callback(channel['url']))
                    lab.grid(row=i+1, column=j, ipadx=6, sticky='nsew')
                
                if key == 'status':
                    if channel[key] == True:
                        lab.configure(text='🔴LIVE', style='LiveLabel.TLabel')
                    else:
                        lab.configure(text='OFFLINE')

                    lab.grid(row=i+1, column=j, sticky='nsew')

                if key == 'id':
                    lab.configure(text='✖', cursor='hand2', anchor=CENTER, padding=(10, 0))
                    lab.bind('<Button-1>', lambda event, h=channel['handle']: self.on_delete_btn(h))
                    lab.bind('<Enter>', lambda event, btn=lab: self.on_enter(btn))
                    lab.bind('<Leave>', lambda event, btn=lab: self.on_leave(btn))
                    lab.grid(row=i+1, column=j, sticky='nsew')
                    
                if key == 'title' or key == 'handle':
                    lab.configure(text=channel[key])
                    lab.grid(row=i+1, column=j, sticky='nsew')

                self.displayed_channel_labels.append(lab)

    # on hover (for button)
    def on_enter(e, btn: Button):
        btn['foreground'] = 'red'

    # on unhover (for button)
    def on_leave(e, btn: Button):
        btn['foreground'] = 'black'

    def on_delete_btn(self, handle: str):
        app.untrack_channel(handle)
        for child in self.displayed_channel_labels:
            child.destroy()

        self.propagate_channels()

    def display_error(self, message: str):
        self.error_label.config(text=message)
        threading.Timer(4, self.clean_error).start()

    def clean_error(self):
        self.error_label.config(text='')

    def upd_setting_1_state(self):
        state = self.setting_1_state.get()
        app.setting_1_state = state == True

        if not state == True:
            self.setting_2.config(state='disabled')
            self.setting_2_state.set(0)
            self.upd_setting_2_state()
        else:
            self.setting_2.config(state='normal')

    def upd_setting_2_state(self):
        state = self.setting_2_state.get()
        app.setting_2_state = state == True

    # minimize gui into system tray
    def withdraw_window(self):
        menu = Menu(MenuItem('Show GUI', self.show_window, default=True), MenuItem('Close app', self.kill_app))
        icon = Icon('Channel Tracker', icon=Image.open(APP_ICON_PATH), menu=menu)
        events.gui_hidden.notify()
        window.withdraw()
        icon.run()

    def show_window(self, icon, item):
        icon.stop()
        window.deiconify()
        events.gui_shown.notify()

    def kill_app(self, icon, item):
        icon.stop()
        window.destroy()

if __name__ == '__main__':
    window = Tk()
    app.load_from_db()

    a = StreamTrackerGUI(window)
    a.propagate_channels(initial=True)

    app.run_bg_threads()

    window.protocol('WM_DELETE_WINDOW', a.withdraw_window)
    window.mainloop()