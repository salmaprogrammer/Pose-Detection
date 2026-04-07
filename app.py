import streamlit as st
import cv2
import numpy as np
import mediapipe as mp
from mediapipe.python.solutions import pose as mp_pose
from mediapipe.python.solutions import drawing_utils as mp_drawing
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import datetime
import time

# --- 1. إعداد الاتصال بـ Google Sheets (استخدام الـ Secrets) ---
def log_violation(action_type):
    try:
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        # تأكد أنك وضعت بيانات الـ JSON في Secrets باسم gcp_service_account
        creds_dict = st.secrets["gcp_service_account"]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        client = gspread.authorize(creds)
        # افتح الملف (يجب أن يكون الاسم مطابقاً تماماً لما في جوجل درايف)
        sheet = client.open("Classroom_Monitoring").sheet1
        
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        sheet.append_row([now, action_type])
        return True
    except Exception as e:
        st.sidebar.error(f"خطأ في التسجيل: {e}")
        return False

# --- 2. إعداد واجهة التطبيق ---
st.set_page_config(page_title="AI Proctoring System", layout="wide")
st.title("🛡️ نظام المراقبة الذكي - الإصدار النهائي")
st.sidebar.header("إعدادات النظام")
sensitivity = st.sidebar.slider("حساسية رصد الحركة", 0.01, 0.20, 0.08)

# --- 3. تهيئة MediaPipe ---
pose = mp_pose.Pose(
    static_image_mode=False,
    model_complexity=1,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5
)

# --- 4. تشغيل الكاميرا ---
img_file_buffer = st.camera_input("اضغط لبدء الرصد (Snapshot Mode)")

if img_file_buffer:
    # تحويل الصورة المعروضة لمعالجة OpenCV
    bytes_data = img_file_buffer.getvalue()
    cv2_img = cv2.imdecode(np.frombuffer(bytes_data, np.uint8), cv2.IMREAD_COLOR)
    img_rgb = cv2.cvtColor(cv2_img, cv2.COLOR_BGR2RGB)
    
    # معالجة الصورة لاستخراج نقاط الجسد
    results = pose.process(img_rgb)
    
    if results.pose_landmarks:
        landmarks = results.pose_landmarks.landmark
        
        # استخراج النقاط الأساسية للتحليل
        nose = landmarks[mp_pose.PoseLandmark.NOSE]
        left_shoulder = landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER]
        right_shoulder = landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER]
        left_ear = landmarks[mp_pose.PoseLandmark.LEFT_EAR]
        right_ear = landmarks[mp_pose.PoseLandmark.RIGHT_EAR]

        # حساب مركز الجسم (الصدر)
        shoulder_center_x = (left_shoulder.x + right_shoulder.x) / 2
        
        status = "✅ التزام بالجلوس"
        violation_detected = False

        # --- مَنطق رصد المخالفات ---
        
        # 1. رصد الالتفات (مقارنة الأنف بمنتصف الأكتاف)
        if abs(nose.x - shoulder_center_x) > sensitivity:
            status = "🚨 تنبيه: التفات أو محاولة غش"
            violation_detected = True
            
        # 2. رصد ترك المكان (إذا كانت نقاط الأكتاف خارج نطاق الرؤية أو مرتفعة جداً)
        elif left_shoulder.y < 0.2 or right_shoulder.y < 0.2:
            status = "⚠️ تنبيه: محاولة مغادرة الكرسي"
            violation_detected = True

        # عرض النتيجة للمستخدم
        if violation_detected:
            st.error(status)
            if st.button("سجل هذه المخالفة في الملف"):
                if log_violation(status):
                    st.success("تم تسجيل البيانات في Google Sheets بنجاح!")
        else:
            st.success(status)

        # رسم النقاط للتوضيح
        mp_drawing.draw_landmarks(cv2_img, results.pose_landmarks, mp_pose.POSE_CONNECTIONS)
        st.image(cv2_img, channels="BGR", caption="تحليل الحركة اللحظي")
    else:
        st.warning("لم يتم رصد جسد بوضوح، تأكد من الإضاءة والجلوس أمام الكاميرا.")

# --- تعليمات التشغيل ---
with st.expander("كيف يعمل النظام؟"):
    st.write("""
    1. **الجلوس:** يعتمد النظام على ثبات الأنف في منتصف المسافة بين الكتفين.
    2. **الالتفات:** عند تحرك الرأس لليسار أو اليمين، تزداد المسافة عن المركز فيسجل النظام مخالفة.
    3. **التنقل:** يتم رصد الإحداثيات الرأسية (Y) للأكتاف؛ إذا ارتفعت عن حد معين، يعني ذلك أن الشخص وقف.
    """)
