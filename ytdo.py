#!/usr/bin/env python
# coding: utf-8

# In[236]:


import os
import tkinter as tk
from tkinter import filedialog, messagebox,ttk
import yt_dlp
import re
import glob
import threading


# In[184]:


# 常見語言代碼對照表
lang_map = {
    'en': '英文',
    'ja': '日文',
    'zh-Hant': '繁體中文',
    'zh-Hans': '簡體中文',
    'fr': '法文',
    'de': '德文',
    'es': '西班牙文',
    'ko': '韓文',
    'ru': '俄文',
    'pt': '葡萄牙文',
    'it': '義大利文',
    'vi': '越南文',
    'th': '泰文',
    'hi': '印地文',
    'id': '印尼文',
    'tr': '土耳其文',
    'pl': '波蘭文',
    'ar': '阿拉伯文',
    'bn': '孟加拉文',
}


# In[253]:


display_to_code = {}
def is_playlist(url):
    return 'list=' in url   
    
def browse_folder():
    folder = filedialog.askdirectory()
    if folder:
        folder_path.set(folder)
        
def clear_batch_file():
    batch_file_path.set('')  # 清空變數
    url_entry.config(state="normal")
    
def browse_batch_file():
    messagebox.showinfo(
            "注意",
            "※ 使用批次檔(.txt)下載請注意以下事項 \n\n"
            "- 文字檔中，每一行請填寫一個網址\n"
            "- 批次檔無法下載字幕及移除業配片段\n"
            "- 若批次檔中包含播放清單網址,則會將清單內所有影片下載"
    )
    file_path = filedialog.askopenfilename(filetypes=[("Text files", "*.txt")])
    if file_path:
        batch_file_path.set(file_path)
        
        # 將網址欄變成唯讀狀態並清空內容
        url_entry.delete(0, tk.END)
        url_entry.config(state="disabled")
    
def on_subtitle_check():
    if batch_file_path.get():  # 批次檔已選擇
        messagebox.showinfo("注意", "您已選擇批次檔，無法使用下載字幕功能。")
        subtitle_var.set(False)  # 自動取消勾選

def on_sponsor_check():
    if batch_file_path.get():  # 批次檔已選擇
        messagebox.showinfo("注意", "您已選擇批次檔，無法使用移除業配片段功能。")
        sponsor_var.set(False)  # 自動取消勾選

def check_subtitles():
    if batch_file_path.get():  # 批次檔已選擇
        messagebox.showinfo("注意", "您已選擇批次檔，無法使用檢查字幕功能。")
        return
    url = url_entry.get().strip()
    if not url:
        messagebox.showwarning("警告", "請先輸入影片網址！")
        return
    
    try:
        with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
            info = ydl.extract_info(url, download=False)

        subs = info.get('subtitles', {})
        all_subs = set(subs.keys())

        if not all_subs:
            messagebox.showinfo("訊息", "影片沒有字幕。")
            subtitle_lang_combo['values'] = []
            subtitle_lang_combo.set('')
            return

    
        display_list = []
        
        
        for code in sorted(all_subs):
            name = lang_map.get(code)
            if not name:
                # 如果沒找到，就用code前兩碼
                prefix = code[:2]
                name = lang_map.get(prefix, "未知語言")
            display = f"{name} ({code})"
            display_list.append(display)
            display_to_code[display] = code

        subtitle_lang_combo['values'] = display_list
        subtitle_lang_combo.set(display_list[0])

        
        messagebox.showinfo("訊息", f"找到字幕語言：{', '.join(display_list)}")

    except Exception as e:
        messagebox.showerror("錯誤", f"無法取得字幕資訊：{e}")


def safe_update_progress(percent, speed, eta, title=None):
    def update():
        if title:
            video_title_label.config(text=f"正在下載：{title}")
        progress_var.set(float(percent.replace('%', '')))
        progress_label.config(text=f"進度：{percent}，速度：{speed}，剩餘時間：{eta}")
    window.after(0, update)

    
def progress_hook(d):
    if d['status'] == 'downloading' and 'info_dict' in d:
        title = d['info_dict'].get('title')
        percent = d.get('_percent_str', '0.0%').strip()
        speed = d.get('_speed_str', '0 KB/s')
        eta_raw = d.get('_eta_str', '')
        eta = re.sub(r"\s*\(.*?\)", "", eta_raw).strip()
        safe_update_progress(percent, speed, eta, title)

        # 更新進度條與文字
        progress_var.set(float(percent.replace('%', '')))
        progress_label.config(text=f"進度：{percent}，速度：{speed}，剩餘時間：{eta}")
        window.update_idletasks()

    elif d['status'] == 'finished':
        progress_label.config(text="下載完成")


def start_download_thread():
    start_button.config(state="disabled")  # 停用按鈕
    threading.Thread(target=start_download).start()
    
def start_download():
    url = url_entry.get().strip()
    save_path = folder_path.get().strip()
    batch_path = batch_file_path.get().strip()
    download_type = type_var.get()
    only_audio = audio_var.get()
    with_subtitle = subtitle_var.get()
    remove_ads = sponsor_var.get()
    subtitle_lang_display = subtitle_lang_combo.get()
    subtitle_lang = display_to_code.get(subtitle_lang_display, '')
    
    
    if with_subtitle:
        messagebox.showinfo(
            "注意",
            "※ 您已選擇「下載字幕」功能，建議使用支援內嵌字幕的播放器播放影片，例如：\n\n"
            "- VLC 媒體播放器（推薦）\n"
            "- MPV 播放器\n"
            "- PotPlayer（支援部分格式）\n"
            "- IINA（macOS）\n\n"
            "部分播放器（如 Windows 內建影片播放器）無法顯示內嵌字幕。"
        )
    if not save_path:
        messagebox.showwarning("注意", "請選擇下載儲存的資料夾。")
        window.after(0, lambda: start_button.config(state="normal"))
        return

    if not url and not batch_path:
        messagebox.showwarning("注意", "請輸入影片 / 播放清單網址，或選擇批次檔案。")
        window.after(0, lambda: start_button.config(state="normal"))
        return
        
    # 播放清單類型檢查
    if download_type == 'single' and is_playlist(url):#最上方宣告的is_playlist
        messagebox.showwarning("警告", "偵測到這是播放清單網址，請改選『整個播放清單』後再執行下載。")
        window.after(0, lambda: start_button.config(state="normal"))
        return

    if download_type == 'playlist' and not is_playlist(url):
        messagebox.showwarning("警告", "偵測到非播放清單網址或是您未輸入網址\n"
                               "若您輸入的是單一影片網址,或使用批次檔,請選擇『單一影片/批次檔』")
        window.after(0, lambda: start_button.config(state="normal"))
        return
        
    ydl_opts = {
        'outtmpl': os.path.join(save_path, '%(playlist_title)s/%(title)s.%(ext)s') if download_type == 'playlist' else os.path.join(save_path, '%(title)s.%(ext)s'),
        'quiet': False,
        'noplaylist': download_type == 'single',
        'postprocessors': [],
        'progress_hooks': [progress_hook],

    }

    if only_audio:
        ydl_opts['format'] = 'bestaudio/best'
        ydl_opts['postprocessors'].append({
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        })
    else:
        ydl_opts['format'] = 'bestvideo+bestaudio/best'

    if with_subtitle and subtitle_lang:
        ydl_opts.update({
            'writesubtitles': True,
            'writeautomaticsub': False,
            'subtitleslangs': [subtitle_lang],
            'embedsubtitles': True,  # 這樣會內嵌字幕軌到影片
            'merge_output_format': 'mkv',
            'postprocessors': [
                {'key': 'FFmpegEmbedSubtitle'}
            ],
        })

    if remove_ads:
        messagebox.showinfo("注意",
                           "您已選擇「移除業配片段」但若該影片並未標記相關片段,則此功能不會生效")
        ydl_opts['sponsorblock_remove'] = ['sponsor', 'intro', 'outro', 'interaction', 'selfpromo']
          
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            if batch_path:
                with open(batch_path, 'r', encoding='utf-8') as f:
                    urls = [line.strip() for line in f if line.strip()]
                ydl.download(urls)
            else:
                ydl.download([url])
        messagebox.showinfo("完成", "下載完成！")
    except Exception as e:
        messagebox.showerror("錯誤", f"下載失敗：{e}")
    finally:
        if batch_path:
            window.after(0, lambda: batch_file_path.set(''))
            window.after(0, lambda: url_entry.config(state="normal"))
            window.after(0, lambda: url_entry.delete(0, tk.END))
    # 無論成功或失敗，都在最後重新啟用按鈕
    window.after(0, lambda: start_button.config(state="normal"))


# In[254]:


# 建立視窗
window = tk.Tk()
window.title("YouTube 下載器 (yt-dlp GUI)")
window.geometry("600x600")

# 資料夾選擇
folder_path = tk.StringVar()
tk.Label(window, text="儲存位置：").pack(anchor='w', padx=10, pady=5)
tk.Entry(window, textvariable=folder_path, width=70).pack(padx=10, anchor='w')
tk.Button(window, text="選擇資料夾", command=browse_folder).pack(padx=10, anchor='w')

# URL 或 批次檔
url_entry = tk.Entry(window, width=70)
tk.Label(window, text="影片 / 播放清單網址：").pack(anchor='w', padx=10, pady=5)
url_entry.pack(padx=10, anchor='w')

batch_file_path = tk.StringVar()
tk.Button(window, text="或選擇批次檔 (.txt)", command=browse_batch_file).pack(padx=10, pady=5, anchor='w')

batch_file_label = tk.Label(window, textvariable=batch_file_path)
batch_file_label.pack(anchor='w', padx=10)

tk.Button(window, text="清除批次檔", command=clear_batch_file).pack(anchor='w', padx=10)



# 選項設定
type_var = tk.StringVar(value='single')
tk.Radiobutton(window, text="單一影片/批次檔", variable=type_var, value='single').pack(anchor='w', padx=10)
tk.Radiobutton(window, text="整個播放清單", variable=type_var, value='playlist').pack(anchor='w', padx=10)

audio_var = tk.BooleanVar()
tk.Checkbutton(window, text="只下載音訊 (MP3)", variable=audio_var).pack(anchor='w', padx=10)

# 新增「檢查字幕」按鈕及字幕語系下拉選單
check_sub_btn = tk.Button(window, text="檢查字幕", command=check_subtitles)
check_sub_btn.pack(anchor='w', padx=10)

subtitle_lang_combo = ttk.Combobox(window, state="readonly")
subtitle_lang_combo.pack(anchor='w', padx=10, pady=(0,10))
subtitle_var = tk.BooleanVar()
tk.Checkbutton(window, text="下載字幕", variable=subtitle_var, command=on_subtitle_check).pack(anchor='w', padx=10)

sponsor_var = tk.BooleanVar()
tk.Checkbutton(window, text="移除業配片段（SponsorBlock）", variable=sponsor_var, command=on_sponsor_check).pack(anchor='w', padx=10)

# 顯示影片名稱
video_title_label = tk.Label(window, text="", fg="blue")
video_title_label.pack(anchor='w', padx=10)

# 下載進度條與文字
progress_var = tk.DoubleVar()
progress_bar = ttk.Progressbar(window, length=400, variable=progress_var, maximum=100)
progress_bar.pack(anchor='w', padx=10, pady=(0, 5))

progress_label = tk.Label(window, text="")
progress_label.pack(anchor='w', padx=10)

# 開始按鈕
start_button = tk.Button(window, text="開始下載", command=start_download_thread, bg='green', fg='white')
start_button.pack(pady=20)

window.mainloop()


# In[ ]:




