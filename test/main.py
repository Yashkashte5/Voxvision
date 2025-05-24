import os
import sys
import time
from gmail_voice_assistant import VoiceGmailAssistant
from extra import VoiceAssistantExtended

def speak(text):
    """Basic text-to-speech function for the menu"""
    print(f"System: {text}")
    # You could use pyttsx3 here if you want voice in the menu too

def listen():
    """Basic voice input function for the menu"""
    import speech_recognition as sr
    r = sr.Recognizer()
    with sr.Microphone() as source:
        print("Listening...")
        audio = r.listen(source)
        try:
            text = r.recognize_google(audio)
            print(f"You said: {text}")
            return text.lower()
        except:
            return ""

def show_menu():
    """Display/announce the available modes"""
    menu_text = """
    Please choose an assistant mode:
    1. Gmail Assistant (focused on email tasks)
    2. Extended Assistant (with all features)
    3. Exit
    """
    print(menu_text)
    speak("Please choose an assistant mode. Say 'Gmail', 'Extended', or 'Exit'")

def get_user_choice():
    """Get user's mode selection"""
    while True:
        choice = listen()
        if not choice:
            speak("I didn't hear your choice. Please try again.")
            continue
        
        if 'gmail' in choice or '1' in choice or 'mail' in choice:
            return 'gmail'
        elif 'extend' in choice or '2' in choice or 'all' in choice:
            return 'extended'
        elif 'exit' in choice or '3' in choice or 'quit' in choice:
            return 'exit'
        else:
            speak("I didn't understand. Please say 'Gmail', 'Extended', or 'Exit'")

def run_gmail_assistant():
    """Run the Gmail-focused assistant"""
    speak("Starting Gmail Assistant. You can say commands like 'read emails' or 'send email'")
    assistant = VoiceGmailAssistant()
    try:
        assistant.authenticate()
        assistant.main_menu()
    except Exception as e:
        print(f"Error in Gmail Assistant: {e}")
        speak("There was an error with the Gmail Assistant. Returning to main menu.")

def run_extended_assistant():
    """Run the extended features assistant"""
    speak("Starting Extended Assistant with all features.")
    assistant = VoiceAssistantExtended()
    try:
        assistant.main()
    except Exception as e:
        print(f"Error in Extended Assistant: {e}")
        speak("There was an error with the Extended Assistant. Returning to main menu.")

def main():
    """Main controller function"""
    speak("Welcome to the Voice Assistant Controller!")
    
    while True:
        show_menu()
        choice = get_user_choice()
        
        if choice == 'gmail':
            run_gmail_assistant()
        elif choice == 'extended':
            run_extended_assistant()
        elif choice == 'exit':
            speak("Goodbye!")
            sys.exit(0)
        
        time.sleep(1)  # Brief pause before showing menu again

if __name__ == "__main__":
    # Check if required modules are installed
    try:
        import speech_recognition
        import pyttsx3
    except ImportError:
        print("Please install required packages first:")
        print("pip install speechrecognition pyttsx3")
        sys.exit(1)
    
    # Verify both assistant files exist
    if not os.path.exists("gmail_voice_assistant.py") or not os.path.exists("extra.py"):
        print("Error: Both gmail_voice_assistant.py and extra.py must be in the same directory")
        sys.exit(1)
    
    main()