import pyttsx3
import subprocess
import os
import speech_recognition as sr
import psutil
import datetime
import pyautogui
import webbrowser
import sqlite3
import torch
from vosk import Model, KaldiRecognizer
from transformers import DistilBertTokenizer, DistilBertForSequenceClassification
import json
import sys

# Initialize Text-to-Speech engine
engine = pyttsx3.init()

def speak(text):
    engine.say(text)
    engine.runAndWait()

# Load Speech Recognition Model
vosk_model = Model("vosk-model-small-en-us-0.15")
recognizer = KaldiRecognizer(vosk_model, 16000)
recognizer.SetWords(True)

# Load DistilBERT for Intent Recognition
device = "cuda" if torch.cuda.is_available() else "cpu"
tokenizer = DistilBertTokenizer.from_pretrained("distilbert-base-uncased")
model = DistilBertForSequenceClassification.from_pretrained("distilbert-base-uncased", num_labels=5).to(device)

def classify_intent(text):
    inputs = tokenizer(text, return_tensors="pt", truncation=True, padding=True).to(device)
    with torch.no_grad():
        outputs = model(**inputs)
    predicted_label = torch.argmax(outputs.logits, dim=1).item()
    return predicted_label

# Speech Recognition Function
def listen_command():
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        speak("I'm listening...")
        recognizer.adjust_for_ambient_noise(source)
        audio = recognizer.listen(source)
    
    try:
        text = recognizer.recognize_vosk(audio)
        text_json = json.loads(text)
        command = text_json.get("text", "").strip().lower()
        print(f"Recognized: {command}")
        return command if command else None
    except Exception as e:
        speak("Sorry, I couldn't understand that.")
        return None

# SQLite Database for User Behavior Tracking
conn = sqlite3.connect("user_behavior.db")
cursor = conn.cursor()
cursor.execute("CREATE TABLE IF NOT EXISTS behaviors (command TEXT, timestamp TEXT)")
conn.commit()

def log_behavior(command):
    timestamp = datetime.datetime.now().isoformat()
    cursor.execute("INSERT INTO behaviors (command, timestamp) VALUES (?, ?)", (command, timestamp))
    conn.commit()

# Core Desktop Functions
def open_application(app_name):
    try:
        subprocess.Popen(app_name)
        speak(f"Opening {app_name}.")
    except Exception as e:
        speak(f"Sorry, I couldn't open {app_name}. Error: {str(e)}")

def close_application(app_name):
    try:
        os.system(f'taskkill /IM {app_name}.exe /F')
        speak(f"Closed {app_name}.")
    except Exception as e:
        speak(f"Sorry, I couldn't close {app_name}. Error: {str(e)}")

def take_screenshot(location="current directory"):
    screenshot = pyautogui.screenshot()
    location_path = os.path.expanduser("~/Desktop/screenshot.png") if location.lower() == "desktop" else os.path.join(os.getcwd(), "screenshot.png")  
    screenshot.save(location_path)
    speak(f"Screenshot taken and saved at {location_path}.")

def get_system_info():
    cpu_usage = psutil.cpu_percent()
    ram = psutil.virtual_memory().available / (1024 ** 2)
    speak(f"CPU usage is {cpu_usage} percent. Available RAM is {ram:.2f} MB.")

def execute_command(command):
    log_behavior(command)
    intent = classify_intent(command)
    
    if "open" in command:
        app_name = command.split("open")[-1].strip()
        open_application(app_name)
    elif "close" in command:
        app_name = command.split("close")[-1].strip()
        close_application(app_name)
    elif "screenshot" in command:
        take_screenshot()
    elif "system info" in command:
        get_system_info()
    elif "open website" in command:
        website = command.replace("open website", "").strip()
        webbrowser.open(f"http://{website}")
        speak(f"Opening {website}.")
    else:
        speak("Sorry, I didn't understand that command.")

def main(user):
    speak(f"Welcome to your AI-powered assistant, {user}! What would you like to do?")
    while True:
        command = listen_command()
        if command:
            execute_command(command)

if __name__ == "__main__":
    user = input("Enter authenticated user: ")
    main(user)
