# views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from .serializers import UserProfileUpdateSerializer, UserProfileSerializer, RequestOTPSerializer, VerifyOTPSerializer

from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.tokens import RefreshToken

from .models import User
from .services import send_and_store_otp, verify_otp_service

class UserProfileAPIView(APIView):
    """
    Endpoint for the authenticated user to update their own profile details.
    """
    # Enforce that a valid JWT token must be provided
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        # request.user automatically holds the user instance attached to the provided JWT token
        serializer = UserProfileSerializer(request.user)
        
        return Response({
            "success": True,
            "user": serializer.data
        }, status=status.HTTP_200_OK)

    def patch(self, request, *args, **kwargs):
        """
        Handles partial updates (PATCH). 
        Users can pass only the fields they want to change.
        """
        # Pass the authenticated user instance and incoming data to the serializer
        serializer = UserProfileUpdateSerializer(
            instance=request.user, 
            data=request.data, 
            partial=True,
            context={'request': request}
        )
        
        if serializer.is_valid():
            serializer.save()
            return Response({
                "success": True,
                "message": "Profile updated successfully.",
                "user": serializer.data
            }, status=status.HTTP_200_OK)
            
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, *args, **kwargs):
        """
        Handles full updates (PUT). 
        Requires all fields to be passed in the payload.
        """
        serializer = UserProfileUpdateSerializer(
            instance=request.user, 
            data=request.data,
            context={'request': request}
        )
        
        if serializer.is_valid():
            serializer.save()
            return Response({
                "success": True,
                "message": "Profile updated successfully.",
                "user": serializer.data
            }, status=status.HTTP_200_OK)
            
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


def get_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)
    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }

class RequestOTPView(APIView):
    """
    API View to request an OTP for a given phone number.
    """
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = RequestOTPSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        phone = serializer.validated_data['phone']

        if not phone:
            return Response(
                {"error": "Phone number is required"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
            
        # Call our service function
        result = send_and_store_otp(phone)
        
        if result['success']:
            return Response(result, status=status.HTTP_200_OK)
        else:
            return Response(result, status=status.HTTP_400_BAD_REQUEST)
    

class VerifyOTPView(APIView):
    """
    API View to verify an OTP and return JWT tokens.
    """
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = VerifyOTPSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        phone = serializer.validated_data['phone']
        otp = serializer.validated_data['otp']
        result = verify_otp_service(phone, otp)

        if not result["success"]:
            return Response({"detail": result["error"]}, status=result["status"])
        
        user, created = User.objects.get_or_create(
            phone=phone,
            defaults={"is_active": True}
        )

        if not user.is_active:
            user.is_active = True
            user.save()

        tokens = get_tokens_for_user(user)
        
        # 6. Return Success Response
        return Response({
            "success": True, 
            "detail": "Login successful.",
            "user": UserProfileSerializer(user).data,
            "tokens": tokens 
        }, status=status.HTTP_200_OK)