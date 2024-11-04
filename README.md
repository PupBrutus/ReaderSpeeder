# ReaderSpeeder

ReaderSpeeder is a Python application that helps you read text files at a faster pace by displaying words one at a time at a specified speed. It also includes an optional Text-to-Speech (TTS) feature.

## Purpose

An offline speed reader application with local TTS and a comfortable UI.

## Features

- Adjustable words per minute (WPM) setting
- Load text files for reading
- Optional Text-to-Speech (TTS) support
- Pause, play, and stop controls
- Night mode for comfortable reading in low light
- Adjustable window opacity
- Support for multiple TTS engines (sapi5, nsss, espeak)
- Save and load user settings
- Progress bar with skip function to navigate through the text

## Requirements

- Python 3.x
- `tkinter` for the graphical user interface
- `pyttsx3` for Text-to-Speech functionality
- `simpleaudio` for audio playback

## Installation

### From Releases

1. Go to the [Releases](https://github.com/yourusername/ReaderSpeeder/releases) page.
2. Download the latest package for Windows.
3. Run the downloaded executable to start the application.

### From Source

1. Clone the repository or download the source code.
2. Install the required dependencies using `pip`:

    ```sh
    pip install -r requirements.txt
    ```

## Usage

### Windows Release

1. Download and run the executable from the [Releases](https://github.com/yourusername/ReaderSpeeder/releases) page.
2. Use the graphical interface to load a text file, adjust the WPM setting, and start speed reading.

### From Source

1. Run the `main.py` script:

    ```sh
    python main.py
    ```

2. Use the graphical interface to load a text file, adjust the WPM setting, and start speed reading.

## How It Works

### Text Chunking

The text is split into chunks based on sentence punctuation and newlines using regular expressions. This allows the application to display and process the text in manageable segments. Specifically, the text is split by terminal punctuation marks such as periods, exclamation points, and question marks.

For each chunk, if Text-to-Speech (TTS) is enabled, the application generates an audio file using the selected TTS engine. This audio file is then played back in sync with the visual display of the text. Once the playback is complete, the temporary audio file is cleaned up to free up space.

### Character Highlighting

The application highlights the middle character of each word to help guide the reader's focus. For words with an even number of characters, the highlight is applied to the character just before the middle.

### Punctuation and New-Line Delays

To provide a more natural reading experience, the application introduces delays based on punctuation and new-lines:
- Commas and semicolons add a short pause (0.3 words' worth of time).
- Ellipses add a longer pause (1 word's worth of time).
- Periods, exclamation points, and question marks add a moderate pause (0.75 words' worth of time).
- New-lines add a significant pause to simulate the end of a paragraph (2.5 words' worth of time).

## Default Text

The `default.txt` file contains a sample from "Frankenstein; Or, The Modern Prometheus" by Mary Wollstonecraft Shelley. This text is sourced from the Project Gutenberg library (gutenberg.org).

## License

This project is licensed under the MIT License.
