import streamlit as st
import cv2
import numpy as np
import mediapipe as mp
# استيراد مباشر للمكونات لتجنب AttributeError
from mediapipe.python.solutions import pose as mp_pose
from mediapipe.python.solutions import drawing_utils as mp_drawing
from streamlit_webrtc import webrtc_streamer, WebRtcMode, VideoProcessorBase

# --- إعداد MediaPipe ---
# نستخدم Model Complexity 0 لأنه الأسرع لمعالجة شاشة بها كاميرات متعددة
pose_detector = mp_pose.Pose(
    static_image_mode=False,
    model_complexity=0, 
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5
)

class VideoProcessor(VideoProcessorBase):
    def recv(self, frame):
        img = frame.to_ndarray(format="bgr24")
        
        # تحويل الصورة لمعالجتها
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        results = pose_detector.process(img_rgb)
        
        if results.pose_landmarks:
            # رسم الهيكل العظمي
            mp_drawing.draw_landmarks(
                img, results.pose_landmarks, mp_pose.POSE_CONNECTIONS)
            
            # منطق الرصد (مثال: الالتفات)
            # بما أنك تراقب 8 كاميرات، سنضع تنبيه عام يظهر فوق الشاشة
            cv2.putText(img, "MOVEMENT TRACKED", (50, 50), 
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            
        return frame.from_ndarray(img, format="bgr24")

st.title("🖥️ نظام مراقبة الشاشة الذكي (8 كاميرات)")
st.info("اضغط Start ثم اختر 'Window' أو 'Tab' الذي يعرض الكاميرات.")

# إعدادات الـ WebRTC لمشاركة الشاشة
webrtc_streamer(
    key="screen-monitor",
    mode=WebRtcMode.SENDRECV,
    video_processor_factory=VideoProcessor,
    rtc_configuration={
        "iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]
    },
    media_stream_constraints={
        "video": {"displaySurface": "monitor"}, # طلب مشاركة الشاشة
        "audio": False
    },
    async_processing=True,
)
