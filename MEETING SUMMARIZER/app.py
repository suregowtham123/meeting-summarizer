import json
import os
import requests
import logging
import base64
from flask import Flask, request, jsonify, abort
from werkzeug.utils import secure_filename
import time # Needed for exponential backoff

# Set up basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

app = Flask(__name__)

# --- CONFIGURATION ---
# !!! CRITICAL: PASTE YOUR NEW API KEY HERE !!!
# The app will first look for an environment variable named GEMINI_API_KEY.
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "AIzaSyDkJaRmRX26M7EX8DGi7rhX9RxtJj4JZEA")
# Using the standard flash model for multimodal audio processing
GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-preview-05-20:generateContent"
# ---------------------

# --- FRONTEND HTML CONTENT (Embedded for single-file deployment) ---
HTML_CONTENT = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI Meeting Summarizer</title>
    <!-- Load Tailwind CSS -->
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
        body {
            font-family: 'Inter', sans-serif;
            background-color: #f8fafc;
        }
        .container-shadow {
            box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
        }
        .pulse-animation {
            animation: pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
        }
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: .5; }
        }
    </style>
</head>
<body class="min-h-screen flex items-center justify-center p-4 bg-gray-50">

    <div class="w-full max-w-4xl bg-white rounded-2xl container-shadow p-6 sm:p-10">
        <header class="text-center mb-10">
            <h1 class="text-4xl font-extrabold text-gray-900 mb-2">AI Meeting Summarizer</h1>
            <p class="text-gray-500">Upload an audio file to get instant transcription, key decisions, and action items.</p>
        </header>

        <!-- Upload Form -->
        <div id="upload-section" class="bg-indigo-50 border border-indigo-200 rounded-xl p-6 mb-8 transition duration-300 hover:border-indigo-400">
            <label for="audioFile" class="block text-lg font-semibold text-indigo-700 mb-3">
                1. Select Meeting Audio (.mp3, .wav, etc.)
            </label>
            <input type="file" id="audioFile" accept="audio/*" class="w-full text-gray-900 bg-white border border-gray-300 rounded-lg cursor-pointer focus:outline-none focus:ring-2 focus:ring-indigo-500 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-semibold file:bg-indigo-500 file:text-white hover:file:bg-indigo-600 transition duration-150">
            
            <button onclick="startSummaryProcess()" id="summarize-btn"
                    class="mt-6 w-full py-3 bg-indigo-600 text-white font-bold text-lg rounded-xl hover:bg-indigo-700 transition duration-150 focus:outline-none focus:ring-4 focus:ring-indigo-300 disabled:opacity-50"
                    disabled>
                Summarize Meeting
            </button>
        </div>

        <!-- Message/Loading Box -->
        <div id="message-box" class="hidden text-center py-4 rounded-xl font-medium text-sm" role="alert"></div>

        <!-- Results Display Section -->
        <div id="results-card" class="space-y-8 mt-10 hidden">
            <h2 class="text-3xl font-bold text-gray-800 border-b pb-3">Analysis Results</h2>

            <!-- Summary -->
            <div class="bg-green-50 border-l-4 border-green-500 rounded-lg p-5 shadow-lg">
                <h3 class="text-xl font-semibold text-green-700 mb-3 flex items-center">
                    <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m5.618-4.27a7 7 0 00-11.233-.09C10.707 5.23 13.522 7.5 15.5 10"/>
                    </svg>
                    Key Summary
                </h3>
                <p id="summary-output" class="text-gray-700 leading-relaxed"></p>
            </div>

            <!-- Action Items -->
            <div class="bg-yellow-50 border-l-4 border-yellow-500 rounded-lg p-5 shadow-lg">
                <h3 class="text-xl font-semibold text-yellow-700 mb-3 flex items-center">
                    <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"/>
                    </svg>
                    Action Items
                </h3>
                <ul id="actions-output" class="list-disc pl-5 space-y-2 text-gray-700"></ul>
            </div>

            <!-- Full Transcript -->
            <div class="bg-gray-100 border border-gray-300 rounded-lg p-5">
                <h3 class="text-xl font-semibold text-gray-700 mb-3">
                    Full Transcript
                </h3>
                <div class="bg-white p-4 rounded-lg border border-gray-200 h-64 overflow-y-auto">
                    <pre id="transcript-output" class="whitespace-pre-wrap text-sm text-gray-800"></pre>
                </div>
            </div>
        </div>

    </div>

    <script>
        const audioInput = document.getElementById('audioFile');
        const summarizeBtn = document.getElementById('summarize-btn');
        const messageBox = document.getElementById('message-box');
        const resultsCard = document.getElementById('results-card');
        
        // Output elements
        const summaryOutput = document.getElementById('summary-output');
        const actionsOutput = document.getElementById('actions-output');
        const transcriptOutput = document.getElementById('transcript-output');

        // --- Utility Functions ---

        function displayMessage(text, type = 'info') {
            messageBox.textContent = text;
            messageBox.className = 'text-center py-4 rounded-xl font-medium text-sm';
            messageBox.classList.remove('hidden');
            
            if (type === 'loading') {
                messageBox.classList.add('bg-blue-100', 'text-blue-700', 'pulse-animation');
            } else if (type === 'success') {
                messageBox.classList.add('bg-green-100', 'text-green-700');
            } else if (type === 'error') {
                messageBox.classList.add('bg-red-100', 'text-red-700');
            } else { // info
                messageBox.classList.add('bg-gray-100', 'text-gray-700');
            }
        }

        function clearResults() {
            resultsCard.classList.add('hidden');
            summaryOutput.textContent = '';
            actionsOutput.innerHTML = '';
            transcriptOutput.textContent = '';
        }

        // --- Event Listener ---

        audioInput.addEventListener('change', () => {
            summarizeBtn.disabled = audioInput.files.length === 0;
            if (audioInput.files.length > 0) {
                // Determine mime type for display
                const mimeType = audioInput.files[0].type || 'audio/*';
                displayMessage(`File ready: ${audioInput.files[0].name} (Type: ${mimeType})`, 'info');
            } else {
                messageBox.classList.add('hidden');
            }
            clearResults();
        });

        // --- Main Processing Function ---
        async function startSummaryProcess() {
            const file = audioInput.files[0];
            if (!file) {
                displayMessage("Please select an audio file first.", 'error');
                return;
            }

            // Client-side MIME check
            if (!file.type.startsWith('audio/')) {
                displayMessage("Invalid file type. Please upload an audio file.", 'error');
                return;
            }

            displayMessage("Processing... Uploading audio and generating summary (This may take 10-30 seconds depending on file size).", 'loading');
            summarizeBtn.disabled = true;
            clearResults();

            try {
                // Prepare form data to send the file
                const formData = new FormData();
                formData.append('audio', file);
                
                // Also send the MIME type, as it's critical for the API call
                formData.append('mime_type', file.type); 

                // Send the request to the Flask backend. 
                const response = await fetch('/api/summarize', {
                    method: 'POST',
                    body: formData,
                });

                // Check for HTTP errors (like 404, 500, 503)
                if (!response.ok) {
                    const errorData = await response.json().catch(() => ({ error: "Server returned a non-JSON error or status code: " + response.status }));
                    throw new Error(errorData.error || `HTTP error! Status: ${response.status}`);
                }

                const data = await response.json();
                
                // --- Display Results ---
                
                // 1. Summary
                summaryOutput.textContent = data.summary;

                // 2. Actions
                actionsOutput.innerHTML = ''; // Clear previous
                
                // NEW LOGIC: Check if actions array is populated
                if (data.actions && data.actions.length > 0) {
                    data.actions.forEach(action => {
                        const li = document.createElement('li');
                        li.textContent = action;
                        actionsOutput.appendChild(li);
                    });
                } else {
                    const li = document.createElement('li');
                    li.classList.add('italic', 'text-gray-500');
                    li.textContent = "No specific action items or tasks were clearly identified in the meeting audio.";
                    actionsOutput.appendChild(li);
                }

                // 3. Transcript
                transcriptOutput.textContent = data.transcript;

                resultsCard.classList.remove('hidden');
                displayMessage("Summary generated successfully!", 'success');

            } catch (error) {
                console.error("Summarization Error:", error);
                displayMessage(`Error: ${error.message || "Failed to generate summary. Check the console for details."}`, 'error');
            } finally {
                summarizeBtn.disabled = false;
            }
        }
    </script>
</body>
</html>
"""

def process_audio_with_gemini(audio_file, mime_type):
    """
    Handles file reading, Base64 encoding, and the single multimodal API call
    to get the transcript, summary, and action items.
    """
    global GEMINI_API_KEY
    max_retries = 3
    
    if GEMINI_API_KEY == "YOUR_NEW_API_KEY_HERE":
        raise ValueError("API Key is still set to the placeholder. Please replace 'YOUR_NEW_API_KEY_HERE' in app.py.")
    
    # 1. Read and Base64 Encode Audio File
    audio_data = audio_file.read()
    base64_audio = base64.b64encode(audio_data).decode('utf-8')
    logging.info(f"Successfully encoded {len(audio_data) / 1024:.2f} KB of audio data.")

    # 2. Define the System Prompt and Structured Schema
    # UPDATED: Added instruction to explicitly return [] if no actions found.
    system_prompt = (
        "You are an expert meeting analysis assistant. Your task is two-fold: "
        "1. Transcribe the provided audio file completely and accurately. "
        "2. Analyze the full transcript to extract: a concise summary (summary), and a list of all actionable tasks (actions). "
        "If no actions are found, the 'actions' array MUST be returned as an empty list (e.g., []). "
        "Return the output STRICTLY as a single JSON object with three keys: 'transcript', 'summary', and 'actions'."
    )

    user_query = "Please perform transcription and meeting analysis on this audio file."
    
    response_schema = {
        "type": "OBJECT",
        "properties": {
            "transcript": {"type": "STRING", "description": "The full, raw transcription of the audio file."},
            "summary": {"type": "STRING", "description": "A concise, 2-3 sentence summary of the meeting's main topics and key decisions."},
            "actions": {
                "type": "ARRAY",
                "items": {"type": "STRING"},
                "description": "A list of actionable tasks, clearly stating the responsible person and the deliverable/deadline."
            }
        },
        "required": ["transcript", "summary", "actions"]
    }

    # 3. Construct the Multimodal Payload
    payload = {
        "contents": [{
            "parts": [
                {"text": user_query},
                {
                    "inlineData": {
                        "mimeType": mime_type,
                        "data": base64_audio
                    }
                }
            ]
        }],
        "systemInstruction": {"parts": [{"text": system_prompt}]},
        "generationConfig": {
            "responseMimeType": "application/json",
            "responseSchema": response_schema
        }
    }
    
    # 4. API Call with Exponential Backoff
    for attempt in range(max_retries):
        try:
            logging.info(f"Attempting API call {attempt + 1}/{max_retries} for audio processing.")
            response = requests.post(f"{GEMINI_API_URL}?key={GEMINI_API_KEY}", json=payload)
            response.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx)
            
            result = response.json()
            # Extract JSON text from the LLM response
            json_text = result['candidates'][0]['content']['parts'][0]['text']
            
            # Parse the structured JSON response
            llm_data = json.loads(json_text)
            
            logging.info("Gemini API call succeeded and JSON was parsed.")
            
            # The model returns the final structured data directly
            return llm_data

        except requests.exceptions.HTTPError as http_err:
            logging.error(f"HTTP Error on attempt {attempt+1}: {http_err}. Status Code: {response.status_code}")
            if response.status_code in (401, 403):
                 # Fail immediately on key errors
                 raise ValueError(f"API Key returned an Authorization error ({response.status_code}). Please check your key.")
            
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)
            else:
                raise http_err
        except Exception as e:
            if attempt < max_retries - 1:
                logging.warning(f"API call failed (Attempt {attempt+1}/{max_retries}): {e}. Retrying...")
                time.sleep(2 ** attempt)
            else:
                logging.error(f"API call failed after {max_retries} attempts.")
                raise e

@app.route('/')
def index():
    """Serves the main frontend HTML content."""
    return HTML_CONTENT
    
@app.route('/api/summarize', methods=['POST'])
def summarize_meeting():
    """
    Handles the audio file upload, performs transcription, and calls the LLM for summarization.
    """
    logging.info("Received request to /api/summarize")
    
    if 'audio' not in request.files:
        return jsonify({"error": "No audio file provided. Please ensure the field name is 'audio'."}), 400
    
    audio_file = request.files['audio']
    # CRITICAL: We retrieve the mime_type sent from the frontend to ensure correct API payload construction
    mime_type = request.form.get('mime_type', 'audio/mpeg') 

    if audio_file.filename == '':
        return jsonify({"error": "No selected file."}), 400

    try:
        filename = secure_filename(audio_file.filename)
        logging.info(f"Processing file: {filename} with MIME type: {mime_type}")
        
        # Combined ASR and LLM Step
        summary_data = process_audio_with_gemini(audio_file, mime_type)
        
        logging.info("Successfully generated and returning summary data.")
        return jsonify(summary_data)

    except ValueError as e:
        return jsonify({"error": f"Configuration Error: {e}"}), 500
    except requests.exceptions.RequestException as e:
        logging.error(f"LLM API Request Error: {e}")
        return jsonify({"error": "Failed to communicate with the summarization service (LLM API). Please ensure your audio format is supported."}), 503 
    except Exception as e:
        logging.critical(f"Critical Internal Server Error: {e}")
        return jsonify({"error": "An unexpected error occurred during processing. Check server logs."}), 500

if __name__ == '__main__':
    # Running on port 5000 is standard for Flask development
    app.run(debug=True, port=5000)
