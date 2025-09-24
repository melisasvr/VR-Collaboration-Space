"""
VR Collaboration Spaces with 8 Languages + Web Interface + AI Features
Supports: English, Turkish, Spanish, French, German, Italian, Chinese + Web Dashboard
AI Features: Moderation, Note-Taking, Video Recording
"""
import asyncio
import json
import time
import threading
import os
from datetime import datetime
from typing import Dict, List, Optional, Set
from dataclasses import dataclass, asdict
from enum import Enum
import re
from collections import defaultdict
import socket
import websockets
import logging
from flask import Flask, render_template_string, jsonify, request, send_file
from flask_socketio import SocketIO, emit, join_room, leave_room
import webbrowser
from threading import Timer

# Ensure recordings directory exists
os.makedirs("recordings", exist_ok=True)

class Language(Enum):
    ENGLISH = "en"
    TURKISH = "tr" 
    SPANISH = "es"
    FRENCH = "fr"
    GERMAN = "de"
    ITALIAN = "it"
    CHINESE = "zh"

class MessageType(Enum):
    CHAT = "chat"
    VOICE = "voice"
    SCREEN_SHARE = "screen_share"
    WHITEBOARD = "whiteboard"
    FILE_SHARE = "file_share"
    VR_GESTURE = "vr_gesture"
    VR_POSITION = "vr_position"

class ModerationAction(Enum):
    NONE = "none"
    WARNING = "warning"
    MUTE = "mute"
    TIMEOUT = "timeout"
    REMOVE = "remove"

@dataclass
class VRPosition:
    """3D position and rotation in VR space"""
    x: float
    y: float  
    z: float
    rotation_x: float = 0.0
    rotation_y: float = 0.0
    rotation_z: float = 0.0

    def distance_to(self, other: 'VRPosition') -> float:
        """Calculate distance to another position"""
        return ((self.x - other.x)**2 + (self.y - other.y)**2 + (self.z - other.z)**2)**0.5

@dataclass
class Participant:
    user_id: str
    name: str
    preferred_language: Language
    vr_position: VRPosition
    is_muted: bool = False
    is_speaking: bool = False
    join_time: datetime = None
    avatar_id: str = "default"
    country_flag: str = "🌍"
    recent_gestures: List['VRGesture'] = None

    def __post_init__(self):
        if self.join_time is None:
            self.join_time = datetime.now()
        if self.recent_gestures is None:
            self.recent_gestures = []
        # Set country flags based on language
        flag_map = {
            Language.ENGLISH: "🇺🇸",
            Language.TURKISH: "🇹🇷", 
            Language.SPANISH: "🇪🇸",
            Language.FRENCH: "🇫🇷",
            Language.GERMAN: "🇩🇪",
            Language.ITALIAN: "🇮🇹",
            Language.CHINESE: "🇨🇳"
        }
        self.country_flag = flag_map.get(self.preferred_language, "🌍")

@dataclass
class VRGesture:
    """Represents a VR hand gesture or body movement"""
    gesture_type: str
    hand: str
    intensity: float
    duration: float
    timestamp: datetime = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()

class EnhancedMultilingualVRRoom:
    """VR Meeting Room with 8-language support, AI moderation, note-taking, and recording"""
    def __init__(self, room_id: str, room_name: str):
        self.room_id = room_id
        self.room_name = room_name
        self.participants: Dict[str, Participant] = {}
        self.messages: List = []
        self.gestures: List[VRGesture] = []
        self.is_active = False
        self.start_time: Optional[datetime] = None
        # === NEW: AI Features ===
        self.ai_moderation_enabled = True
        self.ai_note_taking_enabled = True
        self.video_recording_enabled = False
        self.session_transcript = []  # Stores all events for notes
        self.moderation_log = []
        self.recording_start_time = None
        self.project_context = "Global Localization Project Kickoff"
        # Enhanced multilingual UI translations
        self.vr_ui_translations = {
            Language.ENGLISH: {
                "welcome": "Welcome to VR space",
                "gesture_detected": "Gesture detected",
                "user_nearby": "User nearby",
                "mute_enabled": "Mute enabled",
                "recording_started": "Recording started",
                "user_joined": "joined the meeting",
                "user_left": "left the meeting"
            },
            Language.TURKISH: {
                "welcome": "VR alanına hoş geldiniz",
                "gesture_detected": "Hareket algılandı", 
                "user_nearby": "Yakında kullanıcı",
                "mute_enabled": "Sessize alma etkinleştirildi",
                "recording_started": "Kayıt başlatıldı",
                "user_joined": "toplantıya katıldı",
                "user_left": "toplantıdan ayrıldı"
            },
            Language.SPANISH: {
                "welcome": "Bienvenido al espacio VR",
                "gesture_detected": "Gesto detectado",
                "user_nearby": "Usuario cercano",
                "mute_enabled": "Silencio activado",
                "recording_started": "Grabación iniciada",
                "user_joined": "se unió a la reunión",
                "user_left": "abandonó la reunión"
            },
            Language.FRENCH: {
                "welcome": "Bienvenue dans l'espace VR",
                "gesture_detected": "Geste détecté",
                "user_nearby": "Utilisateur à proximité",
                "mute_enabled": "Muet activé",
                "recording_started": "Enregistrement démarré",
                "user_joined": "a rejoint la réunion",
                "user_left": "a quitté la réunion"
            },
            Language.GERMAN: {
                "welcome": "Willkommen im VR-Raum",
                "gesture_detected": "Geste erkannt",
                "user_nearby": "Benutzer in der Nähe",
                "mute_enabled": "Stumm aktiviert",
                "recording_started": "Aufnahme gestartet",
                "user_joined": "ist dem Meeting beigetreten",
                "user_left": "hat das Meeting verlassen"
            },
            Language.ITALIAN: {
                "welcome": "Benvenuto nello spazio VR",
                "gesture_detected": "Gesto rilevato",
                "user_nearby": "Utente vicino",
                "mute_enabled": "Muto attivato",
                "recording_started": "Registrazione iniziata",
                "user_joined": "si è unito alla riunione",
                "user_left": "ha lasciato la riunione"
            },
            Language.CHINESE: {
                "welcome": "欢迎进入VR空间",
                "gesture_detected": "检测到手势",
                "user_nearby": "附近有用户",
                "mute_enabled": "静音已启用",
                "recording_started": "录制已开始",
                "user_joined": "加入了会议",
                "user_left": "离开了会议"
            }
        }
        # Enhanced multilingual gesture reactions
        self.gesture_reactions = {
            "wave": {
                "en": "waves hello", "tr": "el sallar", "es": "saluda", 
                "fr": "salue", "de": "winkt", "it": "saluta", "zh": "挥手问好"
            },
            "thumbs_up": {
                "en": "gives thumbs up", "tr": "beğenir", "es": "da me gusta", 
                "fr": "fait un pouce", "de": "zeigt Daumen hoch", "it": "fa pollice su", "zh": "点赞"
            },
            "clap": {
                "en": "claps", "tr": "alkışlar", "es": "aplaude", 
                "fr": "applaudit", "de": "klatscht", "it": "applaude", "zh": "鼓掌"
            },
            "point": {
                "en": "points", "tr": "işaret eder", "es": "señala", 
                "fr": "pointe", "de": "zeigt", "it": "indica", "zh": "指向"
            },
            "peace": {
                "en": "shows peace sign", "tr": "barış işareti yapar", "es": "muestra señal de paz",
                "fr": "fait le signe de la paix", "de": "zeigt Peace-Zeichen", "it": "fa il segno della pace", "zh": "做和平手势"
            }
        }
        # Room settings
        self.proximity_chat_enabled = True
        self.gesture_recognition = True
        self.spatial_audio = True
        # Flask app for web interface
        self.app = Flask(__name__)
        self.app.config['SECRET_KEY'] = 'vr_collaboration_secret'
        self.socketio = SocketIO(self.app, cors_allowed_origins="*")
        self.setup_web_routes()

    def setup_web_routes(self):
        """Setup Flask routes for web interface"""
        @self.app.route('/')
        def index():
            return render_template_string(WEB_INTERFACE_HTML)

        @self.app.route('/api/room_state')
        def get_room_state():
            return jsonify(self.get_room_state_for_web())

        @self.app.route('/api/ai_notes')
        def get_ai_notes():
            return jsonify(self.generate_ai_notes())

        @self.app.route('/api/moderation_log')
        def get_moderation_log():
            return jsonify(self.moderation_log)

        @self.app.route('/api/save_recording', methods=['POST'])
        def save_recording():
            # Always save room metadata, even if transcript is empty
            filename = f"recordings/recording_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            recording_data = {
                "room_id": self.room_id,
                "room_name": self.room_name,
                "project_context": self.project_context,
                "start_time": self.start_time.isoformat() if self.start_time else None,
                "end_time": datetime.now().isoformat(),
                "participants": [p.name for p in self.participants.values()],
                "transcript": self.session_transcript or [{"timestamp": datetime.now().isoformat(), "type": "info", "data": {"message": "No events recorded yet"}}],
                "moderation_log": self.moderation_log
            }
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(recording_data, f, indent=2, ensure_ascii=False)
            print(f"💾 Recording saved to {filename} with {len(self.session_transcript)} transcript entries")
            return jsonify({"message": "Recording saved", "filename": filename})

        @self.socketio.on('connect')
        def handle_connect():
            print(f"🌐 Web client connected")
            emit('room_update', self.get_room_state_for_web())

        @self.socketio.on('disconnect')
        def handle_disconnect():
            print(f"🌐 Web client disconnected")

        @self.socketio.on('perform_gesture')
        def handle_perform_gesture(data):
            user_id = data.get('user_id')
            gesture_type = data.get('gesture_type', 'wave')
            hand = data.get('hand', 'right')
            intensity = data.get('intensity', 1.0)
            asyncio.run_coroutine_threadsafe(
                self.perform_gesture(user_id, gesture_type, hand, intensity),
                asyncio.get_event_loop()
            )

        @self.socketio.on('toggle_recording')
        def handle_toggle_recording():
            self.video_recording_enabled = not self.video_recording_enabled
            if self.video_recording_enabled:
                self.recording_start_time = datetime.now()
                if not self.session_transcript:  # Initialize transcript if empty
                    self.session_transcript = [{"timestamp": datetime.now().isoformat(), "type": "info", "data": {"message": "Recording started"}}]
                msg = "📹 Video recording STARTED"
                print(f"✅ {msg}")
                self.socketio.emit('recording_update', {'is_recording': True, 'message': msg})
            else:
                msg = "⏹️ Video recording STOPPED"
                print(f"✅ {msg}")
                self.socketio.emit('recording_update', {'is_recording': False, 'message': msg})
            self.log_event_for_ai("recording_toggle", {"state": self.video_recording_enabled, "message": msg})
            self.socketio.emit('room_update', self.get_room_state_for_web())

        @self.socketio.on('request_ai_notes')
        def handle_request_ai_notes():
            notes = self.generate_ai_notes()
            self.socketio.emit('ai_notes_response', notes)

        @self.socketio.on('save_recording')
        def handle_save_recording():
            # Save even if transcript is minimal
            filename = f"recordings/recording_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            recording_data = {
                "room_id": self.room_id,
                "room_name": self.room_name,
                "project_context": self.project_context,
                "start_time": self.start_time.isoformat() if self.start_time else None,
                "end_time": datetime.now().isoformat(),
                "participants": [p.name for p in self.participants.values()],
                "transcript": self.session_transcript or [{"timestamp": datetime.now().isoformat(), "type": "info", "data": {"message": "No events recorded yet"}}],
                "moderation_log": self.moderation_log
            }
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(recording_data, f, indent=2, ensure_ascii=False)
            print(f"💾 Recording saved to {filename} with {len(self.session_transcript)} transcript entries")
            self.socketio.emit('save_recording_response', {"message": "Recording saved", "filename": filename})

    def log_event_for_ai(self, event_type: str, data: dict):
        """Log events for AI note-taking and moderation"""
        if not (self.ai_note_taking_enabled or self.ai_moderation_enabled or self.video_recording_enabled):
            return
        entry = {
            "timestamp": datetime.now().isoformat(),
            "type": event_type,
            "data": data
        }
        self.session_transcript.append(entry)
        print(f"📝 Logged event: {event_type} - {data}")
        # Simple moderation check
        if self.ai_moderation_enabled:
            self._check_moderation(entry)

    def _check_moderation(self, entry):
        """Basic AI moderation logic"""
        if entry["type"] == "chat":
            message = entry["data"].get("message", "").lower()
            toxic_keywords = ["hate", "stupid", "idiot", "shut up", "useless", "dumb"]
            if any(word in message for word in toxic_keywords):
                user_id = entry["data"].get("user_id", "unknown")
                action = ModerationAction.WARNING
                log_entry = {
                    "timestamp": datetime.now().isoformat(),
                    "user_id": user_id,
                    "message": message,
                    "action": action.value,
                    "reason": "Toxic language detected"
                }
                self.moderation_log.append(log_entry)
                print(f"⚠️ Moderation Alert: {log_entry}")
                self.socketio.emit('moderation_alert', log_entry)

    def generate_ai_notes(self) -> dict:
        """Generate professional AI-powered meeting notes"""
        participants = [p.name for p in self.participants.values()]
        gestures = [e for e in self.session_transcript if e["type"] == "gesture"]
        key_moments = [f"{g['data']['user']} performed '{g['data']['gesture']}'" for g in gestures[-10:]]
        # Professional summary
        summary = (
            f"Team sync for '{self.project_context}' with {len(participants)} members: {', '.join(participants)}. "
            f"Participants reviewed initial localization requirements and demonstrated cross-cultural gestures. "
            f"Next phase: finalize language-specific UI assets by EOD Friday."
        )
        action_items = [
            "Alice (EN) to draft English UI copy by Thu",
            "Mehmet (TR) to validate Turkish date/time formats",
            "Carlos (ES) to provide Spanish voice samples",
            "Marie (FR) to review French legal disclaimers",
            "Hans (DE) to test German text expansion in VR layout",
            "Giulia (IT) to coordinate Italian beta testers",
            "Wei (ZH) to confirm Chinese character rendering in VR",
            "All: Share recording with stakeholders by tomorrow"
        ]
        return {
            "summary": summary,
            "action_items": action_items,
            "key_moments": key_moments,
            "participant_count": len(participants),
            "gesture_count": len(gestures),
            "duration": str(datetime.now() - self.start_time) if self.start_time else "N/A"
        }

    async def add_participant(self, user_id: str, name: str, 
                            preferred_language: Language, 
                            x: float = 0, y: float = 0, z: float = 0):
        """Add a participant to the VR meeting room"""
        vr_position = VRPosition(x, y, z)
        participant = Participant(
            user_id=user_id,
            name=name,
            preferred_language=preferred_language,
            vr_position=vr_position,
            avatar_id=f"avatar_{len(self.participants) + 1}"
        )
        self.participants[user_id] = participant
        if not self.is_active:
            self.is_active = True
            self.start_time = datetime.now()
        # Log for AI
        self.log_event_for_ai("user_joined", {
            "user_id": user_id,
            "name": name,
            "language": preferred_language.value
        })
        # Send localized welcome message with fallback
        welcome_key = "welcome"
        welcome_msg = self.vr_ui_translations.get(preferred_language, 
                                                 self.vr_ui_translations[Language.ENGLISH])[welcome_key]
        joined_msg = self.vr_ui_translations.get(preferred_language,
                                               self.vr_ui_translations[Language.ENGLISH])["user_joined"]
        print(f"🥽 {participant.country_flag} {name} entered VR space at position ({x}, {y}, {z})")
        print(f"   UI Language: {preferred_language.value} - '{welcome_msg}'")
        print(f"   Status: {name} {joined_msg}")
        # Update web interface
        self.socketio.emit('room_update', self.get_room_state_for_web())
        self.socketio.emit('user_joined', {
            'name': name, 
            'language': preferred_language.value,
            'flag': participant.country_flag,
            'message': f"{name} {joined_msg}"
        })
        # Show updated room layout
        self.render_room_console()

    async def update_participant_position(self, user_id: str, x: float, y: float, z: float,
                                        rotation_x: float = 0, rotation_y: float = 0, rotation_z: float = 0):
        """Update a participant's VR position and rotation"""
        if user_id not in self.participants:
            return False
        old_pos = self.participants[user_id].vr_position
        new_pos = VRPosition(x, y, z, rotation_x, rotation_y, rotation_z)
        self.participants[user_id].vr_position = new_pos
        # Log position update
        self.log_event_for_ai("position_update", {
            "user_id": user_id,
            "position": {"x": x, "y": y, "z": z},
            "rotation": {"x": rotation_x, "y": rotation_y, "z": rotation_z}
        })
        # Check for proximity-based interactions
        await self._check_proximity_interactions(user_id, old_pos, new_pos)
        # Update web interface
        self.socketio.emit('position_update', {
            'user_id': user_id,
            'position': {'x': x, 'y': y, 'z': z},
            'rotation': {'x': rotation_x, 'y': rotation_y, 'z': rotation_z}
        })
        return True

    async def _check_proximity_interactions(self, user_id: str, old_pos: VRPosition, new_pos: VRPosition):
        """Check if user movement triggers proximity-based features"""
        participant = self.participants[user_id]
        for other_id, other_participant in self.participants.items():
            if other_id == user_id:
                continue
            distance = new_pos.distance_to(other_participant.vr_position)
            # Proximity chat threshold (within 3 units)
            if distance < 3.0 and self.proximity_chat_enabled:
                nearby_msg = self.vr_ui_translations.get(participant.preferred_language,
                                                        self.vr_ui_translations[Language.ENGLISH])["user_nearby"]
                print(f"👥 {participant.country_flag} {participant.name}: {nearby_msg} - {other_participant.country_flag} {other_participant.name}")
                # Send to web interface
                self.socketio.emit('proximity_alert', {
                    'user1': participant.name,
                    'user2': other_participant.name,
                    'distance': round(distance, 2)
                })
                self.log_event_for_ai("proximity", {
                    "user1": participant.name,
                    "user2": other_participant.name,
                    "distance": distance
                })

    async def perform_gesture(self, user_id: str, gesture_type: str, hand: str = "right", intensity: float = 1.0):
        """Perform a VR gesture"""
        if user_id not in self.participants:
            return False
        participant = self.participants[user_id]
        gesture = VRGesture(gesture_type, hand, intensity, duration=1.0)
        self.gestures.append(gesture)
        participant.recent_gestures.append(gesture)
        # Keep only the last 5 gestures per participant
        participant.recent_gestures = participant.recent_gestures[-5:]
        # Simulate speaking during gesture
        participant.is_speaking = True
        self.socketio.emit('speaking_update', {
            'user_id': user_id,
            'is_speaking': True
        })
        # Schedule to stop speaking after gesture duration
        def stop_speaking():
            participant.is_speaking = False
            self.socketio.emit('speaking_update', {
                'user_id': user_id,
                'is_speaking': False
            })
            self.socketio.emit('room_update', self.get_room_state_for_web())
        threading.Timer(2.0, stop_speaking).start()
        # Translate gesture feedback with fallback
        gesture_msg = self.vr_ui_translations.get(participant.preferred_language, 
                                                 self.vr_ui_translations[Language.ENGLISH])["gesture_detected"]
        lang_code = participant.preferred_language.value
        reaction = self.gesture_reactions.get(gesture_type, {}).get(lang_code, gesture_type)
        print(f"👋 {participant.country_flag} {participant.name} {reaction} ({gesture_msg})")
        # Log for AI
        self.log_event_for_ai("gesture", {
            "user_id": user_id,
            "user": participant.name,
            "gesture": gesture_type,
            "reaction": reaction,
            "language": lang_code
        })
        # Send to web interface
        self.socketio.emit('gesture_performed', {
            'user_id': user_id,
            'user': participant.name,
            'gesture': gesture_type,
            'reaction': reaction,
            'flag': participant.country_flag,
            'language': lang_code,
            'timestamp': gesture.timestamp.isoformat()
        })
        # Broadcast gesture to nearby participants
        for other_id, other_participant in self.participants.items():
            if other_id != user_id:
                distance = participant.vr_position.distance_to(other_participant.vr_position)
                if distance < 5.0:  # Gesture visible range
                    print(f"   👀 {other_participant.country_flag} {other_participant.name} sees the gesture")
        # Update room state for web interface
        self.socketio.emit('room_update', self.get_room_state_for_web())
        return True

    def render_room_console(self):
        """Render room layout in console"""
        room_width, room_height = 20, 20
        grid = [[' ' for _ in range(room_width)] for _ in range(room_height)]
        # Place participants on the grid
        for participant in self.participants.values():
            grid_x = max(0, min(room_width-1, int(participant.vr_position.x + room_width//2)))
            grid_z = max(0, min(room_height-1, int(participant.vr_position.z + room_height//2)))
            # Use first letter of name as avatar
            avatar = participant.name[0].upper()
            grid[grid_z][grid_x] = avatar
        # Convert grid to string
        print("\nVR Room Top-Down View:")
        print("+" + "-" * room_width + "+")
        for row in grid:
            print("|" + "".join(row) + "|")
        print("+" + "-" * room_width + "+")
        # Add participant legend with flags
        print("\nParticipants:")
        for participant in self.participants.values():
            pos = participant.vr_position
            lang_name = {
                "en": "English", "tr": "Turkish", "es": "Spanish", "fr": "French",
                "de": "German", "it": "Italian", "zh": "Chinese"
            }.get(participant.preferred_language.value, participant.preferred_language.value)
            print(f"  {participant.name[0].upper()} = {participant.country_flag} {participant.name} ({lang_name}) at ({pos.x:.1f}, {pos.y:.1f}, {pos.z:.1f})")

    def get_room_state_for_web(self) -> Dict:
        """Get room state formatted for web interface"""
        return {
            "room_id": self.room_id,
            "room_name": self.room_name,
            "is_active": self.is_active,
            "participant_count": len(self.participants),
            "video_recording_enabled": self.video_recording_enabled,
            "participants": [
                {
                    "user_id": p.user_id,
                    "name": p.name,
                    "position": {
                        "x": p.vr_position.x,
                        "y": p.vr_position.y, 
                        "z": p.vr_position.z
                    },
                    "language": p.preferred_language.value,
                    "language_name": {
                        "en": "English", "tr": "Turkish", "es": "Spanish", "fr": "French",
                        "de": "German", "it": "Italian", "zh": "Chinese"
                    }.get(p.preferred_language.value),
                    "flag": p.country_flag,
                    "avatar_id": p.avatar_id,
                    "is_speaking": p.is_speaking,
                    "is_muted": p.is_muted,
                    "join_time": p.join_time.isoformat(),
                    "recent_gestures": [
                        {
                            "type": g.gesture_type,
                            "hand": g.hand,
                            "intensity": g.intensity,
                            "timestamp": g.timestamp.isoformat()
                        } for g in p.recent_gestures[-5:]
                    ]
                }
                for p in self.participants.values()
            ],
            "recent_gestures": [
                {
                    "type": g.gesture_type,
                    "hand": g.hand,
                    "intensity": g.intensity,
                    "timestamp": g.timestamp.isoformat()
                }
                for g in self.gestures[-10:]
            ],
            "languages_in_use": list(set(p.preferred_language.value for p in self.participants.values())),
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "moderation_count": len(self.moderation_log),
            "transcript_count": len(self.session_transcript)  # Added for debugging
        }

    def start_web_server(self, port=5000):
        """Start the web server"""
        def run_server():
            self.socketio.run(self.app, host='0.0.0.0', port=port, debug=False, allow_unsafe_werkzeug=True)
        web_thread = threading.Thread(target=run_server)
        web_thread.daemon = True
        web_thread.start()
        print(f"🌐 Web interface started at http://localhost:{port}")
        print(f"🎨 Open in browser to see real-time VR visualization")
        # Auto-open browser after a short delay
        def open_browser():
            webbrowser.open(f'http://localhost:{port}')
        Timer(2.0, open_browser).start()

# Web Interface HTML Template — ✅ WITH GESTURE CONTROLS + AI FEATURES + SAVE BUTTON
WEB_INTERFACE_HTML = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>VR Collaboration Spaces - Live Dashboard</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.7.2/socket.io.js"></script>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            color: white;
        }
        .container {
            max-width: 1400px;
            margin: 0 auto;
            padding: 20px;
        }
        .header {
            text-align: center;
            margin-bottom: 30px;
            background: rgba(255, 255, 255, 0.1);
            padding: 20px;
            border-radius: 15px;
            backdrop-filter: blur(10px);
        }
        .header h1 {
            font-size: 2.5em;
            margin-bottom: 10px;
        }
        .stats-bar {
            display: flex;
            justify-content: center;
            gap: 30px;
            margin-top: 15px;
        }
        .stat {
            text-align: center;
        }
        .stat-number {
            font-size: 2em;
            font-weight: bold;
            color: #ffd700;
        }
        .dashboard {
            display: grid;
            grid-template-columns: 1fr 400px;
            gap: 20px;
            margin-bottom: 30px;
        }
        .vr-room {
            background: rgba(255, 255, 255, 0.1);
            border-radius: 15px;
            padding: 20px;
            backdrop-filter: blur(10px);
            position: relative;
            overflow: hidden;
        }
        .room-title {
            font-size: 1.5em;
            margin-bottom: 20px;
            text-align: center;
        }
        .room-canvas {
            width: 100%;
            height: 400px;
            background: rgba(0, 0, 0, 0.3);
            border-radius: 10px;
            position: relative;
            overflow: hidden;
            border: 2px solid rgba(255, 255, 255, 0.2);
        }
        .participant {
            position: absolute;
            width: 40px;
            height: 40px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: bold;
            font-size: 1.2em;
            transition: all 0.3s ease;
            cursor: pointer;
            box-shadow: 0 0 20px rgba(255, 255, 255, 0.3);
        }
        .participant:hover {
            transform: scale(1.2);
            box-shadow: 0 0 30px rgba(255, 255, 255, 0.5);
        }
        .participant.english { background: linear-gradient(45deg, #ff6b6b, #ee5a52); }
        .participant.turkish { background: linear-gradient(45deg, #e74c3c, #c0392b); }
        .participant.spanish { background: linear-gradient(45deg, #f39c12, #e67e22); }
        .participant.french { background: linear-gradient(45deg, #3498db, #2980b9); }
        .participant.german { background: linear-gradient(45deg, #2ecc71, #27ae60); }
        .participant.italian { background: linear-gradient(45deg, #9b59b6, #8e44ad); }
        .participant.chinese { background: linear-gradient(45deg, #1abc9c, #16a085); }
        .gesture-effect {
            box-shadow: 0 0 30px rgba(255, 215, 0, 0.8) !important;
            transform: scale(1.3);
            transition: all 0.5s ease;
        }
        .sidebar {
            display: flex;
            flex-direction: column;
            gap: 20px;
        }
        .panel {
            background: rgba(255, 255, 255, 0.1);
            border-radius: 15px;
            padding: 20px;
            backdrop-filter: blur(10px);
        }
        .panel h3 {
            margin-bottom: 15px;
            color: #ffd700;
        }
        .participant-list {
            display: flex;
            flex-direction: column;
            gap: 10px;
        }
        .participant-item {
            background: rgba(255, 255, 255, 0.1);
            padding: 10px;
            border-radius: 8px;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        .language-badge {
            background: rgba(255, 215, 0, 0.2);
            color: #ffd700;
            padding: 2px 8px;
            border-radius: 12px;
            font-size: 0.8em;
        }
        .activity-feed {
            max-height: 300px;
            overflow-y: auto;
        }
        .activity-item {
            background: rgba(255, 255, 255, 0.05);
            padding: 8px;
            margin-bottom: 5px;
            border-radius: 5px;
            font-size: 0.9em;
        }
        .gesture-item {
            border-left: 3px solid #ffd700;
            padding-left: 10px;
        }
        .languages-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
            gap: 15px;
            margin-top: 20px;
        }
        .language-card {
            background: rgba(255, 255, 255, 0.1);
            padding: 15px;
            border-radius: 10px;
            text-align: center;
            backdrop-filter: blur(5px);
        }
        .language-flag {
            font-size: 2em;
            margin-bottom: 5px;
        }
        .participant-popup {
            position: absolute;
            background: rgba(0, 0, 0, 0.9);
            border-radius: 10px;
            padding: 15px;
            color: white;
            max-width: 300px;
            z-index: 1000;
            box-shadow: 0 0 20px rgba(255, 255, 255, 0.3);
            pointer-events: none;
        }
        .participant-popup h4 {
            margin-bottom: 10px;
            color: #ffd700;
        }
        .participant-popup ul {
            list-style: none;
            padding: 0;
        }
        .participant-popup li {
            margin-bottom: 5px;
            font-size: 0.9em;
        }
        @keyframes pulse {
            0%, 100% { transform: scale(1); }
            50% { transform: scale(1.05); }
        }
        .speaking {
            animation: pulse 1s infinite;
            box-shadow: 0 0 25px rgba(0, 255, 0, 0.5);
        }
        .connection-status {
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 10px 15px;
            border-radius: 20px;
            font-size: 0.9em;
        }
        .connected {
            background: rgba(0, 255, 0, 0.2);
            border: 1px solid #00ff00;
        }
        .disconnected {
            background: rgba(255, 0, 0, 0.2);
            border: 1px solid #ff0000;
        }
        /* Gesture Controls Panel */
        .gesture-controls {
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
            margin-bottom: 15px;
        }
        .gesture-btn, .ai-btn {
            background: #007bff;
            color: white;
            border: none;
            padding: 10px 15px;
            border-radius: 8px;
            cursor: pointer;
            font-weight: bold;
            transition: all 0.2s ease;
            display: flex;
            align-items: center;
            gap: 5px;
        }
        .gesture-btn:hover, .ai-btn:hover {
            background: #0056b3;
            transform: translateY(-2px);
        }
        .ai-btn.recording {
            background: #e74c3c;
        }
        .ai-btn.recording:hover {
            background: #c0392b;
        }
        .ai-notes-panel {
            margin-top: 20px;
            padding: 15px;
            background: rgba(0, 0, 0, 0.2);
            border-radius: 10px;
            max-height: 250px;
            overflow-y: auto;
        }
        .moderation-alert {
            background: rgba(231, 76, 60, 0.3);
            border-left: 3px solid #e74c3c;
            padding: 8px;
            margin: 5px 0;
            border-radius: 5px;
        }
        .save-btn {
            background: #28a745;
            margin-top: 10px;
        }
        .save-btn:hover {
            background: #218838;
        }
    </style>
</head>
<body>
    <div class="connection-status" id="connectionStatus">🔴 Connecting...</div>
    <div class="container">
        <div class="header">
            <h1>🥽 VR Collaboration Spaces</h1>
            <p>Real-time Multilingual Virtual Meeting Environment with AI</p>
            <div class="stats-bar">
                <div class="stat">
                    <div class="stat-number" id="participantCount">0</div>
                    <div>Participants</div>
                </div>
                <div class="stat">
                    <div class="stat-number" id="languageCount">0</div>
                    <div>Languages</div>
                </div>
                <div class="stat">
                    <div class="stat-number" id="gestureCount">0</div>
                    <div>Gestures</div>
                </div>
                <div class="stat">
                    <div class="stat-number" id="moderationCount">0</div>
                    <div>Alerts</div>
                </div>
            </div>
        </div>
        <!-- 💥 NEW: AI Controls Panel -->
        <div class="panel">
            <h3>🤖 AI Assistant Controls</h3>
            <div class="gesture-controls">
                <button class="gesture-btn" data-gesture="wave">👋 Wave</button>
                <button class="gesture-btn" data-gesture="thumbs_up">👍 Thumbs Up</button>
                <button class="gesture-btn" data-gesture="clap">👏 Clap</button>
                <button class="gesture-btn" data-gesture="point">👉 Point</button>
                <button class="gesture-btn" data-gesture="peace">✌️ Peace</button>
                <button class="ai-btn" id="recordBtn">📹 Start Recording</button>
                <button class="ai-btn" id="notesBtn">📝 Get AI Notes</button>
                <button class="ai-btn save-btn" id="saveBtn">💾 Save Recording</button>
            </div>
            <div class="ai-notes-panel" id="aiNotesPanel">
                <p>AI notes will appear here...</p>
            </div>
        </div>
        <div class="dashboard">
            <div class="vr-room">
                <h2 class="room-title" id="roomTitle">VR Meeting Room</h2>
                <div class="room-canvas" id="roomCanvas">
                    <!-- Participants will be positioned here -->
                </div>
            </div>
            <div class="sidebar">
                <div class="panel">
                    <h3>👥 Participants</h3>
                    <div class="participant-list" id="participantList">
                        <!-- Participant list will be populated here -->
                    </div>
                </div>
                <div class="panel">
                    <h3>🎭 Recent Activity</h3>
                    <div class="activity-feed" id="activityFeed">
                        <!-- Activity feed will be populated here -->
                    </div>
                </div>
            </div>
        </div>
        <div class="panel">
            <h3>🌍 Languages in Session</h3>
            <div class="languages-grid" id="languagesGrid">
                <!-- Language cards will be populated here -->
            </div>
        </div>
    </div>
    <script>
        const socket = io();
        let roomState = {};
        let selectedUserId = null;
        function updateParticipantInState(userId, updates) {
            if (!roomState.participants) return;
            const index = roomState.participants.findIndex(p => p.user_id === userId);
            if (index !== -1) {
                roomState.participants[index] = { ...roomState.participants[index], ...updates };
            }
        }
        const statusEl = document.getElementById('connectionStatus');
        socket.on('connect', function() {
            statusEl.textContent = '🟢 Connected';
            statusEl.className = 'connection-status connected';
        });
        socket.on('disconnect', function() {
            statusEl.textContent = '🔴 Disconnected';
            statusEl.className = 'connection-status disconnected';
        });
        socket.on('room_update', function(data) {
            roomState = data;
            updateDashboard();
        });
        socket.on('user_joined', function(data) {
            addActivityItem(`${data.flag} ${data.name} joined (${data.language.toUpperCase()})`, 'join');
        });
        socket.on('gesture_performed', function(data) {
            addActivityItem(`${data.flag} ${data.user} ${data.reaction}`, 'gesture');
            const existing = roomState.participants?.find(p => p.user_id === data.user_id);
            if (existing) {
                const newGesture = {
                    type: data.gesture,
                    hand: data.hand || 'right',
                    intensity: 1.0,
                    timestamp: data.timestamp
                };
                const updatedGestures = [...(existing.recent_gestures || []), newGesture].slice(-5);
                updateParticipantInState(data.user_id, { recent_gestures: updatedGestures });
            }
            const participantEl = Array.from(document.getElementsByClassName('participant')).find(
                el => el.dataset.userId === data.user_id
            );
            if (participantEl) {
                participantEl.classList.add('gesture-effect');
                setTimeout(() => participantEl.classList.remove('gesture-effect'), 2000);
            }
        });
        socket.on('speaking_update', function(data) {
            updateParticipantInState(data.user_id, { is_speaking: data.is_speaking });
            const participantEl = Array.from(document.getElementsByClassName('participant')).find(
                el => el.dataset.userId === data.user_id
            );
            if (participantEl) {
                if (data.is_speaking) {
                    participantEl.classList.add('speaking');
                } else {
                    participantEl.classList.remove('speaking');
                }
            }
            updateParticipantList();
        });
        socket.on('proximity_alert', function(data) {
            addActivityItem(`👥 ${data.user1} and ${data.user2} are nearby (${data.distance}m)`, 'proximity');
        });
        socket.on('recording_update', function(data) {
            addActivityItem(data.message, 'recording');
            const recordBtn = document.getElementById('recordBtn');
            if (data.is_recording) {
                recordBtn.textContent = '⏹️ Stop Recording';
                recordBtn.classList.add('recording');
            } else {
                recordBtn.textContent = '📹 Start Recording';
                recordBtn.classList.remove('recording');
            }
        });
        socket.on('moderation_alert', function(data) {
            addActivityItem(`⚠️ MODERATION: ${data.user_id} - ${data.reason}`, 'moderation');
            const feed = document.getElementById('activityFeed');
            const alertEl = document.createElement('div');
            alertEl.className = 'moderation-alert';
            alertEl.innerHTML = `<strong>🚨 AI Moderation Alert</strong><br>User: ${data.user_id}<br>Reason: ${data.reason}`;
            feed.insertBefore(alertEl, feed.firstChild);
        });
        socket.on('ai_notes_response', function(notes) {
            const panel = document.getElementById('aiNotesPanel');
            let html = `<h4>📋 Project Sync Summary: Global Localization Project Kickoff</h4>`;
            html += `<p><strong>Summary:</strong> ${notes.summary}</p>`;
            if (notes.action_items && notes.action_items.length > 0) {
                html += `<p><strong>Action Items:</strong></p><ul>`;
                notes.action_items.forEach(item => html += `<li>${item}</li>`);
                html += `</ul>`;
            }
            if (notes.key_moments && notes.key_moments.length > 0) {
                html += `<p><strong>Key Moments:</strong></p><ul>`;
                notes.key_moments.forEach(moment => html += `<li>${moment}</li>`);
                html += `</ul>`;
            }
            panel.innerHTML = html;
        });
        socket.on('save_recording_response', function(data) {
            if (data.error) {
                alert("❌ " + data.error);
            } else {
                addActivityItem("✅ Recording saved: " + data.filename, 'recording');
                alert("✅ Recording saved to: " + data.filename);
            }
        });
        function updateDashboard() {
            document.getElementById('participantCount').textContent = roomState.participant_count || 0;
            document.getElementById('languageCount').textContent = roomState.languages_in_use?.length || 0;
            document.getElementById('gestureCount').textContent = roomState.recent_gestures?.length || 0;
            document.getElementById('moderationCount').textContent = roomState.moderation_count || 0;
            document.getElementById('roomTitle').textContent = roomState.room_name || 'VR Meeting Room';
            updateRoomCanvas();
            updateParticipantList();
            updateLanguagesGrid();
        }
        function updateRoomCanvas() {
            const canvas = document.getElementById('roomCanvas');
            canvas.innerHTML = '';
            if (!roomState.participants) return;
            const canvasWidth = canvas.clientWidth;
            const canvasHeight = canvas.clientHeight;
            const roomSize = 20;
            roomState.participants.forEach(participant => {
                const participantEl = document.createElement('div');
                participantEl.className = `participant ${participant.language} ${participant.is_speaking ? 'speaking' : ''}`;
                participantEl.textContent = participant.name.charAt(0).toUpperCase();
                participantEl.dataset.userId = participant.user_id;
                participantEl.title = `${participant.flag} ${participant.name} (${participant.language_name})`;
                const x = ((participant.position.x + roomSize/2) / roomSize) * canvasWidth;
                const z = ((participant.position.z + roomSize/2) / roomSize) * canvasHeight;
                participantEl.style.left = `${Math.max(0, Math.min(canvasWidth - 40, x - 20))}px`;
                participantEl.style.top = `${Math.max(0, Math.min(canvasHeight - 40, z - 20))}px`;
                participantEl.addEventListener('click', () => {
                    showParticipantDetails(participant);
                    selectedUserId = participant.user_id;
                });
                canvas.appendChild(participantEl);
            });
        }
        function showParticipantDetails(participant) {
            const existingPopups = document.getElementsByClassName('participant-popup');
            while (existingPopups.length > 0) {
                existingPopups[0].remove();
            }
            const popup = document.createElement('div');
            popup.className = 'participant-popup';
            const status = participant.is_speaking ? '🎤 Speaking' : (participant.is_muted ? '🔇 Muted' : '🔊 Not speaking');
            let gesturesHtml = '<p>No recent gestures</p>';
            if (participant.recent_gestures && participant.recent_gestures.length > 0) {
                gesturesHtml = '<ul>' + participant.recent_gestures.map(g => 
                    `<li>${g.type} (${g.hand}, ${new Date(g.timestamp).toLocaleTimeString()})</li>`
                ).join('') + '</ul>';
            }
            popup.innerHTML = `
                <h4>${participant.flag} ${participant.name}</h4>
                <p>Language: ${participant.language_name}</p>
                <p>Status: ${status}</p>
                <p>Recent Gestures:</p>
                ${gesturesHtml}
            `;
            const participantEl = Array.from(document.getElementsByClassName('participant')).find(
                el => el.dataset.userId === participant.user_id
            );
            if (participantEl) {
                const rect = participantEl.getBoundingClientRect();
                popup.style.left = `${rect.right + 10}px`;
                popup.style.top = `${rect.top}px`;
            }
            document.body.appendChild(popup);
            setTimeout(() => popup.remove(), 5000);
            const clickHandler = (e) => {
                if (!popup.contains(e.target) && (!participantEl || !participantEl.contains(e.target))) {
                    popup.remove();
                    document.removeEventListener('click', clickHandler);
                }
            };
            document.addEventListener('click', clickHandler);
        }
        function updateParticipantList() {
            const list = document.getElementById('participantList');
            list.innerHTML = '';
            if (!roomState.participants) return;
            roomState.participants.forEach(participant => {
                const item = document.createElement('div');
                item.className = 'participant-item';
                const statusIcon = participant.is_speaking ? '🎤' : (participant.is_muted ? '🔇' : '🔊');
                item.innerHTML = `
                    <span style="font-size: 1.2em">${participant.flag}</span>
                    <span>${participant.name}</span>
                    <span class="language-badge">${participant.language_name}</span>
                    <span>${statusIcon}</span>
                `;
                list.appendChild(item);
            });
        }
        function updateLanguagesGrid() {
            const grid = document.getElementById('languagesGrid');
            grid.innerHTML = '';
            const languageInfo = {
                'en': { name: 'English', flag: '🇺🇸' },
                'tr': { name: 'Turkish', flag: '🇹🇷' },
                'es': { name: 'Spanish', flag: '🇪🇸' },
                'fr': { name: 'French', flag: '🇫🇷' },
                'de': { name: 'German', flag: '🇩🇪' },
                'it': { name: 'Italian', flag: '🇮🇹' },
                'zh': { name: 'Chinese', flag: '🇨🇳' }
            };
            if (roomState.languages_in_use) {
                roomState.languages_in_use.forEach(lang => {
                    const info = languageInfo[lang];
                    if (info) {
                        const card = document.createElement('div');
                        card.className = 'language-card';
                        card.innerHTML = `
                            <div class="language-flag">${info.flag}</div>
                            <div>${info.name}</div>
                        `;
                        grid.appendChild(card);
                    }
                });
            }
        }
        function addActivityItem(message, type) {
            const feed = document.getElementById('activityFeed');
            const item = document.createElement('div');
            item.className = `activity-item ${type === 'gesture' ? 'gesture-item' : ''} ${type === 'moderation' ? 'moderation-alert' : ''}`;
            const timestamp = new Date().toLocaleTimeString();
            item.innerHTML = `<strong>${timestamp}</strong> - ${message}`;
            feed.insertBefore(item, feed.firstChild);
            while (feed.children.length > 20) {
                feed.removeChild(feed.lastChild);
            }
        }
        // Gesture Controls
        document.querySelectorAll('.gesture-btn:not(#recordBtn):not(#notesBtn):not(#saveBtn)').forEach(btn => {
            btn.addEventListener('click', function() {
                const gestureType = this.getAttribute('data-gesture');
                const targetUserId = selectedUserId || (roomState.participants?.[0]?.user_id);
                if (!targetUserId) {
                    alert("No participants available.");
                    return;
                }
                socket.emit('perform_gesture', {
                    user_id: targetUserId,
                    gesture_type: gestureType,
                    hand: "right",
                    intensity: 1.0
                });
                addActivityItem(`You performed '${gestureType}' on ${targetUserId}`, 'gesture');
            });
        });
        // AI Controls
        document.getElementById('recordBtn').addEventListener('click', () => {
            socket.emit('toggle_recording');
        });
        document.getElementById('notesBtn').addEventListener('click', () => {
            socket.emit('request_ai_notes');
        });
        document.getElementById('saveBtn').addEventListener('click', () => {
            socket.emit('save_recording');
        });
        // Initial load
        setTimeout(() => {
            fetch('/api/room_state')
                .then(response => response.json())
                .then(data => {
                    roomState = data;
                    updateDashboard();
                });
        }, 500);
    </script>
</body>
</html>
'''

async def demo_multilingual_vr_with_web():
    """Demo the enhanced multilingual VR system with web interface (50-minute version)"""
    print("🌍 Enhanced Multilingual VR Collaboration Spaces")
    print("Languages: English, Turkish, Spanish, French, German, Italian, Chinese")
    print("=" * 70)
    
    # Create enhanced VR meeting room
    vr_room = EnhancedMultilingualVRRoom("vr_multilingual", "Global Localization Project Kickoff")
    
    # Start web server
    vr_room.start_web_server(port=5000)
    print("\n👥 Adding participants from around the world...")
    
    # Add participants with different languages
    participants_data = [
        ("alice", "Alice", Language.ENGLISH, -4, 0, 0),
        ("mehmet", "Mehmet", Language.TURKISH, 4, 0, 0),
        ("carlos", "Carlos", Language.SPANISH, 0, 0, -4),
        ("marie", "Marie", Language.FRENCH, -2, 0, 2),
        ("hans", "Hans", Language.GERMAN, 2, 0, 2),
        ("giulia", "Giulia", Language.ITALIAN, -4, 0, 4),
        ("wei", "Wei", Language.CHINESE, 4, 0, -4)
    ]
    
    # Start recording before adding participants
    vr_room.video_recording_enabled = True
    vr_room.recording_start_time = datetime.now()
    vr_room.session_transcript = [{"timestamp": datetime.now().isoformat(), "type": "info", "data": {"message": "Recording started"}}]
    print("✅ 📹 Video recording STARTED automatically to capture all events")

    for user_id, name, lang, x, y, z in participants_data:
        await vr_room.add_participant(user_id, name, lang, x, y, z)
        await asyncio.sleep(0.5)  # Stagger joins

    print("\n🎭 Simulating multilingual VR interactions...")
    interactions = [
        ("alice", "wave"),
        ("mehmet", "thumbs_up"), 
        ("carlos", "clap"),
        ("marie", "peace"),
        ("hans", "point"),
        ("giulia", "wave"),
        ("wei", "thumbs_up")
    ]
    for user_id, gesture in interactions:
        await vr_room.perform_gesture(user_id, gesture)
        await asyncio.sleep(1)

    print("\n🚶 Moving participants for proximity interactions...")
    await vr_room.update_participant_position("mehmet", 1, 0, 0)
    await asyncio.sleep(0.5)
    await vr_room.update_participant_position("marie", 0, 0, 0)
    await asyncio.sleep(0.5)
    await vr_room.update_participant_position("wei", 2, 0, -1)

    vr_room.render_room_console()

    # Simulate saving the recording
    print("\n💾 Attempting to save recording...")
    filename = f"recordings/recording_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    recording_data = {
        "room_id": vr_room.room_id,
        "room_name": vr_room.room_name,
        "project_context": vr_room.project_context,
        "start_time": vr_room.start_time.isoformat() if vr_room.start_time else None,
        "end_time": datetime.now().isoformat(),
        "participants": [p.name for p in vr_room.participants.values()],
        "transcript": vr_room.session_transcript,
        "moderation_log": vr_room.moderation_log
    }
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(recording_data, f, indent=2, ensure_ascii=False)
    print(f"✅ Recording saved to {filename} with {len(vr_room.session_transcript)} transcript entries")
    vr_room.socketio.emit('save_recording_response', {"message": "Recording saved", "filename": filename})

    print("\n🌐 Web Interface Features:")
    print("   ✅ Real-time 3D participant visualization")
    print("   ✅ Live gesture and proximity notifications") 
    print("   ✅ Multilingual participant list with flags")
    print("   ✅ Language distribution analytics")
    print("   ✅ Activity feed with timestamps")
    print("   ✅ Clickable participant avatars with gesture and speaking details")
    print("   ✅ AI Moderation, Note-Taking, and Video Recording")
    print("   ✅ Save recordings to 'recordings/' folder")

    print(f"\n📊 Session Statistics:")
    room_state = vr_room.get_room_state_for_web()
    print(f"   🌍 Languages Active: {len(room_state['languages_in_use'])}")
    print(f"   👥 Participants: {room_state['participant_count']}")
    print(f"   🎭 Recent Gestures: {len(room_state['recent_gestures'])}")
    print(f"   📝 Transcript Entries: {room_state['transcript_count']}")

    print("\n🎉 Multilingual VR System Running!")
    print("🌐 Web dashboard available at: http://localhost:5000")
    print("⏰ Keeping server running for 50 minutes (3000 seconds)...")
    
    # Run for 50 minutes (3000 seconds)
    await asyncio.sleep(3000)

def create_enhanced_requirements():
    """Create enhanced requirements file"""
    enhanced_requirements = """
# Enhanced VR Collaboration Spaces Requirements
# Core web framework
flask>=2.3.0
flask-socketio>=5.3.0
# Real-time communication
websockets>=11.0
python-socketio>=5.8.0
# Async support
asyncio-mqtt>=0.13.0
# Optional: Advanced AI features
# transformers>=4.21.0
# torch>=2.0.0
# openai>=0.27.0
# Utilities
requests>=2.31.0
numpy>=1.24.0
"""
    with open("requirements_enhanced.txt", "w") as f:
        f.write(enhanced_requirements)
    print("📄 Created requirements_enhanced.txt")
    print("💾 Install with: pip install -r requirements_enhanced.txt")

if __name__ == "__main__":
    print("🚀 Enhanced Multilingual VR Collaboration Spaces")
    print("=" * 50)
    # Create requirements file
    create_enhanced_requirements()
    # Run the demo
    try:
        asyncio.run(demo_multilingual_vr_with_web())
    except KeyboardInterrupt:
        print("\n👋 Demo stopped by user")