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
        latitude = data['latitude']
        longitude = data['longitude']

        try:
            employee = Employee.objects.get(user_id=user_id)
        except Employee.DoesNotExist:
            return Response({"status": "FAIL", "reason": "User not found"}, status=404)

        # 🔍 1. Location tekshirish
        location = Location.objects.filter(filial=employee.filial).first()
        if not location:
            return Response({"status": "FAIL", "reason": "Location not set"}, status=400)

        # 📏 2. Masofa hisoblash
        distance = get_distance_meters(
            lat1=latitude,
            lon1=longitude,
            lat2=location.latitude,
            lon2=location.longitude
        )

        print(f"Masofa: {distance} metr")

        if distance >= 150:
            return Response({"status": "FAIL", "reason": "You are too far from the location."}, status=403)

        # ✅ 3. Userni olish

        today = timezone.localdate()
        now_time = timezone.localtime().time()
        # 🕒 4. Attendance ni yaratish yoki olish
        attendance, created = Attendance.objects.get_or_create(
            employee=employee,
            date=today
        )

        if check_type == 'check_in':
            if not attendance.check_in:
                attendance.check_in = now_time
        elif check_type == 'check_out':
            attendance.check_out = now_time

        attendance.save()
        
        admins = Administrator.objects.filter(filial=employee.filial).all()
        for admin in admins:
            if admin and admin.telegram_id:
                msg_lines = [
                    f" Xodim: {employee.name}",
                    f" {' Keldi' if check_type == 'check_in' else 'Ketdi'} : {now_time.strftime('%H:%M')}",
                ]
                jadval = WorkSchedule.objects.filter(employee=employee, weekday__id=today.weekday()+1).first()
                if jadval:
                    if check_type == 'check_in':
                        expected_time = jadval.start
                        delta_sec = get_time_difference(expected_time, now_time)
                        min_diff = abs(delta_sec) // 60

                        if delta_sec > 0:
                            msg_lines.append(f" Kechikdi: {min_diff} daqiqa")
                        elif delta_sec < 0:
                            msg_lines.append(f" Erta keldi: {min_diff} daqiqa")
                        else:
                            msg_lines.append(" O‘z vaqtida keldi")
                    
                    elif check_type == 'check_out':
                        expected_time = jadval.end
                        delta_sec = get_time_difference(expected_time, now_time)
                        min_diff = abs(delta_sec) // 60

                        if delta_sec < 0:
                            msg_lines.append(f" Erta ketdi: {min_diff} daqiqa")
                        elif delta_sec > 0:
                            msg_lines.append(f" Kech ketdi: {min_diff} daqiqa")
                        else:
                            msg_lines.append(" O‘z vaqtida ketdi")        
                msg_lines.append(f" Sana: {today.strftime('%Y-%m-%d')}",)
        
                message_text = "\n".join(msg_lines)
                
                send_telegram_message_to_admin(admin.telegram_id, message_text)

        return Response({
            "status": "SUCCESS",
            "type": check_type,
            "time": now_time.strftime('%H:%M:%S')
        }, status=200)
