import streamlit as st
from streamlit_webrtc import webrtc_streamer, VideoTransformerBase
import cv2
import mediapipe as mp
import numpy as np

# إعداد MediaPipe
mp_pose = mp.solutions.pose
pose = mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5)
mp_drawing = mp.solutions.drawing_utils

class MotionAnalyzer(VideoTransformerBase):
    def transform(self, frame):
        img = frame.to_ndarray(format="bgr24")
        
        # تحويل الصورة لـ RGB للمعالجة
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        results = pose.process(img_rgb)
        
        if results.pose_landmarks:
            # رسم الهيكل العظمي فوق الفيديو المباشر للشاشة
            mp_drawing.draw_landmarks(img, results.pose_landmarks, mp_pose.POSE_CONNECTIONS)
            
            # منطق بسيط للرصد (مثال: الالتفات)
            nose = results.pose_landmarks.landmark[mp_pose.PoseLandmark.NOSE]
            l_shoulder = results.pose_landmarks.landmark[mp_pose.PoseLandmark.LEFT_SHOULDER]
            r_shoulder = results.pose_landmarks.landmark[mp_pose.PoseLandmark.RIGHT_SHOULDER]
            
            center = (l_shoulder.x + r_shoulder.x) / 2
            if abs(nose.x - center) > 0.05:
                cv2.putText(img, "ALERT: MOVEMENT DETECTED", (50, 50), 
                            cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 3)
        
        return img

st.title("🖥️ رصد حركات الكاميرات عبر مشاركة الشاشة")
st.write("اضغط على Start ثم اختر نافذة برنامج الكاميرات")

webrtc_streamer(
    key="screen-share",
    video_transformer_factory=MotionAnalyzer,
    # هذا السطر هو السر: يطلب مشاركة الشاشة بدلاً من الكاميرا
    rtc_configuration={"iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]},
    media_stream_constraints={"video": True, "audio": False},
)
