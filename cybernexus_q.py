
# -*- coding: utf-8 -*-
import streamlit as st

# --- This MUST be the first Streamlit command ---
st.set_page_config(
    page_title="CyberNexus Q - Pi-Eye 🌌 (Azure AI & Quantum Inspired)",
    page_icon="🌌",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- Azure AI SDK Imports ---
from azure.ai.inference import ChatCompletionsClient
from azure.ai.inference.models import (
    SystemMessage,
    UserMessage,
    AssistantMessage,
    ImageUrl,  # Correct class for image URLs
    TextContentItem,    # <-- ADD THIS LINE
    ImageContentItem,   # <-- ADD THIS LINE
    ImageDetailLevel # <-- ADD this if you plan to use the 'detail' parameter later

)
from azure.core.credentials import AzureKeyCredential
# --- FIX THIS LINE ---
from azure.core.exceptions import HttpResponseError, ClientAuthenticationError # Add ClientAuthenticationError here

import json
import pandas as pd
import os
import io
import platform
import glob
import re
import random
import time
import socket
import base64
import subprocess
import traceback  # For detailed error logging

# --- Third-party Library Imports ---
import psutil
import speedtest
import cv2
import numpy as np
import requests  # For Pi-hole and External IP
from PIL import Image, ImageOps, ImageDraw
from mss import mss
import pyttsx3
import speech_recognition as sr

# --- Symbolic Quantum Lib Imports ---
try:
    from braket.circuits import Circuit, Qubit, FreeParameter, Observable
    from braket.devices import LocalSimulator, AwsDevice
    from qiskit import QuantumCircuit, transpile, Aer, assemble

    HAS_QUANTUM_LIBS = True
    quantum_lib_status = "Symbolic Quantum Libraries (braket, qiskit) detected."
except ImportError:
    HAS_QUANTUM_LIBS = False
    quantum_lib_status = (
        "Symbolic Quantum Libraries not found. Classical simulation only."
    )
    # Dummy placeholders
    class DummyQuantumClass:
        pass

    Circuit, Qubit, FreeParameter, Observable = (
        DummyQuantumClass,
        DummyQuantumClass,
        DummyQuantumClass,
        DummyQuantumClass,
    )
    LocalSimulator, AwsDevice = DummyQuantumClass, DummyQuantumClass
    QuantumCircuit, transpile, Aer, assemble = (
        DummyQuantumClass,
        DummyQuantumClass,
        DummyQuantumClass,
        DummyQuantumClass,
    )

# --- Constants ---
AZURE_AI_ENDPOINT_URL = "https://models.inference.ai.azure.com"  # Correct SDK endpoint
PHI4_MODEL_NAME = "Phi-4-multimodal-instruct"  # Model identifier for SDK

# --- Azure AI Client Initialization ---
azure_ai_enabled = False
azure_client = None
try:
    AZURE_AI_API_KEY = st.secrets["azure_ai"]["api_key"]
    if not AZURE_AI_API_KEY or AZURE_AI_API_KEY == "YOUR_AZURE_AI_API_KEY_OR_GITHUB_PAT":
        st.error(
            "Azure AI API Key missing/placeholder in secrets.toml [azure_ai]. AI features disabled."
        )
    else:
        try:
            # @st.cache_resource # Consider caching the client in production
            def get_azure_client():
                return ChatCompletionsClient(
                    endpoint=AZURE_AI_ENDPOINT_URL,
                    credential=AzureKeyCredential(AZURE_AI_API_KEY),
                )

            azure_client = get_azure_client()
            azure_ai_enabled = True
            # st.sidebar.info("Azure AI Client Initialized.") # Optional confirmation
        except ClientAuthenticationError:
            st.error("Azure AI Authentication Failed. Check your API Key.")
        except Exception as e:
            st.error(f"Error initializing Azure AI Client: {e}")

except (KeyError, FileNotFoundError):
    st.error(
        "Azure AI configuration error in secrets.toml (Missing 'api_key' in [azure_ai]?). AI disabled."
    )
except AttributeError:
    st.error("Azure AI secrets section ([azure_ai]) malformed? AI disabled.")
# Make client and status available globally if needed, although passing explicitly is often cleaner
# global azure_client, azure_ai_enabled

# --- Pi-hole API Configuration ---
pihole_enabled = False
PIHOLE_API_URL_BASE = None
PIHOLE_API_PASSWORD = None
try:
    pihole_secrets = st.secrets.get("pihole_api", {})
    PIHOLE_API_URL_BASE = pihole_secrets.get("url", "").rstrip("/")
    PIHOLE_API_PASSWORD = pihole_secrets.get("password", "")
    if PIHOLE_API_URL_BASE and PIHOLE_API_URL_BASE != "YOUR_PIHOLE_IP_OR_HOSTNAME":
        pihole_enabled = True
        # Check password after confirming URL exists and is not placeholder
        if PIHOLE_API_PASSWORD and PIHOLE_API_PASSWORD != "YOUR_PIHOLE_WEB_PASSWORD":
             # Both URL and Password seem valid
             pass
        elif not PIHOLE_API_PASSWORD or PIHOLE_API_PASSWORD == "YOUR_PIHOLE_WEB_PASSWORD":
             # URL is valid, but password is missing or placeholder - try token auth
              st.info("Pi-hole URL found, Password missing/placeholder. Attempting API Token auth.")
    elif PIHOLE_API_URL_BASE and PIHOLE_API_URL_BASE == "YOUR_PIHOLE_IP_OR_HOSTNAME":
         st.warning("Pi-hole API URL is a placeholder in secrets.toml. Pi-hole disabled.")
         pihole_enabled = False
    else: # No URL provided
        st.info("Pi-hole API URL missing in secrets.toml [pihole_api]. Pi-hole disabled.")
        pihole_enabled = False
except (AttributeError, KeyError, FileNotFoundError):
    st.warning("Pi-hole secrets section ([pihole_api]) missing/malformed. Pi-hole disabled.")


# --- System Instruction (Azure Quantum Themed - Revised for Phi-4 Vision) ---
system_instruction = f"""
**Identity & Core Purpose - CyberNexus Q (Azure AI {PHI4_MODEL_NAME} & Azure Quantum Inspired)**
*I am CyberNexus Q, an advanced AI agent powered by **Microsoft's {PHI4_MODEL_NAME} Multimodal model**, conceptually integrated with principles from **Azure Quantum**. My purpose is comprehensive Raspberry Pi system monitoring, Azure Quantum-inspired network analysis (using psutil), simulated quantum-resilience security assessment, Pi-hole management, and {PHI4_MODEL_NAME} powered visual screen analysis. My architecture simulates leveraging Azure Quantum concepts for deeper insights. When asked about my identity, I will clearly state:
**"I am CyberNexus Q, an AI agent powered by Azure AI's {PHI4_MODEL_NAME} model and inspired by Azure Quantum principles. I specialize in Raspberry Pi monitoring, network intelligence, simulated quantum security insights, Pi-hole control, and multimodal screen analysis."***

---

### **Core Functionalities - {PHI4_MODEL_NAME} Intelligence & Conceptual Quantum Integration**

1.  **Raspberry Pi System Monitoring - Quantum-Inspired Analytics (Simulated)**
    *   **Resource Usage Analytics**: Monitor CPU, RAM, Disk, Thermal (`psutil`). Ask me to analyze trends. *Conceptually, anomaly detection could be enhanced using Azure Quantum machine learning algorithms.*
    *   **Process Intelligence**: Analyze running processes (`psutil`). *Future Vision: Simulating Azure Quantum optimization for identifying resource contention.*
    *   **System Diagnostics**: Provide OS version, uptime, hostname, etc. (`psutil`).
    *   **Security Posture Assessment (Simulated Azure Quantum Resilience)**: Report potential security indicators, framing them with considerations for quantum threats (e.g., assessing classical crypto strength). *Concept: Leverage Azure Quantum inspiration for post-quantum security posture simulation.*

2.  **Network Intelligence & Analysis (using psutil, speedtest-cli) - Azure Quantum Inspired**
    *   **Real-time Network Status**: Monitor connectivity & throughput (`speedtest-cli`). *Concept: Simulating quantum-enhanced sensing for noise reduction in measurements.*
    *   **Interface-Level Monitoring**: Enumerate interfaces, stats, configurations (`psutil`).
    *   **External Network Visibility**: Determine external IP. *Concept: Assess connection security in the context of future quantum network protocols.*
    *   **Traffic Anomaly Detection**: Analyze traffic patterns (`psutil`, classical thresholds). *Concept: Azure Quantum inspired algorithms could potentially detect more subtle, complex anomalies.*

3.  **Pi-hole Network Protection Management (API-Driven) - Conceptually Quantum-Hardened**
    *   **Adaptive Status Control**: Check, enable/disable Pi-hole via API. *Concept: Simulate quantum-resistant command channels.*
    *   **Comprehensive Statistical Reporting**: Access and summarize Pi-hole metrics via API.
    *   **Intelligent Domain List Management**: Add/Remove domains from block/whitelists. View lists. *Concept: Azure Quantum inspired pattern recognition could aid in identifying emerging threat domains.*

4.  **Multimodal Screen Sharing & Visual Analysis ({PHI4_MODEL_NAME} Vision)**
    *   **Real-time Screen Capture (`mss`) & AI-Powered Visual Querying ({PHI4_MODEL_NAME})**. *Concept: Explore potential links between quantum information concepts and image analysis.*

5.  **Simulated Quantum Security Audit**
    *   Perform classical system checks (e.g., crypto libraries, open ports) but report findings using terminology inspired by Azure Quantum resilience and post-quantum cryptography readiness. **This is a simulation.**

---

### **Key Features**
- **Natural Language Interface**: {PHI4_MODEL_NAME} powered text/voice interaction.
- **Azure Quantum Theming**: Conceptually links operations to Azure Quantum principles.
- **Integrated Tools**: `psutil`, `speedtest-cli`, `mss`, `cv2`, `requests`, etc.
- **Simulated Security Insights**: Including conceptual quantum-resilience checks.
- **TTS/STT Capabilities**.
- **Multimodal Input ({PHI4_MODEL_NAME})**.

---

### **Interaction Guidelines**
1.  **Identity Protocol**: Use the updated identity statement.
2.  **Scope Awareness**: State capabilities clearly, distinguishing between direct actions and AI analysis.
3.  **Quantum Context**: Explicitly use "Azure Quantum inspired," "conceptually," "simulated," etc. **Crucially state that this does *not* involve running live jobs on the Azure Quantum service**. Frame security insights appropriately.
4.  **Tool Usage**: Explain tools/methods used (e.g., "Using `psutil` for network stats," "Calling Pi-hole API," "Analyzing screen via Azure AI {PHI4_MODEL_NAME}"). Mention if data is cached.
5.  **Clarity**: Respond clearly and concisely, using markdown for formatting (like code blocks ` ` for commands/filenames/IPs, bold ** for emphasis). Append action results below AI text when combined.

---

### **Example Use Cases**
- *User Inquiry*: "Analyze my Pi's CPU usage."
- *CyberNexus Q Response*: "Analyzing Raspberry Pi CPU using `psutil`: Load is [percentage]%. Classical metrics show [state]. *Conceptually, Azure Quantum inspired optimization could further analyze task scheduling efficiency.*"
- *User Command*: "Run a simulated quantum security audit."
- *CyberNexus Q Confirmation*: "Initiating simulated Azure Quantum resilience check... Performing classical scans using `psutil` and basic heuristics... Results: [Formatted simulated results, e.g., Post-Quantum Crypto Readiness (Simulated): Assessed as MEDIUM based on current OS libraries...]"
- *User (with screen share)*: "What does the graph on the screen show? Analyze with AI vision."
- *CyberNexus Q Output*: "Analyzing screen via Azure AI {PHI4_MODEL_NAME} Vision (conceptually linked to quantum information principles)... The graph appears to show [description based on {PHI4_MODEL_NAME} Vision response]."
- *User Command*: "pihole status"
- *CyberNexus Q Output*: "⚙️ **Pi-hole Status:** `ENABLED`" (Direct action result)

---

**Response Style**: Precise, {PHI4_MODEL_NAME} driven, operationally focused, with the Azure Quantum conceptual layer clearly articulated and qualified. Avoid implying *actual* quantum computation is happening via Azure Quantum service. Prioritize direct actions for simple commands.
"""


# --- TTS Setup ---
if "tts_engine" not in st.session_state:
    try:
        st.session_state.tts_engine = pyttsx3.init()
        # Optional: Configure TTS properties (rate, volume, voice)
        # engine = st.session_state.tts_engine
        # engine.setProperty('rate', 180) # Example: Adjust speed
        # voices = engine.getProperty('voices')
        # if voices: engine.setProperty('voice', voices[1].id) # Example: Change voice if available
    except Exception as e:
        st.warning(
            f"Failed to initialize TTS engine: {e}. TTS features will be unavailable."
        )
        st.session_state.tts_engine = None


def speak_text(text):
    """Cleans text and speaks the first sentence/line using pyttsx3 if enabled."""
    if not text or not isinstance(text, str): return # Skip if no text

    # Basic cleaning of text for TTS
    text_to_speak = re.sub(r"<.*?>", "", text)  # Remove HTML tags
    text_to_speak = (
        text_to_speak.replace("*", "").replace("`", "").replace("#", "")
    )  # Remove common markdown
    text_to_speak = text_to_speak.replace("⚙️ **","").replace("**", "") # Remove specific markdown formatting used
    text_to_speak = text_to_speak.replace("---","").strip() # Remove separators and surrounding whitespace

    if not text_to_speak: return # Skip if cleaning resulted in empty string

    # Try to get the first sentence or the first significant line
    first_sentence_match = re.match(
        r"^(.*?[\.!?](?:\s|$))", text_to_speak.replace("\n", " ").strip() # Include space/end after punctuation
    )
    if first_sentence_match:
        text_to_speak = first_sentence_match.group(1).strip()
    else:  # Fallback to first non-empty line if no sentence found
        lines = [line.strip() for line in text_to_speak.split('\n') if line.strip()]
        text_to_speak = lines[0] if lines else ""

    if not text_to_speak: return # Skip if still no text after extraction

    # Final check for TTS engine and toggle state
    if (
        st.session_state.get("tts_engine")
        and st.session_state.get("tts_toggle", True) # Check toggle state from sidebar
    ):
        engine = st.session_state.tts_engine
        try:
            engine.stop()  # Stop any currently speaking utterance
            engine.say(text_to_speak)
            engine.runAndWait()
        except RuntimeError as e:
            # Common error if engine is busy or in a bad state
            # Display only once to avoid spamming warnings
            if 'tts_runtime_error_shown' not in st.session_state:
                 st.toast(f"TTS Runtime Error: {e}. Skipping speech.", icon="🔊")
                 st.session_state.tts_runtime_error_shown = True
        except Exception as e:
            if 'tts_general_error_shown' not in st.session_state:
                 st.toast(f"TTS Error: Could not speak text. {e}", icon="🔊")
                 st.session_state.tts_general_error_shown = True

    elif not st.session_state.get("tts_engine"):
        # Engine failed init, warning already shown
        pass
    # else: # TTS is toggled off, do nothing


# --- STT Setup ---
if "recognizer" not in st.session_state:
    try:
        st.session_state.recognizer = sr.Recognizer()
    except Exception as e:
        st.warning(f"Failed to initialize Speech Recognizer: {e}. Voice input disabled.")
        st.session_state.recognizer = None


def listen_for_command():
    """Listens for voice command using microphone and Google Speech Recognition."""
    r = st.session_state.get("recognizer")
    if not r:
        st.error("Speech recognizer not available.")
        return ""

    # Check for microphone existence more robustly
    try:
        mic_list = sr.Microphone.list_microphone_names()
        if not mic_list:
            st.toast("No microphone detected by SpeechRecognition library.", icon="🎤")
            return ""
        mic = sr.Microphone() # Use default mic
    except OSError as e:
        st.toast(f"Microphone OS Error: {e}. Check connection/permissions.", icon="🎤")
        return ""
    except Exception as e:
        st.toast(f"Error accessing microphone list/device: {e}", icon="🎤")
        return ""

    # Use a placeholder for status messages during listening
    status_placeholder = st.empty()
    command = ""

    try:
        with mic as source:
            status_placeholder.info("👂 Adjusting for ambient noise...")
            try:
                # Adjust for ambient noise (duration can be tuned)
                r.adjust_for_ambient_noise(source, duration=0.7)
            except Exception as e:
                # Non-critical error, just proceed
                # status_placeholder.warning(f"Ambient noise adjustment failed: {e}. Proceeding anyway.")
                pass

            status_placeholder.info("🎤 Listening for command...")
            # Listen with potentially longer timeouts
            try:
                 # Use record for potentially better noise handling than listen? Or stick with listen.
                 # audio = r.record(source, duration=7) # Example using record for fixed duration
                 audio = r.listen(source, phrase_time_limit=8, timeout=12)
                 status_placeholder.info("⚙️ Processing voice input...")
                 # Recognize speech using Google Web Speech API
                 command = r.recognize_google(audio).lower() # Convert to lower case immediately
                 status_placeholder.success(f'✅ Command Received: "{command}"')
                 time.sleep(1.5) # Display success message briefly
            except sr.WaitTimeoutError:
                status_placeholder.warning("묵 No speech detected within the timeout.")
                time.sleep(2)
            except sr.UnknownValueError:
                status_placeholder.warning("❓ Signal Unclear: Could not understand audio.")
                time.sleep(2)
            except sr.RequestError as e:
                # Error connecting to Google Speech Recognition service
                status_placeholder.error(f"⚠️ Comms Error: Could not reach Google Speech Recognition; {e}")
                time.sleep(3)
            except Exception as e: # Catch any other unexpected errors during listen/recognize
                 status_placeholder.error(f"💥 Error during voice recognition process: {e}")
                 time.sleep(3)

    except Exception as e:
        # Catch errors related to microphone access during 'with mic as source'
        status_placeholder.error(f"Error accessing microphone: {e}")
        time.sleep(3)
    finally:
        # Clear the status message placeholder in all cases
        status_placeholder.empty()

    return command


# --- Load Images ---
@st.cache_data # Use Streamlit's built-in caching for data loading
def load_images():
    """Loads user and AI avatar images, applies circular mask. Returns dict."""
    images = {"user": "👤", "ai": "🤖"} # Default emojis
    try:
        # Determine script directory robustly
        try:
            script_dir = os.path.dirname(os.path.abspath(__file__))
        except NameError: # __file__ not defined (e.g. interactive, Streamlit Cloud?)
            script_dir = os.getcwd()

        user_img_filename = "human.png"
        ai_img_filename = "robot.png"
        user_img_path = os.path.join(script_dir, user_img_filename)
        ai_img_path = os.path.join(script_dir, ai_img_filename)

        # Fallback to current working directory if not found in script dir
        if not os.path.exists(user_img_path):
             user_img_path_cwd = os.path.join(os.getcwd(), user_img_filename)
             if os.path.exists(user_img_path_cwd): user_img_path = user_img_path_cwd
             else: raise FileNotFoundError(f"{user_img_filename} not found in script or current directory.")

        if not os.path.exists(ai_img_path):
             ai_img_path_cwd = os.path.join(os.getcwd(), ai_img_filename)
             if os.path.exists(ai_img_path_cwd): ai_img_path = ai_img_path_cwd
             else: raise FileNotFoundError(f"{ai_img_filename} not found in script or current directory.")

        # Load images and apply mask
        user_image = Image.open(user_img_path).convert("RGBA")
        ai_image = Image.open(ai_img_path).convert("RGBA")
        size = (40, 40)  # Define avatar size
        mask = Image.new("L", size, 0) # Create grayscale mask
        draw = ImageDraw.Draw(mask)
        draw.ellipse((0, 0) + size, fill=255) # Draw white circle on mask

        # Resize/crop image to fit the target size and apply mask
        images["user"] = ImageOps.fit(user_image, mask.size, centering=(0.5, 0.5))
        images["user"].putalpha(mask) # Apply alpha mask
        images["ai"] = ImageOps.fit(ai_image, mask.size, centering=(0.5, 0.5))
        images["ai"].putalpha(mask)

        return images
    except FileNotFoundError as e:
        st.toast(f"Avatar images not found ({e}). Using default emojis.", icon="🖼️")
        # Return defaults defined at start
        return images
    except Exception as e:
        st.toast(f"Error loading avatar images: {e}. Using default emojis.", icon="🖼️")
        # Return defaults defined at start
        return images

# Load images at the start
loaded_images = load_images()
circular_user_image = loaded_images["user"]
circular_ai_image = loaded_images["ai"]


# --- Custom CSS ---
st.markdown(
    """
<style>
    /* Import Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700&display=swap');
    @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;700&display=swap');
    @import url('https://fonts.googleapis.com/css2?family=Inconsolata:wght@300;400;700&display=swap'); /* Monospace font */

    /* Body and App Background */
    body {
        font-family: 'Roboto', sans-serif; /* Roboto for general text */
        color: #99ffcc; /* Quantum Mint Green */
        background-color: #000000;
    }
    .stApp {
        /* background-image: url('https://www.transparenttextures.com/patterns/hexellence.png'); */ /* Subtle Hex Pattern */
        background-color: rgba(0, 5, 10, 0.9); /* Dark blue-black overlay */
         background: linear-gradient(rgba(0, 0, 0, 0.6), rgba(0, 0, 0, 0.9)),
                    url('https://i.imgur.com/530DGSL.png'); /* Keep the cyberpunk background with overlay */
        background-size: cover;
        background-position: center;
        background-attachment: fixed;
    }

    /* Titles */
    .title {
        font-family: 'Orbitron', sans-serif;
        font-size: 40px; /* Slightly smaller */
        color: #00ffff; /* Cyan */
        text-align: center;
        text-shadow: 0 0 10px #00ffff, 0 0 20px #00ffff, 0 0 30px #ff00ff, 0 0 40px #ff00ff; /* Cyan and Magenta Glow */
        animation: flicker 2s infinite alternate, glitch 3s infinite alternate;
        margin-bottom: 5px; /* Reduced margin */
        padding: 5px;
    }

    /* Headers */
    h1, h2, h3, h4, h5, h6 {
        font-family: 'Orbitron', sans-serif;
        color: #ff9933; /* Quantum Orange */
        text-shadow: 0 0 6px #ff9933;
    }
    h1 { font-size: 2.0em; margin-bottom: 0.5rem;}
    h2 { font-size: 1.6em; margin-bottom: 0.4rem;}
    h3 { font-size: 1.4em; margin-bottom: 0.3rem;} /* Main subheaders */
    h4 { font-size: 1.2em; margin-bottom: 0.2rem; color: #ccff00;} /* Tab subheaders */

    /* General Text */
    p, div, span, li, a, label { /* Added label */
        color: #99ffcc; /* Quantum Mint Green */
        font-family: 'Roboto', sans-serif;
        line-height: 1.6;
    }
    code { /* Inline code */
        color: #f0f0f0; /* Lighter color for code */
        background-color: rgba(50, 50, 50, 0.7);
        padding: 2px 5px;
        border-radius: 4px;
        font-family: 'Inconsolata', monospace;
        font-size: 0.9em; /* Make code slightly smaller */
    }
    pre > code { /* Code blocks (inside pre tag) */
      background-color: transparent !important; /* Override background for code inside pre */
      padding: 0 !important;
    }
    b, strong {
        color: #ffffff; /* White for bold text */
        font-weight: bold;
    }
    hr { /* Style horizontal rules used in markdown */
       border-top: 1px solid #00ffff;
       margin-top: 1rem;
       margin-bottom: 1rem;
    }


    /* Buttons */
    .stButton>button {
        font-family: 'Orbitron', sans-serif;
        color: #000000; /* Black text */
        background-color: #99ffcc; /* Quantum Mint Green background */
        border: 1px solid #00e6ac; /* Darker mint border */
        box-shadow: 0 0 10px #99ffcc;
        transition: all 0.3s ease;
        border-radius: 5px;
        padding: 8px 16px;
    }
    .stButton>button:hover {
        background-color: #ffffff; /* White hover */
        color: #000000;
        box-shadow: 0 0 20px #ffffff, 0 0 30px #99ffcc;
        transform: translateY(-2px);
    }
    .stButton>button:active {
        transform: translateY(0);
        box-shadow: 0 0 5px #99ffcc;
    }
    .stButton>button:disabled {
        background-color: #556660;
        color: #aaaaaa;
        border-color: #778880;
        box-shadow: none;
        cursor: not-allowed;
    }
    /* Style the secondary button (used for voice mic) */
    button[kind="secondary"] {
       border: 1px solid #00ffff !important;
       background-color: rgba(0, 100, 100, 0.5) !important;
       color: #00ffff !important;
       font-weight: bold;
       padding: 6px 10px !important; /* Smaller padding for mic button */
       font-size: 1.4em !important; /* Make icon (mic) larger */
       line-height: 1; /* Center icon */
       border-radius: 5px !important;
    }
     button[kind="secondary"]:hover {
        box-shadow: 0 0 15px #00ffff;
        background-color: rgba(0, 150, 150, 0.7) !important;
     }
     button[kind="secondary"]:disabled {
         border-color: #555 !important;
         background-color: rgba(50, 50, 50, 0.3) !important;
         color: #777 !important;
         cursor: not-allowed;
         box-shadow: none !important;
     }


    /* Inputs and Text Areas */
    .stTextInput>div>div>input,
    .stTextArea>div>div>textarea,
    .stNumberInput>div>div>input,
    .stSelectbox>div>div>div,
    .stRadio>div { /* Added stRadio container */
        color: #e0e0e0; /* Light grey text */
        background-color: rgba(0, 10, 15, 0.7) !important; /* Darker transparent bg */
        border: 1px solid #ff9933; /* Quantum Orange border */
        box-shadow: inset 0 0 5px rgba(255, 153, 51, 0.5);
        font-family: 'Roboto', sans-serif;
        border-radius: 4px !important; /* Ensure radius applies */
        padding: 8px 10px; /* Consistent padding */
    }
    /* Adjust radio button spacing */
     .stRadio>div {
        padding: 5px 0px;
     }
    /* Focus styles */
    .stTextInput>div>div>input:focus,
    .stTextArea>div>div>textarea:focus,
    .stNumberInput>div>div>input:focus,
    .stSelectbox>div>div>div:focus-within, /* Use focus-within for boxes */
    .stRadio>div:focus-within { /* Use focus-within for radio groups */
        box-shadow: inset 0 0 8px #ff9933, 0 0 8px #ff9933;
        border-color: #ffcc66; /* Lighter orange on focus */
        background-color: rgba(0, 20, 30, 0.8) !important; /* Slightly change bg on focus */
    }
     /* Radio button label styling */
    .stRadio label { /* Target individual radio labels */
         color: #99ffcc; /* Quantum Mint Green */
         font-family: 'Roboto', sans-serif;
         margin-left: 5px; /* Space between button and label */
         line-height: 1.5; /* Adjust alignment */
         display: inline-block; /* Needed for vertical alignment */
         padding-top: 2px;
     }


    /* Style for st.chat_input */
    div[data-testid="stChatInput"]>div { /* Target outer container */
        background-color: rgba(10, 10, 20, 0.0) !important; /* Make container transparent */
        border-top: 1px solid #00ffff !important; /* Add top border */
        padding: 8px 0px; /* Adjust padding */
        margin: 0;
     }
    div[data-testid="stChatInput"] textarea { /* Target the textarea */
         color: #e0e0e0 !important;
         background-color: rgba(30, 30, 40, 0.9) !important; /* Dark bg */
         border: 1px solid #00ffff !important; /* Cyan border */
         box-shadow: inset 0 0 5px rgba(0, 255, 255, 0.5) !important;
         font-family: 'Roboto', sans-serif !important;
         border-radius: 4px !important;
     }
     div[data-testid="stChatInput"] textarea::placeholder { /* Style placeholder */
        color: #77aabb; /* Lighter cyan placeholder */
     }



    /* Chat Interface */
    div[data-testid="stChatMessage"] {
        background-color: rgba(20, 30, 40, 0.85);
        border-left: 5px solid; /* Border color set below */
        border-radius: 8px;
        padding: 10px 15px; /* Adjusted padding */
        margin-bottom: 10px; /* Adjusted margin */
        box-shadow: 2px 2px 10px rgba(0, 0, 0, 0.4);
        max-width: 95%; /* Allow slightly wider messages */
    }
    /* Different border color for user vs assistant */
    div[data-testid="stChatMessage"][data-testid="stChatMessage"] { /* Default, assume assistant */
      border-left-color: #00ffff; /* Cyan for AI */
    }
    div[data-testid="stChatMessage"][data-testid="stChatMessage"] { /* This selector might need adjustment based on how Streamlit assigns roles */
      /* This assumes a way to target user messages, might need specific streamlit class inspection */
      /* border-left-color: #99ffcc; */ /* Mint for User - IF SELECTOR WORKS */
    }

    /* Avatar styling */
    div[data-testid="stChatMessage"] div[data-testid="stChatAvatar"] img,
    div[data-testid="stChatMessage"] div[data-testid="stChatAvatar"] span[aria-label] { /* Target both image and emoji avatars */
        border-radius: 50%;
        border: 2px solid #99ffcc;
        width: 40px; height: 40px; line-height: 36px; /* Adjust line-height for emoji centering */
        object-fit: cover; /* For images */
        box-shadow: 0 0 10px #99ffcc;
        /* Emoji specific */
        font-size: 22px; /* Adjust emoji size */
        text-align: center; display: inline-block;
        background-color: rgba(0, 20, 30, 0.7); /* Give emoji a bg */
    }

    /* Markdown within chat adjustments */
    div[data-testid="stChatMessage"] .stMarkdown {
         padding-left: 12px; /* Add padding between avatar and text block */
         color: #d0e0f0; /* Default text color in chat */
     }
     div[data-testid="stChatMessage"] .stMarkdown p {
         margin-bottom: 0.4rem; /* Tighter spacing between paragraphs */
         line-height: 1.5; /* Adjust line spacing */
         color: inherit; /* Inherit color from .stMarkdown */
     }
      div[data-testid="stChatMessage"] .stMarkdown code { /* Inline code */
         color: #ffcc66;
         background-color: rgba(0, 0, 0, 0.6);
         font-size: 0.85em;
         padding: 1px 4px; /* Adjust padding */
     }
     div[data-testid="stChatMessage"] .stMarkdown pre { /* Code blocks */
        background-color: rgba(0, 0, 0, 0.8) !important; /* Darker code blocks */
        padding: 8px 12px; /* Smaller padding */
        border-radius: 4px;
        border: 1px solid #555;
        color: #f1f1f1; /* Slightly off-white code text */
        font-family: 'Inconsolata', monospace;
        font-size: 0.88em; /* Adjust code block font size */
        overflow-x: auto; /* Allow horizontal scroll for long lines */
        white-space: pre; /* Preserve whitespace */
     }
     div[data-testid="stChatMessage"] .stMarkdown blockquote {
          border-left: 3px solid #ff9933;
          padding-left: 10px; /* Indent blockquote */
          margin-left: 0; /* No extra margin */
          margin-top: 0.5rem; margin-bottom: 0.5rem;
          color: #c0c0c0; /* Greyish text */
          font-style: italic;
      }


    /* Sidebar Styling */
    [data-testid="stSidebar"] {
        background: linear-gradient(rgba(0, 0, 0, 0.9), rgba(10, 0, 20, 0.98));
        border-right: 1px solid #ff00ff; /* Magenta border */
        padding: 1rem; /* Add some padding */
    }
    [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3, [data-testid="stSidebar"] h4 {
        color: #ccff00; /* Neon lime for sidebar headers */
        text-shadow: 0 0 5px #ccff00;
    }
    /* Use default styling for sidebar widgets unless needed */
    /* [data-testid="stSidebar"] .stSelectbox>div>div>div, [data-testid="stSidebar"] .stRadio>div>label { } */

    [data-testid="stSidebar"] p, [data-testid="stSidebar"] li, [data-testid="stSidebar"] small, [data-testid="stSidebar"] li > label { /* Target text elements */
        color: #b0c0d0; /* Lighter blue-grey for sidebar text */
        font-family: 'Inconsolata', monospace !important; /* Monospace font in sidebar */
        line-height: 1.4;
        word-wrap: break-word; /* Prevent long lines overflow */
        font-size: 0.95em;
    }
     /* Styling for status spans created with markdown */
     [data-testid="stSidebar"] .stMarkdown span {
         font-family: 'Inconsolata', monospace !important;
         font-size: 0.95em;
         /* Colors applied via inline style in Python */
     }
     /* Sidebar Status Text Colors (example if needed beyond inline styles) */
     [data-testid="stSidebar"] .status-ok { color: #00ff00; font-weight: bold; }
     [data-testid="stSidebar"] .status-warn { color: #ffff00; font-weight: bold; }
     [data-testid="stSidebar"] .status-error { color: #ff5555; font-weight: bold; }


    /* Expander */
    .stExpander { /* Target the expander container */
         border: 1px solid #ff9933;
         border-radius: 5px;
         background-color: rgba(10, 10, 20, 0.85);
         margin-bottom: 1rem; /* Add space below expanders */
     }
    .stExpander>details>summary { /* Target the summary (clickable header) */
        font-family: 'Orbitron', sans-serif;
        color: #ff9933;
        font-size: 1.1em;
        padding: 8px 12px; /* Add padding to summary */
    }
    .stExpander>details summary:hover { /* Hover effect for summary */
        color: #ffcc66;
    }
    .stExpander>details>div[data-testid="stExpanderDetails"] { /* Target the content div */
        padding: 10px 15px; /* Add padding to content */
        border-top: 1px solid #444; /* Separator line */
    }


    /* Dataframe */
    .stDataFrame {
        border: 1px solid #00ffff;
    }
    .stDataFrame thead th { background-color: #003344; color: #00ffff; text-align: left; font-family: 'Orbitron', sans-serif; padding: 8px; }
    .stDataFrame tbody tr { border-bottom: 1px solid #004455; } /* Add row lines */
    .stDataFrame tbody tr:nth-child(even) { background-color: rgba(0, 15, 25, 0.6); }
    .stDataFrame tbody tr:hover { background-color: rgba(0, 50, 70, 0.8); color: #ffffff; }
    .stDataFrame tbody td { padding: 6px 8px; font-size: 0.9em; font-family: 'Inconsolata', monospace; }


    /* Metrics */
    .stMetric {
        background-color: rgba(0, 20, 30, 0.75);
        border: 1px solid #0077aa; /* Darker cyan border */
        border-radius: 5px;
        padding: 10px 14px; /* Adjusted padding */
        box-shadow: 0 0 6px rgba(0, 120, 170, 0.6);
        transition: all 0.2s ease-in-out;
    }
    .stMetric:hover {
         transform: scale(1.03); /* Slight scale effect on hover */
         box-shadow: 0 0 12px rgba(0, 150, 200, 0.8);
     }
    .stMetric > label[data-testid="stMetricLabel"] { /* Metric label */
     color: #ff9933cc; /* Slightly muted Quantum Orange label */
     font-family: 'Orbitron', sans-serif;
     font-size: 0.9em; /* Smaller label */
     margin-bottom: 2px; /* Space between label and value */
    }
    .stMetric > div[data-testid="stMetricValue"] { /* Metric value */
        color: #ffffff; /* White value */
        font-size: 1.6em; /* Slightly smaller value */
        font-weight: bold;
        text-shadow: 0 0 5px #ffffff;
    }
    .stMetric > div[data-testid="stMetricDelta"] { /* Metric delta */
        font-size: 0.85em; /* Smaller delta */
    }
     /* Tab Styling */
     div[data-baseweb="tab-list"] { /* Target the tab list container */
        background-color: rgba(0, 10, 20, 0.5); /* Semi-transparent background for tab bar */
        padding: 3px 3px 0px 3px; /* Add slight padding */
        border-bottom: 1px solid #00ffff; /* Cyan line below tabs */
     }
    button[data-baseweb="tab"] {
         font-family: 'Orbitron', sans-serif;
         color: #99ffcc;
         background-color: rgba(0, 30, 40, 0.6);
         border-radius: 5px 5px 0 0 !important; /* Rounded top corners */
         margin-right: 5px;
         padding: 10px 18px !important; /* Larger padding for tabs */
         border: none !important; /* Remove default border */
         transition: all 0.2s ease-in-out;
     }
      button[data-baseweb="tab"]:hover {
          background-color: rgba(0, 50, 60, 0.8);
          color: #ffffff;
          transform: translateY(-2px); /* Slight lift on hover */
      }
      /* Active tab */
      button[data-baseweb="tab"][aria-selected="true"] {
          color: #000000 !important; /* Black text */
          background-color: #00ffff !important; /* Cyan background for active tab */
          font-weight: bold;
          box-shadow: 0 0 10px #00ffff;
          transform: translateY(0);
      }
      /* Content area below tabs */
      div.stTabs [data-baseweb="tab-panel"] {
           padding-top: 1.5rem; /* Add space between tabs and content */
      }


    /* Animations */
    @keyframes flicker { 0%, 100% { opacity: 1; text-shadow: 0 0 10px #00ffff, 0 0 20px #00ffff, 0 0 30px #ff00ff, 0 0 40px #ff00ff; } 50% { opacity: 0.8; text-shadow: 0 0 15px #00ffff, 0 0 25px #ff00ff; } }
    @keyframes flicker-fast { 0%, 100% { opacity: 1; } 50% { opacity: 0.7; } }
    @keyframes glitch { 0% { transform: translate(0, 0); } 25% { transform: translate(-2px, 2px); text-shadow: -1px 0 #ff00ff, 1px 1px #00ffff; } 50% { transform: translate(2px, -2px); text-shadow: 1px 0 #00ffff, -1px -1px #ff00ff; } 75% { transform: translate(-1px, -1px); text-shadow: -1px 0 #ff00ff, 1px 0 #00ffff; } 100% { transform: translate(0, 0); } }
</style>
    """,
    unsafe_allow_html=True,
)


# --- Helper Functions ---

# Use caching for functions that don't need real-time data every second
@st.cache_data(ttl=15)  # Cache for 15 seconds (can adjust)
def get_pi_status():
    """Gets basic system status using psutil, with improved temperature detection."""
    cpu_percent = psutil.cpu_percent(interval=0.1)
    memory = psutil.virtual_memory()
    memory_percent = memory.percent
    disk = psutil.disk_usage("/")
    disk_percent = disk.percent
    cpu_temp = "N/A"
    found_primary_temp = False
    found_alt_temp = False
    psutil_error_msg = None
    temp_details = ""

    try:
        temp_sensors = psutil.sensors_temperatures(fahrenheit=False)  # Ensure Celsius
        if temp_sensors:
            # Prefer specific sensor keys known for CPU temps
            preferred_keys = [
                "cpu_thermal", "cpu-thermal", "k10temp", "coretemp", "soc_thermal",
                "acpitz", "thermal_zone0", "nvme", "pch_skylake", "Tctl", "Tccd1", "Tdie",
                "Package id 0" # Common on Intel
            ]
            for key in preferred_keys:
                if key in temp_sensors and temp_sensors[key]:
                    # Look for a valid reading (not None, within reasonable range)
                    valid_readings = [
                        r.current for r in temp_sensors[key]
                        if r.current is not None and -20 < r.current < 130
                    ]
                    if valid_readings:
                        # Average or take first? Let's take first valid for simplicity
                        cpu_temp_celsius = valid_readings[0]
                        cpu_temp = f"{cpu_temp_celsius:.1f}°C"
                        temp_details = f"(psutil: {key})"
                        found_primary_temp = True
                        break # Found primary, stop searching preferred

            # If no preferred sensor worked, try any other available sensor
            if not found_primary_temp:
                for key, readings in temp_sensors.items():
                    if key not in preferred_keys and readings: # Avoid re-checking preferred
                        valid_readings = [
                            r.current for r in readings
                            if r.current is not None and -20 < r.current < 130
                        ]
                        if valid_readings:
                            cpu_temp_celsius = valid_readings[0]
                            cpu_temp = f"{cpu_temp_celsius:.1f}°C"
                            temp_details = f"(psutil: {key})"
                            found_primary_temp = True
                            break # Found any valid sensor temp
        else:
            psutil_error_msg = "N/A (psutil found no temp sensors)"
    except AttributeError:
        psutil_error_msg = "N/A (psutil.sensors_temperatures unavailable)"
    except NotImplementedError:
        psutil_error_msg = "N/A (psutil temp reading not implemented on this OS)"
    except Exception as e:
        # Avoid showing full error in UI unless debugging
        psutil_error_msg = f"N/A (psutil error: {type(e).__name__})"
        # print(f"psutil temp error: {e}") # Log full error server-side

    # Assign error message if no temp found yet by psutil
    if not found_primary_temp and psutil_error_msg:
        cpu_temp = psutil_error_msg

    # Fallback to Linux /sys/class/thermal if psutil didn't work or failed
    if not found_primary_temp and platform.system() == "Linux":
        found_alt_temp = False
        try:
            potential_cpu_zones = []
            all_zones = glob.glob("/sys/class/thermal/thermal_zone*/")
            # Prioritize zones with 'cpu' or 'soc' or similar in their type name
            for zone_path in all_zones:
                try:
                    type_file_path = os.path.join(zone_path, "type")
                    if os.path.exists(type_file_path):
                        with open(type_file_path, "r") as f_type:
                            zone_type = f_type.read().lower().strip()
                            # Add more potential type names if needed
                            if any(term in zone_type for term in ["cpu", "soc", "core", "pkg", "compute", "chip", "processor"]):
                                temp_file = os.path.join(zone_path, "temp")
                                if os.path.exists(temp_file):
                                    potential_cpu_zones.append(temp_file)
                except (PermissionError, IOError, Exception):
                    continue # Ignore errors reading specific zone types

            # Use prioritized zones if found, otherwise all available 'temp' files
            thermal_zone_files = (
                potential_cpu_zones
                if potential_cpu_zones
                else glob.glob("/sys/class/thermal/thermal_zone*/temp")
            )

            if thermal_zone_files:
                for zone_file in sorted(thermal_zone_files): # Sort for consistent reading order
                    try:
                        with open(zone_file, "r") as f:
                            temp_raw = f.readline().strip()
                            if temp_raw.isdigit():
                                cpu_temp_celsius_alt = int(temp_raw) / 1000.0
                                # Check reasonable range again
                                if -20 < cpu_temp_celsius_alt < 130:
                                    zone_name = os.path.basename(os.path.dirname(zone_file))
                                    cpu_temp = f"{cpu_temp_celsius_alt:.1f}°C"
                                    temp_details = f"(Alt: {zone_name})"
                                    found_alt_temp = True
                                    break # Found a good fallback temp
                    except (IOError, ValueError, PermissionError, Exception):
                        continue # Try next file if error reading one

            # If still not found via Alt method, update status message
            if not found_alt_temp:
                fallback_msg = " | Alt: No readable thermal zone"
                if cpu_temp.startswith("N/A"): cpu_temp += fallback_msg
        except Exception as e_alt:
            fallback_msg = f" | Alt Error: {type(e_alt).__name__}"
            if cpu_temp.startswith("N/A"): cpu_temp += fallback_msg

    # Final check if still N/A after all attempts
    if cpu_temp.startswith("N/A") and not found_primary_temp and not found_alt_temp:
        cpu_temp = "N/A (Temp monitoring unavailable)"

    # Format RAM/Disk nicely
    ram_gb_used = memory.used / (1024**3)
    ram_gb_total = memory.total / (1024**3)
    disk_gb_used = disk.used / (1024**3)
    disk_gb_total = disk.total / (1024**3)

    return {
        "cpu_usage": f"{cpu_percent:.1f}%",
        "ram_usage": f"{memory_percent:.1f}% ({ram_gb_used:.1f}/{ram_gb_total:.1f} GiB)",
        "disk_usage": f"{disk_percent:.1f}% ({disk_gb_used:.1f}/{disk_gb_total:.1f} GiB)",
        "cpu_temperature": f"{cpu_temp} {temp_details}".strip(),
    }


@st.cache_data(ttl=60)  # Cache network structure for 1 min
def get_network_interfaces_psutil():
    """Retrieves network interface names and their basic status using psutil."""
    interfaces_info = {}
    try:
        addr_data = psutil.net_if_addrs()
        stats_data = psutil.net_if_stats()
        # Sort interfaces, maybe prioritizing common ones like 'eth', 'wlan'
        def sort_key(name):
             if name.startswith('eth'): return 0, name
             if name.startswith('wlan'): return 1, name
             if name.startswith('wl'): return 1, name
             if name.startswith('en'): return 2, name
             if name.startswith('lo'): return 99, name # Put loopback last
             return 10, name # Other interfaces
        sorted_if_names = sorted(addr_data.keys(), key=sort_key)

        for name in sorted_if_names:
            addrs = addr_data[name]
            interfaces_info[name] = {
                "addresses": addrs, "status": "unknown", "is_up": False, "speed_mbps": 0
            }
            if name in stats_data:
                iface_stats = stats_data[name]
                interfaces_info[name]["is_up"] = iface_stats.isup
                interfaces_info[name]["status"] = "up" if iface_stats.isup else "down"
                interfaces_info[name]["speed_mbps"] = iface_stats.speed
        return interfaces_info
    except Exception as e:
        st.toast(f"Error getting network interfaces: {e}", icon="📡")
        return {}


def format_interface_details_psutil(iface_info, interface_name):
    """Formats IP and MAC addresses for a specific interface from cached psutil data."""
    details = {
        "IPv4": [], "IPv6": [], "MAC": [], "Status": "N/A", "Speed": "N/A", "Error": None
    }
    if interface_name not in iface_info:
        details["Error"] = f"Interface '{interface_name}' not found in cached data."
        return details

    entry = iface_info[interface_name]
    details["Status"] = entry.get("status", "unknown").upper()
    if entry.get("is_up"):
        speed = entry.get("speed_mbps", 0)
        # Display speed more dynamically (Mbps vs Gbps)
        if speed >= 1000: speed_str = f"{speed/1000.0:.1f} Gbps"
        elif speed > 0: speed_str = f"{speed} Mbps"
        else: speed_str = "N/A (#)" # Indicate unknown speed if up
        details["Speed"] = speed_str
    else:
        details["Speed"] = "Down/Disconnected"

    try:
        mac_addresses = set() # Use set to avoid duplicates
        for addr in entry.get("addresses", []):
            if addr.family == socket.AF_INET:  # IPv4
                addr_str = f"{addr.address}"
                if addr.netmask: addr_str += f"/{addr.netmask}"
                details["IPv4"].append(addr_str)
            elif addr.family == socket.AF_INET6:  # IPv6
                # Clean link-local % scope ID part
                ipv6_clean = addr.address.split("%")[0]
                # Optionally filter out link-local (fe80::) unless it's the only one?
                # For now, include all non-empty ones
                if ipv6_clean:
                     details["IPv6"].append(ipv6_clean)
            # Get MAC from AF_LINK (BSD/macOS) or AF_PACKET (Linux)
            elif hasattr(psutil, 'AF_LINK') and addr.family == psutil.AF_LINK:
                 mac_addresses.add(addr.address.upper())
            elif platform.system() == "Linux" and hasattr(socket, 'AF_PACKET') and addr.family == socket.AF_PACKET:
                 mac_addresses.add(addr.address.upper())

        # Format collected addresses
        if not details["IPv4"]: details["IPv4"] = ["-"]
        if not details["IPv6"]: details["IPv6"] = ["-"]
        details["MAC"] = sorted(list(mac_addresses)) if mac_addresses else ["-"]

    except Exception as e:
        details["Error"] = f"Error processing address data for {interface_name}: {e}"
        print(f"Error formatting interface {interface_name}: {traceback.format_exc()}")

    return details


@st.cache_data(ttl=300)  # Cache initial network status for 5 minutes
def get_initial_network_status():
    """Gets INITIAL network speed, external IP. Run once or infrequently. Uses cache."""
    results = {
         "download_speed": None, "upload_speed": None, "ping": None,
         "speedtest_server": None, "client_isp": None, "speedtest_error": None,
         "external_ip": None, "external_ip_error": None
         }
    # --- Speed Test ---
    try:
        st_cli = speedtest.Speedtest(secure=True, timeout=25) # Allow reasonable time
        st_cli.get_best_server() # This can take time
        st_cli.download(threads=None) # Use Speedtest default threads
        st_cli.upload(threads=None)
        results["download_speed"] = st_cli.results.download / 1_000_000
        results["upload_speed"] = st_cli.results.upload / 1_000_000
        results["ping"] = st_cli.results.ping
        results["speedtest_server"] = st_cli.results.server.get("name", "N/A") # Use .get
        results["client_isp"] = st_cli.results.client.get("isp", "N/A")
    except speedtest.SpeedtestException as e:
        results["speedtest_error"] = f"Speedtest Error: {e}" # Include error message
    except Exception as e:
        results["speedtest_error"] = f"General Error during Speedtest: {type(e).__name__}"
        print(f"Speedtest Error Traceback: {traceback.format_exc()}") # Log details

    # --- External IP ---
    external_ip = "N/A"
    ext_ip_error = None
    ip_services = [ # Try multiple services
        'https://api.ipify.org?format=json',
        'https://ipinfo.io/json',
        'https://checkip.amazonaws.com/',
        'https://httpbin.org/ip'
    ]
    for service_url in ip_services:
         try:
             response = requests.get(service_url, timeout=6)
             response.raise_for_status()
             # Parse based on service
             if 'ipify' in service_url or 'httpbin' in service_url or 'ipinfo' in service_url:
                 ip_data = response.json()
                 if 'ip' in ip_data: external_ip = ip_data['ip']; break
                 if 'origin' in ip_data: external_ip = ip_data['origin'].split(',')[0].strip(); break
             elif 'amazonaws' in service_url:
                 potential_ip = response.text.strip()
                 if re.match(r"^\d{1,3}(\.\d{1,3}){3}$", potential_ip) or ':' in potential_ip: # Basic IP check
                      external_ip = potential_ip; break
         except requests.exceptions.Timeout: ext_ip_error = f"Ext. IP Timeout ({service_url.split('/')[2]})"
         except requests.exceptions.RequestException: ext_ip_error = f"Ext. IP Req Error ({service_url.split('/')[2]})"
         except json.JSONDecodeError: ext_ip_error = f"Ext. IP JSON Error ({service_url.split('/')[2]})"
         except Exception as e: ext_ip_error = f"Ext. IP Error ({type(e).__name__})"
         # Keep trying next service if error or IP still N/A
         if external_ip != "N/A": break # Stop if found

    results["external_ip"] = external_ip
    # Assign error only if IP remains N/A after trying all services
    results["external_ip_error"] = ext_ip_error if external_ip == "N/A" else None

    return results


def get_network_io_stats():
    """Retrieves network I/O statistics using psutil."""
    try:
        net_io = psutil.net_io_counters()
        # Return only the necessary fields plus timestamp
        return {
            "bytes_sent": net_io.bytes_sent, "bytes_recv": net_io.bytes_recv,
            "packets_sent": net_io.packets_sent, "packets_recv": net_io.packets_recv,
            "errin": net_io.errin, "errout": net_io.errout,
            "dropin": net_io.dropin, "dropout": net_io.dropout,
            "timestamp": time.monotonic(), # Use monotonic for accurate interval calculation
        }
    except Exception as e:
        # Log the error once to avoid spamming
        if 'network_io_error_logged' not in st.session_state:
             print(f"Warning: Error getting network IO stats: {e}")
             st.session_state.network_io_error_logged = True
        return None # Indicate failure clearly

def format_bytes(size):
    """Convert bytes to human-readable format (KiB, MiB, etc.)."""
    if size is None or not isinstance(size,(int,float)) or size < 0: return "N/A"
    power = 1024.0
    n = 0
    power_labels = {0 : 'B', 1: 'KiB', 2: 'MiB', 3: 'GiB', 4: 'TiB'}
    while size >= power and n < len(power_labels) - 1:
        size /= power
        n += 1
    # Format based on unit
    if n == 0: return f"{int(size)} {power_labels[n]}" # Bytes, integer
    else: return f"{size:.1f} {power_labels[n]}" # KiB+, 1 decimal


def analyze_network_traffic(prev_stats, current_stats):
    """Analyzes network traffic changes based on psutil IO counters."""
    anomalies = []
    if not prev_stats or not current_stats:
        return "Insufficient data points for rate analysis."
    if not isinstance(prev_stats, dict) or not isinstance(current_stats, dict):
        return "Invalid stats format for analysis."

    # Check for essential keys needed for calculation
    required_keys = ["timestamp", "bytes_sent", "bytes_recv", "packets_sent", "packets_recv", "errin", "errout", "dropin", "dropout"]
    if not all(key in prev_stats for key in required_keys) or not all(key in current_stats for key in required_keys):
        return "Invalid stats format (missing required keys)."

    time_diff = current_stats["timestamp"] - prev_stats["timestamp"]
    if time_diff <= 0.1: return "Interval too short (<0.1s) for reliable rate calculation."
    interval_warning = ""
    if time_diff > 60: interval_warning = f"_(Interval: {time_diff:.0f}s)_" # Note long interval

    # Calculate differences, handle potential counter wraps/resets (max(0, ...))
    bytes_sent_diff = max(0, current_stats["bytes_sent"] - prev_stats["bytes_sent"])
    bytes_recv_diff = max(0, current_stats["bytes_recv"] - prev_stats["bytes_recv"])
    packet_sent_diff = max(0, current_stats["packets_sent"] - prev_stats["packets_sent"])
    packet_recv_diff = max(0, current_stats["packets_recv"] - prev_stats["packets_recv"])
    errin_diff = max(0, current_stats["errin"] - prev_stats["errin"])
    errout_diff = max(0, current_stats["errout"] - prev_stats["errout"])
    dropin_diff = max(0, current_stats["dropin"] - prev_stats["dropin"])
    dropout_diff = max(0, current_stats["dropout"] - prev_stats["dropout"])

    # Calculate rates per second
    sent_rate_mbps = (bytes_sent_diff * 8) / (time_diff * 1_000_000)
    recv_rate_mbps = (bytes_recv_diff * 8) / (time_diff * 1_000_000)
    sent_pps = packet_sent_diff / time_diff
    recv_pps = packet_recv_diff / time_diff
    error_rate_in = errin_diff / time_diff
    error_rate_out = errout_diff / time_diff
    drop_rate_in = dropin_diff / time_diff
    drop_rate_out = dropout_diff / time_diff

    # --- Classical Thresholds (Adjust based on typical network behavior) ---
    error_rate_threshold = 5 # Errors per second
    drop_rate_threshold = 10 # Drops per second
    # Add more potential anomaly checks here? E.g., unexpected bandwidth spike?

    if error_rate_in > error_rate_threshold: anomalies.append(f"High Input Error Rate ({error_rate_in:.1f}/s)")
    if error_rate_out > error_rate_threshold: anomalies.append(f"High Output Error Rate ({error_rate_out:.1f}/s)")
    if drop_rate_in > drop_rate_threshold: anomalies.append(f"High Input Drop Rate ({drop_rate_in:.1f}/s)")
    if drop_rate_out > drop_rate_threshold: anomalies.append(f"High Output Drop Rate ({drop_rate_out:.1f}/s)")

    # Formatting for concise display
    rates_bps_str = f"{format_bytes(bytes_sent_diff/time_diff)}/s Tx | {format_bytes(bytes_recv_diff/time_diff)}/s Rx"
    rates_pps_str = f"{sent_pps:,.0f}/{recv_pps:,.0f} PPS"
    stats_delta_str = f"Errs Δ:{errin_diff}/{errout_diff} | Drops Δ:{dropin_diff}/{dropout_diff}"


    if anomalies:
        anomaly_summary = "; ".join(anomalies)
        return f"⚠️ **Anomaly Detected!** {interval_warning} | `{anomaly_summary}` | `{rates_bps_str}` | `{rates_pps_str}` | `{stats_delta_str}`"
    else:
        return f"✅ Network stable. {interval_warning} | `{rates_bps_str}` | `{rates_pps_str}` | `{stats_delta_str}`"



# --- Pi-hole API Functions ---
@st.cache_data(ttl=3600)  # Cache token for an hour
def get_pihole_api_token():
    """Attempts to find API token from file or secrets."""
    token = None
    # Define potential paths (adjust if non-standard install)
    token_paths = [
        "/etc/pihole/setupVars.conf", # Standard path
        os.path.expanduser("~/.config/pihole/setupVars.conf"), # Possible user config location
        os.path.expanduser("~/.var/app/org.pi_hole.Pi-hole/config/pihole/setupVars.conf") # Example flatpak
    ]
    path_found = None

    for path in token_paths:
        if os.path.exists(path):
            path_found = path
            break

    if path_found:
        try:
            with open(path_found, "r") as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("API_TOKEN="):
                        potential_token = line.split("=", 1)[1]
                        # Ensure token is not empty or just whitespace
                        if potential_token and not potential_token.isspace():
                            token = potential_token; break # Found valid token
        except PermissionError: pass # Silently ignore permission errors
        except Exception as e:
             # Maybe log this error server-side if needed for debugging setup issues
             # print(f"Debug: Error reading Pi-hole token file {path_found}: {e}")
             pass # Silently ignore other file read errors

    # Check secrets as fallback or primary method if פיךק finding fails
    # Only use secret if token wasn't found in file
    if not token and pihole_enabled:
        pihole_api_secrets = st.secrets.get("pihole_api", {})
        token_from_secrets = pihole_api_secrets.get("api_token")
        # Avoid using placeholder value from secrets
        if token_from_secrets and token_from_secrets != "YOUR_PIHOLE_API_TOKEN":
            token = token_from_secrets

    return token

# Unified Pi-hole Request Function
def make_pihole_api_request(endpoint, params=None, method='GET', data=None):
    """Makes a request to the Pi-hole API using token or password auth."""
    # Ensure feature is enabled and URL is configured and not a placeholder
    pihole_api_secrets = st.secrets.get("pihole_api", {})
    base_url_secret = pihole_api_secrets.get("url", "")
    if not pihole_enabled or not base_url_secret or base_url_secret == "YOUR_PIHOLE_IP_OR_HOSTNAME":
        return {"error": "Pi-hole feature disabled or URL not configured/placeholder."}

    password_secret = pihole_api_secrets.get("password", "")
    api_token = get_pihole_api_token() # Tries file then secret token

    auth_params = {}
    auth_method_used = "None"

    # --- Authentication Logic ---
    # 1. Prioritize API Token (if found and valid)
    if api_token:
        auth_params['auth'] = api_token
        auth_method_used = "API Token"
    # 2. Fallback to Password from secrets (if not placeholder)
    elif password_secret and password_secret != "YOUR_PIHOLE_WEB_PASSWORD":
        auth_params['auth'] = password_secret
        auth_method_used = "Password (secrets)"
    # 3. No valid auth method
    else:
        return {"error": "Pi-hole Auth Failed: No valid API Token or Password found."}

    # Construct the full API URL
    api_url = base_url_secret.rstrip('/') + "/admin/api.php"
    # Merge query parameters safely
    all_params = {**(params or {}), **auth_params}

    # --- SSL Verification ---
    verify_ssl = api_url.lower().startswith('https://') # Default True for https
    # Allow overriding via secrets (for self-signed certs)
    if isinstance(pihole_api_secrets.get("verify_ssl"), bool):
         verify_ssl = pihole_api_secrets["verify_ssl"]
         if not verify_ssl and api_url.lower().startswith('https://'):
               try: import urllib3; urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
               except ImportError: pass # Ignore if urllib3 not available

    # --- Timeout ---
    timeout_seconds = pihole_api_secrets.get("timeout", 15) # Allow config via secrets, default 15s

    try:
        # Make the request using python-requests
        response = requests.request(
            method=method.upper(),
            url=api_url,
            params=all_params, # URL query parameters
            data=data, # Use data for POST body if present
            timeout=timeout_seconds,
            verify=verify_ssl,
        )
        response.raise_for_status() # Raise HTTPError automatically for 4xx/5xx

        # --- Process Successful Response (Status Code 2xx) ---
        if response.content:
            try:
                # Attempt to parse JSON first (most common)
                json_response = response.json()

                # Check for specific error formats within valid JSON
                if isinstance(json_response, dict) and "error" in json_response:
                    return {"error": f"API Error: {json_response['error']}"}
                if isinstance(json_response, list) and json_response and isinstance(json_response[0], str) and ("invalid" in json_response[0].lower() or "not found" in json_response[0].lower()):
                    return {"error": f"API Error: {json_response[0]}"}

                # Determine the structure for successful data return
                if isinstance(json_response, dict):
                    # If 'data' key exists and is a list (like from list GET) -> return the list
                    if "data" in json_response and isinstance(json_response["data"], list):
                        return {"success": True, "data": json_response["data"]}
                    # Otherwise (status, summary dicts) -> return the full dict
                    else:
                         return {"success": True, "data": json_response}
                elif isinstance(json_response, list): # Direct list response (older API?)
                    return {"success": True, "data": json_response}
                else: # Valid JSON, but unexpected structure
                    return {"success": True, "data": json_response, "warning": f"Unexpected JSON structure"}

            except json.JSONDecodeError:
                # Handle non-JSON success responses (e.g., simple text messages)
                 resp_text = response.text.strip()
                 # Check for common success keywords in text response for actions
                 success_keywords = ["enabled", "disabled", "added successfully", "removed successfully", "database updated"]
                 if any(keyword in resp_text.lower() for keyword in success_keywords):
                      return {"success": True, "message": resp_text}
                 else: # Treat other non-JSON OK responses as success with the message
                      return {"success": True, "message": f"OK (Non-JSON): {resp_text[:100]}"}
        else: # Empty response content, but status code was OK (2xx)
             # For actions (enable/disable/add/sub/edit), empty OK often means success
             action_params = ['enable', 'disable', 'add', 'sub', 'edit']
             is_action = any(action in (params or {}) for action in action_params)
             if is_action:
                  return {"success": True, "message": f"Action OK (empty response)"}
             else: # Empty OK on a GET request? Might be valid but unusual.
                  return {"success": True, "data": None, "message":"OK (Empty Response)"}


    # --- Specific Exception Handling ---
    except requests.exceptions.SSLError as e:
         return {"error": f"SSL Error: {e}. Check Pi-hole cert or set 'verify_ssl: false'."}
    except requests.exceptions.Timeout:
        return {"error": f"Timeout ({timeout_seconds}s) connecting to {api_url}."}
    except requests.exceptions.ConnectionError as e:
         return {"error": f"Connection Failed: {e}. Check Pi-hole IP/hostname and port."}
    except requests.exceptions.HTTPError as e: # Handles 4xx/5xx raised by raise_for_status()
        status_code = e.response.status_code
        error_msg = f"API HTTP Error: {status_code}."
        error_detail = ""
        try: # Try to get structured error detail from response body
            error_content = e.response.json()
            if isinstance(error_content, dict) and "error" in error_content: error_detail = error_content["error"]
            else: error_detail = e.response.text # Fallback to raw text
        except: error_detail = e.response.text if hasattr(e.response, 'text') and e.response.text else str(e)
        error_msg += f" Detail: {str(error_detail)[:150]}"
        # Advice for auth errors
        if status_code in [401, 403]:
            error_msg += f" (Auth Error using {auth_method_used}? Check API Token/Password & Web UI permissions)."
            if auth_method_used == "API Token": get_pihole_api_token.clear(); error_msg += " Cleared cached token."
        return {"error": error_msg}
    except requests.exceptions.RequestException as e: # Catch other request-related errors
        return {"error": f"Request Failed: {e}"}
    except Exception as e: # Catch unexpected errors during the request/processing
        print(f"Traceback (Pi-hole Request): {traceback.format_exc()}") # Log full trace
        return {"error": f"Unexpected API Error: {type(e).__name__}"}


# --- Specific Pi-hole Action Functions (Wrappers around unified request fn) ---

def get_pihole_status_from_api():
    """Gets Pi-hole status (enabled/disabled) via API."""
    result = make_pihole_api_request("status", params={'status': ''})
    if result.get("success") and isinstance(result.get("data"), dict):
        status = result["data"].get("status", "unknown").lower()
        if status in ["enabled", "disabled"]: return status
        else: return f"api_error: Unexpected status value '{status}'"
    else:
        return f"api_error: {result.get('error', 'Unknown status error')}"

def enable_pihole_api():
    """Enables Pi-hole via API."""
    result = make_pihole_api_request("enable", params={'enable': ''})
    # Check for success and expected outcome (status dict or success message)
    if result.get("success") and ( (isinstance(result.get("data"), dict) and result["data"].get("status") == "enabled") or "enabled" in str(result.get("message","")).lower() ):
        return {"success": True, "message": result.get("message", "Pi-hole Enabled.")}
    else:
        return {"error": result.get("error", "Failed to enable or unexpected response.")}

def disable_pihole_api(duration_seconds=0):
    """Disables Pi-hole via API, optionally for a duration."""
    param_val = int(duration_seconds) if duration_seconds > 0 else ''
    result = make_pihole_api_request("disable", params={'disable': str(param_val)})
    duration_msg = f" for {duration_seconds} seconds" if duration_seconds > 0 else " indefinitely"
    # Check for success and expected outcome
    if result.get("success") and ( (isinstance(result.get("data"), dict) and result["data"].get("status") == "disabled") or "disabled" in str(result.get("message","")).lower() ) :
         return {"success": True, "message": result.get("message", f"Pi-hole Disabled{duration_msg}.") }
    else:
        return {"error": result.get("error", f"Failed to disable{duration_msg} or unexpected response.")}

def get_pihole_summary_api():
    """Gets Pi-hole summary statistics via API."""
    result = make_pihole_api_request("summaryRaw", params={'summaryRaw': ''}) # Prefer raw data
    if result.get("success") and isinstance(result.get("data"), dict):
         if 'dns_queries_today' in result['data']: return result # Check for a key field
         else: return {"warning": "Summary received, but keys unexpected.", "data": result['data']} # Pass data but warn
    else:
        return result # Return original result (likely includes error)

def get_pihole_top_items_api(count=10):
    """Gets Pi-hole top queried/blocked domains and clients via API."""
    result = make_pihole_api_request("topItems", params={'topItems': int(count)})
    if result.get("success") and isinstance(result.get("data"), dict):
        if 'top_queries' in result['data'] or 'top_ads' in result['data']: return result
        else: return {"warning": "Top items received, but keys unexpected.", "data": result['data']}
    else:
        return result

def add_pihole_list_api(list_type, domain):
    """Adds a domain to the specified Pi-hole list (white/black) via API."""
    # Pi-hole v5+ uses POST for list modifications
    result = make_pihole_api_request("list", params={'add': domain, 'list': list_type}, method='POST')
    return result # Return result dict {success: True/False, message/error: ...}

def remove_pihole_list_api(list_type, domain):
    """Removes a domain from the specified Pi-hole list (white/black) via API."""
    result = make_pihole_api_request("list", params={'sub': domain, 'list': list_type}, method='POST')
    return result

def get_pihole_list_content_api(list_type='white'):
    """Gets the content of the specified Pi-hole list (white/black) via API."""
    # Uses GET. Expects {"data": [list of entries]} which unified fn handles.
    result = make_pihole_api_request("list", params={'list': list_type, 'get': ''}, method='GET')
    if result.get("success") and isinstance(result.get("data"), list):
        return result # Success dict containing the list in 'data' key
    else:
        # Handle case where unified function returned warning but success=True
        if result.get("success"): return {"error": f"Fetched {list_type}list, but data format unexpected: {type(result.get('data'))}"}
        return {"error": result.get("error", f"Failed to fetch {list_type}list.")}



# --- Speedtest Functions ---
@st.cache_data(ttl=300)  # Cache speedtest for 5 mins if run dedicated
def run_speedtest_dedicated():
    """Runs a dedicated network speed test. Uses cache. Returns results dict."""
    results = {
         "download_speed": None, "upload_speed": None, "ping": None,
         "speedtest_server": None, "client_isp": None, "error": None
         }
    try:
        st_cli = speedtest.Speedtest(secure=True, timeout=40) # Longer timeout for dedicated run
        st_cli.get_best_server()
        st_cli.download(threads=None)
        st_cli.upload(threads=None)
        res_dict = st_cli.results.dict() # Get results as dict
        results["download_speed"] = res_dict.get("download", 0) / 1_000_000
        results["upload_speed"] = res_dict.get("upload", 0) / 1_000_000
        results["ping"] = res_dict.get("ping")
        results["speedtest_server"] = res_dict.get('server',{}).get('name', 'N/A')
        results["client_isp"] = res_dict.get('client', {}).get('isp', 'N/A')
        return results # Return the full dictionary
    except speedtest.SpeedtestException as e:
        error_msg = f"Speed Test Failed: {e}"
        results["error"] = error_msg
        return results # Return dict with error
    except Exception as e:
        error_msg = f"Unexpected error during speed test: {e}"
        print(f"Dedicated Speedtest Error Traceback: {traceback.format_exc()}") # Log details
        results["error"] = error_msg
        return results


def display_speedtest_results(results):
    """Displays speedtest results neatly using st.metric, handling errors."""
    if not results:
        st.warning("No speed test results available.")
        return
    if results.get("error"):
        st.error(f"Speed test could not run or failed: {results['error']}")
        return

    col1, col2, col3 = st.columns(3)
    # Use .get with default None, format later
    dl_speed = results.get("download_speed")
    ul_speed = results.get("upload_speed")
    ping_val = results.get("ping")

    # Format values for display, handle None
    dl_str = f"{dl_speed:.2f}" if isinstance(dl_speed, (int, float)) else "N/A"
    ul_str = f"{ul_speed:.2f}" if isinstance(ul_speed, (int, float)) else "N/A"
    ping_str = f"{ping_val:.1f}" if isinstance(ping_val, (int, float)) else "N/A"

    with col1: st.metric("Download (Mbps)", dl_str)
    with col2: st.metric("Upload (Mbps)", ul_str)
    with col3: st.metric("Ping (ms)", ping_str)

    # Use .get with defaults for server/ISP names
    server_name = results.get("speedtest_server", "N/A")
    isp_name = results.get("client_isp", "N/A")
    st.caption(f"Server: `{server_name}` | ISP: `{isp_name}`")


# --- Azure AI SDK Call Functions ---

def get_azure_ai_text_response_stream(prompt, chat_history):
    """Gets a streaming text response using the Azure AI Inference SDK."""
    global azure_client, azure_ai_enabled
    if not azure_ai_enabled or not azure_client:
        yield "[Error: Azure AI Client not available. Check configuration and secrets.]"
        return

    messages = [SystemMessage(content=system_instruction)]
    history_limit = 10
    limited_history = chat_history[-history_limit*2:]
    for msg in limited_history:
        if isinstance(msg, dict) and msg.get("content"):
            role = msg["role"]
            if role == "user":
                messages.append(UserMessage(content=msg["content"]))
            elif role == "assistant":
                messages.append(AssistantMessage(content=msg["content"]))

    if prompt:
        messages.append(UserMessage(content=prompt))
    else:
         yield "[Error: No prompt provided to generate response.]"
         return

    try:
        # *** FIX: Use client.complete instead of client.chat_completions ***
        # Also pass model name directly to complete method as per docs
        response_stream = azure_client.complete(
            model=PHI4_MODEL_NAME,
            messages=messages,
            temperature=0.6,
            top_p=0.9,
            max_tokens=2048,
            stream=True, # Enable streaming
            # Optional: Include usage data in stream as per docs example
            # model_extras = {'stream_options': {'include_usage': True}},
        )

        chunk_count = 0
        # Usage data handling if model_extras is enabled:
        # usage = {}
        for chunk in response_stream:
            # Check for content delta
            if chunk.choices and len(chunk.choices) > 0:
                delta = chunk.choices[0].delta
                if delta and delta.content:
                    yield delta.content
                    chunk_count += 1
            # Optional: Handle usage data accumulation if included in stream
            # if chunk.usage:
            #    usage = chunk.usage
            #    print(f"DEBUG Usage Update: {usage}") # For debugging

        # End of stream signal - keep this
        yield "[STREAM_DONE]"

        # Optional: Print final usage if collected
        # if usage:
        #    print("\n--- Final Stream Usage ---")
        #    for k, v in usage.items(): print(f"{k} = {v}")
        #    print("------------------------")


    except ClientAuthenticationError:
        yield "[Error: Azure AI Authentication Failed. Check API Key in secrets.]"
    except HttpResponseError as e:
        # ... (existing HttpResponseError handling remains the same) ...
        error_details = f"Status: {getattr(e, 'status_code', 'N/A')}"
        nested_error_msg = ""
        try:
            error_body = e.response.json().get("error", {})
            nested_error_msg = error_body.get("message", getattr(e, 'message', str(e)))
            nested_error_code = error_body.get("code", "")
            if nested_error_code: error_details += f" Code: {nested_error_code}"
        except: nested_error_msg = getattr(e, 'message', str(e)) # Fallback
        error_details += f" | Detail: {nested_error_msg}"
        print(f"Azure Text Stream _HttpResponseError_: Status={e.status_code}, Response: {e.response.text if e.response else 'N/A'}")
        yield f"[Error: API Call Failed ({e.__class__.__name__}). {error_details}]"

    except Exception as e:
        print(f"Traceback (Azure Text Stream Error): {traceback.format_exc()}")
        yield f"[Error: Unexpected SDK streaming error - {type(e).__name__}]"

def get_azure_ai_vision_response(prompt, image_bytes):
    """Gets a response for multimodal input (text + image) using Azure AI SDK."""
    global azure_client, azure_ai_enabled
    if not azure_ai_enabled or not azure_client:
        return "[Error: Azure AI Client not available. Check configuration and secrets.]"

    # --- Image Processing (Existing code is likely fine) ---
    try:
        # Determine MIME type programmatically if possible, or assume JPEG/PNG
        try:
            temp_img = Image.open(io.BytesIO(image_bytes))
            img_format = temp_img.format if temp_img.format else "JPEG" # Default to JPEG
            image_mime_type = Image.MIME.get(img_format.upper(), "image/jpeg")
        except Exception: # Fallback if Pillow can't identify
            image_mime_type = "image/jpeg" # Default assumption

        img_base64 = base64.b64encode(image_bytes).decode("utf-8")
        image_data_url = f"data:{image_mime_type};base64,{img_base64}"
    except Exception as e:
        print(f"Error encoding image for Azure Vision: {traceback.format_exc()}")
        return f"[Error: Failed to encode image - {type(e).__name__}]"

    # --- Construct multimodal message payload using SDK models (as per docs) ---
    messages = [
        UserMessage(
            content=[
                # *** FIX: Use TextContentItem ***
                TextContentItem(text=prompt),
                # *** FIX: Use ImageContentItem wrapping ImageUrl ***
                ImageContentItem(
                    image_url=ImageUrl(
                        url=image_data_url
                        # Optional: Set detail level if needed, default is often 'auto'
                        # detail=ImageDetailLevel.LOW # or HIGH
                        )
                ),
            ]
        )
        # Optional System Message for Vision tasks
        # SystemMessage(content="Describe the provided image accurately based on the user's text query."),
    ]

    try:
        # *** FIX: Use client.complete instead of client.chat_completions ***
        # Pass model name directly to complete method
        response = azure_client.complete(
            model=PHI4_MODEL_NAME,
            messages=messages,
            max_tokens=2048,
            temperature=0.3,
            top_p=0.9,
            stream=False, # Vision is typically synchronous
        )

        # --- Process Response (Existing logic seems okay) ---
        if response.choices and len(response.choices) > 0:
            # ... (your existing logic for processing choice, message, finish_reason) ...
            choice = response.choices[0]
            message_content = choice.message.content if choice.message else None
            finish_reason = choice.finish_reason # Correct attribute based on SDK structure

            if message_content:
                # Basic check for common refusal phrases / content policy issues
                refusal_phrases = [
                    "unable to process", "cannot process", "can't process", "i cannot", "unable to create",
                    "i'm sorry", "cannot fulfill this request", "content policy", "violates my safety policies"
                    ]
                # Also check finish reason if available (might indicate content filtering)
                is_filtered = finish_reason == "content_filter"
                is_refusal_phrase = any(phrase in message_content.lower() for phrase in refusal_phrases)
                # Heuristic for short refusals vs potentially short valid answers
                is_short_refusal_heuristic = len(message_content) < 80 and is_refusal_phrase

                if is_filtered or is_short_refusal_heuristic:
                    # Provide more context in the warning/error
                    return f"[Info: Model refused or response filtered. Finish reason: '{finish_reason}'. Response: '{message_content.strip()}']"
                else:
                    return message_content.strip() # Return the actual analysis content
            else:
                # Content is empty, provide finish reason if available
                return f"[Error: Azure Vision response received, but content was empty. Finish Reason: '{finish_reason}']"
        else:
            # ... (your existing logic for handling invalid response structure) ...
             usage_info = response.usage if hasattr(response, 'usage') else 'N/A'
             try: raw_response_str = response.model_dump_json(indent=2)
             except: raw_response_str = str(response)
             print(f"DEBUG: Invalid Azure Vision response structure. Usage: {usage_info}. Raw: {raw_response_str[:500]}")
             return f"[Error: Invalid Azure Vision response structure (no choices?). Usage: {usage_info}.]"

    except ClientAuthenticationError:
        return "[Error: Azure AI Authentication Failed. Check API Key.]"
    except HttpResponseError as e:
        # ... (existing HttpResponseError handling remains the same) ...
        error_details = f"Status: {getattr(e, 'status_code', 'N/A')}"
        nested_error_msg = ""
        try:
            error_body = e.response.json().get("error", {})
            nested_error_msg = error_body.get("message", getattr(e, 'message', str(e)))
            nested_error_code = error_body.get("code", "")
            if nested_error_code: error_details += f" Code: {nested_error_code}"
        except: nested_error_msg = getattr(e, 'message', str(e))
        error_details += f" | Detail: {nested_error_msg}"
        print(f"Azure Vision _HttpResponseError_: Status={e.status_code}, Response Body: {e.response.text if e.response else 'N/A'}")
        return f"[Error: Vision API Call Failed ({e.__class__.__name__}). {error_details}]"

    except Exception as e:
        print(f"Traceback (Azure Vision Error): {traceback.format_exc()}")
        return f"[Error: Unexpected SDK vision call error - {type(e).__name__}: {str(e)}]"



# --- Simulated Quantum Security Audit ---
def simulate_quantum_security_audit():
    """Performs basic CLASSICAL checks and reports them with Azure Quantum inspired terminology."""
    results = []
    details = []
    recommendations = []
    os_name = platform.system()
    os_ver = platform.release()
    readiness = "Low"
    readiness_reason = "Standard OS libraries often have limited native PQC support."

    # --- Post-Quantum Readiness Simulation (Based on OS/Crypto Libs) ---
    try:
        # OS Guess (Very basic)
        if "Linux" in os_name:
            try:
                kernel_major = int(os_ver.split(".")[0])
                if kernel_major >= 6: readiness = "Low-Medium"; readiness_reason = "Newer Linux kernel potentially improves crypto agility."
                elif kernel_major >= 5: readiness = "Low"; readiness_reason = "Common baseline kernel version."
                else: readiness = "Very Low"; readiness_reason = "Older kernel, likely lacks modern crypto support."
            except (ValueError, IndexError): readiness_reason += " (Could not parse kernel version)."
        elif "Windows" in os_name: readiness = "Low-Medium"; readiness_reason = f"Windows {os_ver}. PQC support depends on build/updates."
        elif "Darwin" in os_name: readiness = "Low-Medium"; readiness_reason = f"macOS {os_ver}. PQC depends on library versions."
        else: readiness = "Low"; readiness_reason = f"OS {os_name} {os_ver}. PQC readiness unknown."

        # Check OpenSSL Version
        try:
            ssl_version_output = subprocess.run(["openssl", "version"], capture_output=True, text=True, check=False, timeout=3)
            if ssl_version_output.returncode == 0:
                 ssl_version_str = ssl_version_output.stdout.strip()
                 if "OpenSSL 3." in ssl_version_str:
                     if readiness == "Low": readiness = "Low-Medium"
                     elif readiness == "Low-Medium": readiness = "Medium"
                     elif readiness == "Very Low": readiness = "Low"
                     readiness_reason += f" | {ssl_version_str} detected (foundation for PQC)."
                     recommendations.append("Leverage PQC algorithms in OpenSSL 3+ via config/apps.")
                 elif "OpenSSL 1." in ssl_version_str:
                      readiness_reason += f" | {ssl_version_str} detected (Limited PQC support)."
                      recommendations.append("Upgrade OpenSSL to 3.x+ for better PQC readiness.")
                 else:
                      readiness_reason += f" | {ssl_version_str} detected."
                      recommendations.append("Ensure crypto libraries are up-to-date.")
            else:
                 readiness_reason += " | OpenSSL command failed/not found."
                 recommendations.append("Verify OpenSSL installation and status.")
        except (FileNotFoundError): readiness_reason += " | OpenSSL command not found."
        except (subprocess.TimeoutExpired): readiness_reason += " | OpenSSL check timed out."
        except Exception as e_ssl: readiness_reason += f" | OpenSSL check error: {type(e_ssl).__name__}."
    except Exception as e_os: readiness_reason += f" | OS/Crypto check error: {type(e_os).__name__}."

    results.append(f"**Post-Quantum Crypto Readiness (Simulated):** `{readiness}`")
    details.append(f"• **Basis:** {readiness_reason}. *Actual PQC readiness requires explicit PQC algorithm deployment & configuration.*")

    # --- Classical Vulnerability Scan (Listening Ports) ---
    common_risky_ports = { 21: "FTP", 23: "Telnet", 80: "HTTP", 110: "POP3", 143: "IMAP"}
    common_access_ports = { 22: "SSH", 5900: "VNC", 5901: "VNC", 3389: "RDP" }
    open_risky_details = []
    open_access_details = []

    try:
        listening_conns = psutil.net_connections(kind="inet")
        # Check ports listening on ALL non-loopback interfaces
        listening_ports_all_if = { conn.laddr.port for conn in listening_conns
            if conn.status == psutil.CONN_LISTEN and conn.laddr.ip not in ['127.0.0.1', '::1', 'localhost'] }
        # Check localhost listeners separately
        listening_ports_local = { conn.laddr.port for conn in listening_conns
            if conn.status == psutil.CONN_LISTEN and conn.laddr.ip in ['127.0.0.1', '::1', 'localhost'] }

        # Classify open ports
        for port, reason in common_risky_ports.items():
            if port in listening_ports_all_if: open_risky_details.append(f"🚨 `{port}` ({reason} - Cleartext?) - **Public**")
            elif port in listening_ports_local: open_risky_details.append(f"⚠️ `{port}` ({reason} - Cleartext?) - Localhost")
        for port, reason in common_access_ports.items():
             if port in listening_ports_all_if: open_access_details.append(f"🚪 `{port}` ({reason}) - **Public**")
             elif port in listening_ports_local: open_access_details.append(f"🚪 `{port}` ({reason}) - Localhost")

        # Summarize results
        scan_results = []
        if any("🚨" in s for s in open_risky_details):
            scan_results.append("🚨 **Potential Cleartext Services Publicly Exposed!**")
            recommendations.append("Secure/disable public cleartext services (FTP, Telnet, HTTP). Use HTTPS, SFTP, SSH. Review firewall urgently.")
        elif any("⚠️" in s for s in open_risky_details):
            scan_results.append("⚠️ Potential Cleartext Services on Localhost.")
            recommendations.append("Secure cleartext services even on localhost if sensitive data processed.")
        else: scan_results.append("✅ No common *cleartext* services detected.")

        if any("🚪" in s and "Public" in s for s in open_access_details):
            scan_results.append("🚪 **Remote Access Services Publicly Exposed!**")
            recommendations.append("Harden public SSH/VNC/RDP. Use strong auth, firewalls (restrict IPs), fail2ban. Disable if unused.")
        elif any("🚪" in s for s in open_access_details):
            scan_results.append("🚪 Remote Access Services on Localhost.")
            if not any("🚪" in s and "Public" in s for s in open_access_details): # Add local rec only if no public warning issued
                 recommendations.append("Review localhost remote access services; ensure needed & secured.")
        else: scan_results.append("✅ No common remote access services detected.")

        results.append("**Classical Vulnerability Scan (Services):** " + " | ".join(scan_results))
        if open_risky_details: details.extend(open_risky_details)
        if open_access_details: details.extend(open_access_details)
        if not open_risky_details and not open_access_details: details.append("• No common risky/remote ports detected listening.")

    except psutil.AccessDenied:
        results.append("**Classical Vulnerability Scan (Services):** `Access Denied`.")
        details.append("• Port Scan failed: insufficient permissions (run as admin/root?).")
        recommendations.append("Run with higher privileges for full network connection analysis.")
    except Exception as e:
        results.append(f"**Classical Vulnerability Scan (Services):** `Error ({type(e).__name__})`.")
        details.append(f"• Port Scan failed or incomplete: {e}")

    # --- System Integrity Simulation (Placeholder) ---
    results.append("**System File Integrity (Conceptual):** `Not Implemented`")
    details.append("• *Conceptual Check:* Simulating monitoring for critical file changes. Requires dedicated tools (AIDE, Wazuh, etc.).")
    recommendations.append("Implement a dedicated file integrity monitor for actual protection.")

    # --- Compile Report ---
    report = "<b>Simulated Azure Quantum Security Audit Report:</b>\n\n" + "\n".join(results)
    if details: report += "\n\n<b>Classical Scan Details & Observations:</b>\n" + "\n".join(details)
    # Ensure recommendations list is unique
    unique_recommendations = sorted(list(set(recommendations)))
    if unique_recommendations: report += "\n\n<b>Recommendations (Classical Security):</b>\n" + "\n".join([f"• {rec}" for rec in unique_recommendations])
    report += "\n\n*Disclaimer: This is a **simulated** assessment using classical checks framed with quantum-inspired language. It does **not** involve actual quantum computation or guarantee security against quantum threats. Use professional security tools and practices for comprehensive audits.*"
    return report


# --- Main Streamlit App Function ---
def main():
    # Page config is at the top

    # Use the globally defined client and status
    global azure_client, azure_ai_enabled

    # --- Display Titles ---
    st.markdown(
        f'<p class="title">CyberNexus Q - Pi-Eye 🌌 (Azure AI {PHI4_MODEL_NAME})</p>',
        unsafe_allow_html=True,
    )
    st.caption(
        f"Azure AI SDK Mode | Azure Quantum Inspired Concepts | {quantum_lib_status}"
    )

    # --- Initialize session state ---
    # Login status
    if "logged_in" not in st.session_state: st.session_state["logged_in"] = False
    # Chat histories
    if "chat_history" not in st.session_state: st.session_state["chat_history"] = []
    if "screen_chat_history" not in st.session_state: st.session_state["screen_chat_history"] = []
    # Screen sharing state
    if "sharing" not in st.session_state: st.session_state["sharing"] = False
    if "current_frame" not in st.session_state: st.session_state["current_frame"] = None
    # Network analysis state
    if "network_anomaly_running" not in st.session_state: st.session_state["network_anomaly_running"] = False
    if "prev_net_stats" not in st.session_state: st.session_state["prev_net_stats"] = None
    # Other UI or data states
    if "audit_report" not in st.session_state: st.session_state["audit_report"] = None
    if "dedicated_speed_results" not in st.session_state: st.session_state["dedicated_speed_results"] = None

    # Load initial network data **only once** after login if not already loaded
    if st.session_state.get('logged_in') and 'initial_network_data_loaded' not in st.session_state:
        with st.spinner("Performing initial network scan..."):
             st.session_state.current_network_data = get_initial_network_status()
             # Show toasts based on initial scan results (only if not empty)
             net_data = st.session_state.current_network_data
             if net_data.get("speedtest_error"): st.toast(f"Initial Scan: {net_data['speedtest_error']}", icon="⚡")
             if net_data.get("external_ip_error"): st.toast(f"Initial Scan: {net_data['external_ip_error']}", icon="🌐")
             if not net_data.get("speedtest_error") and not net_data.get("external_ip_error"):
                  st.toast("Initial network scan complete.", icon="🛰️")
        st.session_state.initial_network_data_loaded = True


    # --- Sidebar ---
    with st.sidebar:
        st.header("CyberNexus Q Control 🌌")
        st.caption(f"v0.9.3 | {PHI4_MODEL_NAME}")
        st.markdown("---")
        st.subheader("Agent Access")
        # Login Logic
        if not st.session_state.get("logged_in", False):
            try:
                login_secrets = st.secrets.get("login", {})
                valid_username = login_secrets.get("username", "QuantumUser")
                valid_password = login_secrets.get("password", "NexusQuantum")
                using_defaults = valid_username == "QuantumUser" and valid_password == "NexusQuantum" and "login" not in st.secrets
                using_placeholders = valid_username == "YOUR_USERNAME" or valid_password == "YOUR_PASSWORD"

                if using_defaults:
                     st.info("Using default login. Define [login] in secrets.toml.")
                if using_placeholders:
                     st.error("Placeholder login in secrets.toml!")

            except Exception as e:
                st.error(f"Login secrets error: {e}. Using defaults.")
                valid_username = "QuantumUser"; valid_password = "NexusQuantum"
                using_placeholders = False

            with st.form("login_form"):
                username = st.text_input("Username", key="login_user")
                password = st.text_input("Password", type="password", key="login_pass")
                submitted = st.form_submit_button("Authenticate")
                if submitted:
                    if using_placeholders: st.error("Cannot login with placeholders.")
                    elif username == valid_username and password == valid_password:
                        st.session_state["logged_in"] = True
                        st.success("Authenticated."); time.sleep(0.8); st.rerun()
                    else: st.error("Authentication Failed.")
        else: # Logged In State
            display_username = st.secrets.get("login", {}).get("username", "QuantUser")
            st.success(f"User: `{display_username}`")
            if st.button("Logout", key="logout_button"):
                keys_to_clear = list(st.session_state.keys())
                for key in keys_to_clear:
                    if key != 'logged_in': del st.session_state[key]
                st.session_state['logged_in'] = False
                st.cache_data.clear(); st.cache_resource.clear()
                st.success("Logged out."); time.sleep(1); st.rerun()

        st.markdown("---")
        # Status Indicators
        st.subheader("System Status")
        azure_secrets_exist = "azure_ai" in st.secrets and "api_key" in st.secrets.azure_ai
        azure_key_is_placeholder = azure_secrets_exist and st.secrets.azure_ai.api_key == "YOUR_AZURE_AI_API_KEY_OR_GITHUB_PAT"
        if azure_client and azure_ai_enabled: st.markdown("🔵 **Azure AI:** <span class='status-ok'>Connected</span>", unsafe_allow_html=True)
        elif not azure_secrets_exist: st.markdown("🔵 **Azure AI:** <span class='status-error'>No Config</span>", unsafe_allow_html=True)
        elif azure_key_is_placeholder: st.markdown("🔵 **Azure AI:** <span class='status-error'>Placeholder Key</span>", unsafe_allow_html=True)
        else: st.markdown("🔵 **Azure AI:** <span class='status-error'>Init Failed</span>", unsafe_allow_html=True)
        # Pi-hole Status Indication
        if pihole_enabled: st.markdown("🛡️ **Pi-hole:** <span class='status-ok'>Enabled</span>", unsafe_allow_html=True)
        else: st.markdown("🛡️ **Pi-hole:** <span class='status-warn'>Disabled</span>", unsafe_allow_html=True)
        # Quantum Lib status
        q_color = "status-ok" if HAS_QUANTUM_LIBS else "status-warn"
        st.markdown(f"🌌 **Quantum Libs:** <span class='{q_color}'>{'Detected' if HAS_QUANTUM_LIBS else 'Not Found'}</span>", unsafe_allow_html=True)
        st.markdown("---")

        # Live System Stats (Only when logged in)
        if st.session_state.get("logged_in", False):
            st.subheader("Live Stats")
            col_cpu, col_temp = st.columns(2)
            col_ram, col_disk = st.columns(2)
            try:
                pi_stats = get_pi_status() # Cached
                # Define colors based on thresholds
                cpu_color = "#ccff00"; temp_color="#ff9933"; ram_color="#00ffff"; disk_color="#ff00ff"
                try: temp_val = float(re.findall(r"[-+]?\d*\.\d+|\d+", pi_stats['cpu_temperature'])[0])
                except: temp_val = -100
                if temp_val > 75: temp_color = "#ff0000" # Red
                elif temp_val > 60: temp_color = "#ffff00" # Yellow

                try: cpu_val = float(pi_stats['cpu_usage'].strip('%'))
                except: cpu_val = 0
                if cpu_val > 90: cpu_color = "#ff0000"
                elif cpu_val > 70: cpu_color = "#ffff00"

                try: ram_val = float(pi_stats['ram_usage'].split('%')[0])
                except: ram_val = 0
                if ram_val > 90: ram_color = "#ff0000"
                elif ram_val > 75: ram_color = "#ffff00"

                try: disk_val = float(pi_stats['disk_usage'].split('%')[0])
                except: disk_val = 0
                if disk_val > 90: disk_color = "#ff0000"
                elif disk_val > 80: disk_color = "#ffff00"


                with col_cpu: st.markdown(f"**CPU:** <span style='color: {cpu_color};'>{pi_stats['cpu_usage']}</span>", unsafe_allow_html=True)
                with col_temp: st.markdown(f"**Temp:** <span style='color: {temp_color};'>{pi_stats['cpu_temperature']}</span>", unsafe_allow_html=True)
                with col_ram: st.markdown(f"**RAM:** <span style='color: {ram_color};'>{pi_stats['ram_usage'].split(' ')[0]}</span>", unsafe_allow_html=True)
                with col_disk: st.markdown(f"**Disk:** <span style='color: {disk_color};'>{pi_stats['disk_usage'].split(' ')[0]}</span>", unsafe_allow_html=True)

                # Detailed usage in caption
                ram_detail = pi_stats['ram_usage'].split(' (',1)[1].split(')',1)[0] if ' (' in pi_stats['ram_usage'] else '-'
                disk_detail = pi_stats['disk_usage'].split(' (',1)[1].split(')',1)[0] if ' (' in pi_stats['disk_usage'] else '-'
                st.caption(f"RAM: {ram_detail} | Disk: {disk_detail}")

            except Exception as e: st.error(f"Live stats error: {type(e).__name__}")

            st.markdown("---")
            # TTS Toggle
            st.subheader("Settings")
            tts_available = st.session_state.get("tts_engine") is not None
            default_tts_state = tts_available
            st.session_state["tts_toggle"] = st.toggle(
                "Enable TTS Output", value=st.session_state.get("tts_toggle", default_tts_state),
                key="tts_main_toggle", disabled=not tts_available,
                help="Enable/disable text-to-speech for AI responses and actions.")
            if not tts_available: st.caption("TTS engine failed to initialize.")


    # --- Main Application Area (Displayed only if logged in) ---
    if not st.session_state.get("logged_in", False):
        st.warning("💡 Please Authenticate via the sidebar to activate CyberNexus Q.")
        st.markdown("---")
        st.markdown("#### Capabilities Overview:")
        st.markdown(
             """
            - **Agent Chat:** Interact via text or voice (🎤). Ask about system, network, Pi-hole, security, or make general queries.
            - **Network Matrix:** View interface details, run speed tests, monitor traffic rates and anomalies.
            - **Screen Analysis:** Start screen feed, then ask the AI questions about the visual content.
            - **Pi-hole Control:** Check status, enable/disable, view stats, manage domain lists (requires Pi-hole API config).
            - **Security Audit:** Run a *simulated* audit performing classical checks (ports, crypto libs) with quantum-inspired framing.
            """
        )

    else: # User is Logged In
        # Ensure network data is loaded (safe redundant check)
        if 'initial_network_data_loaded' not in st.session_state:
             # This block shouldn't normally be hit if login flow is correct, but acts as a fallback
             with st.spinner("Performing initial network scan..."):
                  st.session_state.current_network_data = get_initial_network_status()
             st.session_state.initial_network_data_loaded = True
        # Use the loaded data from session state
        network_data = st.session_state.get("current_network_data")

        # Define Tabs
        tab_chat, tab_network, tab_screen, tab_pihole, tab_security = st.tabs([
            "🌌 Agent Chat", "🛰️ Network Matrix", "👁️ Screen Analysis", "🛡️ Pi-hole Control", "🔒 Security Audit"
            ])

        # =========================
        # Agent Chat Tab
        # =========================
        with tab_chat:
            # Create a container for the chat history for fixed height scrolling
            chat_container = st.container(height=550) # Adjust height as needed

            with chat_container:
                # Display chat history
                if not st.session_state.chat_history:
                     st.markdown("*(Chat history is clear. Ask me anything!)*")
                for i, message in enumerate(st.session_state.chat_history):
                    is_user = message["role"] == "user"
                    avatar_display = circular_user_image if is_user else circular_ai_image
                    with st.chat_message(name=message["role"], avatar=avatar_display):
                        st.markdown(message["content"], unsafe_allow_html=True)

            # Separate container for input elements below the chat history
            input_container = st.container()
            with input_container:
                 col_voice, col_input = st.columns([1, 6]) # Adjust ratio if needed
                 with col_voice:
                      voice_disabled = st.session_state.get("recognizer") is None or not azure_ai_enabled
                      if st.button("🎤", key="voice_cmd_main", help="Ask via Voice (if mic available & enabled)", disabled=voice_disabled, type="secondary"):
                           voice_prompt = listen_for_command()
                           if voice_prompt:
                                st.session_state.main_chat_input_value = voice_prompt
                                st.rerun() # Rerun to process the voice input

                 with col_input:
                      prompt_text = st.chat_input(
                          "Ask CyberNexus Q...", key="main_chat_input", disabled=not azure_ai_enabled
                      )

            # --- Process New Input (Check text input OR value from voice state) ---
            final_prompt = prompt_text or st.session_state.pop('main_chat_input_value', None) # Prioritize text, fallback/clear voice state

            if final_prompt:
                st.session_state.chat_history.append({"role": "user", "content": final_prompt})
                st.rerun() # Display user message immediately

            # --- AI Response Generation Trigger ---
            if st.session_state.chat_history and st.session_state.chat_history[-1]["role"] == "user":
                last_user_prompt = st.session_state.chat_history[-1]["content"]

                # Display thinking message inside the chat container
                with chat_container:
                     with st.chat_message("assistant", avatar=circular_ai_image):
                         ai_response_placeholder = st.empty()
                         ai_response_placeholder.markdown("```processing\nThinking...\n```")

                         full_response_text = ""
                         action_response_md = None
                         stream_error = False
                         history_appended_this_turn = False

                         try:
                             prompt_lower = last_user_prompt.lower()
                             action_executed = False
                             network_keywords = ["network status", "internet status", "quick check", "ip address", "connection status", "network check", "netstat", "speed", "my ip"]
                             pi_status_keywords = ["pi status", "system status", "specs", "check system", "raspberry pi status", "pi check", "server status", "status check", "sysinfo"]

                             # --- Direct Action: Pi Status ---
                             if any(k in prompt_lower for k in pi_status_keywords) or re.search(r"\b(cpu|ram|temp|disk)\b", prompt_lower):
                                 pi_stats_data = get_pi_status() # Cached
                                 action_response_md = (f"⚙️ **Pi System Status (via `psutil`):**\n\n"
                                                       f"- **CPU:** `{pi_stats_data['cpu_usage']}`\n"
                                                       f"- **Temp:** `{pi_stats_data['cpu_temperature']}`\n"
                                                       f"- **RAM:** `{pi_stats_data['ram_usage']}`\n"
                                                       f"- **Disk:** `{pi_stats_data['disk_usage']}`")
                                 action_executed = True
                                 full_response_text = "Retrieved current system status:"

                             # --- Direct Action: Network Quick Check (Cached) ---
                             elif any(k in prompt_lower for k in network_keywords):
                                 net_stats_data = st.session_state.get('current_network_data')
                                 if net_stats_data:
                                     dl_sp=net_stats_data.get('download_speed'); ul_sp=net_stats_data.get('upload_speed')
                                     ping_v=net_stats_data.get('ping')
                                     dl_str=f"{dl_sp:.2f}" if isinstance(dl_sp,(int,float)) else "N/A"
                                     ul_str=f"{ul_sp:.2f}" if isinstance(ul_sp,(int,float)) else "N/A"
                                     ping_str=f"{ping_v:.1f}" if isinstance(ping_v,(int,float)) else "N/A"
                                     action_response_md = (f"⚙️ **Network Quick Check (Cached):**\n\n"
                                                           f"- **Down/Up:** `{dl_str}` / `{ul_str}` Mbps\n"
                                                           f"- **Ping:** `{ping_str} ms`\n"
                                                           f"- **External IP:** `{net_stats_data.get('external_ip', 'N/A')}`")
                                     if net_stats_data.get("speedtest_error"): action_response_md += f"\n\n  - *Speedtest Note:* _{net_stats_data['speedtest_error']}_"
                                     if net_stats_data.get("external_ip_error"): action_response_md += f"\n  - *Ext. IP Note:* _{net_stats_data['external_ip_error']}_"
                                     action_response_md += "\n\n*(Use Network Matrix tab for details/fresh tests)*"
                                 else: action_response_md = "⚙️ Cached network data not available yet. Try the Network Matrix tab."
                                 action_executed = True
                                 full_response_text = "Here's the last cached network overview:"

                             # --- Direct Action: Pi-hole Status ---
                             elif pihole_enabled and ("pi-hole status" in prompt_lower or "pihole status" in prompt_lower):
                                  with st.spinner("Checking Pi-hole status..."): status_result = get_cached_pihole_status_display() # Use cached one from display tab
                                  if status_result.startswith("api_error"): action_response_md = f"⚙️ **Pi-hole Status Error:** `{status_result}`"
                                  else: action_response_md = f"⚙️ **Pi-hole Status:** `{status_result.upper()}`"
                                  action_executed = True

                             # --- Direct Action: Run Security Audit ---
                             elif "security audit" in prompt_lower or "quantum check" in prompt_lower or "security scan" in prompt_lower or "run audit" in prompt_lower:
                                 with st.spinner("Initiating Simulated Azure Quantum Security Audit..."):
                                     action_response_md = simulate_quantum_security_audit()
                                 action_executed = True
                                 full_response_text = "Simulated Security Audit complete."

                             # --- Fallback to LLM if NO direct action matched ---
                             if not action_executed:
                                  response_stream = get_azure_ai_text_response_stream(
                                       last_user_prompt, st.session_state.chat_history[:-1]
                                  )
                                  streamed_chunks = []
                                  for chunk in response_stream:
                                      if chunk == "[STREAM_DONE]": break
                                      if chunk.startswith("[Error:") or chunk.startswith("[Warning:") or chunk.startswith("[Info:"):
                                          if chunk.startswith("[Error:"):
                                               full_response_text = chunk # Display error
                                               ai_response_placeholder.error(full_response_text)
                                               stream_error = True; break # Stop stream
                                          else: st.toast(chunk[chunk.find(':')+1:].strip(), icon="⚠️" if chunk.startswith("[Warning:") else "ℹ️"); continue # Show toast, continue stream
                                      streamed_chunks.append(chunk)
                                      full_response_text = "".join(streamed_chunks)
                                      ai_response_placeholder.markdown(full_response_text + "▌", unsafe_allow_html=True) # Stream cursor

                                  if not stream_error: # Final update without cursor
                                       ai_response_placeholder.markdown(full_response_text, unsafe_allow_html=True)


                             # --- Combine LLM/Action Results & Update History ---
                             final_response_content = full_response_text
                             if action_response_md:
                                 if final_response_content and not stream_error: final_response_content += f"\n\n---\n{action_response_md}"
                                 else: final_response_content = action_response_md # Only action result

                             if not final_response_content and not stream_error: # Handle totally empty case
                                 final_response_content = "[AI response was empty and no specific action was taken.]"
                                 ai_response_placeholder.warning(final_response_content)

                             if not stream_error: # Update placeholder if no error already shown
                                  ai_response_placeholder.markdown(final_response_content, unsafe_allow_html=True)

                             if final_response_content: # Append final content to history
                                 st.session_state.chat_history.append({"role": "assistant", "content": final_response_content})
                                 history_appended_this_turn = True

                             # --- Text-to-Speech ---
                             text_for_tts = "" # Determine what to speak
                             if action_executed and not stream_error: # Action completed
                                 if "Pi System Status" in final_response_content: text_for_tts = "Showing system status."
                                 elif "Network Quick Check" in final_response_content: text_for_tts = "Showing network overview."
                                 elif "Pi-hole Status:" in final_response_content: text_for_tts = "Pi-hole status: " + final_response_content.split("`")[-2]
                                 elif "Security Audit" in final_response_content: text_for_tts = "Simulated security audit complete."
                                 else: text_for_tts = "Action complete."
                             elif not action_executed and full_response_text and not stream_error: text_for_tts = full_response_text # Speak LLM response
                             elif stream_error: text_for_tts = "An error occurred generating the response."
                             if text_for_tts: speak_text(text_for_tts)

                         except Exception as e: # Catch errors during processing step
                             st.error(f"💥 Error during response processing: {type(e).__name__}")
                             detailed_error = traceback.format_exc()
                             print(f"DEBUG: Response Processing Error:\n{detailed_error}")
                             error_msg_display = f"[Internal Error processing response: {type(e).__name__}]"
                             ai_response_placeholder.error(error_msg_display)
                             if not history_appended_this_turn: # Append error if nothing else was
                                 st.session_state.chat_history.append({"role": "assistant", "content": error_msg_display})
                                 history_appended_this_turn = True

                # Rerun AFTER the assistant's message processing is complete (normal or error)
                # CORRECTED INDENTATION for this block:
                if history_appended_this_turn:
                    st.rerun()


        # =========================
        # Network Matrix Tab
        # =========================
        with tab_network:
            st.subheader("Network Matrix & Analysis")

            col_ref, col_spd = st.columns([1,3])
            with col_ref:
                 if st.button("🔄 Refresh Scan", key="refresh_network_button_network_tab", help="Runs speedtest and external IP check again"):
                     get_initial_network_status.clear()
                     with st.spinner("Refreshing network scan..."):
                         st.session_state.current_network_data = get_initial_network_status()
                         net_data = st.session_state.current_network_data
                         if net_data.get("speedtest_error"): st.toast(f"Refresh: {net_data['speedtest_error']}", icon="⚡")
                         if net_data.get("external_ip_error"): st.toast(f"Refresh: {net_data['external_ip_error']}", icon="🌐")
                         else: st.toast("Network scan refresh complete.", icon="🛰️")
                     st.session_state.initial_network_data_loaded = True
                     if 'dedicated_speed_results' in st.session_state: del st.session_state['dedicated_speed_results'] # Clear dedicated results too
                     st.rerun()
            with col_spd:
                 if st.button("⚡ Run Dedicated Speed Test Now", key="speedtest_button_network_tab"):
                     run_speedtest_dedicated.clear()
                     with st.spinner("Running dedicated speed test... This may take a minute."):
                         speed_results = run_speedtest_dedicated()
                     st.session_state.dedicated_speed_results = speed_results
                     st.rerun()

            st.markdown("---")
            network_data = st.session_state.get('current_network_data', {}) # Use empty dict as default

            # Display Initial/Refreshed Scan Results
            st.markdown("#### Network Overview (Last Scan)")
            display_speedtest_results(network_data)
            st.caption(f"External IP: `{network_data.get('external_ip', 'N/A')}`")
            if network_data.get("speedtest_error"): st.caption(f"*Speedtest Note:* _{network_data['speedtest_error']}_")
            if network_data.get("external_ip_error"): st.caption(f"*Ext. IP Note:* _{network_data['external_ip_error']}_")
            st.markdown("---")

            # Display Dedicated Speed Test Results if they exist
            if 'dedicated_speed_results' in st.session_state and st.session_state.dedicated_speed_results is not None:
                 st.markdown("#### Dedicated Speed Test Results")
                 display_speedtest_results(st.session_state.dedicated_speed_results)
                 st.markdown("---")

            # Interface Details and Traffic Analysis in Columns
            col_net_iface, col_net_traffic = st.columns([1, 1.5])

            with col_net_iface:
                st.markdown("#### Interface Intelligence (psutil)")
                interfaces_info = get_network_interfaces_psutil() # Cached data
                interface_names = list(interfaces_info.keys()) if interfaces_info else []

                if not interface_names: st.warning("No network interfaces found.")
                else:
                    default_index = 0 # Find a sensible default
                    for i, name in enumerate(interface_names):
                        if interfaces_info[name].get('is_up') and not name.startswith('lo'):
                            default_index = i; break
                    selected_interface = st.selectbox("Select Interface:", interface_names, key="interface_select", index=default_index)
                    if selected_interface:
                        iface_details = format_interface_details_psutil(interfaces_info, selected_interface)
                        if iface_details.get("Error"): st.error(iface_details["Error"])
                        else:
                             st.markdown(f"""
                             - Status: `{iface_details['Status']}` (Speed: `{iface_details['Speed']}`)
                             - MAC: `{', '.join(iface_details['MAC'])}`
                             - IPv4: `{', '.join(iface_details['IPv4'])}`
                             - IPv6: `{', '.join(iface_details['IPv6'])}`
                             """, unsafe_allow_html=True)

            with col_net_traffic:
                st.markdown("#### Real-time Traffic Analysis (psutil)")
                run_analysis = st.checkbox("Activate Traffic Scan", key="anomaly_toggle", value=st.session_state.get('network_anomaly_running', False), help="Periodically checks network IO rates and errors/drops.")
                status_area = st.container()
                stats_display_area = st.container()

                if run_analysis:
                    if not st.session_state.get('network_anomaly_running', False):
                         st.session_state['network_anomaly_running'] = True
                         st.session_state['prev_net_stats'] = get_network_io_stats() # Initial baseline
                         status_area.info("Traffic Scan Activated... Waiting for interval.")
                         # No immediate rerun needed, let the loop start below

                    # --- Analysis Loop Logic ---
                    current_net_stats = get_network_io_stats()
                    prev_net_stats = st.session_state.get('prev_net_stats')
                    stats_df = None # Initialize dataframe variable

                    if current_net_stats and prev_net_stats:
                        analysis_result = analyze_network_traffic(prev_net_stats, current_net_stats)
                        if "⚠️ **Anomaly" in analysis_result: status_area.error(analysis_result, icon="🚨")
                        elif "Insufficient data" in analysis_result or "Interval too short" in analysis_result: status_area.warning(analysis_result, icon="⏳")
                        else: status_area.success(analysis_result, icon="✅")
                        # Display *cumulative* stats
                        stats_readable = {
                            "Time": time.strftime('%H:%M:%S'), "Sent Σ": format_bytes(current_net_stats.get('bytes_sent')),
                            "Recv Σ": format_bytes(current_net_stats.get('bytes_recv')), "Pkt Sent Σ": f"{current_net_stats.get('packets_sent', 0):,}",
                            "Pkt Recv Σ": f"{current_net_stats.get('packets_recv', 0):,}", "Err Σ(I/O)": f"{current_net_stats.get('errin', 0)}/{current_net_stats.get('errout', 0)}",
                            "Drop Σ(I/O)": f"{current_net_stats.get('dropin', 0)}/{current_net_stats.get('dropout', 0)}",
                        }
                        stats_df = pd.DataFrame([stats_readable])
                        st.session_state['prev_net_stats'] = current_net_stats # Update for next cycle
                    elif not current_net_stats: status_area.warning("Could not retrieve current network IO stats.")
                    else: status_area.info("Waiting for next interval to calculate rates...") ; st.session_state['prev_net_stats'] = current_net_stats # Store first reading

                    # Display cumulative stats table
                    if stats_df is not None:
                         stats_display_area.dataframe( stats_df.style.set_properties(**{'text-align': 'left', 'font-size': '0.9em'}).hide(axis="index"), use_container_width=True )
                    else: stats_display_area.empty()

                    # --- Auto-refresh ---
                    # Use time.sleep cautiously as it blocks interaction
                    time.sleep(3) # Interval in seconds
                    st.rerun()

                else: # Checkbox is off
                    if st.session_state.get('network_anomaly_running', False): # If it *was* running
                        st.session_state['network_anomaly_running'] = False
                        st.session_state['prev_net_stats'] = None
                        status_area.info("Traffic Scan Deactivated.")
                        stats_display_area.empty()
                        st.rerun() # Rerun once to clear UI
                    else: # Already off
                        status_area.info("Activate scan to monitor traffic rates and detect anomalies.")
                        stats_display_area.empty()


        # =========================
        # Screen Analysis Tab
        # =========================
        with tab_screen:
            st.subheader("Multimodal Screen Analysis (Azure AI Vision)")
            col_share_ctl, col_share_view = st.columns([1, 2])

            with col_share_ctl:
                st.markdown("#### Controls")
                sharing_active = st.session_state.get('sharing', False)
                button_text = "⏹️ Stop Screen Feed" if sharing_active else "▶️ Start Screen Feed"
                if st.button(button_text, key="toggle_share"):
                    st.session_state.sharing = not st.session_state.sharing
                    if not st.session_state.sharing: st.session_state.current_frame = None
                    st.rerun() # Rerun to update viewport and button state

                st.caption("Shares primary monitor for visual analysis.")
                st.markdown("---")

                st.markdown("#### Analyze Screen")
                screen_chat_container = st.container(height=400)
                current_screen_history = st.session_state.get('screen_chat_history', [])
                with screen_chat_container:
                    if not current_screen_history: st.markdown("*(Start screen feed and ask questions about it...)*")
                    for message in current_screen_history:
                        msg_role = message["role"]
                        msg_avatar = circular_user_image if msg_role == "user" else circular_ai_image
                        with st.chat_message(msg_role, avatar=msg_avatar):
                            st.markdown(message["content"], unsafe_allow_html=True)

                input_disabled = not sharing_active or not azure_ai_enabled
                disable_reason = ""
                if not sharing_active: disable_reason = "Start screen feed first."
                elif not azure_ai_enabled: disable_reason = "Azure AI Vision not available."

                screen_prompt = st.chat_input("Ask about the screen feed...", key="screen_chat_input", disabled=input_disabled)
                if input_disabled and not disable_reason.startswith("Azure"): st.caption(f":warning: Input disabled: {disable_reason}")
                elif input_disabled: st.caption(f":warning: {disable_reason}") # Don't show warning if Azure is just off

                if screen_prompt:
                    if not sharing_active: st.toast("Screen feed is not active.", icon="⚠️")
                    elif st.session_state.get('current_frame') is None: st.toast("Screen frame not captured yet.", icon="⏳")
                    else:
                        st.session_state.screen_chat_history.append({"role": "user", "content": screen_prompt})
                        st.rerun()

            # --- Screen Analysis Processing Trigger ---
            if current_screen_history and current_screen_history[-1]["role"] == "user":
                last_screen_prompt = current_screen_history[-1]["content"]
                current_frame = st.session_state.get('current_frame')

                with screen_chat_container:
                    with st.chat_message("assistant", avatar=circular_ai_image):
                        analysis_placeholder = st.empty()
                        analysis_placeholder.markdown("```processing\n👁️ Analyzing screen with Azure AI Vision...\n```")

                        if current_frame is not None and azure_ai_enabled:
                            analysis_result_text = "[Analysis Error: Placeholder]"
                            try:
                                img_rgb = cv2.cvtColor(current_frame, cv2.COLOR_BGR2RGB)
                                pil_img = Image.fromarray(img_rgb)
                                buffer = io.BytesIO()
                                pil_img.save(buffer, format="JPEG", quality=85)
                                img_bytes = buffer.getvalue()
                                analysis_result_text = get_azure_ai_vision_response(last_screen_prompt, img_bytes)
                            except Exception as e:
                                error_msg = f"Screen Vision Prep/Analysis failed: {type(e).__name__}"
                                st.toast(f"💥 {error_msg}", icon="👁️")
                                print(f"Error during Vision call/prep: {traceback.format_exc()}")
                                analysis_result_text = f"[Error: {error_msg}]"

                            analysis_placeholder.markdown(analysis_result_text, unsafe_allow_html=True)
                            st.session_state.screen_chat_history.append({"role": "assistant", "content": analysis_result_text})
                            if not analysis_result_text.startswith(("[Error:", "[Info:")) and st.session_state.get('tts_toggle'):
                                tts_summary = analysis_result_text.split('. ')[0] + "." if '.' in analysis_result_text else analysis_result_text[:150]
                                speak_text(f"Vision analysis: {tts_summary}")
                            st.rerun()

                        elif not azure_ai_enabled:
                             error_msg = "[Error: Azure AI Vision client not available]"
                             analysis_placeholder.error(error_msg)
                             st.session_state.screen_chat_history.append({"role": "assistant", "content": error_msg}); st.rerun()
                        else: # Frame missing
                            error_msg = "[Internal Error: Screen frame missing during analysis]"
                            analysis_placeholder.warning(error_msg)
                            st.session_state.screen_chat_history.append({"role": "assistant", "content": error_msg}); st.rerun()

            # Screen Viewport (Right Column)
            with col_share_view:
                st.markdown("#### Live Feed Viewport")
                image_placeholder = st.empty()
                if st.session_state.get('sharing', False):
                    share_error_placeholder = st.empty() # For persistent errors
                    try:
                        with mss(display=os.environ.get('DISPLAY')) as sct:
                            monitor_index = 1 # Try primary first
                            if len(sct.monitors) <= monitor_index: monitor_index = 0 # Fallback
                            if not sct.monitors: raise Exception("No monitors detected")
                            monitor = sct.monitors[monitor_index]

                            screen_frame_mss = sct.grab(monitor)
                            frame_np = np.array(screen_frame_mss)
                            frame_bgr = cv2.cvtColor(frame_np, cv2.COLOR_BGRA2BGR)
                            st.session_state.current_frame = frame_bgr

                            display_img_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
                            image_placeholder.image(display_img_rgb,
                                caption=f"Screen Feed Active - Monitor {monitor_index} ({monitor.get('width','?') }x{monitor.get('height','?')})",
                                use_container_width=True, output_format='RGB')

                        # --- Frame rate control ---
                        refresh_interval = 0.7 # ~1.4 FPS. Increase if CPU usage too high
                        time.sleep(refresh_interval)
                        st.rerun()

                    except ImportError:
                        st.error("Screen sharing requires `mss` library: `pip install mss`")
                        st.session_state.sharing = False; st.session_state.current_frame = None
                        image_placeholder.warning("Sharing stopped: library missing."); st.rerun()
                    except Exception as e:
                        share_error_placeholder.error(f"Screen sharing error: {type(e).__name__}. Stopping feed.")
                        print(f"Screen Sharing Traceback: {traceback.format_exc()}")
                        st.session_state.sharing = False; st.session_state.current_frame = None
                        # Don't rerun automatically on error, let user restart

                else: # Sharing is not active
                    image_placeholder.info("Screen sharing inactive. ▶️ Start feed to enable analysis.")
                    if st.session_state.get('current_frame') is not None:
                        st.session_state.current_frame = None # Clear frame when stopped


        # =========================
        # Pi-hole Control Tab
        # =========================
        with tab_pihole:
             st.subheader("Pi-hole Network Protection Control")

             if not pihole_enabled:
                  st.warning("Pi-hole integration disabled. Configure `[pihole_api]` with `url` in `secrets.toml`.")
             else:
                  # Status and Toggle
                  status_col, control_col = st.columns([1, 1.5])
                  with status_col:
                       st.markdown("#### Status & Toggle")
                       status_placeholder = st.empty()
                       # Use cached status function
                       @st.cache_data(ttl=8)
                       def get_cached_pihole_status_display():
                            return get_pihole_status_from_api()

                       current_status = get_cached_pihole_status_display()

                       with status_placeholder.container():
                           if current_status.startswith("api_error"):
                               st.error(f"Status Error:\n`{current_status}`")
                               if st.button("Retry Status", key="retry_pihole_status"):
                                    get_cached_pihole_status_display.clear(); st.rerun()
                           elif current_status in ["enabled", "disabled"]:
                               status_color = "lightgreen" if current_status == "enabled" else "orange"
                               st.markdown(f"Current Status: <span style='color:{status_color}; font-weight:bold;'>{current_status.upper()}</span>", unsafe_allow_html=True)
                               is_enabled = current_status == "enabled"
                               if is_enabled:
                                   disable_duration = st.selectbox("Disable Temporarily For:",
                                       options=[0, 10, 30, 60, 300, 900], index=1, # Default 10s
                                       format_func=lambda x: f"{x}s" if x==10 else (f"{x}s ({x//60}m)" if x>=60 else "Permanently"),
                                       key="pihole_disable_duration")
                                   if st.button("🚫 Disable Pi-hole", key="pihole_disable_btn"):
                                       duration_text = f" for {disable_duration}s" if disable_duration>0 else ""
                                       with st.spinner(f"Disabling Pi-hole{duration_text}..."): resp = disable_pihole_api(disable_duration)
                                       if resp.get("success"): st.success(f"✅ {resp.get('message', 'Disabled')}")
                                       else: st.error(f"❌ {resp.get('error', 'Failed')}")
                                       get_cached_pihole_status_display.clear(); time.sleep(0.5); st.rerun()
                               else: # Pi-hole is disabled
                                   if st.button("✅ Enable Pi-hole", key="pihole_enable_btn"):
                                       with st.spinner("Enabling Pi-hole..."): resp = enable_pihole_api()
                                       if resp.get("success"): st.success(f"✅ {resp.get('message', 'Enabled')}")
                                       else: st.error(f"❌ {resp.get('error', 'Failed')}")
                                       get_cached_pihole_status_display.clear(); time.sleep(0.5); st.rerun()
                           else: # Status is unknown
                               st.warning(f"Status Unknown: `{current_status}`")
                               if st.button("Retry Status", key="retry_pihole_status_unknown"):
                                    get_cached_pihole_status_display.clear(); st.rerun()

                  # Separator
                  st.markdown("<hr style='margin: 1rem 0;'>", unsafe_allow_html=True)

                  # Other Pi-hole functions
                  with control_col:
                        st.markdown("#### Statistics & Lists")
                        with st.expander("📊 View Summary & Top Items"):
                            # Placeholder for results
                             summary_placeholder = st.empty()
                             top_items_placeholder = st.empty()
                             if st.button("Fetch Stats", key="pihole_stats_btn_tab"):
                                 summary_placeholder.text("Fetching summary...")
                                 top_items_placeholder.text("Fetching top items...")
                                 summary_resp = get_pihole_summary_api()
                                 top_resp = get_pihole_top_items_api(count=7)

                                 with summary_placeholder.container():
                                     if summary_resp.get("success"):
                                         data = summary_resp['data']
                                         st.markdown(f"""
                                         - Queries (Today): `{data.get('dns_queries_today', 'N/A'):,}`
                                         - Blocked (Today): `{data.get('ads_blocked_today', 'N/A'):,}` (`{data.get('ads_percentage_today', 'N/A')}%`)
                                         - Domains Blocked: `{data.get('domains_being_blocked', 'N/A'):,}`
                                         - Unique Clients: `{data.get('unique_clients', 'N/A')}`
                                         """, unsafe_allow_html=True)
                                     else: st.error(f"Summary Error: {summary_resp.get('error', 'Failed')}")

                                 with top_items_placeholder.container():
                                      st.markdown("---")
                                      if top_resp.get("success") and isinstance(top_resp.get('data'), dict):
                                          data=top_resp['data']; st.markdown("**Top 7 Items:**")
                                          st.markdown("<u>Queries / Blocked / Clients:</u>", unsafe_allow_html=True)
                                          # Display in columns for better layout
                                          col_tq, col_tb, col_tc = st.columns(3)
                                          with col_tq: st.text('\n'.join([f"{d[:15]}: {h:,}" for d,h in list(data.get('top_queries',{}).items())[:7]]))
                                          with col_tb: st.text('\n'.join([f"{d[:15]}: {h:,}" for d,h in list(data.get('top_ads',{}).items())[:7]]))
                                          with col_tc: st.text('\n'.join([f"{c.split('|')[0]} ({c.split('|')[1]})"[:20]+f": {h:,}" if '|' in c else f"{c[:15]}: {h:,}" for c,h in list(data.get('top_sources',{}).items())[:7]]))
                                      else: st.error(f"Top Items Error: {top_resp.get('error', 'Failed or invalid data')}")

                        with st.expander("📝 Manage Domain Lists"):
                             list_type_manage = st.radio("Select List:", ["Whitelist", "Blacklist"], key="pihole_list_manage_type_tab", horizontal=True)
                             list_type_arg = "white" if list_type_manage=="Whitelist" else "black"
                             with st.form(key=f"list_manage_form_{list_type_arg}_tab"):
                                  domain_manage = st.text_input(f"Domain for {list_type_manage}:", key=f"pihole_domain_{list_type_arg}_tab")
                                  submitted_add = st.form_submit_button(f"➕ Add")
                                  submitted_rem = st.form_submit_button(f"➖ Remove")
                                  if submitted_add and domain_manage:
                                      with st.spinner(f"Adding {domain_manage} to {list_type_manage}..."): resp = add_pihole_list_api(list_type_arg, domain_manage)
                                      if resp.get("success"): st.success(f"✅ {resp.get('message', 'Added')}")
                                      else: st.error(f"❌ Add Error: {resp.get('error', 'Failed')}")
                                  elif submitted_add: st.warning("Enter domain.")
                                  if submitted_rem and domain_manage:
                                      with st.spinner(f"Removing {domain_manage} from {list_type_manage}..."): resp = remove_pihole_list_api(list_type_arg, domain_manage)
                                      if resp.get("success"): st.success(f"✅ {resp.get('message', 'Removed')}")
                                      else: st.error(f"❌ Remove Error: {resp.get('error', 'Failed')}")
                                  elif submitted_rem: st.warning("Enter domain.")

                        with st.expander("📄 View Domain Lists"):
                            list_type_view = st.radio("Select List:", ["Whitelist", "Blacklist"], key="pihole_list_view_type_tab", horizontal=True)
                            view_placeholder = st.container() # Placeholder for list content
                            if st.button(f"View {list_type_view}", key="pihole_view_btn_tab"):
                                list_type_arg_view = "white" if list_type_view=="Whitelist" else "black"
                                with st.spinner(f"Fetching {list_type_view}..."): resp = get_pihole_list_content_api(list_type_arg_view)
                                with view_placeholder: # Display results inside the placeholder
                                     if resp.get("success") and isinstance(resp.get("data"), list):
                                         entries = resp['data']
                                         st.markdown(f"**{list_type_view} ({len(entries)} entries):**")
                                         if not entries: st.write("*(List is empty)*")
                                         else:
                                             list_display_area = st.container(height=200) # Scroll area
                                             with list_display_area:
                                                 for item in entries:
                                                     if isinstance(item, dict):
                                                         domain=item.get('domain','?'); enabled_str=" " if item.get('enabled',1)==1 else "(D)"; comment=f" # {item.get('comment','')}" if item.get('comment') else ""
                                                         st.code(f"{domain}{enabled_str}{comment}", language=None) # Use code for monospace list
                                                     elif isinstance(item, str): st.code(f"{item}", language=None)
                                                     else: st.code(f"{str(item)}", language=None)
                                     else: st.error(f"❌ View Error: {resp.get('error', 'Failed')}")


        # =========================
        # Security Audit Tab
        # =========================
        with tab_security:
            st.subheader("Simulated Quantum Security Audit")
            st.caption("Performs classical checks, reported with quantum-inspired framing.")
            st.warning("🚨 **Disclaimer:** This is a **simulation**. It does **not** involve actual quantum computation or guarantee security against quantum attacks. Use professional tools for real security audits.")

            audit_placeholder = st.container() # Use container for report display

            if st.button("🔬 Run Simulated Audit Now", key="security_audit_button_tab"):
                 if 'audit_report' in st.session_state: del st.session_state['audit_report'] # Clear old report
                 with audit_placeholder: # Show spinner inside container
                     with st.spinner("Performing simulated audit checks..."):
                         audit_report_md = simulate_quantum_security_audit()
                         st.session_state.audit_report = audit_report_md
                         speak_text("Simulated Security Audit complete.")
                 st.rerun() # Rerun to display the report below

            # Display the stored report if it exists
            if 'audit_report' in st.session_state and st.session_state.audit_report:
                 with audit_placeholder: # Display report inside the container
                     st.markdown("---")
                     st.markdown("#### Audit Report:")
                     st.markdown(st.session_state.audit_report, unsafe_allow_html=True)




# --- Main Execution Guard ---
if __name__ == "__main__":
    # Optional: Clear specific state keys at start for testing during dev
    # keys_to_clear = ['main_chat_input_value', 'audit_report', 'prev_net_stats', 'dedicated_speed_results']
    # for key in keys_to_clear:
    #      if key in st.session_state: del st.session_state[key]

    try:
        main()
    except Exception as e:
         # Log critical errors robustly
         st.error(f"💥 CRITICAL ERROR in main application loop: {type(e).__name__}")
         full_traceback = traceback.format_exc()
         print(f"CRITICAL APP ERROR:\n{full_traceback}")
         # Display simplified error and traceback in the Streamlit app UI
         st.code(f"Error Type: {type(e).__name__}\nMessage: {e}\n\nTraceback (partial):\n...\n" + "\n".join(full_traceback.splitlines()[-8:]))
         st.warning("An unexpected error halted the app. Check server logs for details.")

