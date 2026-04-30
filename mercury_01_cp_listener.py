"""
Mercury 01: mask listener/constructor, project version 1.25 (with python 3.9).

This file should be ran on a separate computer from the pi-seq microscope computer,
which does not support Cellpose or mask constuction functions.

In an experiment, run this file first, then start mercury_01.py on pi-seq computer,
this file will automatically process mask images at a given interval.

In addition, mercury_01_cp_prototype.py can be used for pi-seq microscope computer,
but only if it has installed Cellpose (and Conda env from the yaml file) correctly.
"""

# pylint: disable=missing-class-docstring
# pylint: disable=missing-function-docstring

import os
import time
import queue
import threading
from datetime import datetime
from tkinter import filedialog

import numpy as np
import customtkinter as ctk
from cellpose import models, io
from PIL import Image, ImageChops

START_FOLDER = os.path.join(os.path.expanduser("~"), "Box")
START_INTERV = 2
ROTATE_MASKS = False


# ── Theme ────────────────────────────────────────────────────────────────────────────────────────
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

DARK_BG      = "#0f1117"
PANEL_BG     = "#1a1d27"
CARD_BG      = "#21253a"
ACCENT       = "#4f8ef7"
ACCENT_HOVER = "#6ba3ff"
SUCCESS      = "#3dd68c"
DANGER       = "#f75f5f"
WARNING      = "#f5a623"
TEXT_MAIN    = "#e8eaf6"
TEXT_MUTED   = "#6b7280"
BORDER       = "#2e3354"
MONO_FONT    = ("Consolas", 12)
LABEL_FONT   = ("Consolas", 12, "bold")


# ── Watcher logic ────────────────────────────────────────────────────────────────────────────────
def get_files(folder: str, extension: str) -> dict:
    ext = extension.strip().lower()
    result = {}
    try:
        for entry in os.scandir(folder):
            if entry.is_file():
                name = entry.name.lower()
                if not ext or name.endswith(ext if ext.startswith(".") else f".{ext}"):
                    result[entry.path] = entry.stat().st_mtime
    except PermissionError:
        pass
    return result


# ── File-ready guard ─────────────────────────────────────────────────────────────────────────────
def wait_until_file_ready(filepath: str, timeout: float = 60.0, poll: float = 1.0) -> bool:
    """
    Block until the file can be opened exclusively (i.e. the writer has closed it).
    Returns True when ready, False if `timeout` seconds elapse without success.
    """
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            with open(filepath, "rb"):
                return True
        except (PermissionError, OSError):
            time.sleep(poll)
    return False


# ── App ──────────────────────────────────────────────────────────────────────────────────────────
class FolderWatcherApp(ctk.CTk):
    # Sentinel embedded in every line written by _log_update so the method can
    # recognise its own previous output and overwrite it instead of appending.
    _LOG_UPDATE_TAG = "\u200b[upd]"   # zero-width space + marker; invisible in the textbox

    def __init__(self):
        super().__init__()
        self.title("Mercury 01 - Extra")
        self.geometry("720x780")
        self.minsize(600, 600)
        self.configure(fg_color=DARK_BG)

        self._watching    = False
        self._watch_thread  = None
        self._stop_event  = threading.Event()
        self._known       = {}

        # GUI update queue (log lines, status refreshes) — drained on the main thread
        self._proc_queue  = queue.Queue()

        # File-processing pipeline: watcher enqueues paths, worker pool consumes them
        self._file_queue  = queue.Queue()   # unbounded; holds filepaths waiting to process
        self._workers     = []              # list of active worker Thread objects
        self._active_jobs = 0              # number of files currently being processed
        self._jobs_lock   = threading.Lock()

        self._build_ui()
        self._drain_queue()   # start the tkinter-safe log-drain loop

    # ── UI Construction ──────────────────────────────────────────────────────────────────────────
    def _build_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)   # log panel expands

        # ── Header ───────────────────────────────────────────────────────────────────────────────
        header = ctk.CTkFrame(self, fg_color=PANEL_BG, corner_radius=0, height=56)
        header.grid(row=0, column=0, sticky="ew")
        header.grid_propagate(False)
        header.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            header,
            text="Mercury 01 - Mask Listener/Constructor",
            font=LABEL_FONT,
            text_color=ACCENT,
        ).grid(row=0, column=0, padx=20, pady=14, sticky="w")

        self._status_dot = ctk.CTkLabel(
            header, text="● IDLE",
            font=LABEL_FONT,
            text_color=TEXT_MUTED,
        )
        self._status_dot.grid(row=0, column=1, padx=20, pady=14, sticky="e")

        # ── Config panel ─────────────────────────────────────────────────────────────────────────
        config = ctk.CTkFrame(self, fg_color=PANEL_BG, corner_radius=12)
        config.grid(row=1, column=0, padx=14, pady=(10, 0), sticky="ew")
        config.grid_columnconfigure(1, weight=1)

        # helper: compact section label
        def slabel(parent, text, row, col=0, colspan=3):
            ctk.CTkLabel(
                parent, text=text,
                font=LABEL_FONT,
                text_color=TEXT_MUTED,
            ).grid(row=row, column=col, columnspan=colspan,
                   padx=(16, 4), pady=(10, 1), sticky="w")

        # helper: folder row (label + entry + browse)
        def folder_row(parent, row, label_text, string_var, browse_cmd):
            slabel(parent, label_text, row * 2)
            ctk.CTkEntry(
                parent, textvariable=string_var,
                font=MONO_FONT, fg_color=CARD_BG, border_color=BORDER,
                text_color=TEXT_MAIN, height=32,
            ).grid(row=row * 2 + 1, column=0, columnspan=2,
                   padx=(16, 4), pady=(0, 4), sticky="ew")
            ctk.CTkButton(
                parent, text="Browse", width=72, height=32,
                fg_color=CARD_BG, hover_color=BORDER,
                border_color=BORDER, border_width=1,
                text_color=TEXT_MAIN, font=LABEL_FONT,
                command=browse_cmd,
            ).grid(row=row * 2 + 1, column=2, padx=(0, 16), pady=(0, 4))

        # — Watch folder (rows 0-1) —
        self._folder_var = ctk.StringVar(value=START_FOLDER)
        folder_row(config, 0, "WATCH FOLDER", self._folder_var, self._browse_watch)

        # — Output folder (rows 2-3) —
        self._outfolder_var = ctk.StringVar(value="")
        folder_row(config, 1, "OUTPUT FOLDER  (blank = same as input)",
                   self._outfolder_var, self._browse_output)

        # — CP Model row (rows 4-5) — entry + browse (may be a built-in name or a file path)
        slabel(config, "CP MODEL  (built-in name, e.g. cyto3, or path to custom model file)", 4)
        self._cpmodel_var = ctk.StringVar(value="cyto3")
        ctk.CTkEntry(
            config, textvariable=self._cpmodel_var,
            font=MONO_FONT, fg_color=CARD_BG, border_color=BORDER,
            text_color=TEXT_MAIN, height=32,
            placeholder_text="cyto3  or  /path/to/model",
        ).grid(row=5, column=0, columnspan=2, padx=(16, 4), pady=(0, 4), sticky="ew")
        ctk.CTkButton(
            config, text="Browse", width=72, height=32,
            fg_color=CARD_BG, hover_color=BORDER,
            border_color=BORDER, border_width=1,
            text_color=TEXT_MAIN, font=LABEL_FONT,
            command=self._browse_cpmodel,
        ).grid(row=5, column=2, padx=(0, 16), pady=(0, 4))

        # — Compact parameter row (row 6) —
        prow = ctk.CTkFrame(config, fg_color="transparent")
        prow.grid(row=6, column=0, columnspan=3, padx=16, pady=(4, 10), sticky="ew")
        for i in range(5):
            prow.grid_columnconfigure(i, weight=1)

        def param_cell(parent, col, label, widget_factory):
            ctk.CTkLabel(
                parent, text=label,
                font=LABEL_FONT, text_color=TEXT_MUTED,
            ).grid(row=0, column=col, padx=(0, 8), pady=(0, 2), sticky="w")
            widget_factory(parent).grid(row=1, column=col, padx=(0, 8), sticky="ew")

        # Interval
        self._interval_var = ctk.StringVar(value=START_INTERV)
        param_cell(prow, 0, "INTERVAL (s)",
                   lambda p: ctk.CTkEntry(p, textvariable=self._interval_var,
                                          font=MONO_FONT, fg_color=CARD_BG,
                                          border_color=BORDER, text_color=TEXT_MAIN,
                                          height=30))

        # Extension
        self._ext_var = ctk.StringVar(value=".tif")
        param_cell(prow, 1, "EXTENSION",
                   lambda p: ctk.CTkEntry(p, textvariable=self._ext_var,
                                          font=MONO_FONT, fg_color=CARD_BG,
                                          border_color=BORDER, text_color=TEXT_MAIN,
                                          height=30, placeholder_text=".tif"))

        # Diameter
        self._diameter_var = ctk.StringVar(value="30")
        param_cell(prow, 2, "DIAMETER (px)",
                   lambda p: ctk.CTkEntry(p, textvariable=self._diameter_var,
                                          font=MONO_FONT, fg_color=CARD_BG,
                                          border_color=BORDER, text_color=TEXT_MAIN,
                                          height=30))

        # Max workers
        self._workers_var = ctk.StringVar(value="1")
        param_cell(prow, 3, "MAX WORKERS",
                   lambda p: ctk.CTkEntry(p, textvariable=self._workers_var,
                                          font=MONO_FONT, fg_color=CARD_BG,
                                          border_color=BORDER, text_color=TEXT_MAIN,
                                          height=30))

        # Checkboxes column
        chk_frame = ctk.CTkFrame(prow, fg_color="transparent")
        chk_frame.grid(row=0, column=4, rowspan=2, sticky="nsew")
        chk_frame.grid_rowconfigure(0, weight=0)
        chk_frame.grid_rowconfigure(1, weight=0)

        self._save_npz_var = ctk.BooleanVar(value=True)

        ctk.CTkLabel(chk_frame, text="OPTIONS",
                     font=LABEL_FONT,
                     text_color=TEXT_MUTED,
        ).grid(row=0, column=0, sticky="w", pady=(0, 2))
        ctk.CTkCheckBox(chk_frame, text="Save NPZ",
                        variable=self._save_npz_var,
                        font=LABEL_FONT, text_color=TEXT_MAIN,
                        checkbox_height=30, checkbox_width=30,
                        corner_radius=6,
        ).grid(row=1, column=0, sticky="w")

        # ── Log panel ────────────────────────────────────────────────────────────────────────────
        log_outer = ctk.CTkFrame(self, fg_color=PANEL_BG, corner_radius=12)
        log_outer.grid(row=2, column=0, padx=14, pady=10, sticky="nsew")
        log_outer.grid_rowconfigure(1, weight=1)
        log_outer.grid_columnconfigure(0, weight=1)

        log_header = ctk.CTkFrame(log_outer, fg_color="transparent")
        log_header.grid(row=0, column=0, padx=14, pady=(10, 4), sticky="ew")
        log_header.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            log_header, text="EVENT LOG",
            font=LABEL_FONT, text_color=TEXT_MUTED,
        ).grid(row=0, column=0, sticky="w")

        ctk.CTkButton(
            log_header, text="Clear", width=56, height=24,
            fg_color="transparent", hover_color=BORDER,
            border_color=BORDER, border_width=1,
            text_color=TEXT_MUTED, font=LABEL_FONT,
            command=self._clear_log,
        ).grid(row=0, column=1, sticky="e")

        self._log_box = ctk.CTkTextbox(
            log_outer,
            font=MONO_FONT,
            fg_color=CARD_BG,
            text_color=TEXT_MAIN,
            border_color=BORDER,
            border_width=1,
            corner_radius=8,
            wrap="word",
            state="disabled",
        )
        self._log_box.tag_config("danger",  foreground=DANGER)
        self._log_box.tag_config("success", foreground=SUCCESS)
        self._log_box.tag_config("warning", foreground=WARNING)
        self._log_box.tag_config("normal",  foreground=TEXT_MAIN)
        self._log_box.grid(row=1, column=0, padx=14, pady=(0, 14), sticky="nsew")

        # ── Start / Stop button ──────────────────────────────────────────────────────────────────
        self._toggle_btn = ctk.CTkButton(
            self,
            text=">  START WATCHING",
            height=44,
            font=LABEL_FONT,
            fg_color=ACCENT,
            hover_color=ACCENT_HOVER,
            corner_radius=10,
            command=self._toggle_watching,
        )
        self._toggle_btn.grid(row=3, column=0, padx=14, pady=(0, 14), sticky="ew")

    # ── Folder browsing ──────────────────────────────────────────────────────────────────────────
    def _browse_watch(self):
        path = filedialog.askdirectory(initialdir=self._folder_var.get())
        if path:
            self._folder_var.set(path)

    def _browse_output(self):
        path = filedialog.askdirectory(initialdir=self._outfolder_var.get()
                                       or self._folder_var.get())
        if path:
            self._outfolder_var.set(path)

    def _browse_cpmodel(self):
        current = self._cpmodel_var.get().strip()
        initdir = (os.path.dirname(current)
                   if current and os.path.exists(current)
                   else os.path.expanduser('~'))
        filepath = filedialog.askopenfilename(
            title='Select Cellpose model file',
            initialdir=initdir,
        )
        if filepath:
            self._cpmodel_var.set(filepath)

    # ── Watch control ────────────────────────────────────────────────────────────────────────────
    def _toggle_watching(self):
        if self._watching:
            self._stop_watching()
        else:
            self._start_watching()

    def _start_watching(self):
        folder       = self._folder_var.get().strip()
        ext          = self._ext_var.get().strip()
        interval_str = self._interval_var.get().strip()
        workers_str  = self._workers_var.get().strip()

        # Numeric fields are validated upfront — bad values are caught immediately
        if not folder:
            self._log("!  Watch folder path cannot be empty.", color="danger")
            return

        try:
            interval = float(interval_str)
            if interval <= 0:
                raise ValueError
        except ValueError:
            self._log("!  Interval must be a positive number.", color="danger")
            return

        try:
            n_workers = int(workers_str)
            if n_workers < 1:
                raise ValueError
        except ValueError:
            self._log("!  Max workers must be a positive integer.", color="danger")
            return

        outfolder = self._outfolder_var.get().strip()

        self._watching = True
        self._stop_event.clear()

        # Clear any leftover items from a previous run
        while not self._file_queue.empty():
            try:
                self._file_queue.get_nowait()
            except queue.Empty:
                break

        # Launch the worker pool — each worker blocks on _file_queue until a sentinel
        self._workers = []
        for _ in range(n_workers):
            t = threading.Thread(target=self._worker_loop, daemon=True)
            t.start()
            self._workers.append(t)

        self._toggle_btn.configure(
            text="■  STOP WATCHING",
            fg_color=DANGER,
            hover_color="#ff7070",
        )

        label     = f"*{ext}" if ext else "all files"
        out_label = outfolder if outfolder else "(same as input)"
        self._log(f">  Armed — watch folder : '{folder}'")
        self._log(f"   Output  → {out_label}")
        self._log(f"   Interval: {interval}s  |  Filter: {label}  |  Workers: {n_workers}")

        self._watch_thread = threading.Thread(
            target=self._watch_loop,
            args=(folder, outfolder, ext, interval),
            daemon=True,
        )
        self._watch_thread.start()

    def _stop_watching(self):
        self._stop_event.set()
        self._watching = False

        # Send one sentinel (None) per worker so every thread exits its blocking get()
        for _ in self._workers:
            self._file_queue.put(None)

        self._toggle_btn.configure(
            text=">  START WATCHING",
            fg_color=ACCENT,
            hover_color=ACCENT_HOVER,
        )
        self._status_dot.configure(text="● IDLE", text_color=TEXT_MUTED)
        self._log("■  Stopped watching.  (any active processing will finish normally)",
                  color="warning")

    # ── Watch loop (watcher thread) ──────────────────────────────────────────────────────────────
    def _watch_loop(self, folder, outfolder, ext, interval):
        # ── Phase 1: wait until both required folders exist ──────────────────────────────────────
        folders_ready = os.path.isdir(folder) and (not outfolder or os.path.isdir(outfolder))

        if not folders_ready:
            self._proc_queue.put(("status_text", "● WAITING FOR FOLDERS", WARNING))
            self._log_threadsafe("?  Folder(s) not found — waiting for them to be created...",
                                 "warning")

            while not self._stop_event.is_set():
                if self._stop_event.wait(timeout=interval):
                    return                  # stopped while waiting
                folder_ok  = os.path.isdir(folder)
                output_ok  = (not outfolder) or os.path.isdir(outfolder)
                if folder_ok and output_ok:
                    break
                # Report which folders are still missing (update in-place each poll)
                missing = []
                if not folder_ok:
                    missing.append(f"watch ('{os.path.basename(folder)}')")
                if not output_ok:
                    missing.append(f"output ('{os.path.basename(outfolder)}')")
                self._proc_queue.put((
                    "log_update",
                    f"?  Still waiting for: {', '.join(missing)}",
                    "warning",
                ))

        # ── Phase 2: folders are ready — snapshot existing files and begin normal loop ──────────
        self._known = get_files(folder, ext)
        out_label   = outfolder if outfolder else "(same as input)"
        self._log_threadsafe(f"   Folders ready.  Output → {out_label}", "normal")
        self._log_threadsafe(f"   Snapshot: {len(self._known)} existing file(s) noted.")

        # Queue any pre-existing files for processing right away
        for fp in sorted(self._known):
            self._log_threadsafe(f"   Queuing existing file: {os.path.basename(fp)}", "success")
            self._file_queue.put(fp)

        self._proc_queue.put(("status_text", "● WATCHING", SUCCESS))

        while not self._stop_event.wait(timeout=interval):
            current   = get_files(folder, ext)
            new_files = set(current) - set(self._known)
            if new_files:
                for fp in sorted(new_files):
                    self._log_threadsafe(
                        f"   New file detected: {os.path.basename(fp)}", "success")
                    self._file_queue.put(fp)
            else:
                self._proc_queue.put(("log_update", "   No new image detected.", "normal"))
            self._known = current

    # ── Worker pool ──────────────────────────────────────────────────────────────────────────────
    def _worker_loop(self):
        """
        Runs on a persistent worker thread.
        Blocks on _file_queue; exits cleanly when it receives a None sentinel.
        """
        while True:
            filepath = self._file_queue.get()
            if filepath is None:        # sentinel sent by _stop_watching
                break
            self._process_file(filepath)

    def _process_file(self, filepath: str):
        """Runs on a worker thread. Calls create_cpmask_single and logs results."""
        basename = os.path.basename(filepath)

        with self._jobs_lock:
            self._active_jobs += 1
        self._log_threadsafe(f"   Waiting for file to be ready: {basename}")
        self._update_status_threadsafe()

        if not wait_until_file_ready(filepath):
            self._log_threadsafe(
                f"!  Timed out waiting for file to be ready: {basename}", "danger")
            with self._jobs_lock:
                self._active_jobs -= 1
            self._update_status_threadsafe()
            return

        self._log_threadsafe(f"   Processing started: {basename}", "normal")

        # Collect parameters (safe to read StringVars from another thread
        # since we're only reading, not writing)
        outfolder  = self._outfolder_var.get().strip() or None
        cp_model   = self._cpmodel_var.get().strip() or "cyto3"
        diameter   = self._diameter_var.get().strip()
        save_npz   = self._save_npz_var.get()

        try:
            diam = int(float(diameter))
        except ValueError:
            diam = 30
            self._log_threadsafe(
                f"   !  Invalid diameter '{diameter}', defaulting to 30.", "warning")

        try:
            create_cpmask_single(
                original=filepath,
                savepath=outfolder,
                cp_model=cp_model,
                diameter=diam,
                save_png=True,
                save_npz=save_npz,
                reversal=False,
                rotate_mask=ROTATE_MASKS,
            )
            self._log_threadsafe(
                f"*  Processing complete: {basename}", "success")
        except Exception as exc:                            # pylint: disable=broad-except
            self._log_threadsafe(
                f"!  ERROR processing {basename}:", "danger")
            self._log_threadsafe(
                f"   {type(exc).__name__}: {exc}", "danger")
        finally:
            with self._jobs_lock:
                self._active_jobs -= 1
            self._update_status_threadsafe()

    # ── Thread-safe helpers ──────────────────────────────────────────────────────────────────────
    def _log_threadsafe(self, msg: str, color: str = "normal"):
        """Queue a log message from any thread; drained by _drain_queue."""
        self._proc_queue.put(("log", msg, color))

    def _update_status_threadsafe(self):
        """Queue a status-dot refresh from any thread."""
        self._proc_queue.put(("status",))

    def _drain_queue(self):
        """
        Called via self.after(); runs on the main thread every 100 ms.
        Safely applies all queued GUI updates.
        """
        try:
            while True:
                item = self._proc_queue.get_nowait()
                if item[0] == "log":
                    self._log(item[1], color=item[2])
                elif item[0] == "log_update":
                    self._log_update(item[1], color=item[2])
                elif item[0] == "status":
                    self._refresh_status_dot()
                elif item[0] == "status_text":
                    # Direct status-dot override from the watcher thread (text, color)
                    self._status_dot.configure(text=item[1], text_color=item[2])
        except queue.Empty:
            pass
        self.after(100, self._drain_queue)

    def _refresh_status_dot(self):
        with self._jobs_lock:
            jobs = self._active_jobs
        if self._watching:
            if jobs > 0:
                self._status_dot.configure(
                    text=f"  PROCESSING ({jobs})", text_color=WARNING)
            else:
                self._status_dot.configure(text="● WATCHING", text_color=SUCCESS)
        else:
            if jobs > 0:
                self._status_dot.configure(
                    text=f"  FINISHING ({jobs})", text_color=WARNING)
            else:
                self._status_dot.configure(text="● IDLE", text_color=TEXT_MUTED)

    # ── Log helpers ──────────────────────────────────────────────────────────────────────────────
    def _log(self, msg: str, color: str = "normal"):
        prefix = datetime.now().strftime("%H:%M:%S")
        line = f"[{prefix}]  {msg}\n"
        self._log_box.configure(state="normal")
        tag = color if color in ("danger", "success", "warning") else "normal"
        self._log_box.insert("end", line, tag)
        self._log_box.see("end")
        self._log_box.configure(state="disabled")

    def _log_update(self, msg: str, color: str = "normal"):
        """
        Overwrite the last log line in-place if it was itself written by _log_update
        (recognised by the UPDATE_TAG sentinel embedded in the line); otherwise append
        a new line as normal.  This keeps repetitive polling messages — folder-wait
        and no-new-image — from flooding the log.
        """
        prefix   = datetime.now().strftime("%H:%M:%S")
        new_line = f"[{prefix}]  {msg}{self._LOG_UPDATE_TAG}\n"
        tag      = color if color in ("danger", "success", "warning") else "normal"
        self._log_box.configure(state="normal")
        last_line = self._log_box.get("end-2l", "end-1c")
        if self._LOG_UPDATE_TAG in last_line:
            self._log_box.delete("end-2l", "end-1c")
        self._log_box.insert("end", new_line, tag)
        self._log_box.see("end")
        self._log_box.configure(state="disabled")

    def _clear_log(self):
        self._log_box.configure(state="normal")
        self._log_box.delete("1.0", "end")
        self._log_box.configure(state="disabled")


# ── Cellpose function ────────────────────────────────────────────────────────────────────────────
def create_cpmask_single(
        original: str,                  # file name with path to the original image
        savepath: str = None,           # full path to output folder of mask images
        savesize: list = None,          # mask save size for output [width, height]
        reversal: bool = False,         # reverse output image color if set to true
        cp_model: str = "cyto3",        # cellpose model type for cell segmentation
        diameter: int = 30,             # average pixel diameter for a typical cell
        channels: list = None,          # segmentation channel [cytoplasm, nucleus]
        save_png: bool = True,          # if a new cellpose png file would be saved
        save_npz: bool = True,          # if a cell masking npz file would be saved
        rotate_mask: bool = True        # rotate the output mask 180° before saving
):
    """
    ### Construct and save mask for a multichannel image (as png or npz).

    `original` : file name and path to the original images.
    ---------------------------------------------------------------------------
    #### Optional:
    `savepath`    : full path to output folder of mask images = *(same as input image)*
    `savesize`    : size of the output images [width, height] = *(same as input image)*.
    `reversal`    : reverse output image color if set to true = `False`.
    `cp_model`    : cellpose segmentation model (str or path) = `"cyto3"`.
    `diameter`    : average pixel diameter for a typical cell = `30`.
    `channels`    : segmentation channel [cytoplasm, nucleus] = `[0,0]`.
    `save_png`    : if a new cellpose png file would be saved = `True`.
    `save_npz`    : if a cell masking npz file would be saved = `True`.
    `rotate_mask` : rotate the output mask 180° before saving = `True`.
    """
    if cp_model.lower() == "none" or cp_model is None:
        return
    io.logger_setup()
    _head, tail = os.path.split(original)
    if channels is None:
        channels = [0, 0]
    img = io.imread(original)
    if os.path.exists(cp_model):
        cp3 = models.CellposeModel(gpu=True, pretrained_model=cp_model)
        masks, _flows, _styles = cp3.eval(img, diameter=float(diameter), channels=channels)
    else:
        cp3 = models.Cellpose(gpu=True, model_type=cp_model)
        masks, _flows, _styles, _diams = cp3.eval(img, diameter=float(diameter), channels=channels)
    if save_png:
        binary = (masks > 0).astype(np.uint8) * 255
        msk = Image.fromarray(binary, mode="L")
        if reversal is False:
            msk = ImageChops.invert(msk)
        if rotate_mask:
            msk = msk.rotate(180)
        if savesize is not None:
            msk = msk.resize(savesize)
        if savepath is None:
            msk.save(os.path.splitext(original)[0] + '_cp_masks.png')
        else:
            msk.save(os.path.join(savepath, os.path.splitext(tail)[0] + '_cp_masks.png'))
    if save_npz:
        if savepath is None:
            np.savez_compressed(os.path.splitext(original)[0] + '_cp_array.npz', masks=masks)
        else:
            np.savez_compressed(
                os.path.join(savepath, os.path.splitext(tail)[0] + '_cp_array.npz'), masks=masks)


# ── Entry point ──────────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app = FolderWatcherApp()
    app.attributes("-topmost", True)
    app.after_idle(app.attributes, "-topmost", False)
    app.after(10, app.focus)
    app.mainloop()
