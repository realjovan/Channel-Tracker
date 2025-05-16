from tkinter import *
from tkinter import ttk
import app, webbrowser, os, time
import tkinter.font as tkFont
import sv_ttk # third-party ttk theme

class StreamTrackerGUI():
    def __init__(self, window):
        self.window = window
        self.displayed_channel_labels = []
        ''' 
        FILE PATHS 
        '''
        self.app_icon_path = r'static/app_icon.png'

        '''
        MISC VARIABLES
        '''
        # Color:
        self.clr_main = '#f0f0f0'
        self.clr_secondary = '#e5e5e5'
        self.clr_accent = '#2e7fe8'
        self.clr_secondary_accent = '#ff5151'

        # Fonts:
        self.fnt_main = 'Cascadia Code'
        self.fnt_size_main = 8

        # Icons:
        self.icn_app = PhotoImage(file=self.app_icon_path)

        # Settings states:
        self.setting_1_state = IntVar()

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
        self.search_youtuber_frame = Frame(window, bg=self.clr_secondary, height=150, padx=1)
        self.search_youtuber_frame.rowconfigure((0, 1, 2), weight=1)
        self.search_youtuber_frame.columnconfigure(0, weight=1)
        self.search_youtuber_frame.columnconfigure(1, weight=0)
        self.search_youtuber_frame.columnconfigure(2, weight=1)
        self.search_youtuber_frame.grid_propagate(0)

        self.channels_list_frame = Frame(window, pady=8)
        self.channels_list_frame.columnconfigure((0, 1), weight=0)
        self.channels_list_frame.columnconfigure((2, 3), weight=1)
        self.channels_list_frame.columnconfigure(4, weight=0)

        self.optionals_settings = Frame(window,bg=self.clr_secondary)
        self.optionals_settings.columnconfigure((0, 1), weight=1)

        # pack frames
        self.search_youtuber_frame.pack(fill='x')
        self.channels_list_frame.pack(fill='x')
        self.optionals_settings.pack(fill='x', side='bottom')
        '''
        WIDGETS
        '''
        self.channel_handle_label = Label(self.search_youtuber_frame, text='Channel Handle:', bg=self.clr_secondary)
        self.channel_handle_entry = Entry(self.search_youtuber_frame)
        self.channel_handle_submit = Button(self.search_youtuber_frame, text='Track', command=self.search_for_channel)

        self.channel_handle_label.configure(font=(self.fnt_main, self.fnt_size_main))
        self.channel_handle_submit.configure(font=(self.fnt_main, self.fnt_size_main))
        self.channel_handle_entry.configure(font=('Arial', self.fnt_size_main))

        self.header_title_label = Label(self.channels_list_frame, text='Channel')
        self.header_handle_label = Label(self.channels_list_frame, text='Handle')
        self.header_status_label = Label(self.channels_list_frame, text='Status')
        self.header_remove_label = Label(self.channels_list_frame, text='Remove')

        self.header_title_label.configure(font=(self.fnt_main, self.fnt_size_main))
        self.header_handle_label.configure(font=(self.fnt_main, self.fnt_size_main))
        self.header_status_label.configure(font=(self.fnt_main, self.fnt_size_main))
        self.header_remove_label.configure(font=(self.fnt_main, self.fnt_size_main), padx=10)

        self.setting_1 = Checkbutton(self.optionals_settings, bg=self.clr_secondary, text='Enable desktop notification',
                                     variable=self.setting_1_state, command=self.upd_setting_1_state, offvalue=0, onvalue=1)
        self.setting_1.select()
        self.setting_1.configure(activebackground=self.clr_secondary)

        # place widgets
        self.channel_handle_label.grid(row=1, column=0, sticky=E)
        self.channel_handle_entry.grid(row=1, column=1, padx=7, pady=7, sticky=EW)
        self.channel_handle_submit.grid(row=1, column=2, sticky=W)

        self.header_title_label.grid(row=0, column=1, sticky=EW)
        self.header_handle_label.grid(row=0, column=2, sticky=EW)
        self.header_status_label.grid(row=0, column=3, sticky=EW)
        self.header_remove_label.grid(row=0, column=4, sticky=EW)

        self.setting_1.grid(row=0, column=0, ipady=2, sticky=EW)


    def search_for_channel(self):
        handle = self.channel_handle_entry.get()
        try:
            if handle[0] != '@':
                handle = '@' + handle
            
        except IndexError:
            print('No entry received')

        data = app.search_youtube_channel(handle)
        self.channel_handle_entry.delete(0, END)
        self.propagate_channels()

    def propagate_channels(self):
        for i, channel in enumerate(app.channels):
            for j, key in enumerate(channel):
                lab = Label(self.channels_list_frame, text='', pady=4, bg=self.clr_secondary if i % 2 == 0 else self.clr_main, 
                            font=(self.fnt_main, self.fnt_size_main))
                
                if j == 0:
                    lab.configure(text='🔗', fg='blue', width=2, cursor='hand2', padx=10)
                    lab.bind('<Button-1>', app.callback(channel['url']))
                    lab.grid(row=i+1, column=j, stick=EW)
                
                if key == 'status':
                    if channel[key] == True:
                        lab.configure(text='🔴LIVE', fg='red')
                    else:
                        lab.configure(text='OFFLINE')

                    lab.grid(row=i+1, column=j, sticky=EW)

                if key == 'icon':
                    lab.configure(text='✖', pady=4, cursor='hand2')
                    lab.bind('<Button-1>', lambda event, h=channel['handle']: self.on_delete_btn(h))
                    lab.bind('<Enter>', lambda event, btn=lab: self.on_enter(btn))
                    lab.bind('<Leave>', lambda event, btn=lab: self.on_leave(btn))
                    lab.grid(row=i+1, column=j, sticky=EW)
                    
                if key == 'title' or key == 'handle':
                    lab.configure(text=channel[key])
                    lab.grid(row=i+1, column=j, sticky=EW)

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

    def upd_setting_1_state(self):
        app.setting_1_state = self.setting_1_state.get() == True

if __name__ == '__main__':
    window = Tk()
    app.load_from_db()
    a = StreamTrackerGUI(window)
    a.propagate_channels()
    window.mainloop()