import streamlit as st
import cv2
import mediapipe as mp
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import datetime
import time

# --- إعداد الاتصال بـ Google Sheets ---
def log_event(status):
    try:
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        # تأكد من وضع بيانات الـ JSON هنا أو رفع الملف باسم credentials.json
        creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
        client = gspread.authorize(creds)
        sheet = client.open("Classroom_Monitoring").sheet1
        
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        sheet.append_row([timestamp, status])
        return True
    except Exception as e:
        st.error(f"خطأ في الاتصال بـ Google Sheets: {e}")
        return False

# --- إعداد MediaPipe ---
mp_pose = mp.solutions.pose
pose = mp_pose.Pose(min_detection_confidence=0.7, min_tracking_confidence=0.7)
mp_drawing = mp.solutions.drawing_utils

st.title("نظام مراقبة الطلاب الذكي 🕵️‍♂️")
st.write("الوضع الحالي: رصد الالتفات، الحديث، أو ترك المكان.")

run = st.checkbox('تشغيل الكاميرا')
FRAME_WINDOW = st.image([])

camera = cv2.VideoCapture(0)

last_log_time = 0 # لتجنب تكرار التسجيل في نفس الثواني

while run:
    ret, frame = camera.read()
    if not ret:
        break
    
    frame = cv2.flip(frame, 1)
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = pose.process(rgb_frame)
    
    status = "مستقر"
    
    if results.pose_landmarks:
        # رسم النقاط على الجسم
        mp_drawing.draw_landmarks(frame, results.pose_landmarks, mp_pose.POSE_CONNECTIONS)
        
        # استخراج الإحداثيات (مثال لنقطة الأنف والكتفين)
        landmarks = results.pose_landmarks.landmark
        nose = landmarks[mp_pose.PoseLandmark.NOSE]
        left_shoulder = landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER]
        right_shoulder = landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER]

        # منطق بسيط: إذا كان الأنف بعيداً جداً عن منتصف الكتفين = التفات
        shoulder_center = (left_shoulder.x + right_shoulder.x) / 2
        if abs(nose.x - shoulder_center) > 0.1: 
            status = "حركة مشبوهة (التفات)"
            
        # تسجيل الحركة في Google Sheet إذا مر أكثر من 5 ثواني على آخر تسجيل
        if status != "مستقر" and (time.time() - last_log_time > 5):
            log_event(status)
            last_log_time = time.time()
            st.warning(f"تم رصد: {status} وتم التسجيل في الملف")

    # عرض الفيديو في Streamlit
    cv2.putText(frame, f"Status: {status}", (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
    FRAME_WINDOW.image(frame, channels="BGR")

else:
    st.write('الكاميرا متوقفة')