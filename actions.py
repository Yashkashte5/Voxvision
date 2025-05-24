import pyttsx3
import gmail_funcs
import desktop_funcs
import speech_recognition as sr

# Initialize the text-to-speech engine
engine = pyttsx3.init()

def speak(text):
    engine.say(text)
    engine.runAndWait()

def listen():
    # Initialize the recognizer
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        print("Listening...")
        recognizer.adjust_for_ambient_noise(source)  # Adjust for ambient noise
        try:
            audio = recognizer.listen(source)  # Listen for input
            command = recognizer.recognize_google(audio)  # Recognize speech using Google Web Speech API
            print(f"You said: {command}")  # For debugging
            return command.lower()
        except sr.UnknownValueError:
            speak("Sorry, I did not understand that.")
            return ""
        except sr.RequestError:
            speak("Could not request results from the speech recognition service.")
            return ""
        except KeyboardInterrupt:
            speak("Listening interrupted. Please try again.")
            return ""

def main(user):
    speak(f"Hello, {user}. What would you like to do today?")
    speak("You can say 'Gmail functions' to check your inbox or send an email.")
    speak("You can say 'Desktop functions' to open applications.")
    speak("You can also say 'exit' to quit the application.")

    while True:
        command = listen()  # Get the command from voice input

        if "gmail functions" in command:
            speak("Proceeding to Gmail functions...")
            gmail_funcs.main(user)  # Ensure this function only takes user as a parameter
            
        elif "desktop functions" in command:
            speak("Proceeding to Desktop functions...")
            desktop_funcs.main(user)  # Ensure this function only takes user as a parameter
            
        elif "exit" in command:
            speak("Exiting the application. Goodbye!")
            break
            
        else:
            speak("I didn't understand that. Please try again.")

if __name__ == "__main__":
    user = input("Enter authenticated user (for testing purposes): ")  # Remove this line in the actual implementation
    main(user)
