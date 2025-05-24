# 🎙️ VoxVision – Your Voice. Your Control. Your Assistant.

**VoxVision** is an AI-powered voice-controlled desktop assistant built to empower **blind and visually impaired users**. With just your voice, you can open applications, read or send emails, browse the web, and much more—no keyboard, no mouse, no hassle. Just speak, and VoxVision responds.

This project is part of our mission to create **inclusive, accessible technology** that gives control back to those who need it most.

---

## 🔍 What is VoxVision?

VoxVision is a Python-based assistant that listens, understands, and acts—**all in real time**. It’s specifically designed for hands-free operation, using **speech recognition, NLP (Natural Language Processing), and automation** to handle daily digital tasks. Whether you're composing an email or launching an application, VoxVision is your voice-powered bridge to technology.

---

## 🚀 What Can It Do?

Here’s what VoxVision brings to the table:

- 🎤 **Voice-Driven Control Panel**  
  Control your desktop entirely by voice—no more clicks or typing.

- 📧 **Email Management via Voice**  
  Compose, send, read, and navigate Gmail conversations hands-free. All credentials are securely encrypted.

- 🖥️ **Desktop Automation**  
  Open or close apps, control windows, type using voice, and perform common system tasks.

- 🌐 **Web Browsing via Voice**  
  Use natural commands to search, navigate, and interact with websites.

- 🔒 **Face Recognition for Authentication** *(optional)*  
  Add a security layer by verifying the user’s identity via webcam before access.

- 🧠 **Smart NLP Intent Detection**  
  Instead of rigid if-else logic, VoxVision understands your intent using a lightweight NLP model (DistilBERT) so you can speak naturally.

- 🔊 **Voice Feedback System**  
  VoxVision speaks back to confirm actions, report errors, or ask for clarification—perfect for visually impaired users.

- 🧩 **Modular Architecture**  
  Easily extend the assistant with new voice commands or automation tasks. Clean, modular code for future improvements.

---

## 🛠️ Tech Stack

| Category | Tools & Libraries |
|----------|-------------------|
| **Language** | Python 3.x |
| **UI** | `tkinter` |
| **Speech Recognition** | `speech_recognition`, `Vosk` |
| **Text-to-Speech** | `pyttsx3` |
| **Email API** | Gmail API with OAuth 2.0 + AES encryption |
| **Face Authentication** | `face_recognition`, `OpenCV` |
| **Automation** | `pyautogui`, `selenium`, `webbrowser` |
| **NLP Engine** | `DistilBERT` (via HuggingFace Transformers) |
| **Security** | `pycryptodome` for AES-encrypted credentials |

---

## 🧪 How to Run Locally

1. **Clone the repository**  
   ```bash
   git clone https://github.com/Yashkashte5/Voxvision.git
   cd Voxvision
