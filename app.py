import streamlit as st
import cv2
import mediapipe as mp
# أحياناً نحتاج لاستيراد المكونات مباشرة في النسخ الحديثة
from mediapipe.python.solutions import pose as mp_pose
from mediapipe.python.solutions import drawing_utils as mp_drawing

# --- إعداد MediaPipe ---
# لاحظ التغيير هنا، نستخدم mp_pose مباشرة
pose_tracker = mp_pose.Pose(
    min_detection_confidence=0.5, 
    min_tracking_confidence=0.5,
    model_complexity=1 # 1 هو الخيار الوسط المناسب للسيرفرات
)

st.title("🛡️ نظام رصد محاولات الغش والشغب")

# بقية الكود...
