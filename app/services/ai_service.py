import boto3
import json
import base64
from io import BytesIO
from PIL import Image
from typing import Dict, Optional
import streamlit as st
import re
import time
import random
from botocore.exceptions import ClientError

from config.config import (
    AWS_REGION, 
    AWS_ACCESS_KEY_ID, 
    AWS_SECRET_ACCESS_KEY,
    CLAUDE_SONNET_MODEL_ID,
    CLAUDE_HAIKU_MODEL_ID
)

class AIService:
    def __init__(self):
        self.bedrock_client = boto3.client(
            service_name='bedrock-runtime',
            region_name=AWS_REGION,
            aws_access_key_id=AWS_ACCESS_KEY_ID,
            aws_secret_access_key=AWS_SECRET_ACCESS_KEY
        )
        self.last_request_time = 0
        self.min_request_interval = 1.0  # Minimum 1 second between requests
    
    def _rate_limit(self):
        """Implement rate limiting between requests"""
        current_time = time.time()
        time_since_last_request = current_time - self.last_request_time
        
        if time_since_last_request < self.min_request_interval:
            sleep_time = self.min_request_interval - time_since_last_request
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()
    
    def _invoke_model_with_retry(self, model_id: str, body: str, max_retries: int = 5) -> Dict:
        """Invoke Bedrock model with exponential backoff retry logic"""
        for attempt in range(max_retries):
            try:
                self._rate_limit()  # Apply rate limiting
                
                response = self.bedrock_client.invoke_model(
                    modelId=model_id,
                    body=body
                )
                return json.loads(response['body'].read())
                
            except ClientError as e:
                error_code = e.response['Error']['Code']
                
                if error_code == 'ThrottlingException':
                    if attempt < max_retries - 1:
                        # Exponential backoff with jitter
                        wait_time = (2 ** attempt) + random.uniform(0, 1)
                        st.warning(f"Rate limit reached. Waiting {wait_time:.1f} seconds before retry {attempt + 1}/{max_retries}...")
                        time.sleep(wait_time)
                        continue
                    else:
                        raise Exception(f"Max retries reached for {model_id}. Please wait a few minutes before trying again.")
                else:
                    # For other errors, don't retry
                    raise e
            except Exception as e:
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt
                    st.warning(f"Error occurred. Retrying in {wait_time} seconds... (attempt {attempt + 1}/{max_retries})")
                    time.sleep(wait_time)
                    continue
                else:
                    raise e
        
        raise Exception(f"Failed to invoke {model_id} after {max_retries} attempts")

    def _prepare_image(self, image: Image.Image) -> str:
        """Convert image to base64 encoded string with compression if needed"""
        # Convert to RGB if it's RGBA
        if image.mode == 'RGBA':
            image = image.convert('RGB')
            
        img_byte_arr = BytesIO()  
        image.save(img_byte_arr, format='JPEG', quality=70)  
        
        if img_byte_arr.tell() > 5 * 1024 * 1024:  
            st.warning("Image too large, applying aggressive compression")  
            img_byte_arr = BytesIO()  
            image.save(img_byte_arr, format='JPEG', quality=30)  
        
        return base64.b64encode(img_byte_arr.getvalue()).decode('utf-8')
    
    def _validate_cheque_image(self, encoded_image: str, model_id: str) -> bool:
        """Check if the image is a valid cheque"""
        validation_prompt = """
        Is this image a bank cheque/check? Respond with just 'yes' or 'no'.
        Look for key cheque elements: bank name, payee line, date field, amount box, 
        signature line, account details, etc. If multiple of these elements are missing,
        it's likely not a valid cheque image.
        """
        
        validation_body = {  
            "anthropic_version": "bedrock-2023-05-31",  
            "max_tokens": 10,  
            "temperature": 0.1,  
            "messages": [  
                {  
                    "role": "user",  
                    "content": [  
                        {"type": "text", "text": validation_prompt},  
                        {  
                            "type": "image",  
                            "source": {  
                                "type": "base64",  
                                "media_type": "image/jpeg",  
                                "data": encoded_image  
                            }  
                        }  
                    ]  
                }  
            ]  
        }  
        
        try:
            validation_response_body = self._invoke_model_with_retry(
                model_id, 
                json.dumps(validation_body)
            )
            validation_text = validation_response_body['content'][0]['text'].strip().lower()
            return "yes" in validation_text
        except Exception as e:
            st.error(f"Failed to validate cheque image: {str(e)}")
            return False
    
    def _extract_json_from_response(self, response_text: str) -> Dict:
        """Extract JSON from model response text"""
        start_idx = response_text.find('{')  
        end_idx = response_text.rfind('}') + 1  
        
        if start_idx == -1 or end_idx == 0:  
            raise ValueError("No JSON object found in response")  
            
        json_str = response_text[start_idx:end_idx]  
        return json.loads(json_str)
    
    def _clean_extraction_result(self, result: Dict) -> Dict:
        """Clean and normalize extraction result"""
        # Clean amount field
        if "amount" in result and result["amount"] != "N/A":
            amount_str = str(result["amount"])
            cleaned_amount = ''.join(filter(str.isdigit, amount_str))
            if cleaned_amount and len(cleaned_amount) <= 15:
                result["amount"] = int(cleaned_amount)
            else:
                result["amount"] = "N/A"
        
        # Ensure all fields are present
        required_fields = ["bank", "account_holder", "account_number", 
                        "ifsc_code", "date", "has_signature"]
        for field in required_fields:
            if field not in result:
                result[field] = "N/A"
                
        return result
    
    def _process_extraction(self, image: Image.Image, model_id: str, prompt: str) -> Optional[Dict]:
        """Process image extraction with specified model and prompt"""
        try:
            encoded_image = self._prepare_image(image)
            
            # First validate if this is a cheque image
            if not self._validate_cheque_image(encoded_image, model_id):
                return {"error": "Invalid cheque image. Please upload a valid bank cheque."}
            
            # Prepare model request
            body = {  
                "anthropic_version": "bedrock-2023-05-31",  
                "max_tokens": 1000,  
                "temperature": 0.1,  
                "messages": [  
                    {  
                        "role": "user",  
                        "content": [  
                            {"type": "text", "text": prompt},  
                            {  
                                "type": "image",  
                                "source": {  
                                    "type": "base64",  
                                    "media_type": "image/jpeg",  
                                    "data": encoded_image  
                                }  
                            }  
                        ]  
                    }  
                ]  
            }  
            
            # Call model with retry logic
            response_body = self._invoke_model_with_retry(
                model_id, 
                json.dumps(body)
            )
            
            # Process response
            response_text = response_body['content'][0]['text'].strip()  
            
            # Extract and clean result
            result = self._extract_json_from_response(response_text)
            return self._clean_extraction_result(result)
            
        except Exception as e:
            st.error(f"Extraction failed with {model_id}: {str(e)}")
            return None
    
    def extract_with_haiku(self, image: Image.Image) -> Optional[Dict]:
        """Extract cheque data using Claude 3 Haiku"""
        prompt = """  
        Analyze this cheque image and extract the following details in EXACTLY this JSON format:  
        {  
            "bank": "Bank Name",  
            "account_holder": "Account Holder Name",  
            "account_number": "Account Number",  
            "amount": "Amount in numbers (digits only, no symbols, e.g., 3300000)",  
            "ifsc_code": "IFSC Code",  
            "date": "DD/MM/YYYY",  
            "has_signature": true/false  
        }  

        CRITICAL INSTRUCTIONS FOR AMOUNT EXTRACTION:  
        1. Locate both the numerical amount (digits) and written amount (words)  
        2. If numerical amount is present and clear, use that  
        3. If numerical amount is unclear, convert the written amount to digits:  
            - "Thirty Three Lakhs" → 3300000  
            - "Thirty Three Thousand" → 33000  
        4. Amount must be digits only (no ₹, Rs, commas, or spaces)  
        5. If amount cannot be determined, use "N/A"  

        IMPORTANT:  
        1. Return ONLY the JSON object  
        2. Do not include any additional text or explanations  
        3. All amounts must be in complete rupees (no paise)  
        """
        
        return self._process_extraction(image, CLAUDE_HAIKU_MODEL_ID, prompt)
    
    def extract_with_sonnet(self, image: Image.Image) -> Optional[Dict]:
        """Extract cheque data using Claude 3 Sonnet"""
        prompt = """Extract the following details from this cheque image in JSON format:
        {
            "bank": "Bank Name",
            "account_holder": "Account Holder Name",
            "account_number": "Account Number",
            "amount": "Amount in numbers (digits only, no symbols)",
            "ifsc_code": "IFSC Code",
            "date": "DD/MM/YYYY",
            "has_signature": true/false
        }
        
        IMPORTANT:
        1. For amount, extract both numerical and written amounts if available
        2. Convert written amounts to digits (e.g., "Thirty Three Thousand" → 33000)
        3. Return ONLY valid JSON with no additional text
        """
        
        return self._process_extraction(image, CLAUDE_SONNET_MODEL_ID, prompt) 