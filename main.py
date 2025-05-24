import auth
import actions  
import speech
import os
import Register  

def main():
    """Main function to run the application."""
    
    
    user = auth.authenticate_user()  

    if not user:  
        speech.speak("Face authentication failed. Would you like to register a new face or retry?")
        response = speech.listen()  
        
        if "register" in response.lower():  
            speech.speak("Please provide your name for registration.")
            user_name = speech.listen()  
            if user_name:  
                speech.speak(f"Redirecting to registration for {user_name}.")
                Register.register_user(user_name)  
                speech.speak(f"Registration successful for {user_name}. Please proceed with authentication.")
                
                user = auth.authenticate_user()
                if user:
                    speech.speak(f"Authentication successful for {user}. Proceeding to actions.")
                else:
                    speech.speak("Authentication failed again. Please try again later.")
                    return
            else:
                speech.speak("No name provided. Exiting application.")
                return
        elif "retry" in response.lower():  
            speech.speak("Retrying authentication...")
            return main()  
        else:
            speech.speak("You chose neither to register nor retry. Please try again later.")
            return

    
    speech.speak(f"Face authentication successful! Proceeding to actions, {user}.")
    while True:
        actions.main(user)  

if __name__ == '__main__':
    main()
