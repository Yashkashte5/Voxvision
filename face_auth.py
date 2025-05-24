import cv2
import os
import pyttsx3
import numpy as np
from deepface import DeepFace
import actions  # Import the actions module

# Initialize the text-to-speech engine
engine = pyttsx3.init()

def speak(text):
    engine.say(text)
    engine.runAndWait()

def load_embeddings():
    """Load embeddings for registered users from files."""
    embeddings = {}
    for file in os.listdir('registered_users'):
        if file.endswith('.npy'):  # Assuming embeddings are stored as .npy files
            user_name = file[:-4]  # Remove '.npy' extension
            embeddings[user_name] = np.load(os.path.join('registered_users', file))
    return embeddings

def authenticate_user(embeddings):
    cap = cv2.VideoCapture(0)
    speak("Authenticating. Please look at the camera...")

    while True:
        ret, frame = cap.read()
        if not ret:
            speak("Failed to grab frame.")
            break
        
        cv2.imshow('Authenticate - Please look at the camera', frame)

        # Convert the frame to RGB and compute embedding
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        current_embedding = DeepFace.represent(rgb_frame, model_name="VGG-Face")[0]["embedding"]

        for user, stored_embedding in embeddings.items():
            # Calculate similarity
            similarity = np.dot(current_embedding, stored_embedding) / (np.linalg.norm(current_embedding) * np.linalg.norm(stored_embedding))
            
            # Define a threshold for similarity (adjust based on testing)
            if similarity > 0.5:  # Example threshold, you might need to tune this
                success_message = f"Authentication successful for {user}."
                speak(success_message)
                print(success_message)

                # Welcome message
                welcome_message = f"Welcome, {user}! You are now logged in."
                speak(welcome_message)

                # Redirect to actions.py
                actions.main(user)  # Call the main function from actions.py
                cap.release()
                cv2.destroyAllWindows()
                return user  # Optionally return the authenticated user

        speak("Authentication failed. Please try again.")
        if cv2.waitKey(1000) & 0xFF == ord('q'):
            speak("Authentication process ended.")
            break

    cap.release()
    cv2.destroyAllWindows()
    return None  # Return None if authentication fails

if __name__ == "__main__":
    embeddings = load_embeddings()  # Load embeddings at the start
    if embeddings:
        authenticate_user(embeddings)  # Pass embeddings to the authenticate function
    else:
        speak("No embeddings found.")
