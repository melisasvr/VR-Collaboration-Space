# 🥽 VR Collaboration Spaces
- VR Collaboration Spaces is a multilingual virtual reality meeting platform designed to facilitate global team collaboration. 
- It supports seven languages (English, Turkish, Spanish, French, German, Italian, Chinese) and includes a web-based dashboard for real-time visualization. 
- The platform integrates AI-powered features such as moderation, note-taking, and video recording, making it ideal for cross-cultural project coordination.

## 🌍 Key Features:
- Multilingual Support: UI translations and gesture reactions in seven languages with country flag indicators.
- VR Interactions: 3D positioning, proximity-based chat, and gesture recognition (wave, thumbs up, clap, point, peace).
- Web Dashboard: Real-time visualization of VR room, participant list, activity feed, and language analytics.
- AI Features:
- ⚠️Moderation: Detects toxic language in chat messages and logs warnings.
- 📝Note-Taking: Generates professional meeting summaries and action items.
- 📹Video Recording: Captures session events (joins, gestures, movements) and saves them as JSON files.
- Proximity Interactions: Triggers notifications when participants are within 3 units of each other.
- Recording Storage: Saves session data, including transcripts and moderation logs, to the recordings/ directory.

## Prerequisites
- Python 3.8+
- pip for installing dependencies
- A modern web browser (e.g., Chrome, Firefox) for the dashboard
- Optional: VR headset for full experience (simulated in demo)

## Installation
1. Clone the Repository (or create the project directory):
- `git clone <repository-url>`
- `cd vr-collaboration-spaces`
- Alternatively, save the main.py and requirements_enhanced.txt files in a new directory.
2. Install Dependencies: Create a virtual environment (optional but recommended):
- `python -m venv venv`
- `source venv/bin/activate  # On Windows: venv\Scripts\activate`
- Install required packages:
- `pip install -r requirements_enhanced.txt`
3. Ensure Directory Structure: The script automatically creates a `recordings/` directory for saving session data. Ensure write permissions in the project directory.

## Usage
1. Run the Application:
- `python main.py`
- This starts the web server on `http://localhost:5000` and runs a 50-minute demo simulating a multilingual VR meeting.
2. Access the Web Dashboard: Open `http://localhost:5000` in a browser to view the real-time dashboard. The browser should open automatically after a short delay.
3. Interact with the Dashboard:
- VR Room Visualization: See participants' positions in a 2D top-down view.
- Participant List: Displays names, languages, and speaking/muted status with country flags.
- Activity Feed: Shows real-time events (joins, gestures, proximity alerts, moderation warnings).
- AI Controls:
- Click gesture buttons (e.g.,👋 Wave, 👍Thumbs Up) to simulate VR gestures for selected participants.
- Toggle recording with the "📹Start/Stop Recording" button.
- Request AI-generated notes with the "📝Get AI Notes" button.
- Save session recordings to the recordings/ directory with the "💾Save Recording" button.
4. Stop the Demo: Press Ctrl+C in the terminal to stop the demo early. The server will shut down gracefully.

## Demo Details
- The main.py script includes a demo_multilingual_vr_with_web function that:
- Creates a VR room named "Global Localization Project Kickoff".
- Adds seven participants with different languages and initial positions.
- Simulates gestures (e.g., wave, clap) and movements for proximity interactions.
- Automatically starts recording to capture all events.
- Saves a recording to the recordings/ directory during the demo.
- Runs for 50 minutes (3000 seconds) to showcase real-time updates.
- Sample Output
- Console: Displays participant joins, gestures, proximity alerts, and room layout.
- Web Dashboard: Visualizes participant positions, activity feed, and AI-generated notes.
- Recordings: JSON files in recordings/ contain room metadata, participant list, session transcript, and moderation logs.

## 📁 File Structure
```
vr-collaboration-spaces/
├── main.py                   # Main application script
├── requirements_enhanced.txt # Dependency list
├── recordings/               # Directory for saved session recordings
```

## Requirements
- The `requirements_enhanced.txt` file lists the necessary Python packages:
```
# Core web framework
flask>=2.3.0
flask-socketio>=5.3.0
# Real-time communication
websockets>=11.0
python-socketio>=5.8.0
# Async support
asyncio-mqtt>=0.13.0
# Utilities
requests>=2.31.0
numpy>=1.24.0
```
- Optional AI dependencies (commented out) can be enabled for advanced features like natural language processing.

## Troubleshooting
- "No data to save" Error: Ensure recording is started before interactions. The demo now saves recordings with at least minimal metadata.
- Web Dashboard Not Loading: Verify the server is running (http://localhost:5000) and check for firewall/port conflicts.
- Missing Dependencies: Run pip install -r requirements_enhanced.txt to install all required packages.
- Recording Files Empty: Check console logs for transcript entries. Ensure video_recording_enabled is True during interactions.

## 📜 License
- This project is licensed under the MIT License. See the LICENSE file for details (if applicable).
## 🙌 Acknowledgements
- Built with:
- Flask
- Flask-SocketIO
- Pure HTML/CSS/JavaScript for real-time dashboard


## Contributing
1. Fork the repository
2. Create a feature branch (git checkout -b feature/new-scenario)
3. Commit your changes (git commit -am 'Add new scenario')
4. Push to the branch (git push origin feature/new-scenario)
5. Create a Pull Request

**Star ⭐ this project if you believe this project is helpful!**
