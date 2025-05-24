
import os
import io
import speech_recognition as sr
import pyttsx3
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
import base64
import json

# Encryption settings
SECRET_KEY = b'\x99\xe9\xa0\xebGr\xb7\xdd\xcb\x8f\xd1\x89b\x969Gd/H\xd5\xef\x81\xc5yxX8Q*k^d'
IV = b'\x83\x14]\xf1\x8f\xda\xa4\x98\xcf\xf0zA\x88H\xfe\xac'

class SecureCredentials:
    @staticmethod
    def encrypt(data: str) -> str:
        cipher = AES.new(SECRET_KEY, AES.MODE_CBC, IV)
        ct_bytes = cipher.encrypt(pad(data.encode(), AES.block_size))
        return base64.b64encode(ct_bytes).decode('utf-8')

    @staticmethod
    def decrypt(encrypted_data: str) -> str:
        ct = base64.b64decode(encrypted_data)
        cipher = AES.new(SECRET_KEY, AES.MODE_CBC, IV)
        pt = unpad(cipher.decrypt(ct), AES.block_size)
        return pt.decode('utf-8')

    @staticmethod
    def save_credentials(creds: Credentials, filename: str = 'encrypted_creds.bin'):
        creds_data = {
            'token': creds.token,
            'refresh_token': creds.refresh_token,
            'token_uri': creds.token_uri,
            'client_id': creds.client_id,
            'client_secret': creds.client_secret,
            'scopes': creds.scopes
        }
        encrypted = SecureCredentials.encrypt(json.dumps(creds_data))
        with open(filename, 'wb') as f:
            f.write(encrypted.encode())

    @staticmethod
    def load_credentials(filename: str = 'encrypted_creds.bin') -> Credentials:
        with open(filename, 'rb') as f:
            encrypted = f.read().decode()
        decrypted = json.loads(SecureCredentials.decrypt(encrypted))
        return Credentials.from_authorized_user_info(decrypted)

class VoiceGmailAssistant:
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.engine = pyttsx3.init()
        self.service = None
        self.SCOPES = ['https://mail.google.com/']
        
        # Voice settings
        self.engine.setProperty('rate', 150)
        self.engine.setProperty('volume', 1.0)
        
    def speak(self, text):
        """Convert text to speech"""
        self.engine.say(text)
        self.engine.runAndWait()
        
    def listen(self):
        """Listen to microphone and convert speech to text"""
        with sr.Microphone() as source:
            self.recognizer.adjust_for_ambient_noise(source)
            self.speak("I'm listening")
            audio = self.recognizer.listen(source)
            
            try:
                text = self.recognizer.recognize_google(audio)
                self.speak(f"You said: {text}")
                return text.lower()
            except sr.UnknownValueError:
                self.speak("Sorry, I didn't catch that. Please try again.")
                return ""
            except sr.RequestError:
                self.speak("Sorry, my speech service is down. Please try again later.")
                return ""
    
    def authenticate(self):
        """Authenticate with Gmail API using OAuth 2.0"""
        creds = None
        encrypted_creds_file = 'encrypted_creds.bin'
        
        if os.path.exists(encrypted_creds_file):
            try:
                creds = SecureCredentials.load_credentials(encrypted_creds_file)
            except Exception as e:
                self.speak("Authentication error. Starting fresh authentication.")
                os.remove(encrypted_creds_file)
                
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    'credentials.json', self.SCOPES)
                self.speak("Please authenticate via the browser. I'll wait.")
                creds = flow.run_local_server(port=0)
            
            SecureCredentials.save_credentials(creds, encrypted_creds_file)
        
        self.service = build('gmail', 'v1', credentials=creds)
        self.speak("Successfully connected to Gmail")
    
    def get_emails(self, max_results=5):
        """Get the latest emails"""
        if not self.service:
            self.speak("Not authenticated. Please authenticate first.")
            return
        
        results = self.service.users().messages().list(
            userId='me', maxResults=max_results).execute()
        messages = results.get('messages', [])
        
        if not messages:
            self.speak("No messages found.")
        else:
            self.speak(f"Here are your {len(messages)} most recent emails:")
            for message in messages:
                msg = self.service.users().messages().get(
                    userId='me', id=message['id']).execute()
                headers = msg['payload']['headers']
                subject = next(h['value'] for h in headers if h['name'] == 'Subject')
                sender = next(h['value'] for h in headers if h['name'] == 'From')
                self.speak(f"From {sender}. Subject: {subject}")
    
    def send_email(self):
        """Compose and send an email by voice"""
        if not self.service:
            self.speak("Not authenticated. Please authenticate first.")
            return
            
        self.speak("Who should I send the email to?")
        to = self.listen()
        
        self.speak("What's the subject?")
        subject = self.listen()
        
        self.speak("What should the message say?")
        body = self.listen()
        
        self.speak(f"Should I send this email to {to} with subject {subject} and message {body}? Say yes to confirm.")
        confirmation = self.listen()
        
        if 'yes' in confirmation:
            message = self._create_message(to, 'me', subject, body)
            self._send_message(message)
            self.speak("Email sent successfully.")
        else:
            self.speak("Email cancelled.")
    
    def _create_message(self, to, sender, subject, message_text):
        """Create a message for an email"""
        message = {
            'raw': base64.urlsafe_b64encode(
                f"From: {sender}\nTo: {to}\nSubject: {subject}\n\n{message_text}"
                .encode()
            ).decode()
        }
        return message
    
    def _send_message(self, message):
        """Send an email message"""
        self.service.users().messages().send(
            userId='me', body=message).execute()
    
    def main_menu(self):
        """Main voice interaction loop"""
        self.speak("Welcome to Voice Controlled Gmail Assistant")
        
        while True:
            self.speak("What would you like to do? You can say: read emails, send email, or exit.")
            command = self.listen()
            
            if not command:
                continue
                
            if 'read' in command or 'email' in command:
                self.get_emails()
            elif 'send' in command:
                self.send_email()
            elif 'exit' in command or 'quit' in command:
                self.speak("Goodbye!")
                break
            else:
                self.speak("I didn't understand that command. Please try again.")

if __name__ == '__main__':
    # First time setup: Get credentials.json from Google Cloud Console
    # Enable Gmail API and create OAuth 2.0 credentials
    
    assistant = VoiceGmailAssistant()
    assistant.authenticate()
    assistant.main_menu()