# CyberNexus Q - Pi-Eye 🌌 (Azure AI & Quantum Inspired)

**Entry for the AI_AGENTS_HACKATHON**

[![Python Version](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-Deployed-orange.svg)](https://streamlit.io)
<!-- Add other badges if relevant (e.g., License) -->

CyberNexus Q is an advanced AI agent designed for comprehensive Raspberry Pi (or other Linux/Windows/macOS system) monitoring, network analysis, and interaction, leveraging the power of Azure AI's Phi-4 Multimodal model and drawing conceptual inspiration from Azure Quantum principles.

Built with Streamlit, it provides a web-based interface for monitoring system resources, analyzing network traffic, managing Pi-hole ad-blocking, performing simulated quantum-resilience security checks, and analyzing visual content via screen sharing combined with Azure AI Vision.

![Alt Text](https://media4.giphy.com/media/v1.Y2lkPTc5MGI3NjExd210cW1wcjlxZjB5azB6YXUxdXR2NHZlb2I4dW1zM2dhbzVxajZnNSZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/T2bO8PkfwL0qYbW5li/giphy.gif)

---

## ✨ Features

*   **🤖 AI Agent Chat:** Interact with CyberNexus Q using text or voice commands (STT/TTS). Ask about system status, network details, run audits, control Pi-hole, or make general queries answered by Azure AI Phi-4.
*   **📊 System Monitoring:** Real-time display of CPU usage, RAM usage, Disk usage, and CPU Temperature using `psutil`.
*   **🛰️ Network Matrix:**
    *   View detailed information about network interfaces (IP/MAC addresses, speed, status).
    *   Run initial and dedicated network speed tests (`speedtest-cli`).
    *   Determine external IP address.
    *   Activate real-time network traffic analysis to monitor data rates (Tx/Rx Bps, PPS) and detect potential anomalies (high error/drop rates).
*   **👁️ Multimodal Screen Analysis:**
    *   Share your primary screen feed directly within the app (`mss`).
    *   Ask the AI (Azure AI Phi-4 Vision) questions about the content displayed on the shared screen.
*   **🛡️ Pi-hole Control (Optional):**
    *   Check Pi-hole status (Enabled/Disabled).
    *   Enable/Disable Pi-hole (instantly or temporarily).
    *   View summary statistics (queries, blocked ads).
    *   View top queried/blocked domains and clients.
    *   Add/Remove domains from Whitelist/Blacklist.
    *   View Whitelist/Blacklist content.
*   **🔒 Simulated Quantum Security Audit:**
    *   Performs *classical* system checks (e.g., listening ports, OpenSSL version).
    *   Reports findings using terminology inspired by Azure Quantum resilience and post-quantum cryptography readiness. **(Disclaimer: This is a simulation and does not involve actual quantum computation or guarantee security).**
*   **🔊 Accessibility:** Text-to-Speech (TTS) for AI responses and Speech-to-Text (STT) for voice commands.
*   **🎨 Themed UI:** Custom Streamlit theme inspired by quantum computing and cyberpunk aesthetics.

---

## 🛠️ Technology Stack

*   **Framework:** Streamlit
*   **AI Model:** Microsoft Azure AI Phi-4 Multimodal (via `azure-ai-inference` SDK)
*   **System/Network Info:** `psutil`
*   **Speed Test:** `speedtest-cli`
*   **Screen Capture:** `mss`
*   **Image Processing:** `Pillow`, `opencv-python`
*   **API Interaction:** `requests`
*   **TTS/STT:** `pyttsx3`, `SpeechRecognition`
*   **Data Handling:** `pandas`, `numpy`
*   **(Optional) Symbolic Quantum:** `amazon-braket-sdk`, `qiskit` (for conceptual simulation aspects, not core functionality)

---

## 📃 Repository Structure

## 📃 Repository Structure 
```
DocuNexus-AGI-Agent/
├── .gitignore
├── LICENSE
├── README.md
├── cybernexus_q.py           # Your main Streamlit application script (the modified one)
├── requirements.txt
├── secrets.toml.example      # Example configuration file (IMPORTANT!)
├── assets/
│   ├── human.png             # Placeholder for user avatar
│   └── robot.png             # Placeholder for AI avatar
```

---

## 🚀 Setup & Installation

1.  **Clone the Repository:**
    ```bash
    git clone <your-repository-url>
    cd CyberNeXus-Q
    ```

2.  **Create and Activate Virtual Environment (Recommended):**
    ```bash
    python -m venv venv
    # On Windows:
    # venv\Scripts\activate
    # On macOS/Linux:
    # source venv/bin/activate
    ```

3.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
    *Note: You might need system libraries depending on your OS (e.g., `sudo apt-get install espeak` on Debian/Ubuntu for `pyttsx3`). Ensure your system has microphone access enabled for STT.*

4.  **Configure Secrets:**
    *   Navigate to the `.streamlit` directory: `cd .streamlit`
    *   Copy the template: `cp secrets.toml.template secrets.toml`
    *   Edit `secrets.toml` with your actual credentials:
        *   `[azure_ai] api_key`: Your Azure AI Phi-4 endpoint key.
        *   `[login] username / password`: Credentials to access the Streamlit app.
        *   `[pihole_api] url / password / api_token`: Your Pi-hole details (if using). See template comments for details.
    *   **IMPORTANT:** The `.gitignore` file prevents `secrets.toml` from being committed. **Never commit your actual secrets file.**

5.  **Add Avatar Images:**
    *   Place your `human.png` and `robot.png` avatar files inside the `assets/` directory. If missing, the app will use default emojis.

6.  **(Optional) Pi-hole API Token File:**
    *   If you don't provide the `api_token` in `secrets.toml`, the script will attempt to read it from `/etc/pihole/setupVars.conf` (requires read permissions for the user running Streamlit).

---

## ▶️ Running the App

Ensure your virtual environment is activated. From the project's root directory (`CyberNeXus-Q/`):

```bash
streamlit run cybernexus_q.py
