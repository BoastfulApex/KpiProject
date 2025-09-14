from rest_framework.response import Response
from rest_framework import serializers, generics, status
from rest_framework.renderers import JSONRenderer
from .models import Location, Attendance, Employee, WorkSchedule
from django.utils import timezone
from apps.superadmin.models import Administrator
from django.utils import timezone
from datetime import datetime, timedelta
from data import config
import requests
from django.shortcuts import get_object_or_404
import face_recognition
import numpy as np
import base64, io, os
from PIL import Image
from django.conf import settings


from django.core.files.base import ContentFile

def save_uploaded_image(base64_image, filename="debug_uploaded.jpg"):
    """Debug uchun kelgan base64 rasmni MEDIA_ROOT ichida saqlab qo‘yadi"""
    header, data = base64_image.split(",", 1)
    decoded = base64.b64decode(data)

    save_path = os.path.join(settings.MEDIA_ROOT, filename)
    with open(save_path, "wb") as f:
        f.write(decoded)

    return save_path


def get_distance_meters(lat1, lon1, lat2, lon2):
    from geopy.distance import geodesic
    return geodesic((lat1, lon1), (lat2, lon2)).meters


def verify_face(employee, base64_image):
    print("verify_face called")

    # ❗ Debug uchun
    # debug_path = save_uploaded_image(base64_image, "last_uploaded.jpg")
    # print("Uploaded image saved to:", debug_path)

    if not employee.image:
        return False, "Employee image not found"

    # 1. Xodim rasmi
    known_image = face_recognition.load_image_file(employee.image.path)
    known_encodings = face_recognition.face_encodings(known_image)
    if not known_encodings:
        return False, "No face found in employee image"
    known_encoding = known_encodings[0]

    # 2. Kelgan rasmni numpy array qilib ochish
    header, data = base64_image.split(",", 1)
    decoded = base64.b64decode(data)

    import numpy as np, cv2
    
    file_bytes = np.frombuffer(decoded, np.uint8)
    unknown_image = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)

    if unknown_image is None:
        return False, "Uploaded image decode error"

    # 🔄 BGR → RGB
    unknown_image = cv2.cvtColor(unknown_image, cv2.COLOR_BGR2RGB)

    # 3. Face encoding qilish
    unknown_encodings = face_recognition.face_encodings(unknown_image)
    if not unknown_encodings:
        return False, "No face found in uploaded image"

    unknown_encoding = unknown_encodings[0]

    # 4. Taqqoslash
    results = face_recognition.compare_faces([known_encoding], unknown_encoding, tolerance=0.5)

    return bool(results[0])


BOT_TOKEN = config.BOT_TOKEN


def send_telegram_message_to_admin(chat_id, text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text
    }
    requests.post(url, data=payload)

def get_time_difference(sch_time, now_time):
    """Haqiqiy vaqtdan jadval vaqti farqini hisoblaydi"""
    sch_dt = datetime.combine(timezone.localdate(), sch_time)
    now_dt = datetime.combine(timezone.localdate(), now_time)
    delta = (now_dt - sch_dt).total_seconds()
    return int(delta)

def get_distance_meters(lat1, lon1, lat2, lon2):
    from geopy.distance import geodesic
    return geodesic((lat1, lon1), (lat2, lon2)).meters


# class CheckRequestSerializer(serializers.Serializer):
#     user_id = serializers.IntegerField()
#     type = serializers.ChoiceField(choices=['check_in', 'check_out'])
#     latitude = serializers.FloatField()
#     longitude = serializers.FloatField()


class CheckRequestSerializer(serializers.Serializer):
    user_id = serializers.IntegerField()
    type = serializers.ChoiceField(choices=['check_in', 'check_out'])
    latitude = serializers.FloatField()
    longitude = serializers.FloatField()
    image = serializers.CharField()  # base64 encoded

    def validate(self, attrs):
        # Barcha maydonlar majburiy
        if not attrs.get("latitude") or not attrs.get("longitude"):
            raise serializers.ValidationError("Latitude va longitude majburiy.")
        if not attrs.get("image"):
            raise serializers.ValidationError("Image majburiy.")
        return attrs


class SimpleCheckAPIView(generics.ListCreateAPIView):
    serializer_class = CheckRequestSerializer
    renderer_classes = [JSONRenderer] 
    
    def get_queryset(self):
        return []

    def create(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        user_id = data['user_id']
        check_type = data['type']
        latitude = data['latitude']
        longitude = data['longitude']
        image_base64 = data['image']

        # 🔍 Employee olish
        try:
            employee = Employee.objects.get(user_id=user_id)
        except Employee.DoesNotExist:
            return Response({"status": "FAIL", "reason": "Foydalanuvchi topilmadi"}, status=404)

        # 🔍 Location tekshirish
        location = Location.objects.filter(filial=employee.filial).first()
        if not location:
            return Response({"status": "FAIL", "reason": "Filial manzili tasdiqlanmagan"}, status=400)

        if employee.image:
            cf = verify_face(employee, image_base64)
            if cf is not True:
                return Response({"status": "FAIL", "reason": "FaceID Mos kelmadi"}, status=403)

        # 📏 Masofa hisoblash
        distance = get_distance_meters(latitude, longitude, location.latitude, location.longitude)
        if distance >= 150:
            return Response({"status": "FAIL", "reason": "Siz manzildan uzoqdasiz."}, status=403)

        # 🕒 Bugungi sana/vaqt
        today = timezone.localdate()
        now_time = timezone.localtime().time()

        # 🗂 Attendance yaratish yoki olish
        attendance, _ = Attendance.objects.get_or_create(employee=employee, date=today)

        if check_type == 'check_in':
            attendance.check_number += 1
            attendance.check_in = attendance.check_in or now_time
        elif check_type == 'check_out':
            attendance.check_out = now_time
            if attendance.check_in:
                worked = datetime.combine(today, attendance.check_out) - datetime.combine(today, attendance.check_in)
                hours, remainder = divmod(int(worked.total_seconds()), 3600)
                minutes, _ = divmod(remainder, 60)
                msg = (
                    f"👤 Hodim: {employee.name}\n"
                    f"📅 Sana: {today}\n"
                    f"⏰ Kirish: {attendance.check_in.strftime('%H:%M')}\n"
                    f"🚪 Chiqish: {attendance.check_out.strftime('%H:%M')}\n"
                    f"⌛ Ish vaqt: {hours:02d}:{minutes:02d}"
                )
                send_telegram_message_to_admin(employee.user_id, msg)

        attendance.save()

        # 📩 Adminlarga xabar yuborish
        def build_schedule_message(jadval, check_type, now_time):
            if not jadval:
                return None

            expected_time = jadval.start if check_type == 'check_in' else jadval.end
            delta_sec = get_time_difference(expected_time, now_time)
            min_diff = abs(delta_sec) // 60

            if delta_sec == 0:
                return " O‘z vaqtida keldi" if check_type == 'check_in' else " O‘z vaqtida ketdi"
            if check_type == 'check_in':
                return f" Kechikdi: {min_diff} daqiqa" if delta_sec > 0 else f" Erta keldi: {min_diff} daqiqa"
            else:
                return f" Erta ketdi: {min_diff} daqiqa" if delta_sec < 0 else f" Kech ketdi: {min_diff} daqiqa"

        admins = Administrator.objects.filter(filial=employee.filial)
        jadval = WorkSchedule.objects.filter(employee=employee, weekday__id=today.weekday()+1).first()

        status_text = build_schedule_message(jadval, check_type, now_time)

        for admin in admins:
            if not admin.telegram_id:
                continue
            msg_lines = [
                f" Xodim: {employee.name}",
                f" {' Keldi' if check_type == 'check_in' else 'Ketdi'} : {now_time.strftime('%H:%M')}",
            ]
            if status_text:
                msg_lines.append(status_text)
            msg_lines.append(f" Sana: {today.strftime('%Y-%m-%d')}")

            if check_type == 'check_in':
                if attendance.check_number == 1:
                    send_telegram_message_to_admin(admin.telegram_id, "\n".join(msg_lines))
            else:
                send_telegram_message_to_admin(admin.telegram_id, "\n".join(msg_lines))

        return Response({
            "status": "SUCCESS",
            "type": check_type,
            "time": now_time.strftime('%H:%M:%S')
        }, status=200)