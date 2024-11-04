import pyttsx3
import logging
import os
import simpleaudio as sa

# Configure logging
logging.basicConfig(level=logging.INFO)

def list_audio_devices(engine):
    devices = engine.getProperty('voices')
    logging.info("Available audio devices:")
    for device in devices:
        logging.info(f" - {device.name} ({device.id})")

def test_tts():
    try:
        engine = pyttsx3.init()
        logging.info("TTS engine initialized.")
        
        list_audio_devices(engine)
        
        engine.setProperty('rate', 150)  # Set speech rate
        logging.info("Speech rate set to 150.")
        
        engine.setProperty('volume', 1)  # Set volume level (0.0 to 1.0)
        logging.info("Volume level set to 1.")
        
        # Save the TTS output to a file
        output_file = "test.wav"
        engine.save_to_file("Hello, this is a test of the text-to-speech functionality.", output_file)
        logging.info("Text-to-speech command issued.")
        
        engine.runAndWait()
        logging.info("Engine run and wait completed.")
        
        # Check if the engine is still busy
        if engine.isBusy():
            logging.info("Engine is still busy after runAndWait.")
        else:
            logging.info("Engine is not busy after runAndWait.")
        
        # Play the generated file
        if os.path.exists(output_file):
            logging.info(f"Playing the generated file: {output_file}")
            wave_obj = sa.WaveObject.from_wave_file(output_file)
            play_obj = wave_obj.play()
            play_obj.wait_done()
        else:
            logging.error(f"Generated file {output_file} does not exist.")
        
    except Exception as e:
        logging.error(f"An error occurred: {e}")

if __name__ == "__main__":
    test_tts()
