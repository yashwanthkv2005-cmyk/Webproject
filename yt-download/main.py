"""
YouTube Downloader Application
Uses yt-dlp (most reliable, actively maintained fork of youtube-dl)
Install dependencies: pip install yt-dlp
Optional GUI: pip install tkinter (usually bundled with Python)
"""

import os
import sys
import threading
import subprocess

# ── Try importing yt-dlp ──────────────────────────────────────────────────────
try:
    import yt_dlp
except ImportError:
    print("yt-dlp not found. Installing...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "yt-dlp"])
    import yt_dlp

# ── Try importing tkinter for GUI ─────────────────────────────────────────────
try:
    import tkinter as tk
    from tkinter import ttk, filedialog, messagebox
    GUI_AVAILABLE = True
except ImportError:
    GUI_AVAILABLE = False


# ══════════════════════════════════════════════════════════════════════════════
#  Core Downloader Logic (works headless too)
# ══════════════════════════════════════════════════════════════════════════════

def get_video_info(url: str) -> dict:
    """Fetch video metadata without downloading."""
    opts = {"quiet": True, "no_warnings": True, "skip_download": True}
    with yt_dlp.YoutubeDL(opts) as ydl:
        return ydl.extract_info(url, download=False)


def build_ydl_opts(
    output_dir: str,
    quality: str = "best",
    audio_only: bool = False,
    progress_hook=None,
) -> dict:
    """Build yt-dlp options dict."""
    outtmpl = os.path.join(output_dir, "%(title)s.%(ext)s")

    if audio_only:
        fmt = "bestaudio/best"
        postprocessors = [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }
        ]
    elif quality == "best":
        fmt = "best[ext=mp4]/best"
        postprocessors = []
    elif quality == "720p":
        fmt = "bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best[height<=720]"
        postprocessors = []
    elif quality == "480p":
        fmt = "bestvideo[height<=480][ext=mp4]+bestaudio[ext=m4a]/best[height<=480]"
        postprocessors = []
    elif quality == "360p":
        fmt = "bestvideo[height<=360][ext=mp4]+bestaudio[ext=m4a]/best[height<=360]"
        postprocessors = []
    else:
        fmt = "best"
        postprocessors = []

    opts = {
        "format": fmt,
        "outtmpl": outtmpl,
        "merge_output_format": "mp4",
        "postprocessors": postprocessors,
        "quiet": False,
        "no_warnings": False,
    }

    if progress_hook:
        opts["progress_hooks"] = [progress_hook]

    return opts


def download_video(
    url: str,
    output_dir: str = "downloads",
    quality: str = "best",
    audio_only: bool = False,
    progress_hook=None,
) -> bool:
    """Download a video/audio. Returns True on success."""
    os.makedirs(output_dir, exist_ok=True)
    opts = build_ydl_opts(output_dir, quality, audio_only, progress_hook)
    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            ydl.download([url])
        return True
    except yt_dlp.utils.DownloadError as e:
        print(f"Download error: {e}")
        return False


# ══════════════════════════════════════════════════════════════════════════════
#  CLI Interface
# ══════════════════════════════════════════════════════════════════════════════

def cli_main():
    import argparse

    parser = argparse.ArgumentParser(
        description="YouTube Downloader powered by yt-dlp",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python youtube_downloader.py https://youtu.be/dQw4w9WgXcQ
  python youtube_downloader.py https://youtu.be/dQw4w9WgXcQ -q 720p
  python youtube_downloader.py https://youtu.be/dQw4w9WgXcQ -a
  python youtube_downloader.py https://youtu.be/dQw4w9WgXcQ -o ~/Videos
        """,
    )
    parser.add_argument("url", help="YouTube video or playlist URL")
    parser.add_argument(
        "-q",
        "--quality",
        choices=["best", "720p", "480p", "360p"],
        default="best",
        help="Video quality (default: best)",
    )
    parser.add_argument(
        "-a", "--audio", action="store_true", help="Download audio only (MP3)"
    )
    parser.add_argument(
        "-o",
        "--output",
        default="downloads",
        help="Output directory (default: downloads/)",
    )
    parser.add_argument(
        "-i", "--info", action="store_true", help="Show video info without downloading"
    )

    args = parser.parse_args()

    if args.info:
        print(f"\nFetching info for: {args.url}\n")
        info = get_video_info(args.url)
        print(f"  Title    : {info.get('title', 'N/A')}")
        print(f"  Uploader : {info.get('uploader', 'N/A')}")
        print(f"  Duration : {info.get('duration_string', 'N/A')}")
        print(f"  Views    : {info.get('view_count', 'N/A'):,}")
        print(f"  Upload   : {info.get('upload_date', 'N/A')}")
        return

    def cli_hook(d):
        if d["status"] == "downloading":
            pct = d.get("_percent_str", "?%").strip()
            speed = d.get("_speed_str", "?/s").strip()
            eta = d.get("_eta_str", "?s").strip()
            print(f"\r  Downloading {pct} at {speed} — ETA {eta}   ", end="", flush=True)
        elif d["status"] == "finished":
            print(f"\n  ✓ Done: {d['filename']}")

    print(f"\nDownloading: {args.url}")
    print(f"Quality    : {'Audio MP3' if args.audio else args.quality}")
    print(f"Output dir : {args.output}\n")

    success = download_video(
        url=args.url,
        output_dir=args.output,
        quality=args.quality,
        audio_only=args.audio,
        progress_hook=cli_hook,
    )

    if success:
        print("\nDownload complete!")
    else:
        print("\nDownload failed.")
        sys.exit(1)


# ══════════════════════════════════════════════════════════════════════════════
#  GUI Application
# ══════════════════════════════════════════════════════════════════════════════

class YouTubeDownloaderGUI:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("YouTube Downloader")
        self.root.geometry("620x520")
        self.root.resizable(False, False)
        self.root.configure(bg="#0f0f0f")

        self._is_downloading = False
        self._setup_styles()
        self._build_ui()

    # ── Styles ────────────────────────────────────────────────────────────────

    def _setup_styles(self):
        style = ttk.Style()
        style.theme_use("clam")

        bg = "#0f0f0f"
        card = "#1a1a1a"
        accent = "#ff0000"
        fg = "#ffffff"
        muted = "#888888"
        border = "#2a2a2a"

        self.colors = {
            "bg": bg, "card": card, "accent": accent,
            "fg": fg, "muted": muted, "border": border,
        }

        style.configure("TFrame", background=bg)
        style.configure("Card.TFrame", background=card)
        style.configure(
            "TLabel", background=bg, foreground=fg, font=("Helvetica", 11)
        )
        style.configure(
            "Card.TLabel", background=card, foreground=fg, font=("Helvetica", 11)
        )
        style.configure(
            "Muted.TLabel", background=bg, foreground=muted, font=("Helvetica", 10)
        )
        style.configure(
            "Title.TLabel",
            background=bg,
            foreground=fg,
            font=("Helvetica", 20, "bold"),
        )
        style.configure(
            "Sub.TLabel",
            background=bg,
            foreground=accent,
            font=("Helvetica", 10, "bold"),
        )
        style.configure(
            "Download.TButton",
            background=accent,
            foreground=fg,
            font=("Helvetica", 12, "bold"),
            borderwidth=0,
            focusthickness=0,
            padding=(20, 10),
        )
        style.map(
            "Download.TButton",
            background=[("active", "#cc0000"), ("disabled", "#333333")],
            foreground=[("disabled", "#666666")],
        )
        style.configure(
            "TCombobox",
            fieldbackground=card,
            background=card,
            foreground=fg,
            selectbackground=card,
            selectforeground=fg,
            bordercolor=border,
            arrowcolor=fg,
        )
        style.map(
            "TCombobox",
            fieldbackground=[("readonly", card)],
            selectbackground=[("readonly", card)],
        )
        style.configure(
            "Horizontal.TProgressbar",
            troughcolor=card,
            background=accent,
            bordercolor=border,
            lightcolor=accent,
            darkcolor=accent,
        )

    # ── UI Construction ───────────────────────────────────────────────────────

    def _build_ui(self):
        bg = self.colors["bg"]
        card = self.colors["card"]
        fg = self.colors["fg"]
        muted = self.colors["muted"]
        border = self.colors["border"]
        accent = self.colors["accent"]

        root = self.root

        # Header
        hdr = tk.Frame(root, bg=bg)
        hdr.pack(fill="x", padx=30, pady=(28, 0))

        tk.Label(
            hdr, text="▶  YouTube", font=("Helvetica", 22, "bold"),
            bg=bg, fg=accent
        ).pack(side="left")
        tk.Label(
            hdr, text=" Downloader", font=("Helvetica", 22, "bold"),
            bg=bg, fg=fg
        ).pack(side="left")

        tk.Label(
            root, text="Download videos and audio directly to your computer",
            bg=bg, fg=muted, font=("Helvetica", 10)
        ).pack(anchor="w", padx=30, pady=(4, 20))

        # URL card
        url_card = tk.Frame(root, bg=card, bd=0, highlightbackground=border,
                            highlightthickness=1)
        url_card.pack(fill="x", padx=30, pady=(0, 12))

        tk.Label(url_card, text="VIDEO URL", bg=card, fg=accent,
                 font=("Helvetica", 9, "bold")).pack(anchor="w", padx=14, pady=(12, 4))

        self.url_var = tk.StringVar()
        url_entry = tk.Entry(
            url_card, textvariable=self.url_var, bg=card, fg=fg,
            insertbackground=fg, relief="flat", font=("Helvetica", 11),
            bd=0
        )
        url_entry.pack(fill="x", padx=14, pady=(0, 12), ipady=2)

        # Options row
        opts_frame = tk.Frame(root, bg=bg)
        opts_frame.pack(fill="x", padx=30, pady=(0, 12))

        # Quality
        q_frame = tk.Frame(opts_frame, bg=card, bd=0,
                           highlightbackground=border, highlightthickness=1)
        q_frame.pack(side="left", fill="both", expand=True, padx=(0, 8))
        tk.Label(q_frame, text="QUALITY", bg=card, fg=accent,
                 font=("Helvetica", 9, "bold")).pack(anchor="w", padx=14, pady=(10, 4))
        self.quality_var = tk.StringVar(value="Best Quality")
        q_combo = ttk.Combobox(
            q_frame, textvariable=self.quality_var,
            values=["Best Quality", "720p", "480p", "360p", "Audio Only (MP3)"],
            state="readonly", font=("Helvetica", 11)
        )
        q_combo.pack(fill="x", padx=14, pady=(0, 10))

        # Output folder
        out_frame = tk.Frame(opts_frame, bg=card, bd=0,
                             highlightbackground=border, highlightthickness=1)
        out_frame.pack(side="left", fill="both", expand=True)
        tk.Label(out_frame, text="SAVE TO", bg=card, fg=accent,
                 font=("Helvetica", 9, "bold")).pack(anchor="w", padx=14, pady=(10, 4))
        self.output_var = tk.StringVar(
            value=os.path.join(os.path.expanduser("~"), "Downloads")
        )
        out_row = tk.Frame(out_frame, bg=card)
        out_row.pack(fill="x", padx=14, pady=(0, 10))
        tk.Entry(
            out_row, textvariable=self.output_var, bg=card, fg=fg,
            insertbackground=fg, relief="flat", font=("Helvetica", 10), bd=0
        ).pack(side="left", fill="x", expand=True)
        tk.Button(
            out_row, text="…", bg=card, fg=muted, activebackground=card,
            activeforeground=fg, relief="flat", bd=0, cursor="hand2",
            font=("Helvetica", 12, "bold"),
            command=self._browse_folder
        ).pack(side="right", padx=(6, 0))

        # Info panel
        self.info_frame = tk.Frame(root, bg=card, bd=0,
                                   highlightbackground=border, highlightthickness=1)
        self.info_frame.pack(fill="x", padx=30, pady=(0, 12))
        self.info_label = tk.Label(
            self.info_frame, text="Paste a YouTube URL above to get started",
            bg=card, fg=muted, font=("Helvetica", 10), anchor="w",
            wraplength=540, justify="left"
        )
        self.info_label.pack(fill="x", padx=14, pady=10)

        # Fetch info button
        fetch_btn = tk.Button(
            root, text="Fetch Info", bg="#1a1a1a", fg=muted, activebackground="#222",
            activeforeground=fg, relief="flat", bd=0, cursor="hand2",
            font=("Helvetica", 10), command=self._fetch_info_async
        )
        fetch_btn.pack(anchor="e", padx=30, pady=(0, 12))

        # Progress
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(
            root, variable=self.progress_var, maximum=100,
            style="Horizontal.TProgressbar", length=560
        )
        self.progress_bar.pack(padx=30, pady=(0, 8))

        self.status_var = tk.StringVar(value="Ready")
        tk.Label(root, textvariable=self.status_var, bg=bg, fg=muted,
                 font=("Helvetica", 10)).pack(anchor="w", padx=30, pady=(0, 12))

        # Download button
        self.dl_btn = ttk.Button(
            root, text="⬇  Download", style="Download.TButton",
            command=self._start_download
        )
        self.dl_btn.pack(fill="x", padx=30, pady=(0, 8))

        # Footer
        tk.Label(
            root,
            text="Powered by yt-dlp  •  For personal use only  •  Respect copyright",
            bg=bg, fg=muted, font=("Helvetica", 9)
        ).pack(pady=(8, 0))

    # ── Actions ───────────────────────────────────────────────────────────────

    def _browse_folder(self):
        folder = filedialog.askdirectory(title="Choose download folder")
        if folder:
            self.output_var.set(folder)

    def _fetch_info_async(self):
        url = self.url_var.get().strip()
        if not url:
            self.info_label.config(text="Please enter a URL first.")
            return
        self.info_label.config(text="Fetching video information…")
        threading.Thread(target=self._fetch_info, args=(url,), daemon=True).start()

    def _fetch_info(self, url: str):
        try:
            info = get_video_info(url)
            title = info.get("title", "Unknown")
            uploader = info.get("uploader", "Unknown")
            dur = info.get("duration_string", "?")
            views = info.get("view_count", 0)
            msg = f"🎬  {title}\n👤  {uploader}   ⏱  {dur}   👁  {views:,} views"
            self.root.after(0, lambda: self.info_label.config(text=msg, fg=self.colors["fg"]))
        except Exception as e:
            self.root.after(
                0, lambda: self.info_label.config(
                    text=f"Could not fetch info: {e}", fg="#ff4444"
                )
            )

    def _start_download(self):
        if self._is_downloading:
            return
        url = self.url_var.get().strip()
        if not url:
            messagebox.showwarning("No URL", "Please paste a YouTube URL first.")
            return

        self._is_downloading = True
        self.dl_btn.state(["disabled"])
        self.progress_var.set(0)
        self.status_var.set("Starting download…")

        quality_map = {
            "Best Quality": "best",
            "720p": "720p",
            "480p": "480p",
            "360p": "360p",
            "Audio Only (MP3)": "best",
        }
        selected = self.quality_var.get()
        quality = quality_map.get(selected, "best")
        audio_only = selected == "Audio Only (MP3)"

        threading.Thread(
            target=self._download_thread,
            args=(url, self.output_var.get(), quality, audio_only),
            daemon=True,
        ).start()

    def _download_thread(self, url, output_dir, quality, audio_only):
        def hook(d):
            if d["status"] == "downloading":
                raw = d.get("_percent_str", "0%").strip().replace("%", "")
                try:
                    pct = float(raw)
                except ValueError:
                    pct = 0
                speed = d.get("_speed_str", "").strip()
                eta = d.get("_eta_str", "").strip()
                msg = f"Downloading… {pct:.1f}%"
                if speed:
                    msg += f"  at {speed}"
                if eta:
                    msg += f"  — ETA {eta}"
                self.root.after(0, lambda p=pct, m=msg: self._update_progress(p, m))
            elif d["status"] == "finished":
                self.root.after(0, lambda: self._update_progress(99, "Processing file…"))

        success = download_video(
            url=url,
            output_dir=output_dir,
            quality=quality,
            audio_only=audio_only,
            progress_hook=hook,
        )

        def finish():
            self._is_downloading = False
            self.dl_btn.state(["!disabled"])
            if success:
                self.progress_var.set(100)
                self.status_var.set(f"✓ Download complete! Saved to: {output_dir}")
            else:
                self.progress_var.set(0)
                self.status_var.set("✗ Download failed. Check the URL and try again.")
                messagebox.showerror(
                    "Download Failed",
                    "Could not download the video.\n\n"
                    "• Check the URL is valid\n"
                    "• Ensure the video is not age-restricted\n"
                    "• Try a different quality setting",
                )

        self.root.after(0, finish)

    def _update_progress(self, pct: float, msg: str):
        self.progress_var.set(pct)
        self.status_var.set(msg)


def gui_main():
    root = tk.Tk()
    app = YouTubeDownloaderGUI(root)
    root.mainloop()


# ══════════════════════════════════════════════════════════════════════════════
#  Entry Point
# ══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Arguments provided → use CLI
        cli_main()
    elif GUI_AVAILABLE:
        # No arguments + tkinter available → launch GUI
        gui_main()
    else:
        print("No URL provided and tkinter is not available.")
        print("Usage: python youtube_downloader.py <URL> [options]")
        print("Run with --help for more info.")
        sys.exit(1)