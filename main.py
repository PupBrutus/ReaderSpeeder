import tkinter as tk
from tkinter import filedialog, messagebox
import pyttsx3
import threading
import time
import os
import simpleaudio as sa
import logging  # Add logging import
import re  # Add regex import
import json  # Add JSON import
import tkinter.ttk as ttk  # Add ttk import
import queue  # Add queue import

class SpeedReader:
    def __init__(self, master):
        self.root = master
        self.root.title("ReaderSpeeder")
        
        self.wpm = 200
        self.tts_enabled = True
        self.text = ""
        self.chunks = []
        self.current_chunk_index = 0
        self.is_paused = True
        self.is_stopped = True
        self.highlight_color = "#42a832"
        
        self.tts_var = tk.IntVar(value=1)  # Enable TTS by default
        self.text_box = None  # Add text box attribute
        self.text_scrollbar = None  # Add scrollbar attribute
        self.night_mode_var = tk.IntVar(value=1)  # Enable night mode by default
        self.opacity_var = tk.DoubleVar(value=1.0)  # Set default opacity to 100%
        self.tts_engine_var = tk.StringVar(value="sapi5")  # Default TTS engine
        self.reading_window = None  # Add reading window attribute
        self.font_size_var = tk.IntVar(value=48)  # Default font size
        
        self.setup_ui()
        self.initialize_tts_engine()  # Initialize TTS engine
        try:
            self.tts_engine = pyttsx3.init()
            self.tts_engine.setProperty('rate', 500)  # Set default rate
        except (pyttsx3.EngineError, RuntimeError) as e:
            logging.error("Failed to initialize TTS engine: %s", exc_info=e)
            self.tts_engine = None  # Set to None if initialization fails
        
        self.tts_playback_event = threading.Event()
        self.tts_stop_event = threading.Event()
        self.tts_complete_event = threading.Event()  # Add event to signal TTS completion
        self.tts_playback_lock = threading.Lock()  # Add a lock to prevent multiple TTS playback threads
        
        self.load_settings()  # Load settings on initialization
        self.reading_thread = None  # Initialize reading_thread attribute
        
        self.shutdown_event = threading.Event()  # Add shutdown event
        
        self.next_chunk_queue = queue.Queue(maxsize=1)  # Add a queue to hold the next chunk
        self.next_chunk_thread = None  # Add a thread for preparing the next chunk
        self.current_chunk = None  # Add a variable to hold the current chunk
        self.first_chunk_prepared = False  # Add a flag to indicate if the first chunk is prepared
        
        self.preprocessed_chunks = []  # Add a list to hold preprocessed chunks
        self.tts_audio_files = []  # Remove the list to hold TTS audio file paths
        
        # Automatically load default.txt for debugging purposes
        #self.load_file("default.txt", show_confirmation=False)
        self.reading_window.protocol("WM_DELETE_WINDOW", self.on_closing_reading_window)  # Handle reading window close event
        
    def setup_ui(self):
        self.settings_frame = tk.Frame(self.root)
        self.settings_frame.pack(pady=20)
        
        tk.Label(self.settings_frame, text="Words per minute:").grid(row=0, column=0)
        self.wpm_entry = tk.Entry(self.settings_frame, state=tk.NORMAL)  # Ensure state is NORMAL
        self.wpm_entry.grid(row=0, column=1)
        self.wpm_entry.insert(0, "500")
        
        tk.Label(self.settings_frame, text="Highlight Color:").grid(row=1, column=0)
        self.color_entry = tk.Entry(self.settings_frame, state=tk.NORMAL)  # Ensure state is NORMAL
        self.color_entry.grid(row=1, column=1)
        self.color_entry.insert(0, "#42a832")
        
        self.tts_check = tk.Checkbutton(self.settings_frame, text="Enable Text-to-Speech", variable=self.tts_var)
        self.tts_check.grid(row=2, columnspan=2)
        
        tk.Label(self.settings_frame, text="Text Content:").grid(row=3, column=0, columnspan=2)
        
        self.text_scrollbar = tk.Scrollbar(self.settings_frame)
        self.text_scrollbar.grid(row=4, column=2, sticky='ns')
        
        self.text_box = tk.Text(self.settings_frame, height=10, width=50, yscrollcommand=self.text_scrollbar.set)
        self.text_box.grid(row=4, column=0, columnspan=2, pady=10)
        
        self.text_scrollbar.config(command=self.text_box.yview)
        
        self.load_button = tk.Button(self.settings_frame, text="Load Text File", command=self.load_file)
        self.load_button.grid(row=5, columnspan=2, pady=10)
        
        self.start_button = tk.Button(self.settings_frame, text="Start Speed Reading", command=self.start_speed_reading)
        self.start_button.grid(row=6, columnspan=2, pady=10)
        
        self.night_mode_check = tk.Checkbutton(self.settings_frame, text="Enable Night Mode", variable=self.night_mode_var, command=self.toggle_night_mode)
        self.night_mode_check.grid(row=7, columnspan=2, pady=10)
        
        tk.Label(self.settings_frame, text="Window Opacity:").grid(row=8, column=0)
        self.opacity_scale = tk.Scale(self.settings_frame, variable=self.opacity_var, from_=0.1, to=1.0, resolution=0.1, orient="horizontal", command=self.change_opacity)
        self.opacity_scale.grid(row=8, column=1)
        
        tk.Label(self.settings_frame, text="TTS Engine:").grid(row=9, column=0)
        self.tts_engine_menu = tk.OptionMenu(self.settings_frame, self.tts_engine_var, "sapi5", "nsss", "espeak", command=self.change_tts_engine)
        self.tts_engine_menu.grid(row=9, column=1)
        
        tk.Label(self.settings_frame, text="Font Size:").grid(row=10, column=0)
        self.font_size_scale = tk.Scale(self.settings_frame, variable=self.font_size_var, from_=10, to=200, orient="horizontal", command=self.change_font_size)
        self.font_size_scale.grid(row=10, column=1)
        
        self.reading_window = tk.Toplevel(self.root)  # Change to Toplevel window
        self.reading_window.withdraw()  # Hide initially
        self.reading_frame = tk.Frame(self.reading_window)  # Use reading_window as parent
        self.reading_frame.pack(pady=20)
        
        self.word_label = tk.Text(self.reading_frame, font=("Helvetica", 48), height=1, width=15)
        self.word_label.pack(pady=20)
        self.word_label.tag_configure("center", justify='center')
        self.word_label.config(state=tk.DISABLED)
        
        self.progress = tk.DoubleVar()
        self.progress_bar = tk.Scale(self.reading_frame, variable=self.progress, orient="horizontal", length=400)
        self.progress_bar.pack(pady=10)
        self.progress_bar.bind("<ButtonPress-1>", self.on_progress_press)  # Bind mouse press event
        self.progress_bar.bind("<ButtonRelease-1>", self.on_progress_release)  # Bind mouse release event
        
        self.control_frame = tk.Frame(self.reading_frame)
        self.control_frame.pack(pady=10)
        
        self.pause_button = tk.Button(self.control_frame, text="Pause", command=self.pause)
        self.pause_button.grid(row=0, column=0, padx=5)
        
        self.play_button = tk.Button(self.control_frame, text="Play", command=self.play)
        self.play_button.grid(row=0, column=1, padx=5)
        
        self.stop_button = tk.Button(self.control_frame, text="Stop", command=self.stop)
        self.stop_button.grid(row=0, column=2, padx=5)
        
        self.apply_night_mode()  # Apply night mode settings initially
        
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)  # Handle window close event
        
    def toggle_night_mode(self):
        self.apply_night_mode()
        
    def apply_night_mode(self):
        style = ttk.Style()
        if self.night_mode_var.get():
            night_bg = "#2e2e2e"
            night_fg = "#ffffff"
            self.root.config(bg=night_bg)
            self.settings_frame.config(bg=night_bg)
            self.reading_frame.config(bg=night_bg)
            self.control_frame.config(bg=night_bg)
            self.word_label.config(bg=night_bg, fg=night_fg)
            self.text_box.config(bg=night_bg, fg=night_fg, insertbackground=night_fg)
            self.wpm_entry.config(bg=night_bg, fg=night_fg, insertbackground=night_fg)
            self.color_entry.config(bg=night_bg, fg=night_fg, insertbackground=night_fg)
            self.progress_bar.config(bg=night_bg, fg=night_fg, troughcolor="#4d4d4d")
            self.opacity_scale.config(bg=night_bg, fg=night_fg, troughcolor="#4d4d4d")
            self.text_scrollbar.config(bg=night_bg, troughcolor="#4d4d4d", activebackground="#4d4d4d")
            self.night_mode_check.config(bg=night_bg, fg=night_fg, selectcolor="#4d4d4d")
            self.tts_check.config(bg=night_bg, fg=night_fg, selectcolor="#4d4d4d")
            self.root.tk_setPalette(background=night_bg, foreground=night_fg, activeBackground=night_bg, activeForeground=night_fg)
            style.configure("TScrollbar", background=night_bg, troughcolor="#4d4d4d", arrowcolor=night_fg)
            for widget in self.settings_frame.winfo_children():
                if isinstance(widget, tk.Label) or isinstance(widget, tk.Button):
                    widget.config(bg=night_bg, fg=night_fg)
        else:
            day_bg = "#f0f0f0"
            day_fg = "#000000"
            self.root.config(bg=day_bg)
            self.settings_frame.config(bg=day_bg)
            self.reading_frame.config(bg=day_bg)
            self.control_frame.config(bg=day_bg)
            self.word_label.config(bg=day_bg, fg=day_fg)
            self.text_box.config(bg="#ffffff", fg=day_fg, insertbackground=day_fg)
            self.wpm_entry.config(bg="#ffffff", fg=day_fg, insertbackground=day_fg)
            self.color_entry.config(bg="#ffffff", fg=day_fg, insertbackground=day_fg)
            self.progress_bar.config(bg=day_bg, fg=day_fg, troughcolor="#d9d9d9")
            self.opacity_scale.config(bg=day_bg, fg=day_fg, troughcolor="#d9d9d9")
            self.text_scrollbar.config(bg=day_bg, troughcolor="#d9d9d9", activebackground="#d9d9d9")
            self.night_mode_check.config(bg=day_bg, fg=day_fg, selectcolor="#d9d9d9")
            self.tts_check.config(bg=day_bg, fg=day_fg, selectcolor="#d9d9d9")
            self.root.tk_setPalette(background=day_bg, foreground=day_fg, activeBackground=day_bg, activeForeground=day_fg)
            style.configure("TScrollbar", background=day_bg, troughcolor="#d9d9d9", arrowcolor=day_fg)
            for widget in self.settings_frame.winfo_children():
                if isinstance(widget, tk.Label) or isinstance(widget, tk.Button):
                    widget.config(bg=day_bg, fg=day_fg)
            self.word_label.config(font=("Helvetica", self.font_size_var.get()))  # Apply font size
        
    def load_file(self, file_path=None, show_confirmation=True):
        if not file_path:
            file_path = filedialog.askopenfilename(filetypes=[("Text files", "*.txt")])
        if file_path:
            with open(file_path, "r", encoding="utf-8") as file:
                self.text = file.read()
            self.text_box.delete("1.0", tk.END)  # Clear the text box
            self.text_box.insert(tk.END, self.text)  # Insert the loaded text into the text box
            if show_confirmation:
                messagebox.showinfo("File Loaded", "Text file loaded successfully!")
        
    def start_speed_reading(self):
        try:
            self.wpm = int(self.wpm_entry.get())
        except ValueError:
            messagebox.showerror("Invalid Input", "Please enter a valid number for words per minute.")
            return
        
        self.highlight_color = self.color_entry.get()
        self.tts_enabled = bool(self.tts_var.get())
        if self.tts_enabled and self.tts_engine:
            self.tts_engine.setProperty('rate', self.wpm)  # Adjust TTS rate to match WPM
            logging.info("TTS Enabled: Adjusting rate to %d", self.wpm)
        
        self.text = self.text_box.get("1.0", tk.END).strip()  # Get the text from the text box
        self.chunks = re.split(r'(?<=[.!?])\s+', self.text)  # Split text into chunks by terminal punctuation
        
        self.current_chunk_index = 0
        self.is_paused = False
        self.is_stopped = False
        self.settings_frame.pack_forget()
        self.reading_window.deiconify()  # Show the reading window
        self.root.withdraw()  # Hide the main settings window
        self.progress.set(0)
        
        self.preprocess_chunks()  # Preprocess all chunks before starting
        
        self.reading_thread = threading.Thread(target=self.speed_reading)
        self.reading_thread.start()
        self.prepare_next_chunk()  # Prepare the next chunk

    def preprocess_chunks(self):
        self.preprocessed_chunks = []
        for chunk in self.chunks:
            if chunk.strip():
                self.prepare_chunk(chunk)
                self.preprocessed_chunks.append(chunk)
        logging.info("Preprocessing complete. Total chunks: %d", len(self.preprocessed_chunks))
        
    def prepare_next_chunk(self):
        if self.current_chunk_index + 1 < len(self.chunks):
            next_chunk = self.chunks[self.current_chunk_index + 1]
            if next_chunk.strip():
                self.prepare_chunk(next_chunk)
                self.preprocessed_chunks.append(next_chunk)
                self.first_chunk_prepared = True
        
    def speed_reading(self):
        while self.current_chunk_index < len(self.preprocessed_chunks) and not self.is_stopped:
            if self.shutdown_event.is_set():  # Check for shutdown event
                break
            if not self.is_paused:
                self.current_chunk = self.preprocessed_chunks[self.current_chunk_index]
                
                chunk = self.current_chunk
                logging.info("Processing chunk %d/%d: %s", self.current_chunk_index + 1, len(self.preprocessed_chunks), chunk)
                if chunk.strip():  # Ensure chunk is not empty
                    words = chunk.split()
                    if self.tts_enabled:
                        logging.info("TTS Speaking: %s", chunk)
                        self.tts_complete_event.clear()  # Clear the completion event
                        tts_thread = threading.Thread(target=self.play_tts_audio, args=(chunk,))
                        tts_thread.start()
                    
                    for word in words:
                        if self.is_paused or self.is_stopped:
                            break
                        self.display_word(word)
                        self.progress.set((self.current_chunk_index / len(self.preprocessed_chunks)) * 100)
                        word_length_factor = (len(word) / 5.0) * 0.75  # Adjust time based on word length with 75% impact
                        time.sleep((60 / self.wpm) * word_length_factor)  # Adjust sleep duration based on WPM and word length
                        
                        # Add pause based on punctuation marks
                        if word.endswith((',', ';')):
                            time.sleep((60 / self.wpm) * .3) # Pause for 0.3 words' worth of time
                        elif word.endswith(('...',)):
                            time.sleep((60 / self.wpm) * 1) # Pause for 1 words' worth of time
                        elif word.endswith(('.', '!', '?')):
                            time.sleep((60 / self.wpm) * 0.75) # Pause for 0.75 words' worth of time
                    self.check_completion()
                    
                    # Add pause based on newline
                    if '\n' in chunk:
                        time.sleep(2.5 * (60 / self.wpm))  # Pause for 2.5 words' worth of time
                    
                self.current_chunk_index += 1
                self.current_chunk = None  # Reset the current chunk
                self.prepare_next_chunk()  # Prepare the next chunk
            else:
                time.sleep(0.1)
        
        if self.current_chunk_index >= len(self.preprocessed_chunks):
            self.stop()
        
    def prepare_chunk(self, chunk):
        # Ensure the text is loaded and ready to be displayed visually
        if chunk.split() and self.word_label.winfo_exists():  # Ensure chunk is not empty and word_label exists
            self.display_word(chunk.split()[0])
        
    def generate_tts_audio(self, chunk):
        if not self.tts_engine:
            logging.error("TTS engine is not initialized.")
            return None
        try:
            output_file = f"temp_chunk_{self.current_chunk_index}.wav"
            self.tts_engine.save_to_file(chunk, output_file)
            self.tts_engine.runAndWait()
            if os.path.exists(output_file):
                return output_file
            else:
                logging.error("Generated file %s does not exist.", output_file)
                return None
        except (pyttsx3.EngineError, RuntimeError, OSError) as e:
            logging.error("An error occurred during TTS generation: %s", e)
            return None
        
    def play_tts_audio(self, chunk):
        with self.tts_playback_lock:
            try:
                audio_file = self.generate_tts_audio(chunk)
                if (audio_file and os.path.exists(audio_file)):
                    wave_obj = sa.WaveObject.from_wave_file(audio_file)
                    play_obj = wave_obj.play()
                    self.tts_playback_event.set()
                    while play_obj.is_playing():
                        if self.tts_stop_event.is_set() or self.shutdown_event.is_set():  # Check for shutdown event
                            play_obj.stop()
                            break
                        if self.is_paused:
                            play_obj.stop()
                            break
                        time.sleep(0.1)
                    self.tts_playback_event.clear()
                    self.tts_complete_event.set()  # Signal that TTS playback is complete
                    os.remove(audio_file)  # Clean up the temp_chunk audio file
                else:
                    logging.error("Generated file %s does not exist.", audio_file)
            except (sa.SimpleaudioError, OSError) as e:
                logging.error("An error occurred during TTS playback: %s", e)
        
    def check_completion(self):
        # Ensure both the visual and audio components have completed
        if self.tts_enabled:
            logging.info("Waiting for TTS playback to complete...")
            while self.tts_playback_event.is_set() or not self.tts_complete_event.is_set():
                time.sleep(0.1)
            logging.info("TTS playback completed.")
        
    def display_word(self, word):
        if not self.word_label.winfo_exists():
            logging.error("Word label does not exist.")
            return
        mid_index = (len(word) // 2) - 1 if len(word) % 2 == 0 else len(word) // 2  # Adjust middle index for even character counts
        self.word_label.config(state=tk.NORMAL)
        self.word_label.delete("1.0", tk.END)
        self.word_label.insert("1.0", word)
        self.word_label.tag_add("center", "1.0", "end")
        self.word_label.tag_add("highlight", f"1.{mid_index}", f"1.{mid_index+1}")
        self.word_label.tag_config("highlight", foreground=self.highlight_color)
        self.word_label.config(state=tk.DISABLED, font=("Helvetica", self.font_size_var.get()))  # Apply font size
        self.word_label.tag_configure("center", justify='center')  # Ensure center justification
        
    def pause(self):
        self.is_paused = True
        self.tts_playback_event.set()
        self.tts_stop_event.set()  # Ensure any ongoing playback is paused
        
    def play(self):
        self.is_paused = False
        self.tts_playback_event.clear()
        self.tts_stop_event.clear()  # Ensure the stop event is cleared when resuming
        
    def stop(self):
        self.is_stopped = True
        self.tts_stop_event.set()
        self.tts_playback_event.set()  # Ensure any ongoing playback is stopped
        self.reading_window.withdraw()  # Hide the reading window
        self.root.deiconify()  # Show the main settings window
        self.settings_frame.pack(pady=20)
        self.tts_stop_event.clear()  # Reset the stop event for future use
        if self.tts_enabled and self.tts_engine:
            self.tts_engine.stop()  # Stop the TTS engine
        self.tts_complete_event.set()  # Ensure the TTS completion event is set

    def change_opacity(self):
        self.reading_window.attributes('-alpha', float(self.opacity_var.get()))
        
    def save_settings(self):
        settings = {
            "wpm": self.wpm_entry.get(),
            "highlight_color": self.color_entry.get(),
            "tts_enabled": self.tts_var.get(),
            "night_mode": self.night_mode_var.get(),
            "opacity": self.opacity_var.get(),
            "tts_engine": self.tts_engine_var.get(),
            "font_size": self.font_size_var.get()
        }
        with open("settings.json", "w", encoding="utf-8") as settings_file:
            json.dump(settings, settings_file)
        logging.info("Settings saved.")

    def load_settings(self):
        try:
            with open("settings.json", "r", encoding="utf-8") as settings_file:
                settings = json.load(settings_file)
                self.wpm_entry.delete(0, tk.END)  # Clear existing content
                self.wpm_entry.insert(0, settings.get("wpm", "500"))
                self.color_entry.delete(0, tk.END)  # Clear existing content
                self.color_entry.insert(0, settings.get("highlight_color", "#42a832"))
                self.tts_var.set(settings.get("tts_enabled", 1))
                self.night_mode_var.set(settings.get("night_mode", 1))
                self.opacity_var.set(settings.get("opacity", 1.0))
                self.tts_engine_var.set(settings.get("tts_engine", "sapi5"))
                self.font_size_var.set(settings.get("font_size", 48))
                self.change_tts_engine(self.tts_engine_var.get())  # Apply TTS engine settings
                self.apply_night_mode()  # Apply night mode settings
                self.change_opacity()  # Apply opacity settings
                self.change_font_size(self.font_size_var.get())  # Apply font size settings
            logging.info("Settings loaded.")
        except FileNotFoundError:
            logging.warning("Settings file not found. Using default settings.")
        except (json.JSONDecodeError, IOError) as e:
            logging.error("Failed to load settings: %s", e)

    def on_closing_reading_window(self):
        self.stop()  # Stop playback
        self.reading_window.withdraw()  # Hide the reading window
        self.root.deiconify()  # Show the main settings window

    def on_closing(self):
        self.shutdown_event.set()  # Set shutdown event
        self.is_stopped = True
        self.tts_stop_event.set()
        self.tts_playback_event.set()  # Ensure any ongoing playback is stopped
        if self.tts_enabled and self.tts_engine:
            self.tts_engine.stop()  # Stop the TTS engine
        self.tts_complete_event.set()  # Ensure the TTS completion event is set
        self.save_settings()  # Save settings when the window is closed
        self.root.destroy()

    def on_progress_press(self, event=None):
        self.is_paused = True  # Pause when the user clicks the progress bar

    def on_progress_release(self, event=None):
        if self.is_stopped:
            return
        new_index = int((self.progress.get() / 100) * len(self.chunks))
        if new_index != self.current_chunk_index:
            self.current_chunk_index = new_index
            if self.current_chunk_index < len(self.chunks) and self.chunks[self.current_chunk_index].strip():
                self.display_word(self.chunks[self.current_chunk_index].split()[0])
                if self.tts_enabled:
                    self.tts_stop_event.set()  # Stop any ongoing TTS playback
                    self.tts_complete_event.set()  # Ensure the TTS completion event is set
                    self.tts_playback_event.clear()  # Clear the playback event
                    self.generate_tts_audio(self.chunks[self.current_chunk_index])  # Generate TTS for the new chunk
                    if self.tts_complete_event.is_set() and not self.tts_playback_event.is_set():  # Ensure the TTS file is generated and not already playing
                        with self.tts_playback_lock:  # Ensure only one playback thread is started
                            tts_thread = threading.Thread(target=self.play_tts_audio)
                            tts_thread.start()
                self.play()  # Resume playback
            else:
                logging.error("Chunk index out of range or chunk is empty.")

    def initialize_tts_engine(self):
        try:
            self.tts_engine = pyttsx3.init(self.tts_engine_var.get())
            self.tts_engine.setProperty('rate', 500)  # Set default rate
        except (pyttsx3.EngineError, RuntimeError) as e:
            logging.error("Failed to initialize TTS engine: %s", e)
            self.tts_engine = None  # Set to None if initialization fails

    def change_tts_engine(self, value, _event=None):
        self.tts_engine_var.set(value)
        self.initialize_tts_engine()

    def change_font_size(self, value):
        self.word_label.config(font=("Helvetica", int(value)))

if __name__ == "__main__":
    root = tk.Tk()
    app = SpeedReader(root)
    root.mainloop()