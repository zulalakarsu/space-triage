# Space Triage: AI-Guided Ultrasound Assistant

Space Triage is an AI-powered medical assistant designed for space missions, helping astronauts perform and interpret ultrasound scans with real-time guidance.

## Features

- **Welcome Page**: User-friendly interface with login functionality
- **Health Records Dashboard**: Comprehensive view of organ health status
- **Organ Selection**: Interactive interface for selecting target organs
- **AI-Guided Ultrasound**: Real-time assistance for ultrasound scanning
- **Diagnosis Support**: AI-powered analysis and recommendations

## Getting Started

### Prerequisites

- Python 3.8+
- pip (Python package manager)

### Installation

1. Clone the repository:
```bash
git clone https://github.com/zulalakarsu/space-triage.git
cd space-triage
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install required packages:
```bash
pip install -r requirements.txt
```

### Running the Application

1. Start the Streamlit app:
```bash
streamlit run streamlit_app.py
```

2. Open your web browser and navigate to the URL shown in the terminal (typically http://localhost:8501)

## Project Structure

- `streamlit_app.py`: Main application file
- `requirements.txt`: Python package dependencies
- `assets/`: Directory for static assets (images, etc.)

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## How It Works

1. **Area Specification:**  
   The astronaut specifies the anatomical area for analysis by speaking a simple command.

2. **Image Capture and Input:**  
   An ultrasound image is captured using the NASA Ultrasound-2 system and is then fed into Space Triage.

3. **Segmentation Analysis:**  
   The segmentation model processes the image to verify whether the specified anatomical area is present.  
   - **If the target area is found:**  
     The system provides a detailed diagnostic assessment.
   - **If the target area is missing:**  
     Voice-guided instructions are generated to help transition the probe to the correct position.

4. **Voice Guidance and Feedback:**  
   The system's voice agent produces a transcript that can be read aloud, instructing the astronaut on necessary adjustments. This includes:
   - Verification of the current image.
   - Step-by-step movements and probe positioning.
   - Optimization of machine settings (depth, gain, frequency).
   - Final confirmation when the correct view is achieved.

## Example Workflow

1. **Astronaut Command:** "Heart."
2. **Image Capture:** An ultrasound image is taken and fed into the segmentation model.
3. **Segmentation Outcome:**
   - **If the Heart is Visible:**  
     The system says:  
     "The heart is visible. The image displays clear cardiac landmarks including chamber walls and valve motion. Proceed with the cardiac evaluation."
   - **If the Heart is Not Visible:**  
     The system says:  
     "The current image does not show the heart. Please slide the probe upward and adjust the angle slightly toward the chest. Once repositioned, recapture the image."
