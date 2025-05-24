import os
import re
import json
import base64
import pickle
import logging
import time
import numpy as np
from typing import Dict, List, Optional, Tuple
from email.mime.text import MIMEText

import pyttsx3
import pyaudio
import whisper
import torch
from transformers import pipeline
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from bs4 import BeautifulSoup
from cryptography.fernet import Fernet
from fuzzywuzzy import process

# Configuration
SCOPES = [
    'https://www.googleapis.com/auth/gmail.send',
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/contacts.readonly'
]
DOWNLOAD_DIRECTORY = "downloads"
HARMFUL_EXTENSIONS = {'.exe', '.bat', '.cmd', '.msi', '.js', '.vbs', '.ps1'}
MAX_EMAIL_LENGTH = 1000  # Characters to read for long emails
MAX_ATTACHMENT_SIZE = 10 * 1024 * 1024  # 10MB
NOISE_THRESHOLD = 500  # Threshold for noise gate
SILENCE_THRESHOLD = 0.01  # Threshold for silence detection
SAMPLE_RATE = 16000
CHUNK_SIZE = 4096
RECORD_TIMEOUT = 5  # seconds

# Initialize logging
logging.basicConfig(
    filename='gmail_operations.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Initialize speech engine
engine = pyttsx3.init()
engine.setProperty('rate', 150)  # Adjust speech rate

# Initialize encryption
KEY = Fernet.generate_key()
cipher_suite = Fernet(KEY)


class GmailVoiceAssistant:
    def __init__(self):
        self.audio_interface = pyaudio.PyAudio()
        self.audio_stream = None
        self.whisper_model = None
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        # Initialize AI models
        self.initialize_models()
        self.load_nlp_models()

    def load_nlp_models(self):
        """Load NLP models for email summarization and generation."""
        try:
            # Initialize the summarizer model
            self.summarizer = pipeline(
                "summarization",
                model="facebook/bart-large-cnn",
                truncation=True
            )
            
            # Initialize the email generation model
            self.email_generator = pipeline(
                "text-generation",
                model="gpt2",
                truncation=True
            )
            
            logging.info("NLP models loaded successfully")
        except Exception as e:
            logging.error(f"Failed to load NLP models: {e}")
            self.summarizer = None
            self.email_generator = None

    def initialize_models(self):
        """Initialize speech recognition models."""
        try:
            # Load Whisper model (medium size for good balance of speed/accuracy)
            self.whisper_model = whisper.load_model("medium", device=self.device)
            logging.info("Whisper model loaded successfully")
        except Exception as e:
            logging.error(f"Model initialization failed: {e}")
            raise

    def speak(self, text: str) -> None:
        """Convert text to speech with error handling."""
        try:
            if not text:
                return
                
            # Clean up text for speech
            clean_text = re.sub(r'http\S+|www\S+|https\S+', '', text, flags=re.MULTILINE)
            clean_text = clean_text.replace('\n', ' ')
            
            engine.say(clean_text)
            engine.runAndWait()
        except Exception as e:
            logging.error(f"Error in speech synthesis: {e}")

    def setup_audio_stream(self):
        """Set up high-quality audio input stream."""
        try:
            device_index = self.get_best_microphone()
            
            self.audio_stream = self.audio_interface.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=SAMPLE_RATE,
                input=True,
                frames_per_buffer=CHUNK_SIZE,
                input_device_index=device_index
            )
            return True
        except Exception as e:
            logging.error(f"Audio stream setup failed: {e}")
            return False
            
    def get_best_microphone(self):
        """Select the best available microphone."""
        try:
            device_index = None
            max_channels = 0
            info = self.audio_interface.get_host_api_info_by_index(0)
            
            for i in range(info.get('deviceCount')):
                device = self.audio_interface.get_device_info_by_host_api_device_index(0, i)
                if device.get('maxInputChannels') > max_channels:
                    max_channels = device.get('maxInputChannels')
                    device_index = i
                    
            if device_index is None:
                # Fallback to default device
                device_index = self.audio_interface.get_default_input_device_info()['index']
                
            return device_index
        except Exception as e:
            logging.error(f"Error finding microphone: {e}")
            return None

    def cleanup_audio(self) -> None:
        """Clean up audio resources."""
        try:
            if self.audio_stream:
                if self.audio_stream.is_active():
                    self.audio_stream.stop_stream()
                self.audio_stream.close()
            if self.audio_interface:
                self.audio_interface.terminate()
        except Exception as e:
            logging.error(f"Error cleaning up audio: {e}")

    def record_audio(self, timeout=RECORD_TIMEOUT):
        """Record audio until silence is detected or timeout is reached."""
        frames = []
        silence_count = 0
        start_time = time.time()
        
        while (time.time() - start_time) < timeout:
            data = self.audio_stream.read(CHUNK_SIZE, exception_on_overflow=False)
            frames.append(data)
            
            # Convert audio chunk to numpy array for analysis
            audio_data = np.frombuffer(data, dtype=np.int16).astype(np.float32) / 32768.0
            rms = np.sqrt(np.mean(audio_data**2))
            
            if rms < SILENCE_THRESHOLD:
                silence_count += 1
                if silence_count > 5:  # 5 consecutive silent chunks
                    break
            else:
                silence_count = 0
        
        return b''.join(frames)

    def transcribe_audio(self, audio_data):
        """Transcribe audio using Whisper model."""
        try:
            # Convert bytes to numpy array
            audio_np = np.frombuffer(audio_data, dtype=np.int16).astype(np.float32) / 32768.0
            
            # Transcribe with Whisper
            result = self.whisper_model.transcribe(
                audio_np,
                language='en',
                fp16=(self.device == "cuda")
            )
            
            return result['text'].strip()
        except Exception as e:
            logging.error(f"Transcription error: {e}")
            return None

    def listen(self, prompt: str = "Listening...") -> Optional[str]:
        """Capture and recognize speech using Whisper."""
        try:
            self.speak(prompt)
            
            if not self.setup_audio_stream():
                return None

            logging.info("Listening for speech input...")
            print("Listening...")

            audio_data = self.record_audio()
            if not audio_data:
                self.speak("I didn't hear anything. Please try again.")
                return None

            text = self.transcribe_audio(audio_data)
            
            if not text:
                self.speak("I didn't catch that. Please try again.")
                return None

            print(f"Recognized: {text}")
            logging.info(f"Recognized speech: {text}")
            return text.lower()

        except Exception as e:
            logging.error(f"Error during speech recognition: {e}")
            self.speak("There was an error processing your speech. Please try again.")
            return None
        finally:
            self.cleanup_audio()
            
    def listen_with_context(self, prompt=None, expected_phrases=None, timeout=5):
        """Listen with context-aware recognition."""
        if prompt:
            self.speak(prompt)
            
        if not self.setup_audio_stream():
            return None
            
        try:
            audio_data = self.record_audio(timeout)
            if not audio_data:
                return None
                
            text = self.transcribe_audio(audio_data)
            if not text:
                return None
                
            print(f"Recognized: {text}")
            
            if expected_phrases:
                # Use fuzzy matching if we know expected phrases
                matches = process.extractOne(text, expected_phrases)
                if matches and matches[1] > 70:  # 70% confidence threshold
                    return matches[0]
            
            return text.lower()
                    
        except Exception as e:
            logging.error(f"Error in context listening: {e}")
            return None
        finally:
            self.cleanup_audio()
            
    def interactive_listen(self, prompt=None, confirm=False):
        """Interactive listening with immediate feedback."""
        if prompt:
            self.speak(prompt)
        
        while True:
            text = self.listen_with_context()
            if not text:
                self.speak("I didn't catch that. Please try again.")
                continue
                
            if confirm:
                self.speak(f"I heard: {text}. Is this correct?")
                confirmation = self.listen_with_context(expected_phrases=["yes", "no"])
                if confirmation == "yes":
                    return text
            else:
                return text

    def listen_with_retries(self, prompt: str = "Listening...", max_attempts: int = 3) -> Optional[str]:
        """Retry listening up to max_attempts times before giving up."""
        for attempt in range(max_attempts):
            logging.info(f"Attempt {attempt + 1} of {max_attempts} to listen for input.")
            command = self.listen(prompt)
            
            if command:
                return command
                
            if attempt < max_attempts - 1:  # Don't say this on the last attempt
                self.speak("I couldn't understand you. Please try again.")
            
            logging.warning(f"Failed to recognize speech on attempt {attempt + 1}.")
        
        self.speak("Moving on.")
        logging.warning("Max attempts reached. Moving on.")
        return None

    def encrypt_token(self, token: bytes) -> bytes:
        """Encrypt the token using Fernet."""
        return cipher_suite.encrypt(token)

    def decrypt_token(self, encrypted_token: bytes) -> bytes:
        """Decrypt the token using Fernet."""
        return cipher_suite.decrypt(encrypted_token)

    def authenticate_gmail_api(self):
        """Authenticate with Gmail API using OAuth."""
        creds = None
        
        # Try to load existing token
        if os.path.exists('token.pickle'):
            try:
                with open('token.pickle', 'rb') as token:
                    encrypted_token = token.read()
                    creds = pickle.loads(self.decrypt_token(encrypted_token))
            except Exception as e:
                logging.error(f"Error loading token.pickle: {e}")
                os.remove('token.pickle')

        # If no valid credentials, authenticate
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                try:
                    flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
                    creds = flow.run_local_server(port=0)
                except FileNotFoundError:
                    logging.error("credentials.json file not found")
                    self.speak("Authentication failed. Please ensure credentials.json file exists.")
                    return None

            # Save the credentials
            with open('token.pickle', 'wb') as token:
                encrypted_token = self.encrypt_token(pickle.dumps(creds))
                token.write(encrypted_token)

        return creds

    def format_email(self, recognized_text: str) -> Optional[str]:
        """Format spoken email address into valid format."""
        if not recognized_text:
            return None
            
        replacements = {
            " at the rate ": "@", " at ": "@", " dot ": ".", 
            " underscore ": "_", " dash ": "-"
        }
        
        num_map = {
            "zero": "0", "one": "1", "two": "2", "three": "3",
            "four": "4", "five": "5", "six": "6", "seven": "7",
            "eight": "8", "nine": "9"
        }
        
        # Apply replacements
        for phrase, symbol in replacements.items():
            recognized_text = recognized_text.replace(phrase, symbol)

        # Replace number words with digits
        for word, digit in num_map.items():
            recognized_text = re.sub(rf"\b{word}\b", digit, recognized_text)

        # Final cleanup and validation
        email = recognized_text.replace(" ", "")
        if re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", email):
            return email
        return None

    def create_message(self, recipient: str, subject: str, body: str, content_type: str = 'plain') -> str:
        """Create a MIME message for sending via Gmail API."""
        message = MIMEText(body, content_type)
        message['to'] = recipient
        message['subject'] = subject
        return base64.urlsafe_b64encode(message.as_bytes()).decode()

    def send_email_helper(self, service, recipient_email: str, subject: str, body: str) -> bool:
        """Helper function to send an email."""
        try:
            raw_message = self.create_message(recipient_email, subject, body)
            message = {'raw': raw_message}

            service.users().messages().send(userId='me', body=message).execute()
            self.speak("Email sent successfully!")
            logging.info(f"Email sent to {recipient_email} with subject: {subject}")
            return True
        except Exception as e:
            self.speak(f"Failed to send email: {str(e)}. Please check your internet connection and try again.")
            logging.error(f"Error sending email: {str(e)}")
            return False

    def get_contacts(self, contacts_service) -> Dict[str, List[str]]:
        """Retrieve user's contacts from Google People API."""
        contacts = {}
        next_page_token = None

        try:
            while True:
                results = contacts_service.people().connections().list(
                    resourceName='people/me',
                    pageSize=100,
                    personFields='names,emailAddresses',
                    pageToken=next_page_token
                ).execute()

                connections = results.get('connections', [])
                for person in connections:
                    names = person.get('names', [])
                    emails = person.get('emailAddresses', [])
                    
                    if names and emails:
                        name = names[0].get('displayName').lower()
                        for email in emails:
                            email_value = email.get('value')
                            contacts.setdefault(name, []).append(email_value)

                next_page_token = results.get('nextPageToken')
                if not next_page_token:
                    break
                    
            return contacts
        except Exception as e:
            logging.error(f"Error retrieving contacts: {e}")
            return {}

    def summarize_email(self, email_body: str) -> str:
        """Summarize the email body using BART model."""
        try:
            if not email_body:
                return "No content to summarize."
                
            if not self.summarizer:
                return "Email summarization is not available."
                
            # Truncate to model's max input length
            input_text = email_body[:1024]
            summary = self.summarizer(
                input_text,
                max_length=130,
                min_length=30,
                do_sample=False
            )
            return summary[0]['summary_text']
        except Exception as e:
            logging.error(f"Error summarizing email: {e}")
            return "Unable to summarize this email."

    def generate_email_draft(self, prompt: str) -> str:
        """Generate an email draft using GPT-2."""
        try:
            if not prompt:
                return "No prompt provided for email generation."
                
            if not self.email_generator:
                return "Email generation is not available."
                
            email_draft = self.email_generator(
                f"Write a professional email about: {prompt}",
                max_length=200,
                num_return_sequences=1,
                temperature=0.7
            )
            return email_draft[0]['generated_text']
        except Exception as e:
            logging.error(f"Error generating email draft: {e}")
            return "Unable to generate an email draft at this time."

    def get_email_body(self, msg: dict) -> str:
        """Extract email body, handling HTML emails."""
        try:
            payload = msg.get('payload', {})
            parts = payload.get('parts', [])
            
            # Handle non-multipart emails
            if not parts:
                data = payload.get('body', {}).get('data', '')
                if data:
                    return base64.urlsafe_b64decode(data).decode('utf-8', errors='replace')
            
            # Handle multipart emails
            for part in parts:
                if part.get('mimeType') == 'text/plain':
                    data = part.get('body', {}).get('data', '')
                    if data:
                        return base64.urlsafe_b64decode(data).decode('utf-8', errors='replace')
                elif part.get('mimeType') == 'text/html':
                    html_content = base64.urlsafe_b64decode(part.get('body', {}).get('data', '')).decode('utf-8', errors='replace')
                    return BeautifulSoup(html_content, "html.parser").get_text()
            
            # Fallback to snippet if no body found
            return msg.get('snippet', 'No body content found.')
        except Exception as e:
            logging.error(f"Error extracting email body: {e}")
            return "Could not extract email content."

    def send_email(self, creds) -> None:
        """Handle the complete email sending process."""
        if not creds:
            self.speak("Gmail authentication failed. Cannot send email.")
            return
            
        try:
            # Initialize services
            service = build('gmail', 'v1', credentials=creds)
            contacts_service = build('people', 'v1', credentials=creds)
            contacts = self.get_contacts(contacts_service)

            # Get recipient
            recipient_name = self.listen_with_retries("Please say the name of the recipient.")
            if not recipient_name:
                self.speak("No valid name was provided. Email not sent.")
                return

            recipient_name = recipient_name.strip().lower()
            recipient_emails = contacts.get(recipient_name)

            # Get recipient email
            if not recipient_emails:
                self.speak("I could not find that name in your contacts. Please say the recipient's email address.")
                recipient_email_input = self.listen_with_retries()
                recipient_email = self.format_email(recipient_email_input) if recipient_email_input else None
            else:
                if len(recipient_emails) == 1:
                    recipient_email = recipient_emails[0]
                else:
                    self.speak(f"I found multiple contacts for {recipient_name}. Here are the options:")
                    for idx, email in enumerate(recipient_emails, start=1):
                        self.speak(f"Option {idx}: {email}")
                    
                    choice = self.listen_with_retries("Please say the number of the email you want to use.")
                    try:
                        choice_index = int(choice) - 1
                        if 0 <= choice_index < len(recipient_emails):
                            recipient_email = recipient_emails[choice_index]
                        else:
                            self.speak("Invalid choice. Email not sent.")
                            return
                    except (ValueError, TypeError):
                        self.speak("Invalid input. Email not sent.")
                        return

            if not recipient_email:
                self.speak("No valid recipient email provided. Email not sent.")
                return

            # Get email subject
            subject = self.listen_with_retries("Please say the subject of the email.")
            if not subject:
                self.speak("No subject provided. Email not sent.")
                return

            # Get email body
            compose_choice = self.listen_with_retries("Would you like me to help you compose the email? Say yes or no.")
            if compose_choice and "yes" in compose_choice.lower():
                email_prompt = self.listen_with_retries("Please describe the email you'd like to send.")
                body = self.generate_email_draft(email_prompt)
                self.speak(f"Here's the draft email: {body}")
            else:
                body = self.listen_with_retries("Please dictate the body of the email.")
                if not body:
                    self.speak("No body provided. Email not sent.")
                    return

            # Confirm before sending
            preview = body[:100] + "..." if len(body) > 100 else body
            confirmation = self.listen_with_retries(
                f"You are about to send an email to {recipient_email} with the subject '{subject}' "
                f"and the body: '{preview}'. Say 'send' to confirm or 'cancel' to abort."
            )

            if confirmation and "send" in confirmation.lower():
                if self.send_email_helper(service, recipient_email, subject, body):
                    self.speak("Email sent successfully!")
            else:
                self.speak("Email not sent.")
                
        except Exception as e:
            self.speak(f"Error occurred while sending email: {str(e)}")
            logging.error(f"Error in send_email function: {str(e)}")

    def check_inbox(self, creds) -> None:
        """Check Gmail inbox and read emails via voice control."""
        if not creds:
            self.speak("Gmail authentication failed. Cannot check inbox.")
            return
            
        try:
            service = build('gmail', 'v1', credentials=creds)
            results = service.users().messages().list(
                userId='me',
                maxResults=10,
                labelIds=['INBOX']
            ).execute()
            messages = results.get('messages', [])

            if not messages:
                self.speak("Your inbox is empty.")
                return

            self.speak(f"You have {len(messages)} new messages. Here are the latest ones:")

            for message in messages:
                try:
                    msg = service.users().messages().get(
                        userId='me',
                        id=message['id'],
                        format='full'
                    ).execute()
                    
                    headers = msg.get('payload', {}).get('headers', [])
                    sender = next((h['value'] for h in headers if h['name'] == 'From'), 'Unknown sender')
                    subject = next((h['value'] for h in headers if h['name'] == 'Subject'), 'No subject')

                    self.speak(f"From: {sender}. Subject: {subject}. Would you like to read this email? Say yes or no.")
                    command = self.listen_with_retries()

                    if not command or "no" in command or "skip" in command:
                        self.speak("Skipping this email.")
                        continue

                    if "yes" in command or "read" in command:
                        body = self.get_email_body(msg)
                        summary = self.summarize_email(body)
                        
                        self.speak(f"Here's a summary of the email: {summary}")
                        
                        full_email_choice = self.listen_with_retries(
                            "Would you like to hear the full email? Say yes or no."
                        )
                        
                        if full_email_choice and "yes" in full_email_choice.lower():
                            # Read only the first part of long emails
                            email_preview = body[:MAX_EMAIL_LENGTH]
                            if len(body) > MAX_EMAIL_LENGTH:
                                email_preview += "... (email truncated)"
                            self.speak(f"Reading email: {email_preview}")
                            
                        self.handle_email_actions(service, msg)

                except Exception as e:
                    logging.error(f"Error processing email {message['id']}: {str(e)}")
                    self.speak("There was an issue processing this email. Moving to the next one.")

        except Exception as e:
            logging.error(f"Error checking inbox: {str(e)}")
            self.speak(f"Failed to check inbox: {str(e)}")

    def handle_email_actions(self, service, msg) -> None:
        """Handle user actions for a specific email."""
        while True:
            command = self.listen_with_retries(
                "What would you like to do? You can say 'next email', 'download attachments', "
                "'reply', 'forward', or 'exit'."
            )

            if not command:
                continue

            command = command.lower()

            if "next email" in command or "skip" in command:
                self.speak("Moving to the next email.")
                break

            elif "download attachments" in command:
                self.download_attachments(service, msg)
                break

            elif "reply" in command:
                self.reply_to_email(service, msg)
                break

            elif "forward" in command:
                self.forward_email(service, msg)
                break

            elif "exit" in command:
                self.speak("Exiting inbox check.")
                return

            else:
                self.speak("I didn't understand that. Please try again.")

    def download_attachments(self, service, msg) -> None:
        """Download email attachments with safety checks."""
        parts = msg.get('payload', {}).get('parts', [])
        if not parts:
            self.speak("No attachments found.")
            return

        os.makedirs(DOWNLOAD_DIRECTORY, exist_ok=True)
        attachment_found = False

        for part in parts:
            if not part.get('filename') or not part.get('body', {}).get('size', 0) > 0:
                continue

            attachment_found = True
            filename = part['filename']
            file_ext = os.path.splitext(filename)[1].lower()

            if file_ext in HARMFUL_EXTENSIONS:
                self.speak(f"Warning: The file {filename} is blocked for security reasons.")
                logging.warning(f"Blocked harmful file: {filename}")
                continue

            if part['body']['size'] > MAX_ATTACHMENT_SIZE:
                self.speak(f"Warning: The file {filename} is too large to download.")
                logging.warning(f"Skipped large file: {filename}")
                continue

            try:
                if 'attachmentId' not in part['body']:
                    self.speak(f"Attachment {filename} cannot be downloaded.")
                    continue

                attachment_id = part['body']['attachmentId']
                attachment = service.users().messages().attachments().get(
                    userId='me',
                    messageId=msg['id'],
                    id=attachment_id
                ).execute()

                file_data = base64.urlsafe_b64decode(attachment['data'].encode('UTF-8'))
                file_path = os.path.join(DOWNLOAD_DIRECTORY, filename)

                counter = 1
                base_name, ext = os.path.splitext(filename)
                while os.path.exists(file_path):
                    file_path = os.path.join(DOWNLOAD_DIRECTORY, f"{base_name}_{counter}{ext}")
                    counter += 1

                with open(file_path, 'wb') as f:
                    f.write(file_data)

                self.speak(f"Downloaded attachment: {filename}")
                logging.info(f"Downloaded file: {filename} to {file_path}")

            except Exception as e:
                self.speak(f"Failed to download attachment: {str(e)}")
                logging.error(f"Error downloading {filename}: {str(e)}")

        if not attachment_found:
            self.speak("No attachments found in this email.")

    def reply_to_email(self, service, msg) -> None:
        """Handle replying to an email."""
        try:
            headers = msg.get('payload', {}).get('headers', [])
            recipient = next(
                (h['value'] for h in headers if h['name'].lower() == 'from'),
                None
            )

            if not recipient:
                self.speak("Could not find recipient for reply.")
                return

            self.speak(f"Replying to {recipient}. Please dictate your reply.")
            reply_body = self.listen_with_retries()

            if not reply_body:
                self.speak("No reply content provided.")
                return

            subject_header = next((h['value'] for h in headers if h['name'].lower() == 'subject'), 'No subject')
            subject = f"Re: {subject_header}"
            full_body = f"Reply to: {recipient}\n\n{reply_body}"

            self.speak(f"Your reply is ready. Say 'send' to confirm or 'cancel' to abort.")
            confirmation = self.listen_with_retries()

            if confirmation and "send" in confirmation.lower():
                if self.send_email_helper(service, recipient, subject, full_body):
                    self.speak("Reply sent successfully.")
            else:
                self.speak("Reply canceled.")

        except Exception as e:
            self.speak(f"An error occurred while replying: {str(e)}")
            logging.error(f"Error replying to email: {str(e)}")

    def forward_email(self, service, msg) -> None:
        """Handle forwarding an email."""
        try:
            # Get forwarding recipient
            self.speak("Please say the email address to forward to.")
            recipient_input = self.listen_with_retries()
            recipient = self.format_email(recipient_input)
            
            if not recipient:
                self.speak("Invalid email address. Forwarding canceled.")
                return

            # Get original email content
            original_body = self.get_email_body(msg)
            
            # Get original sender and subject
            headers = msg.get('payload', {}).get('headers', [])
            original_sender = next((h['value'] for h in headers if h['name'] == 'From'), 'Unknown sender')
            original_subject = next((h['value'] for h in headers if h['name'] == 'Subject'), 'No subject')
            
            subject = f"Fwd: {original_subject}"
            forward_body = (f"---------- Forwarded message ---------\n"
                           f"From: {original_sender}\n"
                           f"Subject: {original_subject}\n\n"
                           f"{original_body}\n\n"
                           f"---\nForwarded by Gmail Voice Assistant")

            self.speak(f"Ready to forward to {recipient}. Say 'send' to confirm or 'cancel' to abort.")
            confirmation = self.listen_with_retries()

            if confirmation and "send" in confirmation.lower():
                if self.send_email_helper(service, recipient, subject, forward_body):
                    self.speak("Email forwarded successfully.")
            else:
                self.speak("Forwarding canceled.")

        except Exception as e:
            self.speak(f"An error occurred while forwarding: {str(e)}")
            logging.error(f"Error forwarding email: {str(e)}")

    def is_valid_email(self, email: str) -> bool:
        """Validate an email address."""
        if not email:
            return False
        pattern = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
        return re.match(pattern, email) is not None

    def main(self, user: str = "User") -> None:
        """Main entry point for the Gmail Voice Assistant."""
        self.speak(f"Welcome, {user}. What would you like to do?")
        creds = self.authenticate_gmail_api()
        
        if not creds:
            self.speak("Authentication failed. Please check your credentials and try again.")
            return

        attempts = 3
        while attempts > 0:
            command = self.listen_with_retries("Please say your command: send email, check inbox, or exit.")
            
            if not command:
                attempts -= 1
                continue

            command = command.lower()

            if "send email" in command:
                self.send_email(creds)
                break
            elif "check inbox" in command or "read email" in command:
                self.check_inbox(creds)
                break
            elif "exit" in command or "quit" in command:
                self.speak("Exiting Gmail Voice Assistant.")
                return
            else:
                self.speak("I didn't understand that. Please say 'send email', 'check inbox', or 'exit'.")
                attempts -= 1

        if attempts == 0:
            self.speak("Too many failed attempts. Exiting.")


if __name__ == "__main__":
    try:
        assistant = GmailVoiceAssistant()
        user = os.getenv("USER", "User")  # Get system username or default to "User"
        assistant.main(user)
    except Exception as e:
        logging.error(f"Fatal error in main execution: {e}")
        print(f"An error occurred: {e}. Please check the logs.")