from rest_framework.response import Response
from rest_framework import serializers, generics, status
from rest_framework.renderers import JSONRenderer
from .models import Location, Attendance, Employee
from django.utils import timezone


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

        # 🔍 1. Location tekshirish
        location = Location.objects.first()
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

        if distance >= 50:
            return Response({"status": "FAIL", "reason": "You are too far from the location."}, status=403)

        # ✅ 3. Userni olish
        try:
            employee = Employee.objects.get(user_id=user_id)
        except Employee.DoesNotExist:
            return Response({"status": "FAIL", "reason": "User not found"}, status=404)

        today = timezone.localdate()
        now_time = timezone.localtime().time()

        # 🕒 4. Attendance ni yaratish yoki olish
        attendance, created = Attendance.objects.get_or_create(
            employee=employee,
            date=today
        )

        if check_type == 'check_in':
            if attendance.check_in:
                return Response({"status": "ALREADY_CHECKED_IN", "time": attendance.check_in.strftime('%H:%M:%S')})
            attendance.check_in = now_time
        elif check_type == 'check_out':
            if attendance.check_out:
                return Response({"status": "ALREADY_CHECKED_OUT", "time": attendance.check_out.strftime('%H:%M:%S')})
            attendance.check_out = now_time

        attendance.save()

        return Response({
            "status": "SUCCESS",
            "type": check_type,
            "time": now_time.strftime('%H:%M:%S')
        }, status=200)
