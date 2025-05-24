# config.py

# Path to the Vosk model
MODEL_PATH = "vosk-model-small-en-us-0.15"

# Gmail API scopes
SCOPES = [
    'https://www.googleapis.com/auth/gmail.send',
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/contacts.readonly'
]

# Directory for downloaded attachments
DOWNLOAD_DIRECTORY = "downloads"

# Harmful file extensions to block
HARMFUL_EXTENSIONS = ['.exe', '.bat', '.sh', '.cmd', '.vbs']