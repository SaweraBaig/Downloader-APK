import os
import threading
import yt_dlp
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.image import AsyncImage
from kivy.uix.progressbar import ProgressBar
from kivy.clock import mainthread
from kivy.graphics import Color, Rectangle
from kivy.utils import platform, get_color_from_hex
from kivy.core.window import Window

# --- EXACT COLOR PALETTE FROM YOUR TKINTER CODE ---
BG_COLOR = get_color_from_hex("#F0F4F8")
HEADER_BG = get_color_from_hex("#2C3E50")
HEADER_FG = get_color_from_hex("#FFFFFF")
ACCENT_COLOR = get_color_from_hex("#3498DB")
DANGER_COLOR = get_color_from_hex("#E74C3C")
TEXT_COLOR = get_color_from_hex("#333333")

Window.clearcolor = BG_COLOR

class ColoredLabel(Label):
    def __init__(self, bg_color, **kwargs):
        super().__init__(**kwargs)
        self.bg_color = bg_color
        self.bind(pos=self.update_rect, size=self.update_rect)
        with self.canvas.before:
            Color(*self.bg_color)
            self.rect = Rectangle(pos=self.pos, size=self.size)

    def update_rect(self, *args):
        self.rect.pos = self.pos
        self.rect.size = self.size

class MrBaigDownloaderApp(App):
    def build(self):
        self.request_android_permissions()
        
        # Download path for Android
        if platform == 'android':
            from android.storage import primary_external_storage_path
            # Points to Phone's internal Downloads folder
            self.download_path = os.path.join(primary_external_storage_path(), 'Download')
        else:
            self.download_path = os.path.join(os.path.expanduser('~'), 'Downloads')

        self.root_layout = BoxLayout(orientation='vertical', padding=10, spacing=10)

        # 1. HEADER
        header = ColoredLabel(bg_color=HEADER_BG, text="Mr.Baig Downloader", color=HEADER_FG, font_size='22sp', bold=True, size_hint_y=None, height=60)
        dev_label = Label(text="Developed By Zawar Baig", color=get_color_from_hex("#7F8C8D"), font_size='12sp', italic=True, bold=True, size_hint_y=None, height=30, halign='left')
        dev_label.bind(size=dev_label.setter('text_size'))
        
        self.root_layout.add_widget(header)
        self.root_layout.add_widget(dev_label)

        # 2. URL INPUT ROW
        url_row = BoxLayout(orientation='horizontal', size_hint_y=None, height=40, spacing=10)
        url_row.add_widget(Label(text="Video URL:", color=TEXT_COLOR, bold=True, size_hint_x=0.2))
        self.url_var = TextInput(multiline=False, size_hint_x=0.5, background_color=(1,1,1,1))
        url_row.add_widget(self.url_var)
        
        fetch_btn = Button(text="Download", background_normal='', background_color=ACCENT_COLOR, color=HEADER_FG, bold=True, size_hint_x=0.15)
        fetch_btn.bind(on_press=self.start_fetch_thread)
        url_row.add_widget(fetch_btn)
        
        clear_btn = Button(text="Clear", background_normal='', background_color=DANGER_COLOR, color=HEADER_FG, bold=True, size_hint_x=0.15)
        clear_btn.bind(on_press=self.clear_all)
        url_row.add_widget(clear_btn)
        
        self.root_layout.add_widget(url_row)

        # 3. SAVE PATH ROW
        path_row = BoxLayout(orientation='horizontal', size_hint_y=None, height=40, spacing=10)
        path_row.add_widget(Label(text="Save To:", color=TEXT_COLOR, bold=True, size_hint_x=0.2))
        self.path_var = TextInput(text=self.download_path, readonly=True, size_hint_x=0.65, background_color=(0.9,0.9,0.9,1))
        path_row.add_widget(self.path_var)
        
        browse_btn = Button(text="Browse", background_normal='', background_color=ACCENT_COLOR, color=HEADER_FG, bold=True, size_hint_x=0.15)
        path_row.add_widget(browse_btn)
        
        self.root_layout.add_widget(path_row)

        # 4. THUMBNAIL AND TITLE ROW
        info_row = BoxLayout(orientation='horizontal', size_hint_y=None, height=100, spacing=10)
        self.thumb_label = AsyncImage(size_hint_x=0.3)
        self.title_label = Label(text="", color=TEXT_COLOR, bold=True, size_hint_x=0.7, halign='left', valign='top')
        self.title_label.bind(size=self.title_label.setter('text_size'))
        info_row.add_widget(self.thumb_label)
        info_row.add_widget(self.title_label)
        
        self.root_layout.add_widget(info_row)

        # 5. FORMATS TREEVIEW
        self.h_scroll = ScrollView(size_hint=(1, 1), do_scroll_x=True, do_scroll_y=True)
        self.treeview = GridLayout(cols=6, spacing=1, size_hint_y=None, size_hint_x=None, width=1200)
        self.treeview.bind(minimum_height=self.treeview.setter('height'))
        
        headers = ["ID", "Extension", "Resolution", "Quality/Note", "Size", "Action"]
        widths = [0.1, 0.1, 0.15, 0.35, 0.1, 0.2]
        for idx, h in enumerate(headers):
            lbl = ColoredLabel(bg_color=get_color_from_hex("#BDC3C7"), text=h, color=get_color_from_hex("#2C3E50"), bold=True, size_hint_y=None, height=40, size_hint_x=widths[idx])
            self.treeview.add_widget(lbl)

        self.h_scroll.add_widget(self.treeview)
        self.root_layout.add_widget(self.h_scroll)

        # 6. STATUS & PROGRESS
        self.status_var = Label(text="Ready", color=get_color_from_hex("#7F8C8D"), italic=True, size_hint_y=None, height=30, halign='left')
        self.status_var.bind(size=self.status_var.setter('text_size'))
        self.root_layout.add_widget(self.status_var)

        self.progress_var = ProgressBar(max=100, size_hint_y=None, height=20)
        self.root_layout.add_widget(self.progress_var)

        return self.root_layout

    def request_android_permissions(self):
        if platform == 'android':
            from android.permissions import request_permissions, Permission
            request_permissions([Permission.INTERNET, Permission.WRITE_EXTERNAL_STORAGE, Permission.READ_EXTERNAL_STORAGE])

    def clear_all(self, instance):
        self.url_var.text = ""
        self.title_label.text = ""
        self.thumb_label.source = ""
        self.clear_treeview()
        self.status_var.text = "Ready"
        self.progress_var.value = 0

    def clear_treeview(self):
        widgets_to_remove = self.treeview.children[:-6] 
        for w in widgets_to_remove:
            self.treeview.remove_widget(w)

    def format_size(self, bytes_size):
        if not bytes_size: return "Unknown"
        mb = bytes_size / (1024 * 1024)
        return f"{mb:.2f} MB"

    def start_fetch_thread(self, instance):
        url = self.url_var.text.strip()
        if not url:
            self.status_var.text = "Error: Please enter a URL"
            return
        
        self.status_var.text = "Fetching video information... Please wait."
        self.clear_treeview()
        self.title_label.text = ""
        threading.Thread(target=self.fetch_formats, args=(url,), daemon=True).start()

    def fetch_formats(self, url):
        ydl_opts = {'quiet': True, 'no_warnings': True, 'nocheckcertificate': True}
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                
                thumb_url = info.get('thumbnail', '')
                title = info.get('title', 'Unknown Title')
                self.update_info_ui(thumb_url, title)

                formats = info.get('formats', [])
                
                formatted_list = [("best", "mp4/mkv", "Best Quality", "Best Pre-merged Audio/Video", "Auto", "📥 Click to Download")]

                for f in formats:
                    f_id = f.get('format_id', 'N/A')
                    ext = f.get('ext', 'N/A')
                    res = f.get('resolution', f.get('width', 'N/A'))
                    if res == 'audio only' or f.get('vcodec') == 'none':
                        res = "Audio Only"
                    elif f.get('height'):
                        res = f"{f.get('width', '?')}x{f.get('height', '?')}"
                    
                    note = f.get('format_note', '')
                    vcodec = f.get('vcodec', '')
                    acodec = f.get('acodec', '')
                    details = f"{note} (V: {vcodec[:4] if vcodec != 'none' else 'none'}, A: {acodec[:4] if acodec != 'none' else 'none'})"
                    filesize = f.get('filesize') or f.get('filesize_approx')
                    size_str = self.format_size(filesize)
                    
                    formatted_list.append((f_id, ext, res, details, size_str, "📥 Click to Download"))

                self.update_treeview(formatted_list)
        except Exception as e:
            self.update_status(f"Failed to fetch formats: {str(e)[:50]}")

    @mainthread
    def update_info_ui(self, thumb_url, title):
        if thumb_url:
            self.thumb_label.source = thumb_url
        self.title_label.text = title

    @mainthread
    def update_treeview(self, formats):
        for index, item in enumerate(formats):
            bg_color = get_color_from_hex("#FFFFFF") if index % 2 == 0 else get_color_from_hex("#F9F9F9")
            
            for col_idx, text in enumerate(item):
                if col_idx == 5: 
                    btn = Button(text=text, background_normal='', background_color=bg_color, color=ACCENT_COLOR, bold=True, size_hint_y=None, height=40)
                    btn.bind(on_press=lambda instance, fid=item[0]: self.start_download(fid))
                    self.treeview.add_widget(btn)
                else:
                    lbl = ColoredLabel(bg_color=bg_color, text=str(text), color=TEXT_COLOR, size_hint_y=None, height=40)
                    self.treeview.add_widget(lbl)
                    
        self.status_var.text = "Formats loaded. Click '📥 Click to Download' in any row to start."

    def start_download(self, format_id):
        url = self.url_var.text.strip()
        self.progress_var.value = 0
        self.status_var.text = "Starting download..."
        threading.Thread(target=self.download_video, args=(url, format_id), daemon=True).start()

    def download_video(self, url, format_id):
        def progress_hook(d):
            if d['status'] == 'downloading':
                percent_str = d.get('_percent_str', '0.0%').strip('% \x1b[0;39m')
                try:
                    self.update_progress(float(percent_str))
                except ValueError:
                    pass
            elif d['status'] == 'finished':
                self.update_status("Finalizing file... Please wait.")
                self.update_progress(100)

        # Force Android to use single pre-merged stream to avoid FFmpeg crashing
        fmt_str = 'best' if str(format_id) == 'best' else str(format_id)

        ydl_opts = {
            'format': fmt_str,
            'outtmpl': os.path.join(self.download_path, '%(title)s.%(ext)s'),
            'progress_hooks': [progress_hook],
            'quiet': True,
            'nocheckcertificate': True # Prevents SSL verification errors on Android
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            self.update_status(f"Download Complete! Saved to Downloads folder.")
        except Exception as e:
            self.update_status(f"Download Failed: {str(e)[:50]}")

    @mainthread
    def update_progress(self, value):
        self.progress_var.value = value
        if value < 100:
            self.status_var.text = f"Downloading... {value}%"

    @mainthread
    def update_status(self, text):
        self.status_var.text = text

if __name__ == "__main__":
    MrBaigDownloaderApp().run()
