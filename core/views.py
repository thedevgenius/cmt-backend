import os
from django.core.files.storage import default_storage
from django.utils.timezone import now
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework import status
from PIL import Image

class CentralImageUploadAPIView(APIView):
    """
    High-speed gatekeeper endpoint. Validates frontend-compressed WebP 
    images and streams them directly to Cloudflare R2.
    """
    parser_classes = [MultiPartParser, FormParser]
    permission_classes = [AllowAny]

    # Valid subfolders in your R2 bucket based on context
    ALLOWED_FOLDERS = {
        'business_logo': 'business_logos',
        'business_cover': 'business_covers',
        'user_avatar': 'avatars',
        'review_image': 'reviews',
    }

    def post(self, request, *args, **kwargs):
        upload_type = request.query_params.get('type')
        if upload_type not in self.ALLOWED_FOLDERS:
            return Response(
                {"error": f"Invalid 'type'. Choose from: {list(self.ALLOWED_FOLDERS.keys())}"}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        file_obj = request.FILES.get('image')
        if not file_obj:
            return Response({"error": "No image file provided."}, status=status.HTTP_400_BAD_REQUEST)

        # -----------------------------------------------------------
        # PRODUCTION SECURITY GUARDRAILS
        # -----------------------------------------------------------
        # 1. Enforce a strict max size payload (e.g., 1.5MB max for compressed WebP)
        if file_obj.size > 1.5 * 1024 * 1024:
            return Response({"error": "Compressed file too large. Max allowed is 1.5MB."}, status=status.HTTP_400_BAD_REQUEST)

        # 2. Light validation to ensure it's a valid image layout without reading all pixels into memory
        try:
            img = Image.open(file_obj)
            img.verify() 
        except Exception:
            return Response({"error": "Invalid or corrupt image file."}, status=status.HTTP_400_BAD_REQUEST)

        # -----------------------------------------------------------
        # STREAM DIRECTLY TO CLOUDFLARE R2
        # -----------------------------------------------------------
        folder = self.ALLOWED_FOLDERS[upload_type]
        date_path = now().strftime("%Y/%m")
        
        # Reset pointer after pillow verify()
        file_obj.seek(0)
        
        # Generate clean, unique filename to completely avoid overwrites
        original_name = os.path.splitext(file_obj.name)[0]
        clean_name = "".join([c for c in original_name if c.isalnum() or c==' ']).rstrip().replace(' ', '_')
        r2_storage_path = f"{folder}/{date_path}/{clean_name}_{now().timestamp()}.webp"

        try:
            # Streams straight to R2 via django-storages
            saved_path = default_storage.save(r2_storage_path, file_obj)
            public_url = default_storage.url(saved_path)

            return Response({
                "success": True,
                "url": public_url,
                "type": upload_type
            }, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response({"error": f"Storage upload failed: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)