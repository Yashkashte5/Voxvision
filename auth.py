import cv2
import os
import pyttsx3
from deepface import DeepFace
import logging


logging.basicConfig(filename='auth_attempts.log', level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')


engine = pyttsx3.init()

def speak(text):
    """Convert text to speech."""
    engine.say(text)
    engine.runAndWait()

def authenticate_user():
    """Authenticate the user based on the detected face."""
    cap = cv2.VideoCapture(0)
    speak("Authenticating. Please look at the camera...")

    registered_users = [f[:-4] for f in os.listdir('registered_users') if f.endswith('.jpg')]  

    if not registered_users:
        speak("No registered users found.")
        cap.release()
        cv2.destroyAllWindows()
        return False

    retry_count = 3  

    while retry_count > 0:
        ret, frame = cap.read()
        if not ret:
            speak("Failed to grab frame.")
            break
        
        cv2.imshow('Authenticate - Please look at the camera', frame)

        
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        
        for user in registered_users:
            registered_image_path = f'registered_users/{user}.jpg'
            if os.path.exists(registered_image_path):
                try:
                    
                    result = DeepFace.verify(rgb_frame, registered_image_path, model_name="VGG-Face")
                    if result["verified"]:
                        success_message = f"Authentication successful for {user}."
                        speak(success_message)
                        logging.info(success_message)  
                        print(success_message)  
                        cap.release()
                        cv2.destroyAllWindows()
                        return user  
                except Exception as e:
                    logging.error(f"Error during face verification: {str(e)}")
                    speak("Face could not be detected. Please ensure you are facing the camera clearly.")
                    break  

        retry_count -= 1
        speak(f"Authentication failed. You have {retry_count} attempts remaining.")
        logging.warning(f"Authentication failed. Attempts remaining: {retry_count}")  

        if retry_count == 0:
            speak("Authentication failed after multiple attempts. Exiting.")
            logging.error("Authentication failed after multiple attempts.")  
            cap.release()
            cv2.destroyAllWindows()
            return False  

        
        cv2.waitKey(1000)

    cap.release()
    cv2.destroyAllWindows()
    return False  

if __name__ == "__main__":
    authenticate_user()
