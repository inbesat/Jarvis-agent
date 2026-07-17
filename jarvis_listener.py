import openwakeword
from openwakeword.model import Model
import sounddevice as sd
import pyautogui

# Load the "jarvis" model
oww_model = Model(wakeword_models=["jarvis"], inference_framework="onnx")

print("Jarvis is listening for your command...")

def callback(indata, frames, time, status):
    # indata is the audio buffer, frames is the number of frames
    # Flatten the input data to a 1D array as expected by the model
    audio_data = indata.flatten()
    
    # Process audio stream
    prediction = oww_model.predict(audio_data)
    
    # Access the score for "jarvis"
    if prediction.get("jarvis", 0) > 0.5:
        print("Jarvis detected! Waking up...")
        pyautogui.hotkey('alt', 'space')
        
# Set blocksize to 1280 to match the model's input requirements
with sd.InputStream(callback=callback, channels=1, samplerate=16000, blocksize=1280):
    while True:
        sd.sleep(100)