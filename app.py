# ----- Cell -----
# Music Downloader
# Author: AC Roy

import customtkinter as ctk
from PIL import Image, ImageTk
import yt_dlp
import os
import re
import requests
from io import BytesIO
from urllib.parse import urlparse, parse_qs
import threading
import subprocess
import winsound
from tkinter import filedialog

# ---------- PATH ----------
BASE_FOLDER = r"E:\Song\Files"
DOWNLOAD_FOLDER = os.path.join(BASE_FOLDER, "Downloads")
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

# ---------- STYLE ----------
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

# ---------- HELPERS ----------
def clean_title(title):
    title = re.sub(r'\(.*?\)|\[.*?\]|\{.*?\}', '', title)
    junk = ["official video","official audio","lyrics","audio","video","hd","4k"]
    title = re.sub(r'|'.join(junk), '', title, flags=re.IGNORECASE)
    title = re.sub(r'[\\/*?:"<>|]', '', title)
    return re.sub(r'\s+', ' ', title).strip()

def split_artist_song(title):
    if " - " in title:
        return title.split(" - ", 1)
    return "Unknown Artist", title

def extract_video_id(url):
    parsed = urlparse(url)
    if "youtube.com" in parsed.netloc:
        return parse_qs(parsed.query).get("v", [None])[0]
    if "youtu.be" in parsed.netloc:
        return parsed.path.strip("/")
    return None

def fetch_thumbnail(url):
    try:
        with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
            info = ydl.extract_info(url, download=False)
        thumb_url = info.get('thumbnail')
        if thumb_url:
            response = requests.get(thumb_url)
            img = Image.open(BytesIO(response.content))
            img = img.resize((550, 200))
            return ImageTk.PhotoImage(img)
    except:
        return None

def play_notification():
    try:
        winsound.MessageBeep()
    except:
        pass

# ---------- TOOLTIP ----------
class ToolTip:
    def __init__(self, widget):
        self.widget = widget
        self.tipwindow = None

    def show(self, text):
        if self.tipwindow or not text:
            return
        x = self.widget.winfo_rootx() + 20
        y = self.widget.winfo_rooty() + 25

        self.tipwindow = tw = ctk.CTkToplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.geometry(f"+{x}+{y}")

        label = ctk.CTkLabel(tw, text=text, fg_color="#222", corner_radius=6)
        label.pack(ipadx=6, ipady=2)

    def hide(self):
        if self.tipwindow:
            self.tipwindow.destroy()
            self.tipwindow = None

# ---------- FOLDER FUNCTIONS ----------
def choose_folder():
    global DOWNLOAD_FOLDER
    folder = filedialog.askdirectory()
    if folder:
        DOWNLOAD_FOLDER = folder
        folder_label.configure(text=f"📁 {os.path.basename(folder)}")

def open_selected_folder(event=None):
    subprocess.Popen(f'explorer "{DOWNLOAD_FOLDER}"')

# ---------- UI ----------
root = ctk.CTk()
root.geometry("600x520")
root.title("🎵 Easy Music Downloader")
root.resizable(False, False)

# Header
header_label = ctk.CTkLabel(root, text="🎵 Download and Enjoy!",
                            font=("Segoe UI", 22, "bold"))
header_label.pack(pady=5)

# Entry
entry = ctk.CTkEntry(root, width=500, height=35, corner_radius=20,
                     placeholder_text="Paste YouTube link here...")
entry.pack(pady=3)

# ---------- FOLDER UI (CENTERED) ----------
folder_frame = ctk.CTkFrame(root, fg_color="transparent")
folder_frame.pack(pady=8, fill="x")  # fill x to take full width

# Inner frame to hold buttons and label centered
inner_frame = ctk.CTkFrame(folder_frame, fg_color="transparent")
inner_frame.pack()

choose_btn = ctk.CTkButton(inner_frame, text="📂 Choose",
                           width=100, height=28,
                           command=choose_folder)
choose_btn.pack(side="left", padx=5)

folder_label = ctk.CTkLabel(
    inner_frame,
    text=f"📁 {os.path.basename(DOWNLOAD_FOLDER)}",
    text_color="#1f6aa5",
    cursor="hand2",
    width=300,
    anchor="center"  # center the text inside label
)
folder_label.pack(side="left", padx=5)

# Bind click to open folder
folder_label.bind("<Button-1>", open_selected_folder)

# Hover color effect
folder_label.bind("<Enter>", lambda e: folder_label.configure(text_color="#4da6ff"))
folder_label.bind("<Leave>", lambda e: folder_label.configure(text_color="#1f6aa5"))

# Tooltip
tooltip = ToolTip(folder_label)
folder_label.bind("<Enter>", lambda e: tooltip.show(DOWNLOAD_FOLDER))
folder_label.bind("<Leave>", lambda e: tooltip.hide())

# ---------- MAIN FRAME ----------
main_frame = ctk.CTkFrame(root, corner_radius=15)
main_frame.pack(padx=10, pady=5, fill="both", expand=True)

# Thumbnail
thumbnail_label = ctk.CTkLabel(main_frame, text="", width=550, height=200)
thumbnail_label.pack()

# Song info
song_title_label = ctk.CTkLabel(main_frame, text="Song Title", font=("Segoe UI", 16, "bold"))
song_title_label.pack(pady=(0,0))

artist_label = ctk.CTkLabel(main_frame, text="Artist", text_color="#AAAAAA")
artist_label.pack()

# Status
status_label = ctk.CTkLabel(main_frame, text="Idle", text_color="#00FF00",
                            font=("Segoe UI", 16, "bold"))
status_label.pack(pady=5)

# Progress
progress_bar = ctk.CTkProgressBar(main_frame, width=480)
progress_bar.pack(pady=5)

# Download button
download_btn = ctk.CTkButton(main_frame, text="⬇ Download",
                             width=200, height=32,
                             fg_color="#1DB954", hover_color="#1ed760")
download_btn.pack(pady=10)

# ---------- DOWNLOAD ----------
def download_song_thread(url):
    vid = extract_video_id(url)
    if not vid:
        status_label.after(0, lambda: status_label.configure(text="Invalid link"))
        return

    url = f"https://www.youtube.com/watch?v={vid}"

    try:
        status_label.after(0, lambda: status_label.configure(text="Fetching info..."))

        with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
            info = ydl.extract_info(url, download=False)

        title = clean_title(info.get("title","Unknown"))
        artist, song = split_artist_song(title)
        filename = f"{artist} - {song}"
        final_path = os.path.join(DOWNLOAD_FOLDER, filename+".mp3")

        if os.path.exists(final_path):
            status_label.after(0, lambda: status_label.configure(text="Already exists"))
            return

        thumb = fetch_thumbnail(url)
        if thumb:
            thumbnail_label.after(0, lambda: thumbnail_label.configure(image=thumb))
            thumbnail_label.image = thumb

        song_title_label.after(0, lambda: song_title_label.configure(text=song))
        artist_label.after(0, lambda: artist_label.configure(text=artist))

        ydl_opts = {
            'format':'bestaudio/best',
            'outtmpl': os.path.join(DOWNLOAD_FOLDER, filename+'.%(ext)s'),
            'postprocessors':[{
                'key':'FFmpegExtractAudio',
                'preferredcodec':'mp3',
            }],
            'quiet': True,
            'ffmpeg_location': r"E:\Song\Files\ffmpeg\bin"  # Point to your ffmpeg folder
        }

        def progress(d):
            if d['status']=='downloading':
                percent = float(d.get('_percent_str','0%').replace('%',''))
                progress_bar.set(percent/100)
                status_label.after(0, lambda: status_label.configure(
                    text=f"Downloading... {percent:.1f}%"))

        ydl_opts['progress_hooks'] = [progress]

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        status_label.after(0, lambda: status_label.configure(text="Saved Successfully"))
        progress_bar.set(1.0)
        play_notification()
        entry.after(0, lambda: entry.delete(0, 'end'))

    except Exception as e:
        status_label.after(0, lambda: status_label.configure(text=f"Error: {str(e)}"))
        progress_bar.set(0)

def download_song():
    url = entry.get().strip()
    if not url:
        status_label.configure(text="Paste a YouTube link")
        return
    threading.Thread(target=download_song_thread, args=(url,), daemon=True).start()

download_btn.configure(command=download_song)

# Enter key
entry.bind("<Return>", lambda event: download_song())

root.mainloop()

# ----- Cell -----


