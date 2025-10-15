
# 🧠 AI Meeting Summarizer (Flask + Gemini API)

This project provides a simple, **single-file web application** built with **Python (Flask)** and the **Google Gemini API** to automatically transcribe meeting audio, generate a concise summary, and extract key action items using multimodal and structured output generation.

The entire application — including the frontend (HTML + JavaScript) and backend (Flask server logic) — is contained in a single `app.py` file for easy deployment and testing.


## video
https://drive.google.com/file/d/1_oMPojLokgC1sjB-Qr4iiPexzpKWz0yT/view?usp=sharing
##✨ Features

* 🎙️ **Multimodal Processing:** Upload and process audio files (`.mp3`, `.wav`, `.m4a`, etc.) directly using the Gemini API.
* 📝 **Automatic Transcription:** Generates a full transcript of meeting audio.
* 🧩 **Structured Output:** Extracts a **Key Summary** and a list of **Action Items** using a predefined JSON schema for reliable parsing.
* 💻 **Responsive Frontend:** Simple, modern interface built with **Tailwind CSS**, responsive on all devices.
* ⚙️ **Action Item Handling:** Displays a clear message if the model finds no explicit action items in the audio.



## 🛠️ Technical Stack

| Component     | Technology                                                            |
| ------------- | --------------------------------------------------------------------- |
| **Backend**   | Python 3 + Flask                                                      |
| **AI Model**  | Gemini 2.5 Flash (`generateContent` API for multimodal + JSON output) |
| **Frontend**  | HTML5, Vanilla JavaScript, Tailwind CSS (via CDN)                     |
| **Libraries** | `requests`, `werkzeug`                                                |



## 🚀 Setup and Installation

### 1. Prerequisites

Make sure you have the following installed:

* Python 3.x
* pip (Python package installer)



### 2. Install Dependencies

Run the following command to install the required Python libraries:

```bash
pip install Flask requests
```

---

### 3. API Key Configuration (Crucial Step)

This app requires a **Gemini API Key**.

1. Get your key from [Google AI Studio](https://aistudio.google.com/).
2. Open `app.py`.
3. Find this section and replace the placeholder with your key:

```python
# --- CONFIGURATION ---
# !!! CRITICAL: PASTE YOUR NEW API KEY HERE !!!
# The app will first look for an environment variable named GEMINI_API_KEY.
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "PASTE_YOUR_API_KEY_HERE")
```



### ▶️ How to Run

1. Save the code as `app.py`.
2. Open a terminal in the same directory and start the server:

```bash
python app.py
```

3. Once the server starts, you’ll see a message like:

```
* Running on http://127.0.0.1:5000/ (Press CTRL+C to quit)
```

4. Open the link in your web browser.



## 💡 Usage

1. **Upload Audio:** Click the **“Select Meeting Audio”** button and choose a file (e.g., `.mp3`, `.wav`, `.m4a`).
2. **Summarize:** Click **“Summarize Meeting”**. The app will upload the file and call the Gemini API.
3. **View Results:** After processing (10–30 seconds depending on file size), results will appear:

   * ✅ **Key Summary** of the meeting
   * 📋 **Action Items** list (or a note if none found)
   * 🗒️ **Full Transcript** of the meeting



## 🧩 Example Output

```json
{
  "key_summary": "The team discussed Q4 sales targets, new client onboarding, and marketing budget adjustments.",
  "action_items": [
    "Schedule follow-up with new clients by Friday",
    "Finalize Q4 marketing budget by next Monday"
  ],
  "full_transcript": "John: Let's begin with the Q4 targets... "
}
```



## 🧰 Folder Structure

```
📦 ai-meeting-summarizer
 ┣ 📜 app.py
 ┣ 📜 README.md
 ┗ 📁 uploads/        # (created automatically for uploaded audio files)
```



## ⚡ Example Technologies Used

* **Flask:** Lightweight backend web framework.
* **Tailwind CSS:** Modern, responsive styling via CDN.
* **Gemini API:** Multimodal model capable of audio → text + structured summary generation.
* **JSON Schema Output:** Ensures cleanly parsed, consistent AI responses.





---

Would you like me to **include the complete working `app.py` code** (with frontend + Gemini API integration) below this in the README so it’s a self-contained repository file?
