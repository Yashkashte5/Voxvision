import pyttsx3
import subprocess
import os
import psutil
from PIL import ImageGrab
import speech_recognition as sr


engine = pyttsx3.init()

def speak(text):
    """Speak the given text using text-to-speech."""
    engine.say(text)
    engine.runAndWait()

def open_application(app_name):
    """Open the specified application."""
    apps = {
        "notepad": "notepad.exe",
        "calculator": "calc.exe",
        "word": "winword.exe",  
        "excel": "excel.exe",    
        "powerpoint": "powerpnt.exe",  
        "browser": "chrome.exe",  
        "firefox": "firefox.exe",  
        "file explorer": "explorer.exe",  
        "edge": "msedge.exe",  
        "music": "wmplayer.exe",  
        "vlc": "vlc.exe",  
        "zoom": "zoom.exe",  
        "teams": "Teams.exe",  
        "discord": "Discord.exe",  
        "steam": "steam.exe",  
        "visual studio": "devenv.exe",  
        "eclipse": "eclipse.exe",  
        "pycharm": "pycharm64.exe",  
        "git bash": "git-bash.exe",  
        "command prompt": "cmd.exe",  
        "powershell": "powershell.exe",  
        "notepad++": "notepad++.exe",  
        "adobe reader": "AcroRd32.exe",  
        "photoshop": "Photoshop.exe",  
        "illustrator": "Illustrator.exe",  
        "microsoft access": "MSACCESS.EXE",  
        "outlook": "OUTLOOK.EXE",  
        "filezilla": "filezilla.exe",  
        "git": "git.exe",  
        "winrar": "WinRAR.exe",
        "photos": "start shell:AppsFolder\\Microsoft.Windows.Photos_8wekyb3d8bbwe!App"  # Fixed Photos app
    }

    if app_name in apps:
        try:
            subprocess.Popen(apps[app_name], shell=True)
            speak(f"Opening {app_name}.")
        except Exception as e:
            speak(f"Sorry, I could not open {app_name}. Error: {str(e)}")
    else:
        speak(f"Sorry, I cannot find {app_name}. Try opening a different application.")

def close_application(app_name):
    """Close the specified application."""
    app_processes = {
        "notepad": "notepad.exe",
        "calculator": "calc.exe",
        "word": "winword.exe",  
        "excel": "excel.exe",    
        "powerpoint": "powerpnt.exe",  
        "browser": "chrome.exe",  
        "firefox": "firefox.exe",  
        "file explorer": "explorer.exe",  
        "edge": "msedge.exe",  
        "music": "wmplayer.exe",  
        "vlc": "vlc.exe",  
        "zoom": "zoom.exe",  
        "teams": "Teams.exe",  
        "discord": "Discord.exe",  
        "steam": "steam.exe",  
        "visual studio": "devenv.exe",  
        "eclipse": "eclipse.exe",  
        "pycharm": "pycharm64.exe",  
        "git bash": "git-bash.exe",  
        "command prompt": "cmd.exe",  
        "powershell": "powershell.exe",  
        "notepad++": "notepad++.exe",  
        "adobe reader": "AcroRd32.exe",  
        "photoshop": "Photoshop.exe",  
        "illustrator": "Illustrator.exe",  
        "microsoft access": "MSACCESS.EXE",  
        "outlook": "OUTLOOK.EXE",  
        "filezilla": "filezilla.exe",  
        "git": "git.exe",  
        "winrar": "WinRAR.exe"
    }

    if app_name in app_processes:
        if is_application_running(app_processes[app_name]):
            speak(f"Are you sure you want to close {app_name}? Please say yes or no.")
            confirmation = listen_command()
            if confirmation and "yes" in confirmation.lower():
                try:
                    subprocess.run(["taskkill", "/IM", app_processes[app_name], "/F"], check=True)
                    speak(f"Closed {app_name}.")
                except Exception as e:
                    speak(f"Failed to close {app_name}: {str(e)}")
            else:
                speak(f"Did not close {app_name}.")
        else:
            speak(f"{app_name} is not currently running.")
    else:
        speak(f"Sorry, I cannot close {app_name}.")

def is_application_running(app_name):
    """Check if the specified application is currently running."""
    for process in psutil.process_iter(attrs=['pid', 'name']):
        if process.info['name'].lower() == app_name.lower():
            return True
    return False

def take_screenshot():
    """Take a screenshot and save it to the screenshots folder."""
    speak("What would you like to name the screenshot?")
    
    screenshot_name = listen_command()
    
    if screenshot_name is None:
        speak("Could not understand screenshot name. Please try again.")
        return
    
    screenshot_dir = "screenshots"
    os.makedirs(screenshot_dir, exist_ok=True)

    base_filename = screenshot_name
    counter = 1
    while os.path.exists(os.path.join(screenshot_dir, f"{screenshot_name}.png")):
        screenshot_name = f"{base_filename}_{counter}"
        counter += 1
    
    screenshot = ImageGrab.grab()
    screenshot.save(os.path.join(screenshot_dir, f"{screenshot_name}.png"))
    speak(f"Screenshot saved as {screenshot_name}.png in the screenshots folder.")

def listen_command():
    """Listen for voice commands and return the recognized text."""
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        speak("Listening for your command...")
        try:
            audio = recognizer.listen(source, timeout=5)
            command = recognizer.recognize_google(audio)
            return command.lower()
        except sr.UnknownValueError:
            speak("Sorry, I did not catch that. Please try again.")
            return None
        except sr.RequestError as e:
            speak(f"Could not request results. {str(e)}")
            return None
        except Exception:
            speak("There was an issue with the microphone.")
            return None

def main():
    """Main function to run the application control module."""
    speak("Welcome! What would you like to do?")
    while True:
        command = listen_command()
        if command:
            if "open" in command:
                open_application(command.replace("open ", ""))
            elif "close" in command:
                close_application(command.replace("close ", ""))
            elif "screenshot" in command:
                take_screenshot()
            elif "exit" in command:
                speak("Exiting. Have a great day!")
                break
            else:
                speak("I didn't understand that. Please try again.")

if __name__ == "__main__":
    main()
