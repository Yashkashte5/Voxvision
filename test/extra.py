import speech_recognition as sr
import pyttsx3
import datetime
import wikipedia
import wolframalpha
import requests
import os
import webbrowser
import pyjokes
import time
import subprocess
import random
from difflib import get_close_matches
import json
from threading import Timer
import re
import smtplib
import imaplib
import email
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import pywhatkit as whatsapp
from bs4 import BeautifulSoup
import urllib.request
import pyautogui
import sys

# Initialize speech engine
engine = pyttsx3.init()
voices = engine.getProperty('voices')
engine.setProperty('voice', voices[1].id)  # 0 for male, 1 for female
engine.setProperty('rate', 150)

# Configure APIs (replace with your actual keys)
WOLFRAM_ALPHA_APP_ID = '54QQTY-VERK4TRPA7'
OPENWEATHER_API_KEY = 'bd2bd9b64ae6b40b3f714a764d301f86'
NEWS_API_KEY = '808f74cb58a8471d9c8a789b6744af41'
EMAIL = "sagarchavan142003@gmail.com"
EMAIL_PASSWORD = "loau jaii qepv rkco"  # Use App Password for Gmail
SMTP_SERVER = "smtp.gmail.com"
IMAP_SERVER = "imap.gmail.com"

# Command mappings
COMMAND_MAPPINGS = {
    'open': ['launch', 'start', 'run'],
    'search': ['find', 'look up', 'google'],
    'weather': ['forecast', 'temperature', 'weather in'],
    'reminder': ['remind me', 'alert me', 'set a reminder'],
    'email': ['send mail', 'compose email', 'check email'],
    'news': ['headlines', 'latest news', 'today\'s news'],
    'music': ['play song', 'play music'],
    'time': ['current time', 'what time is it'],
    'date': ['today\'s date', 'what date is it'],
    'joke': ['tell joke', 'make me laugh'],
    'calculate': ['what is', 'math', 'calculation'],
    'whatsapp': ['send message', 'whatsapp'],
    'download': ['download file', 'get file'],
    'website': ['open website', 'visit site'],
    'shutdown': ['turn off', 'shutdown'],
    'exit': ['quit', 'goodbye', 'bye', 'stop']
}

# Application mappings
APP_MAPPINGS = {
    'notepad': 'notepad.exe',
    'calculator': 'calc.exe',
    'paint': 'mspaint.exe',
    'word': 'winword.exe',
    'excel': 'excel.exe',
    'chrome': 'chrome.exe',
    'firefox': 'firefox.exe',
    'spotify': 'spotify.exe',
    'youtube': 'https://www.youtube.com',
    'google': 'https://www.google.com'
}

# Contact names to numbers mapping (add your contacts here)
CONTACTS = {
    'john': '+91 98926 50547',
    'parth': '+91 95613 20823',
    'mom': '+1122334455',
    'dad': '+5566778899'
}

# User preferences
user_prefs = {
    'name': 'User',
    'city': 'Mumbai'
}

def speak(text, wait=True):
    """Convert text to speech with improved error handling"""
    print(f"Assistant: {text}")
    try:
        engine.say(text)
        if wait:
            engine.runAndWait()
    except Exception as e:
        print(f"Speech synthesis error: {e}")

def listen():
    """Listen to microphone input with better error handling"""
    r = sr.Recognizer()
    with sr.Microphone() as source:
        print("Listening...")
        r.adjust_for_ambient_noise(source, duration=0.5)
        r.pause_threshold = 1
        try:
            audio = r.listen(source, timeout=5)
            print("Recognizing...")
            query = r.recognize_google(audio, language='en-in')
            print(f"User: {query}")
            return query.lower()
        except sr.WaitTimeoutError:
            print("Listening timed out")
            return ""
        except sr.UnknownValueError:
            print("Could not understand audio")
            return ""
        except sr.RequestError as e:
            print(f"Could not request results; {e}")
            return ""
        except Exception as e:
            print(f"Error in recognition: {e}")
            return ""

def greet():
    """Personalized greeting based on time and user preferences"""
    hour = datetime.datetime.now().hour
    greeting = ""
    
    if 5 <= hour < 12:
        greeting = "Good morning"
    elif 12 <= hour < 17:
        greeting = "Good afternoon"
    else:
        greeting = "Good evening"
    
    if user_prefs['name']:
        greeting += f", {user_prefs['name']}"
    
    greeting += "! I'm your virtual assistant. How can I help you today?"
    speak(greeting)

def extract_keywords(query):
    """Extract important keywords from query using simple pattern matching"""
    patterns = {
        'city': r'(?:weather|forecast) in (\w+)',
        'time': r'(?:what|current) time',
        'date': r'(?:what|today\'s) date',
        'app_name': r'open (\w+)',
        'search_query': r'(?:search|google) (?:for )?(.+)',
        'calculation': r'(?:calculate|what is) (.+)',
        'contact': r'send (?:message|whatsapp) to (\w+)',
        'message': r'send (?:message|whatsapp) (?:to \w+ )?(.+)',
        'url': r'(?:open|visit) (?:website|site) (.+)',
        'download_url': r'download (?:file|from) (.+)'
    }
    
    extracted = {}
    for key, pattern in patterns.items():
        match = re.search(pattern, query)
        if match:
            extracted[key] = match.group(1) if match.groups() else True
    
    return extracted

def understand_command(query):
    """Understand user intent without spaCy"""
    if not query:
        return None
    
    # First check for exact command matches
    for command, aliases in COMMAND_MAPPINGS.items():
        if any(alias in query for alias in [command] + aliases):
            return command
    
    # Then try to find closest matching command
    all_commands = list(COMMAND_MAPPINGS.keys()) + [item for sublist in COMMAND_MAPPINGS.values() for item in sublist]
    matches = get_close_matches(query, all_commands, n=1, cutoff=0.5)
    
    return matches[0] if matches else None

def open_application(app_name=None):
    """Open applications or websites"""
    if not app_name:
        speak("Which application would you like me to open?")
        app_name = listen()
    
    if not app_name:
        speak("I didn't catch that. Please try again.")
        return
    
    # Find closest matching app
    matches = get_close_matches(app_name, APP_MAPPINGS.keys(), n=1, cutoff=0.6)
    app_to_open = matches[0] if matches else app_name
    
    if app_to_open in APP_MAPPINGS:
        try:
            if app_to_open in ['youtube', 'google']:  # Web apps
                webbrowser.open(APP_MAPPINGS[app_to_open])
            else:  # Local apps
                subprocess.Popen(APP_MAPPINGS[app_to_open])
            speak(f"Opening {app_to_open}")
        except Exception as e:
            print(f"Error opening application: {e}")
            speak(f"Sorry, I couldn't open {app_to_open}")
    else:
        speak(f"I don't know how to open {app_name}. I can open: {', '.join(APP_MAPPINGS.keys())}")

def send_whatsapp_message(contact=None, message=None):
    """Send WhatsApp message using contact names"""
    if not contact:
        speak("Who should I send the message to? Please say the contact name.")
        contact = listen()
        if not contact:
            speak("I didn't catch that. Please try again.")
            return
    
    # Find contact in CONTACTS dictionary
    contact_matches = get_close_matches(contact, CONTACTS.keys(), n=1, cutoff=0.6)
    contact_name = contact_matches[0] if contact_matches else contact
    
    if contact_name not in CONTACTS:
        speak(f"Sorry, I don't have a number for {contact_name}. Please add it to the CONTACTS dictionary.")
        return
    
    phone = CONTACTS[contact_name]
    
    if not message:
        speak(f"What should the message to {contact_name} say?")
        message = listen()
        if not message:
            speak("I didn't catch that. Please try again.")
            return
    
    try:
        speak(f"Sending WhatsApp message to {contact_name}: {message}")
        whatsapp.sendwhatmsg_instantly(phone, message, wait_time=15)
        time.sleep(2)
        pyautogui.press('enter')  # Ensure message is sent
        speak("Message sent successfully!")
    except Exception as e:
        speak(f"Sorry, I couldn't send the WhatsApp message. Error: {e}")

def send_email_with_attachment(to=None, subject=None, body=None, file_path=None):
    """Send email with optional attachment"""
    if not to:
        speak("Who should I send the email to?")
        to = listen()
        if not to:
            speak("I didn't catch the recipient. Please try again.")
            return
    
    if not subject:
        speak("What should the subject be?")
        subject = listen()
        if not subject:
            speak("I didn't catch the subject. Please try again.")
            return
    
    if not body:
        speak("What should the email say?")
        body = listen()
        if not body:
            speak("I didn't catch the message. Please try again.")
            return
    
    try:
        msg = MIMEMultipart()
        msg['From'] = EMAIL
        msg['To'] = to
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))
        
        if file_path and os.path.exists(file_path):
            attachment = open(file_path, "rb")
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(attachment.read())
            encoders.encode_base64(part)
            part.add_header('Content-Disposition', f"attachment; filename= {os.path.basename(file_path)}")
            msg.attach(part)
            attachment.close()
        
        server = smtplib.SMTP(SMTP_SERVER, 587)
        server.starttls()
        server.login(EMAIL, EMAIL_PASSWORD)
        server.sendmail(EMAIL, to, msg.as_string())
        server.quit()
        speak("Email sent successfully!")
    except Exception as e:
        speak(f"Sorry, I couldn't send the email. Error: {e}")

def read_emails(limit=3):
    """Read latest emails from inbox"""
    try:
        mail = imaplib.IMAP4_SSL(IMAP_SERVER)
        mail.login(EMAIL, EMAIL_PASSWORD)
        mail.select('inbox')
        
        status, messages = mail.search(None, 'ALL')
        if status != 'OK':
            speak("Could not fetch emails.")
            return
        
        email_ids = messages[0].split()
        latest_emails = email_ids[-limit:]  # Get last 'limit' emails
        
        speak(f"You have {len(latest_emails)} new emails. Here are the latest:")
        
        for email_id in latest_emails:
            status, msg_data = mail.fetch(email_id, '(RFC822)')
            if status != 'OK':
                continue
            
            raw_email = msg_data[0][1]
            msg = email.message_from_bytes(raw_email)
            
            speak(f"From: {msg['from']}")
            speak(f"Subject: {msg['subject']}")
            
            # Extract plain text content
            for part in msg.walk():
                if part.get_content_type() == 'text/plain':
                    body = part.get_payload(decode=True).decode()
                    speak(f"Message: {body[:100]}...")  # Read first 100 chars
                    break
        
        mail.close()
        mail.logout()
    except Exception as e:
        speak(f"Sorry, I couldn't read your emails. Error: {e}")

def download_file(url=None):
    """Download file from URL"""
    if not url:
        speak("Which file should I download? Please say the URL.")
        url = listen()
        if not url:
            speak("I didn't catch that. Please try again.")
            return
    
    try:
        file_name = url.split('/')[-1]
        speak(f"Downloading {file_name} from {url}")
        urllib.request.urlretrieve(url, file_name)
        speak(f"Downloaded {file_name} successfully!")
    except Exception as e:
        speak(f"Sorry, I couldn't download the file. Error: {e}")

def scrape_website(url=None):
    """Extract text content from a website"""
    if not url:
        speak("Which website should I visit?")
        url = listen()
        if not url:
            speak("I didn't catch that. Please try again.")
            return
    
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
    
    try:
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Extract main content (simplified)
        text = ' '.join([p.get_text() for p in soup.find_all('p')])
        summary = text[:200] + "..."  # First 200 chars
        
        speak(f"Here's a summary from {url}: {summary}")
    except Exception as e:
        speak(f"Sorry, I couldn't fetch information from the website. Error: {e}")

def get_weather(city=None):
    """Get weather information with improved error handling"""
    if not city:
        city = user_prefs.get('city', 'New York')
    
    base_url = "http://api.openweathermap.org/data/2.5/weather?"
    complete_url = f"{base_url}appid={OPENWEATHER_API_KEY}&q={city}"
    
    try:
        response = requests.get(complete_url)
        response.raise_for_status()
        result = response.json()
        
        if result["cod"] != "404":
            main = result["main"]
            temperature = main["temp"] - 273.15  # Convert Kelvin to Celsius
            pressure = main["pressure"]
            humidity = main["humidity"]
            weather = result["weather"]
            description = weather[0]["description"]
            
            speak(f"Weather in {city}:")
            speak(f"Temperature: {temperature:.1f}°C")
            speak(f"Weather conditions: {description}")
            speak(f"Humidity: {humidity}%")
        else:
            speak(f"Sorry, I couldn't find weather information for {city}.")
    except requests.exceptions.RequestException as e:
        speak("Sorry, I'm having trouble accessing weather information right now.")
        print(f"Weather API error: {e}")

def set_reminder():
    """Improved reminder function with confirmation"""
    speak("What should I remind you about?")
    reminder_text = listen()
    
    if not reminder_text:
        speak("I didn't catch that. Please try again.")
        return
    
    speak("In how many minutes should I remind you?")
    minutes_input = listen()
    
    try:
        minutes = float(''.join(filter(str.isdigit, minutes_input)))
        seconds = minutes * 60
        
        def remind():
            speak(f"Reminder: {reminder_text}")
        
        Timer(seconds, remind).start()
        speak(f"Okay, I'll remind you in {minutes} minute{'s' if minutes != 1 else ''}.")
    except ValueError:
        speak("Sorry, I didn't understand the time. Please try again.")

def search_web(query=None):
    """Enhanced web search"""
    if not query:
        speak("What would you like me to search for?")
        query = listen()
        
    if query:
        search_url = f"https://www.google.com/search?q={query}"
        webbrowser.open(search_url)
        speak(f"Here's what I found for {query}")
    else:
        speak("I didn't catch that. Please try again.")

def calculate(expression=None):
    """Improved calculation with Wolfram Alpha"""
    if not expression:
        speak("What would you like me to calculate?")
        expression = listen()
    
    if not expression:
        speak("I didn't catch that. Please try again.")
        return
    
    try:
        client = wolframalpha.Client(WOLFRAM_ALPHA_APP_ID)
        res = client.query(expression)
        answer = next(res.results).text
        speak(f"The answer is {answer}")
    except Exception as e:
        print(f"Calculation error: {e}")
        speak("Sorry, I couldn't perform that calculation.")

def tell_joke():
    """Tell a joke with category selection"""
    categories = ['neutral', 'chuck', 'all']
    joke = pyjokes.get_joke(language='en', category=random.choice(categories))
    speak(joke)

def handle_unknown_command():
    """Handle unrecognized commands gracefully"""
    responses = [
        "I'm not sure I understand. Could you rephrase that?",
        "I don't know how to help with that yet.",
        "Sorry, I didn't catch that. Can you try again?",
        "My capabilities are limited. Could you ask something else?"
    ]
    speak(random.choice(responses))

def process_command(command, query):
    """Process the identified command"""
    keywords = extract_keywords(query)
    
    if command == 'open':
        app_name = keywords.get('app_name', query.replace('open', '').strip())
        open_application(app_name)
    elif command == 'search':
        search_query = keywords.get('search_query', query.replace('search', '').strip())
        search_web(search_query)
    elif command == 'weather':
        city = keywords.get('city', None)
        get_weather(city)
    elif command == 'reminder':
        set_reminder()
    elif command == 'email':
        if 'check' in query or 'read' in query:
            read_emails()
        else:
            send_email_with_attachment()
    elif command == 'news':
        get_news()
    elif command == 'music':
        speak("Playing music on Spotify...")
        open_application('spotify')
    elif command == 'time':
        current_time = datetime.datetime.now().strftime("%I:%M %p")
        speak(f"The current time is {current_time}")
    elif command == 'date':
        current_date = datetime.datetime.now().strftime("%B %d, %Y")
        speak(f"Today's date is {current_date}")
    elif command == 'joke':
        tell_joke()
    elif command == 'calculate':
        expression = keywords.get('calculation', query.replace('calculate', '').strip())
        calculate(expression)
    elif command == 'whatsapp':
        contact = keywords.get('contact', None)
        message = keywords.get('message', query.replace('send', '').replace('whatsapp', '').strip())
        send_whatsapp_message(contact, message)
    elif command == 'download':
        url = keywords.get('download_url', query.replace('download', '').strip())
        download_file(url)
    elif command == 'website':
        url = keywords.get('url', query.replace('open', '').replace('website', '').strip())
        scrape_website(url)
    elif command == 'shutdown':
        speak("Shutting down the system in 10 seconds...")
        time.sleep(10)
        os.system("shutdown /s /t 1")
    elif command == 'exit':
        return False
    else:
        handle_unknown_command()
    return True

def main():
    """Main function to run the assistant"""
    greet()
    
    running = True
    while running:
        query = listen()
        
        if not query:
            continue
            
        command = understand_command(query)
        
        if command:
            running = process_command(command, query)
        else:
            try:
                results = wikipedia.summary(query, sentences=2)
                speak("Here's what I found:")
                speak(results)
            except:
                try:
                    client = wolframalpha.Client(WOLFRAM_ALPHA_APP_ID)
                    res = client.query(query)
                    answer = next(res.results).text
                    speak(f"The answer is {answer}")
                except:
                    handle_unknown_command()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        speak("Goodbye!")
        sys.exit(0)
    except Exception as e:
        print(f"Unexpected error: {e}")
        speak("Sorry, I encountered an error. Restarting...")
        main()