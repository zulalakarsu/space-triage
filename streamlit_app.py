from dotenv import load_dotenv
load_dotenv()
import streamlit as st
import requests
from PIL import Image
import io
import time
import json
from typing import List, Dict, Any, Optional
import base64
import os
from elevenlabs.client import ElevenLabs
# from pydub import AudioSegment


# Initialize ElevenLabs client
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
eleven_client = ElevenLabs(api_key=ELEVENLABS_API_KEY)

# Configure the page - MUST BE FIRST STREAMLIT COMMAND
st.set_page_config(
    page_title="Space Triage: AI-Guided Ultrasound",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Define API endpoints
BASE_URL = "https://space-triage-199983032721.us-central1.run.app"
IDENTIFY_API = f"{BASE_URL}/identify"
NAVIGATE_API = f"{BASE_URL}/navigate"
DESCRIBE_API = f"{BASE_URL}/describe"

# Add CSS for the days label
st.markdown("""
    <style>
    .health-chain-container {
        display: flex;
        align-items: center;
        gap: 15px;
        margin: 10px 0;
    }
    
    .days-label {
        color: white;
        font-size: 14px;
        font-weight: 500;
        text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.3);
        min-width: 45px;
    }
    
    .health-chain {
        display: flex;
        gap: 4px;
        align-items: center;
        background: rgba(0, 0, 0, 0.3);
        padding: 15px;
        border-radius: 20px;
        justify-content: flex-start;
        overflow-x: auto;
        min-height: 50px;
        flex-grow: 1;
    }
    </style>
""", unsafe_allow_html=True)

def display_health_history(organ_name):
    """Display a chain of health status for the past 7 days and future days up to 30 days total"""
    # Mock data - in real app, this would come from your database
    mock_history = {
        "Liver": ["green", "yellow", "red", "green", "green", "yellow", "red"],
        "Kidneys": ["green", "green", "yellow", "green", "green", "green", "green"],
        "Pancreas": ["yellow", "yellow", "green", "green", "yellow", "green", "green"],
        "Breasts": ["green", "green", "green", "yellow", "green", "green", "yellow"],
        "Thyroid": ["yellow", "red", "red", "yellow", "yellow", "yellow", "red"],
        "Heart": ["green", "green", "yellow", "green", "green", "green", "green"],
        "Lungs": ["green", "yellow", "green", "green", "green", "yellow", "green"]
    }
    
    # Mock daily reports data
    if "daily_reports" not in st.session_state:
        st.session_state.daily_reports = {
            str(i): {
                "date": f"2024-03-{i:02d}",
                "status": "healthy" if i % 3 != 0 else "unhealthy",
                "notes": "Regular checkup completed" if i % 3 != 0 else "Some concerns noted",
                "vitals": {
                    "heart_rate": f"{60 + i}",
                    "blood_pressure": f"120/{70 + i}",
                    "temperature": f"{36.5 + i/10:.1f}",
                },
                "recommendations": [
                    "Continue regular monitoring",
                    "Maintain exercise routine" if i % 3 != 0 else "Schedule follow-up",
                    "Stay hydrated"
                ],
                "alerts": [] if i % 3 != 0 else ["Elevated readings detected"]
            } for i in range(1, 31)
        }
    
    history = mock_history.get(organ_name, ["green"] * 7)
    future_days = ["inactive"] * 23
    all_statuses = history + future_days
    days = [str(i) for i in range(1, 31)]
    
    # Create the chain HTML with the days label - using compact format
    chain_html = '<div class="health-chain-container"><div class="days-label">Days</div><div class="health-chain">'
    
    for i, (day, status) in enumerate(zip(days, all_statuses)):
        current_class = " current" if i == 6 else ""
        if status == "inactive":
            chain_html += f'<div class="health-day health-{status}{current_class}" title="Day {day}: No data" onclick="handleDayClick(\'{day}\')" style="cursor: pointer;">{day}</div>'
        else:
            status_text = "Healthy" if status == "green" else "Warning" if status == "yellow" else "Critical"
            chain_html += f'<div class="health-day health-{status}{current_class}" title="Day {day}: {status_text}" onclick="handleDayClick(\'{day}\')" style="cursor: pointer;">{day}</div>'
    
    chain_html += '</div></div>'
    
    # Add JavaScript for handling clicks
    js_code = '<script>function handleDayClick(day) {window.parent.postMessage({type: "streamlit:setComponentValue", value: day}, "*");}</script>'
    
    # Render the chain and JavaScript
    st.markdown(chain_html + js_code, unsafe_allow_html=True)
    
    # Handle day selection using session state
    if "selected_day" not in st.session_state:
        st.session_state.selected_day = None
        
    selected_day = st.query_params.get("selected_day", None)
    if selected_day:
        st.session_state.selected_day = selected_day
        
    # Show day's dashboard if a day is selected
    if st.session_state.selected_day and st.session_state.selected_day in st.session_state.daily_reports:
        report = st.session_state.daily_reports[st.session_state.selected_day]
        
        # Create three columns for the dashboard cards
        col1, col2, col3 = st.columns([1, 1, 1])
        
        with col1:
            # Status Overview Card
            st.markdown(f"""
                <div class="organ-card">
                    <h3>Status Overview</h3>
                    <p><strong>Latest Check:</strong> {report['date']}</p>
                    <p><strong>Status:</strong> 
                        <span class="status-{report['status']}">
                            {report['status'].upper()}
                        </span>
                    </p>
                </div>
            """, unsafe_allow_html=True)
        
        with col2:
            # Active Alerts
            alerts_html = """
                <div class="organ-card">
                    <h3>⚠️ Active Alerts</h3>
            """
            
            # Add notes if they exist
            if report['notes']:
                alerts_html += f'<p class="organ-notes">{report["notes"]}</p>'
            
            # Add alerts if they exist
            if report['alerts']:
                alerts_html += '<ul class="alert-list">'
                for alert in report['alerts']:
                    alerts_html += f'<li class="alert-item">{alert}</li>'
                alerts_html += '</ul>'
            elif not report['notes']:  # If no alerts and no notes
                alerts_html += '<p class="no-alerts">No active alerts</p>'
            
            alerts_html += "</div>"
            st.markdown(alerts_html, unsafe_allow_html=True)
        
        with col3:
            # Recommendations
            recommendations_html = """
                <div class="organ-card">
                    <h3>Recommendations</h3>
                    <p>Based on your latest assessment:</p>
                    <ul>
            """
            for rec in report.get('recommendations', []):
                recommendations_html += f"<li>{rec}</li>"
            recommendations_html += """
                    </ul>
                </div>
            """
            st.markdown(recommendations_html, unsafe_allow_html=True)
        
        # Add a close button
        if st.button("Close Report", key=f"close_report_{st.session_state.selected_day}"):
            st.session_state.selected_day = None
            st.query_params.clear()
            st.rerun()

# Add CSS for the report summary
st.markdown("""
    <style>
    /* Report Summary Styling */
    .report-summary {
        background: rgba(255, 255, 255, 0.95);
        border-radius: 15px;
        padding: 2rem;
        margin: 1rem 0;
        box-shadow: 0 4px 10px rgba(0, 0, 0, 0.1);
    }
    
    .report-header {
        border-bottom: 1px solid #eee;
        margin-bottom: 1.5rem;
        padding-bottom: 1rem;
    }
    
    .report-header h3 {
        color: #2D3748;
        margin: 0;
        font-size: 1.5rem;
    }
    
    .report-date {
        color: #718096;
        margin: 0.5rem 0 0 0;
        font-size: 0.9rem;
    }
    
    .report-section {
        margin-bottom: 1.5rem;
    }
    
    .report-section h4 {
        color: #4A5568;
        margin-bottom: 0.5rem;
        font-size: 1.1rem;
    }
    
    .report-section ul {
        list-style-type: none;
        padding: 0;
        margin: 0;
    }
    
    .report-section ul li {
        margin-bottom: 0.5rem;
        color: #4A5568;
    }
    
    .report-section.alerts {
        background: rgba(254, 226, 226, 0.5);
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #EF4444;
    }
    
    .report-section.alerts h4 {
        color: #DC2626;
    }
    
    .report-section.alerts ul li {
        color: #B91C1C;
    }
    
    .health-day {
        cursor: pointer;
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    
    .health-day:hover {
        transform: scale(1.1);
        box-shadow: 0 0 15px rgba(255, 255, 255, 0.4);
    }
    </style>
""", unsafe_allow_html=True)

# Initialize session state variables if they don't exist
if "messages" not in st.session_state:
    st.session_state.messages = []
if "current_stage" not in st.session_state:
    st.session_state.current_stage = "welcome"  # Stages: welcome, login, dashboard, select_organ, initial, identify, navigate, describe
if "uploaded_image" not in st.session_state:
    st.session_state.uploaded_image = None
if "needs_navigation" not in st.session_state:
    st.session_state.needs_navigation = False
if "navigate_response" not in st.session_state:
    st.session_state.navigate_response = None
if "description_response" not in st.session_state:
    st.session_state.description_response = None
if "astronaut_name" not in st.session_state:
    st.session_state.astronaut_name = ""
if "selected_organ" not in st.session_state:
    st.session_state.selected_organ = None
if "target_organ" not in st.session_state:
    st.session_state.target_organ = ""
if "health_records" not in st.session_state:
    # Sample health records data structure
    st.session_state.health_records = {
        "liver": {
            "latest_date": "2024-03-15",
            "status": "unhealthy",
            "notes": "Slight inflammation detected, elevated enzyme levels",
            "recommendations": [
                "Monitor liver function tests",
            ],
            "alerts": ["Elevated ALT levels", "Mild fatty changes"]
        },
        "kidneys": {
            "latest_date": "2024-03-14",
            "status": "healthy",
            "notes": "Normal function, good filtration rate",
            "recommendations": [
                "Continue regular hydration",
                "Monitor blood pressure",
                "Maintain balanced diet"
            ],
            "alerts": []
        },
        "pancreas": {
            "latest_date": "2024-03-13",
            "status": "healthy",
            "notes": "Normal size and function, no abnormalities detected",
            "recommendations": [
                "Monitor blood sugar levels",
                "Maintain healthy diet",
                "Regular exercise"
            ],
            "alerts": []
        },
        "breasts": {
            "latest_date": "2024-03-12",
            "status": "healthy",
            "notes": "Normal capacity and function",
            "recommendations": [
                "Maintain good hydration",
                "Regular voiding schedule",
                "Monitor for any changes"
            ],
            "alerts": []
        },
        "thyroid": {
            "latest_date": "2024-03-11",
            "status": "unhealthy",
            "notes": "Slightly enlarged, elevated TSH levels",
            "recommendations": [
                "Follow-up in 1 month",
                "Monitor thyroid function",
                "Consider medication adjustment"
            ],
            "alerts": ["Elevated TSH", "Mild enlargement"]
        },
        "heart": {
            "latest_date": "2024-03-10",
            "status": "healthy",
            "notes": "Normal rhythm, good ejection fraction",
            "recommendations": [
                "Continue regular exercise",
                "Monitor blood pressure",
                "Maintain heart-healthy diet"
            ],
            "alerts": []
        },
        "lungs": {
            "latest_date": "2024-03-09",
            "status": "healthy",
            "notes": "Clear lung fields, normal breathing capacity",
            "recommendations": [
                "Continue regular exercise",
                "Avoid exposure to irritants",
                "Practice deep breathing exercises"
            ],
            "alerts": []
        }
    }


# Text to speech 
if "voice_bytes" not in st.session_state:
    st.session_state.voice_bytes = None

def text_to_speech_bytes(text: str) -> bytes:
    """Convert text to speech using ElevenLabs API"""
    try:
        voice = Voice(
            voice_id="21m00Tcm4TlvDq8ikWAM",  # Default voice ID
            settings=VoiceSettings(stability=0.5, similarity_boost=0.75)
        )
        chunk_gen = eleven_client.text_to_speech.convert(
            text=text,
            voice=voice,
            model_id="eleven_monolingual_v1"
        )
        return b"".join(chunk_gen)
    except Exception as e:
        st.error(f"Error generating speech: {str(e)}")
        return b""

def speak(text: str):
    st.session_state.voice_bytes = text_to_speech_bytes(text)

if st.session_state.voice_bytes:
    audio_bytes = st.session_state.voice_bytes

    with open("debug_elevenlabs.mp3", "wb") as f:
        f.write(audio_bytes)
    b64 = base64.b64encode(audio_bytes).decode("utf-8")
    audio_html = f"""
    <audio controls autoplay>
      <source src="data:audio/mp3;base64,{b64}" type="audio/mp3">
      Your browser does not support the audio element.
    </audio>
    """
    st.markdown(audio_html, unsafe_allow_html=True)


# Custom functions
def image_to_bytes(uploaded_image):
    """Convert uploaded image to bytes"""
    if uploaded_image is None:
        return None
    
    img = Image.open(uploaded_image)
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()

def call_identify_api(image_bytes, target_organ):
    """Call the identify API endpoint with an image and organ name"""
    try:
        files = {"image": ("image.jpg", image_bytes, "image/jpeg")}
        data = {"entity_name": target_organ}
        response = requests.post(IDENTIFY_API, files=files, data=data)
        return response.json()
    except Exception as e:
        st.error(f"Error calling identify API: {e}")
        return {"found": False, "entity": target_organ, "error": str(e)}

def call_navigate_api(image_bytes, target_organ):
    """Call the navigate API endpoint with image and entity name"""
    try:
        files = {"image": ("image.jpg", image_bytes, "image/jpeg")}
        data = {"entity_name": target_organ}
        
        # Send entity_name as form data and the image file
        response = requests.post(NAVIGATE_API, files=files, data=data)
        return response.json()
    except Exception as e:
        st.error(f"Error calling navigate API: {e}")
        return {"response": "Error occurred during navigation guidance.", "error": str(e)}

def call_description_api(image_bytes, target_organ):
    """Call the describe API endpoint with an image"""
    try:
        files = {"image": ("image.jpg", image_bytes, "image/jpeg")}
        data = {"target_organ": target_organ}
        response = requests.post(DESCRIBE_API, files=files, data=data)
        return response.json()
    except Exception as e:
        st.error(f"Error calling describe API: {e}")
        return {"description": "Error occurred during diagnosis.", "error": str(e)}

def process_image_flow():
    """Process the uploaded image through the flow based on current stage"""
    if st.session_state.uploaded_image is None:
        return
    
    image_bytes = image_to_bytes(st.session_state.uploaded_image)
    
    if st.session_state.current_stage == "identify":
        # Call identify API
        with st.spinner("Analyzing image..."):
            response = call_identify_api(
                image_bytes,
                st.session_state.target_organ
            )
            
        if response.get("found", False):
            st.session_state.messages.append({"role": "assistant", "content": f"✅ The {response.get('entity', 'target organ')} has been successfully identified in the image."})
            st.session_state.current_stage = "describe"
            
            # Move directly to description
            with st.spinner("Generating diagnosis..."):
                description_response = call_description_api(image_bytes, st.session_state.target_organ)
                st.session_state.description_response = description_response
                
            diagnosis_text = description_response.get("description", "No diagnosis available")
            st.session_state.messages.append({"role": "assistant", "content": f"🔬 **Diagnosis Results**:\n\n{diagnosis_text}"})
            
        else:
            # 🚩 not found → go *directly* to navigation guidance
            st.session_state.messages.append({
                "role": "assistant",
                "content": f"❌ I couldn't clearly identify the {st.session_state.target_organ} in this image. Here's how to reposition for a better {st.session_state.target_organ} view:"
            })

            # call your navigation API immediately
            with st.spinner("Generating navigation guidance…"):
                nav = call_navigate_api(image_bytes, st.session_state.target_organ)

            nav_text = nav.get("response", "No navigation guidance available.")
            st.session_state.messages.append({
                "role": "assistant",
                "content": f"🧭 **Navigation Guidance**:\n\n{nav_text}\n\nPlease adjust your probe accordingly and re‑upload your image when ready."
            })
            speak(nav_text)
            # set stage so on next upload we go back to identify
            st.session_state.current_stage = "wait_for_new_image"
    
    elif st.session_state.current_stage == "navigate":
        # Call navigate API with image and entity name
        with st.spinner("Generating navigation guidance..."):
            response = call_navigate_api(image_bytes, st.session_state.target_organ)
            st.session_state.navigate_response = response
            
        navigation_text = response.get("response", "No navigation guidance available")
        st.session_state.messages.append({"role": "assistant", "content": f"🧭 **Navigation Guidance**:\n\n{navigation_text}\n\nPlease adjust your probe following these instructions and upload a new image when ready."})
        st.session_state.current_stage = "wait_for_new_image"
    
    elif st.session_state.current_stage == "describe":
        # Call describe API
        with st.spinner("Generating diagnosis..."):
            response = call_description_api(image_bytes, st.session_state.target_organ)
            st.session_state.description_response = response
            
        diagnosis_text = response.get("description", "No diagnosis available")
        st.session_state.messages.append({"role": "assistant", "content": f"🔬 **Diagnosis Results**:\n\n{diagnosis_text}"})
        st.session_state.current_stage = "chat"  # Move to open chat for follow-up questions

def handle_user_input(user_input):
    """Process text input from the user"""
    if user_input:
        # Add user message to chat
        st.session_state.messages.append({"role": "user", "content": user_input})
        
        # Handle user response based on current stage
        if st.session_state.current_stage == "ask_navigation" and st.session_state.needs_navigation:
            if "yes" in user_input.lower() or "sure" in user_input.lower() or "ok" in user_input.lower():
                st.session_state.current_stage = "navigate"
                st.session_state.messages.append({"role": "assistant", "content": "I'll help you navigate to get a better view. Processing your current image..."})
                process_image_flow()
            else:
                st.session_state.messages.append({"role": "assistant", "content": "Please upload a different image that shows the target organ more clearly."})
                st.session_state.current_stage = "wait_for_new_image"
        
        # If we're in chat mode (after diagnosis), respond to follow-up questions
        elif st.session_state.current_stage == "chat":
            # Here you could integrate with an LLM to answer follow-up questions
            # For now we'll use a simple response
            st.session_state.messages.append({
                "role": "assistant", 
                "content": "Thank you for your question. To provide a more detailed answer, I would need to connect to a medical knowledge base. Is there something specific about the diagnosis you'd like to know more about?"
            })

def restart_session():
    """Reset the session state to start over"""
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.session_state.messages = []
    st.session_state.current_stage = "initial"
    st.session_state.uploaded_image = None
    st.session_state.needs_navigation = False
    st.session_state.navigate_response = None
    st.session_state.description_response = None
    st.session_state.selected_organ = None
    st.session_state.target_organ = ""
    st.rerun()

# Custom CSS for better styling
st.markdown("""
    <style id="space-triage-styles">
    /* Main background */
    .stApp {
        background-image: url('https://images.unsplash.com/photo-1451187580459-43490279c0fa?ixlib=rb-1.2.1&auto=format&fit=crop&w=1950&q=80');
        background-size: cover;
        background-position: center;
        background-attachment: fixed;
    }
    
    /* Welcome page container */
    .welcome-container {
        max-width: 800px;
        margin: 0 auto;
        padding: 2rem;
        text-align: center;
    }
    
    /* Text background container */
    .text-background {
        background: rgba(0, 0, 0, 0.7);
        padding: 2rem;
        border-radius: 15px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
        backdrop-filter: blur(5px);
        margin-bottom: 2rem;
    }
    
    /* Welcome header */
    .welcome-header {
        text-align: center;
        padding: 1rem 0;
        color: #FFFFFF !important;
        font-size: 2.5rem;
        font-weight: bold;
        text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.3);
        margin: 0;
    }
    
    /* Welcome message */
    .welcome-message {
        font-size: 1.2rem;
        color: #FFFFFF !important;
        line-height: 1.6;
        margin: 0;
        text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.3);
    }
    
    /* Start button */
    .stButton > button {
        background-color: #3B82F6 !important;
        color: white !important;
        border: 1px solid rgba(255, 255, 255, 0.2) !important;
        padding: 0.5rem 1rem !important;
        width: 100% !important;
        border-radius: 8px !important;
        backdrop-filter: blur(5px) !important;
        transition: all 0.3s ease !important;
        font-size: 0.9rem !important;
        margin-top: 0 !important;
    }
    
    .stButton > button:hover {
        background-color: #2563EB !important;
        border-color: rgba(255, 255, 255, 0.3) !important;
        transform: translateY(-2px) !important;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1) !important;
    }
    
    /* Sidebar styling */
    .css-1d391kg {
        background-color: rgba(255, 255, 255, 0.95);
    }
    
    /* Chat message styling */
    .stChatMessage {
        background-color: rgba(255, 255, 255, 0.9);
        border-radius: 10px;
        padding: 1rem;
        margin: 0.5rem 0;
    }
    
    /* Dashboard styles */
    .dashboard-container {
        max-width: 1200px;
        margin: 0 auto;
        padding: 2rem;
    }
    
    .organ-card {
        background: rgba(255, 255, 255, 0.9);
        border-radius: 10px;
        padding: 1.5rem;
        margin-bottom: 1rem;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        transition: transform 0.2s;
        height: 100%;
        min-height: 200px;
    }
    
    .organ-card h3 {
        color: #2D3748;
        margin-bottom: 1rem;
        font-size: 1.2rem;
        font-weight: bold;
    }
    
    .organ-card ul {
        list-style-type: none;
        padding-left: 0;
        margin-top: 1rem;
    }
    
    .organ-card ul li {
        margin-bottom: 0.5rem;
        padding-left: 1.5rem;
        position: relative;
    }
    
    .organ-card ul li:before {
        content: "•";
        position: absolute;
        left: 0;
        color: #EF4444;
    }
    
    .status-healthy {
        color: #10B981;
        font-weight: bold;
    }
    
    .status-unhealthy {
        color: #EF4444;
        font-weight: bold;
    }
    
    .dashboard-header {
        color: #FFFFFF !important;
        text-align: left;
        margin-bottom: 1rem;
        text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.3);
    }
    
    /* Start New Assessment button styling */
    .stButton > button {
        background-color: #3B82F6 !important;
        color: white !important;
        border: 1px solid rgba(255, 255, 255, 0.2) !important;
        padding: 0.75rem 1rem !important;
        font-size: 1rem !important;
        border-radius: 8px !important;
        transition: all 0.3s ease !important;
        margin-top: 1rem !important;
    }
    
    .stButton > button:hover {
        background-color: #2563EB !important;
        border-color: rgba(255, 255, 255, 0.3) !important;
        transform: translateY(-2px) !important;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1) !important;
    }
    
    /* Organ selection styles */
    .organ-selection-card {
        background: rgba(255, 255, 255, 0.9);
        border-radius: 15px;
        padding: 1.5rem;
        margin-bottom: 1rem;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        transition: all 0.3s ease;
        text-align: center;
        cursor: pointer;
        border: 2px solid transparent;
    }
    
    .organ-selection-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 6px 12px rgba(0, 0, 0, 0.15);
    }
    
    .organ-icon {
        font-size: 2.5rem;
        margin: 0;
        padding: 0.5rem;
    }
    
    .organ-name {
        font-size: 1.2rem;
        font-weight: bold;
        margin: 0.5rem 0;
        color: #2D3748;
    }
    
    .organ-description {
        font-size: 0.9rem;
        color: #718096;
        margin: 0;
    }
    
    /* Tab styling */
    .stTabs [data-baseweb="tab-list"] {
        background-color: rgba(0, 0, 0, 0.5);
        border-radius: 10px;
        padding: 0.5rem;
    }
    
    .stTabs [data-baseweb="tab"] {
        color: #FFFFFF !important;
        text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.3);
    }
    
    .stTabs [aria-selected="true"] {
        background-color: rgba(255, 255, 255, 0.2) !important;
        color: #FFFFFF !important;
    }
    
    /* Main title styling */
    .main-title {
        color: #FFFFFF !important;
        text-align: center;
        text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.3);
        margin-bottom: 2rem;
        margin-top: 1rem !important;
    }
    
    /* Input label styling */
    .stTextInput label {
        color: #FFFFFF !important;
        text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.3);
    }
    
    .health-chain {
        display: flex;
        gap: 4px;
        align-items: center;
        margin: 10px 0;
        background: rgba(0, 0, 0, 0.3);
        padding: 15px;
        border-radius: 20px;
        justify-content: flex-start;
        overflow-x: auto;
        min-height: 50px;
    }
    
    .health-day {
        width: 35px;
        height: 35px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 14px;
        color: white;
        font-weight: bold;
        border: 2px solid rgba(255, 255, 255, 0.2);
        flex-shrink: 0;
    }
    
    .health-green {
        background-color: #28a745;
    }
    
    .health-yellow {
        background-color: #ffc107;
    }
    
    .health-red {
        background-color: #dc3545;
    }
    
    .health-inactive {
        background-color: rgba(255, 255, 255, 0.1);
        color: rgba(255, 255, 255, 0.5);
        border: 2px dashed rgba(255, 255, 255, 0.2);
    }
    
    .health-day.current {
        border: 2px solid white;
        box-shadow: 0 0 10px rgba(255, 255, 255, 0.3);
    }
    
    /* Active Alerts styling */
    .organ-notes {
        color: #4A5568;
        margin-bottom: 1rem;
        font-size: 1rem;
        line-height: 1.5;
    }
    
    .alert-list {
        list-style-type: none;
        padding-left: 0;
        margin: 0;
    }
    
    .alert-item {
        color: #EF4444;
        margin-bottom: 0.5rem;
        padding-left: 1.5rem;
        position: relative;
        font-weight: 500;
    }
    
    .alert-item:before {
        content: "⚠️";
        position: absolute;
        left: 0;
        font-size: 1rem;
    }
    
    .no-alerts {
        color: #10B981;
        font-style: italic;
        text-align: center;
        margin: 1rem 0;
    }
    
    /* Navigation buttons container */
    div[data-testid="column"]:nth-child(3) {
        display: flex;
        flex-direction: column;
        gap: 0.5rem;
    }
    
    /* Navigation buttons */
    div[data-testid="column"] button {
        margin-bottom: 0.5rem !important;
    }
    
    /* Finish Assessment button */
    div[data-testid="column"]:nth-child(3) button[kind="primary"] {
        background-color: #10B981 !important;
        color: white !important;
        border: 1px solid rgba(255, 255, 255, 0.2) !important;
        padding: 0.5rem 1rem !important;
        width: 100% !important;
        border-radius: 8px !important;
        backdrop-filter: blur(5px) !important;
        transition: all 0.3s ease !important;
        font-size: 0.9rem !important;
        margin-top: 0.5rem !important;
    }
    
    div[data-testid="column"]:nth-child(3) button[kind="primary"]:hover {
        background-color: #059669 !important;
        border-color: rgba(255, 255, 255, 0.3) !important;
        transform: translateY(-2px) !important;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1) !important;
    }
    
    /* Save Dialog */
    .save-dialog {
        background: rgba(0, 0, 0, 0.8);
        border-radius: 12px;
        padding: 2rem;
        margin: 1rem 0;
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        text-align: center;
        color: white;
    }
    
    .save-dialog h3 {
        color: white;
        margin-bottom: 1rem;
        font-size: 1.2rem;
    }
    
    .save-dialog p {
        color: rgba(255, 255, 255, 0.8);
        margin-bottom: 1.5rem;
    }
    
    /* Save Dialog Buttons */
    .save-dialog button {
        min-width: 120px;
    }
    
    /* Save & Exit Button */
    .element-container:has(button:contains("Save & Exit")) button {
        background-color: #10B981 !important;
    }
    
    .element-container:has(button:contains("Save & Exit")) button:hover {
        background-color: #059669 !important;
    }
    
    /* Exit without Saving Button */
    .element-container:has(button:contains("Exit without Saving")) button {
        background-color: #EF4444 !important;
    }
    
    .element-container:has(button:contains("Exit without Saving")) button:hover {
        background-color: #DC2626 !important;
    }
    
    /* Cancel Button */
    .element-container:has(button:contains("Cancel")) button {
        background-color: #6B7280 !important;
    }
    
    .element-container:has(button:contains("Cancel")) button:hover {
        background-color: #4B5563 !important;
    }
    
    /* Button text nowrap */
    div[data-testid="column"] button {
        white-space: nowrap !important;
        overflow: hidden !important;
        text-overflow: ellipsis !important;
        min-width: fit-content !important;
    }
    </style>
""", unsafe_allow_html=True)

# Welcome Page
if st.session_state.current_stage == "welcome":
    # Navigation buttons container
    col1, col2, col3 = st.columns([6, 1, 1])
    with col2:
        if st.button("🏠 Home", key="home_welcome"):
            st.session_state.current_stage = "welcome"
            st.rerun()
    with col3:
        if st.button("👤 Profile", key="profile_welcome"):
            st.session_state.current_stage = "login"
            st.rerun()
    
    st.markdown('<div class="welcome-container">', unsafe_allow_html=True)
    
    # Text content with background
    st.markdown("""
        <div class="text-background">
            <h1 class="welcome-header">Welcome Astronaut!</h1>
            <div class="welcome-message">
                Welcome to Space Triage, your AI-powered medical assistant for space missions.
                <br>Let's begin your medical assessment journey!
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    # Login Button
    if st.button("Login", key="login_button"):
        st.session_state.current_stage = "login"
        st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)

# Login Page
elif st.session_state.current_stage == "login":
    # Navigation buttons container
    col1, col2, col3 = st.columns([6, 1, 1])
    with col2:
        if st.button("🏠 Home", key="home_login"):
            st.session_state.current_stage = "welcome"
            st.rerun()
    with col3:
        if st.button("👤 Profile", key="profile_login"):
            st.session_state.current_stage = "login"
            st.rerun()
    
    st.markdown('<div class="welcome-container">', unsafe_allow_html=True)
    
    # Text content with background
    st.markdown("""
        <div class="text-background">
            <h1 class="welcome-header">Astronaut Login</h1>
            <div class="welcome-message">
                Please enter your name to begin your medical assessment.
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    # Login Form with white label
    st.markdown('<p style="color: white; text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.3);">Astronaut Name</p>', unsafe_allow_html=True)
    astronaut_name = st.text_input("", key="login_name")
    
    if st.button("Continue", key="continue_button"):
        if astronaut_name.strip():
            st.session_state.astronaut_name = astronaut_name
            st.session_state.current_stage = "dashboard"
            st.rerun()
        else:
            st.error("Please enter your name to continue.")
    
    st.markdown('</div>', unsafe_allow_html=True)

# Dashboard Page
elif st.session_state.current_stage == "dashboard":
    st.markdown('<div class="dashboard-container">', unsafe_allow_html=True)
    
    # Navigation buttons container
    col1, col2, col3 = st.columns([6, 1, 1])
    with col2:
        if st.button("🏠 Home", key="home_dashboard"):
            st.session_state.current_stage = "welcome"
            st.rerun()
    with col3:
        if st.button("👤 Profile", key="profile_dashboard"):
            st.session_state.current_stage = "login"
            st.rerun()
    
    # Dashboard Header with Start New Assessment button
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown(f"""
            <h1 class="dashboard-header">Health Records Dashboard</h1>
            <h2 class="dashboard-header">Welcome, {st.session_state.astronaut_name}</h2>
        """, unsafe_allow_html=True)
    with col2:
        if st.button("Start New Assessment", key="new_assessment", use_container_width=True):
            st.session_state.current_stage = "select_organ"
            st.rerun()
    
    # Create tabs for each organ
    tabs = st.tabs([organ.capitalize() for organ in st.session_state.health_records.keys()])
    
    # Display detailed information for each organ in its respective tab
    for tab, (organ, data) in zip(tabs, st.session_state.health_records.items()):
        with tab:
            # Health History Chain first
            display_health_history(organ.capitalize())
            
            # Create three columns for the main boxes
            col1, col2, col3 = st.columns([1, 1, 1])
            
            with col1:
                # Status Overview Card
                st.markdown(f"""
                    <div class="organ-card">
                        <h3>Status Overview</h3>
                        <p><strong>Latest Check:</strong> {data['latest_date']}</p>
                        <p><strong>Status:</strong> 
                            <span class="status-{data['status']}">
                                {data['status'].upper()}
                            </span>
                        </p>
                    </div>
                """, unsafe_allow_html=True)
            
            with col2:
                # Active Alerts
                alerts_html = """
                    <div class="organ-card">
                        <h3>⚠️ Active Alerts</h3>
                """
                
                # Add notes if they exist
                if data['notes']:
                    alerts_html += f'<p class="organ-notes">{data["notes"]}</p>'
                
                # Add alerts if they exist
                if data['alerts']:
                    alerts_html += '<ul class="alert-list">'
                    for alert in data['alerts']:
                        alerts_html += f'<li class="alert-item">{alert}</li>'
                    alerts_html += '</ul>'
                elif not data['notes']:  # If no alerts and no notes
                    alerts_html += '<p class="no-alerts">No active alerts</p>'
                
                alerts_html += "</div>"
                st.markdown(alerts_html, unsafe_allow_html=True)
            
            with col3:
                # Recommendations
                recommendations_html = """
                    <div class="organ-card">
                        <h3>Recommendations</h3>
                        <p>Based on your latest assessment:</p>
                        <ul>
                """
                for rec in data.get('recommendations', []):
                    recommendations_html += f"<li>{rec}</li>"
                recommendations_html += """
                        </ul>
                    </div>
                """
                st.markdown(recommendations_html, unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)

# Organ Selection Page
elif st.session_state.current_stage == "select_organ":
    st.markdown('<div class="dashboard-container">', unsafe_allow_html=True)
    
    # Top navigation row with Back to Dashboard, Home, and Profile buttons
    col1, col2, col3, col4 = st.columns([2, 4, 1, 1])
    with col1:
        if st.button("← Back to Dashboard", key="back_to_dashboard"):
            st.session_state.current_stage = "dashboard"
            st.rerun()
    with col3:
        if st.button("🏠 Home", key="home_select"):
            st.session_state.current_stage = "welcome"
            st.rerun()
    with col4:
        if st.button("👤 Profile", key="profile_select"):
            st.session_state.current_stage = "login"
            st.rerun()
    
    # Header
    st.markdown(f"""
        <h1 class="dashboard-header">Select Organ to Assess</h1>
        <h2 class="dashboard-header">Welcome, {st.session_state.astronaut_name}</h2>
    """, unsafe_allow_html=True)
    
    # Create a grid of organ selection buttons
    col1, col2, col3 = st.columns(3)
    
    # Define organ icons and descriptions
    organs = {
        "liver": {
            "icon": "🟤",
            "color": "#FF6B6B",
            "description": "Check liver function and health"
        },
        "kidneys": {
            "icon": "🫘",
            "color": "#4ECDC4",
            "description": "Assess kidney function"
        },
        "pancreas": {
            "icon": "🔬",
            "color": "#FFD93D",
            "description": "Evaluate pancreatic health"
        },
        "bladder": {
            "icon": "💧",
            "color": "#6C5CE7",
            "description": "Check bladder condition"
        },
        "thyroid": {
            "icon": "🦋",
            "color": "#A8E6CF",
            "description": "Assess thyroid function"
        },
        "heart": {
            "icon": "❤️",
            "color": "#FF8B94",
            "description": "Evaluate heart health"
        },
        "lungs": {
            "icon": "🫁",
            "color": "#95E1D3",
            "description": "Check lung function"
        }
    }
    
    # Create buttons for each organ
    for i, (organ, details) in enumerate(organs.items()):
        col = [col1, col2, col3][i % 3]
        with col:
            st.markdown(f"""
                <div class="organ-selection-card" style="border-color: {details['color']};">
                    <div class="organ-icon">{details['icon']}</div>
                    <div class="organ-name">{organ.capitalize()}</div>
                    <div class="organ-description">{details['description']}</div>
                </div>
            """, unsafe_allow_html=True)
            if st.button(f"Select {organ.capitalize()}", key=f"select_{organ}"):
                st.session_state.selected_organ = organ
                st.session_state.target_organ = organ  # Set the target organ to the selected organ
                st.session_state.current_stage = "initial"
                st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)

# Main Application (only show if not on welcome or login page)
elif st.session_state.current_stage not in ["welcome", "login"]:
    # Top navigation row with Finish Assessment button
    col1, col2, col3, col4 = st.columns([2, 4, 1, 1])
    with col1:
        if st.button("← Change Organ", key="change_organ_main"):
            st.session_state.current_stage = "select_organ"
            st.rerun()
    with col3:
        if st.button("🏠 Home", key="home_main"):
            st.session_state.current_stage = "welcome"
            st.rerun()
    with col4:
        if st.button("👤 Profile", key="profile_main"):
            st.session_state.current_stage = "login"
            st.rerun()
        if st.button("✓ Finish", key="finish_assessment", type="primary"):
            st.session_state.show_save_dialog = True
            st.rerun()

    # Save/Exit Dialog
    if "show_save_dialog" in st.session_state and st.session_state.show_save_dialog:
        with st.container():
            st.markdown("""
                <div class='save-dialog'>
                    <h3>Save Assessment?</h3>
                    <p>Do you want to save your assessment before exiting?</p>
                </div>
            """, unsafe_allow_html=True)
            
            col1, col2, col3 = st.columns([1, 1, 1])
            with col1:
                if st.button("Save & Exit", key="save_and_exit"):
                    # Here you would implement the save logic
                    st.session_state.show_save_dialog = False
                    st.session_state.current_stage = "dashboard"
                    st.rerun()
            with col2:
                if st.button("Exit without Saving", key="exit_without_save"):
                    st.session_state.show_save_dialog = False
                    st.session_state.current_stage = "dashboard"
                    st.rerun()
            with col3:
                if st.button("Cancel", key="cancel_exit"):
                    st.session_state.show_save_dialog = False
                    st.rerun()
    
    # Main title with white color
    st.markdown('<h1 class="main-title">Space Triage: AI-Guided Ultrasound</h1>', unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.title("🚀 Space Triage")
        st.subheader(f"Welcome, {st.session_state.astronaut_name}")
        
        # Display the selected organ
        if st.session_state.selected_organ:
            st.markdown(f"### Target Organ: {st.session_state.selected_organ.capitalize()}")
        else:
            st.markdown("### No organ selected")
            if st.button("Select Organ", key="select_organ_button"):
                st.session_state.current_stage = "select_organ"
                st.rerun()
        
        # Additional information or settings could go here
        st.markdown("---")
        st.markdown("### How to use:")
        st.markdown("1. Select the organ you wish to diagnose")
        st.markdown("2. Upload an ultrasound image in the chat")
        st.markdown("3. Follow the AI guidance to improve your scan")
        st.markdown("4. Receive an AI-assisted diagnosis")
        
        # Reset button
        if st.button("🔄 Start New Session"):
            restart_session()

    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            # If the message has an image, display it
            if "image" in message:
                st.image(message["image"])

    # Welcome message on first load
    if st.session_state.current_stage == "initial" and not st.session_state.messages:
        with st.chat_message("assistant"):
            st.markdown("👋 Welcome to Space Triage! I'm your AI ultrasound assistant. Please enter the organ you wish to diagnose in the sidebar, then upload an ultrasound image to begin.")
        st.session_state.current_stage = "waiting_for_image"

    # Image uploader in chat input
    uploaded_file = st.file_uploader(
        "Upload an ultrasound image", 
        type=["png", "jpg", "jpeg"],
        key="chat_file_uploader",
        label_visibility="collapsed"
    )

    # Handle file upload
    if uploaded_file is not None and (st.session_state.uploaded_image is None or uploaded_file != st.session_state.uploaded_image):
        # Store the uploaded image
        st.session_state.uploaded_image = uploaded_file
        
        # Add user message with image
        st.session_state.messages.append({
            "role": "user", 
            "content": f"I've uploaded an ultrasound image for {st.session_state.target_organ} analysis.",
            "image": uploaded_file  # Store image in message for reference
        })
        
        # Display the image
        with st.chat_message("user"):
            st.markdown(f"I've uploaded an ultrasound image for {st.session_state.target_organ} analysis.")
            st.image(uploaded_file, caption="Uploaded Ultrasound Image")
        
        # Set stage to identify if we have an organ target
        if st.session_state.target_organ:
            st.session_state.current_stage = "identify"
            # Process the image through our flow
            process_image_flow()
        else:
            with st.chat_message("assistant"):
                st.markdown("❗ Please specify the target organ in the sidebar before proceeding.")
        
        # Force a rerun to update the UI
        st.rerun()

    # Chat input for text messages
    user_input = st.chat_input("Ask a question or provide additional information...")
    if user_input:
        handle_user_input(user_input)
        st.rerun()

    # Add a footer
    st.markdown("---")
    st.caption("Space Triage | AI-Guided Ultrasound Assistant | Demo Version")