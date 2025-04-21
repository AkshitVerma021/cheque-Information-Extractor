import boto3
from io import BytesIO
from PIL import Image
from typing import Optional
import streamlit as st
from datetime import datetime

from config.config import AWS_REGION, AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, S3_BUCKET_NAME

class S3Service:
    def __init__(self):
        self.s3_client = boto3.client(
            's3',
            region_name=AWS_REGION,
            aws_access_key_id=AWS_ACCESS_KEY_ID,
            aws_secret_access_key=AWS_SECRET_ACCESS_KEY
        )
        self.bucket_name = S3_BUCKET_NAME
        
    def upload_image(self, image: Image.Image, s3_key: str, content_type: str = 'image/jpeg') -> Optional[str]:
        """Upload PIL Image to S3 and return public URL"""
        try:
            # Convert to bytes
            img_byte_arr = BytesIO()
            image.save(img_byte_arr, format='JPEG')
            return self.upload_bytes(img_byte_arr.getvalue(), s3_key, content_type)
        except Exception as e:
            st.error(f"Failed to upload image to S3: {str(e)}")
            return None
    
    def upload_bytes(self, file_bytes: bytes, s3_key: str, content_type: str) -> Optional[str]:
        """Upload bytes to S3 and return public URL"""
        try:
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=s3_key,
                Body=file_bytes,
                ContentType=content_type
            )
            return f"s3://{self.bucket_name}/{s3_key}"
        except Exception as e:
            st.error(f"Failed to upload to S3: {str(e)}")
            return None
    
    def upload_excel(self, excel_bytes: bytes) -> Optional[str]:
        """Upload Excel file to S3 and return URL"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            s3_key = f"excel_reports/cheque_report_{timestamp}.xlsx"
            
            return self.upload_bytes(
                excel_bytes, 
                s3_key, 
                'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
        except Exception as e:
            st.error(f"Failed to upload Excel to S3: {str(e)}")
            return None
            
    def crop_and_upload_signature(self, image: Image.Image, cheque_id: str) -> Optional[str]:
        """Crop signature area from cheque image and upload to S3"""
        try:
            # Convert to RGB if needed
            if image.mode == 'RGBA':
                image = image.convert('RGB')
                
            # Crop signature area
            width, height = image.size
            left = int(width * 0.75)
            top = int(height * 0.57)
            right = width
            bottom = int(height * 0.92)
            signature = image.crop((left, top, right, bottom))
            
            # Generate unique timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            s3_key = f"signatures/signature_{timestamp}_{cheque_id}.jpg"
            
            return self.upload_image(signature, s3_key)
        except Exception as e:
            st.error(f"Failed to crop and upload signature: {str(e)}")
            return None 