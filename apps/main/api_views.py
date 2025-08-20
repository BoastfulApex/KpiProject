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


class CheckRequestSerializer(serializers.Serializer):
    user_id = serializers.IntegerField()
    type = serializers.ChoiceField(choices=['check_in', 'check_out'])
    latitude = serializers.FloatField()
    longitude = serializers.FloatField()


class SimpleCheckAPIView(generics.ListCreateAPIView):
    serializer_class = CheckRequestSerializer
    renderer_classes = [JSONRenderer] 
    
    def get_queryset(self):
        return []

    def create(self, request):
        serializer = CheckRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=400)

        data = serializer.validated_data
        user_id = data['user_id']
        check_type = data['type']
        latitude, longitude = data['latitude'], data['longitude']

        # 🔍 Employee olish
        employee = get_object_or_404(Employee, user_id=user_id)

        # 🔍 Location tekshirish
        location = Location.objects.filter(filial=employee.filial).first()
        if not location:
            return Response({"status": "FAIL", "reason": "Location not set"}, status=400)

        # 📏 Masofa hisoblash
        distance = get_distance_meters(latitude, longitude, location.latitude, location.longitude)
        if distance >= 150:
            return Response({"status": "FAIL", "reason": "You are too far from the location."}, status=403)

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