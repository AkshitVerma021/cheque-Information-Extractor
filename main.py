# import streamlit as st
# from app.main import run_app

# if __name__ == "__main__":
#     run_app()
import streamlit as st  
from PIL import Image  
import os  
import json  
import pandas as pd  
import boto3  
import base64  
from dotenv import load_dotenv  
from io import BytesIO  
from typing import Dict, List, Tuple
import re
from datetime import datetime
import time
import random
# import google.generativeai as genai

# Load environment variables  
load_dotenv()  

# --- App Setup ---  
st.set_page_config(  
    page_title="ChequeAI - Document Extractor",  
    page_icon="🏦",  
    layout="wide"  
)  

# Add logo at the top center  
col1, col2, col3 = st.columns([1,1,1])  
with col2:  
    logo = Image.open("logo.png")  # Load logo from same directory  
    st.image(logo, width=600)  

# Custom CSS   
st.markdown("""  
<style>  
.header { font-size: 2.5em; color: #2e86c1; text-align: center; padding: 20px; border-bottom: 2px solid #3498db; margin-bottom: 30px; }  
.upload-box { border: 2px dashed #3498db; border-radius: 5px; padding: 20px; text-align: center; }  
.result-box { margin-top: 20px; padding: 20px; border: 1px solid #3498db; border-radius: 5px; background-color: #f8f9fa; }  
.clear-btn { margin-top: 20px; }  
.data-table { width: 100%; margin-top: 20px; }  
.cheque-container { margin-bottom: 30px; padding: 15px; border: 1px solid #eee; border-radius: 5px; }  
.bill-container { margin-bottom: 30px; padding: 15px; border: 1px solid #f39c12; border-radius: 5px; }  
.stButton>button, .stDownloadButton>button { background-color: #2e86c1 !important; color: white !important; border: none !important; width: 100%; margin: 5px 0 !important; transition: background-color 0.3s; }  
.stButton>button:hover, .stDownloadButton>button:hover { background-color: #2874a6 !important; }  
.stButton, .stDownloadButton { display: flex; justify-content: center; }  
.accuracy-meter { margin-bottom: 20px; }  
.accuracy-value { font-weight: bold; color: #2e86c1; }  
.discrepancy { color: #e74c3c; font-weight: bold; }  
.validation-pass { color: #27ae60; font-weight: bold; }  
.document-type-badge { padding: 5px 10px; border-radius: 15px; color: white; font-weight: bold; margin-bottom: 10px; }
.cheque-badge { background-color: #2e86c1; }
.bill-badge { background-color: #f39c12; }
</style>  
""", unsafe_allow_html=True)  

# --- Initialize Clients ---  
bedrock = boto3.client(  
    service_name='bedrock-runtime',  
    region_name=os.getenv("AWS_REGION"),  
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),  
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY")  
)

# --- Initialize S3 Client ---
s3 = boto3.client(
    's3',
    region_name=os.getenv("AWS_REGION"),
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY")
)
S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME")

# --- Validation Rules ---
BANK_NAME_PATTERNS = [
    r'STATE BANK OF INDIA', r'SBI', r'HDFC BANK', r'ICICI BANK', 
    r'AXIS BANK', r'PUNJAB NATIONAL BANK', r'PNB', r'CANARA BANK',
    r'BANK OF BARODA', r'BOB', r'UNION BANK OF INDIA'
]

IFSC_CODE_PATTERN = r'^[A-Z]{4}0[A-Z0-9]{6}$'
ACCOUNT_NUMBER_PATTERN = r'^\d{9,18}$'
DATE_PATTERN = r'^\d{1,2}/\d{1,2}/\d{4}$'

# --- Bill Validation Patterns ---
BILL_NUMBER_PATTERN = r'^[A-Z0-9\-/]{5,20}$'
GST_NUMBER_PATTERN = r'^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}$'
PHONE_PATTERN = r'^[\+]?[0-9\s\-\(\)]{10,15}$'
EMAIL_PATTERN = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'

# --- Currency Detection Patterns ---
INDIAN_PHONE_PATTERNS = [
    r'^0\d{2,4}-\d{6,8}$',  # Landline format like 0381-2325984
    r'^\+91[\s\-]?\d{10}$',  # Mobile with +91
    r'^91\d{10}$',  # Mobile with 91
    r'^[6-9]\d{9}$'  # Indian mobile numbers
]

US_PHONE_PATTERNS = [
    r'^\+1[\s\-]?\d{10}$',  # US format with +1
    r'^1[\s\-]?\d{10}$',   # US format with 1
    r'^\(\d{3}\)\s?\d{3}-\d{4}$',  # (555) 123-4567
    r'^\d{3}-\d{3}-\d{4}$'  # 555-123-4567
]

# --- Retry Logic Helper Functions ---
def exponential_backoff_delay(attempt: int, base_delay: float = 3.0, max_delay: float = 120.0) -> float:
    """Calculate exponential backoff delay with jitter - more aggressive for rate limiting"""
    delay = min(base_delay * (2 ** attempt), max_delay)
    # Add jitter to avoid thundering herd problem
    jitter = random.uniform(0.1, 0.3) * delay
    return delay + jitter

def invoke_model_with_retry(model_id: str, body: Dict, max_retries: int = 5) -> Dict:
    """Invoke Bedrock model with exponential backoff retry logic"""
    for attempt in range(max_retries):
        try:
            response = bedrock.invoke_model(
                modelId=model_id,
                body=json.dumps(body)
            )
            return json.loads(response['body'].read())
        except Exception as e:
            error_str = str(e).lower()
            
            # Check if it's a throttling exception
            if "throttling" in error_str or "too many requests" in error_str or "rate exceeded" in error_str:
                if attempt < max_retries - 1:  # Don't wait on the last attempt
                    delay = exponential_backoff_delay(attempt)
                    st.warning(f"⏳ Rate limit reached. Waiting {delay:.1f} seconds before retry {attempt + 1}/{max_retries}...")
                    time.sleep(delay)
                    continue
                else:
                    raise Exception(f"Max retries reached due to rate limiting: {str(e)}")
            else:
                # For non-throttling errors, re-raise immediately
                raise e
    
    raise Exception("Max retries exceeded")

# --- Core Functions ---
def extract_cheque_data(image: Image) -> Dict:
    """Send cheque image to Claude 3 Haiku and parse response"""
    try:
        # Convert image to RGB if it's RGBA
        if image.mode == 'RGBA':
            image = image.convert('RGB')
            
        img_byte_arr = BytesIO()  
        image.save(img_byte_arr, format='JPEG', quality=70)  
        
        if img_byte_arr.tell() > 5 * 1024 * 1024:  
            st.warning("Image too large, applying aggressive compression")  
            img_byte_arr = BytesIO()  
            image.save(img_byte_arr, format='JPEG', quality=30)  
        
        encoded_image = base64.b64encode(img_byte_arr.getvalue()).decode('utf-8') 
        
        # First check if this is a valid cheque image
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
        
        validation_response = invoke_model_with_retry("anthropic.claude-3-haiku-20240307-v1:0", validation_body)  
        
        validation_text = validation_response['content'][0]['text'].strip().lower()
        
        if "no" in validation_text:
            return {"error": "Invalid cheque image. Please upload a valid bank cheque."}
        
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
        
        response = invoke_model_with_retry("anthropic.claude-3-haiku-20240307-v1:0", body)  
        
        response_text = response['content'][0]['text'].strip()  
        
        start_idx = response_text.find('{')  
        end_idx = response_text.rfind('}') + 1  
        if start_idx == -1 or end_idx == 0:  
            raise ValueError("No JSON object found in response")  
            
        response_text = response_text[start_idx:end_idx]  
        result = json.loads(response_text)  
        
        if "amount" in result and result["amount"] != "N/A":  
            amount_str = str(result["amount"])  
            cleaned_amount = ''.join(filter(str.isdigit, amount_str))  
            if cleaned_amount and len(cleaned_amount) <= 15:  
                result["amount"] = int(cleaned_amount)  
            else:  
                result["amount"] = "N/A"  
        
        required_fields = ["bank", "account_holder", "account_number",   
                        "ifsc_code", "date", "has_signature"]  
        for field in required_fields:  
            if field not in result:  
                result[field] = "N/A"  
                
        return result  
        
    except json.JSONDecodeError as e:  
        st.error(f"Failed to parse JSON response: {str(e)}")  
        st.text(f"Raw response: {response_text}")  
        return None  
    except Exception as e:  
        st.error(f"Extraction failed: {str(e)}")  
        return None

def validate_cheque_data(data: Dict) -> Dict:
    """Apply rule-based validation to extracted cheque data"""
    validation_results = {
        "bank": {"valid": False, "message": ""},
        "account_number": {"valid": False, "message": ""},
        "ifsc_code": {"valid": False, "message": ""},
        "date": {"valid": False, "message": ""},
        "amount": {"valid": False, "message": ""}
    }
    
    # Bank name validation
    if data.get('bank', 'N/A') != 'N/A':
        bank_name = str(data['bank']).upper()
        validation_results['bank']['valid'] = any(re.search(pattern, bank_name) for pattern in BANK_NAME_PATTERNS)
        if not validation_results['bank']['valid']:
            validation_results['bank']['message'] = "Bank name doesn't match known patterns"
    
    # Account number validation
    account_num = str(data.get('account_number', ''))
    if account_num and account_num != 'N/A':
        validation_results['account_number']['valid'] = bool(re.fullmatch(ACCOUNT_NUMBER_PATTERN, account_num))
        if not validation_results['account_number']['valid']:
            validation_results['account_number']['message'] = "Account number format invalid (should be 9-18 digits)"
    
    # IFSC code validation
    ifsc = str(data.get('ifsc_code', ''))
    if ifsc and ifsc != 'N/A':
        validation_results['ifsc_code']['valid'] = bool(re.fullmatch(IFSC_CODE_PATTERN, ifsc))
        if not validation_results['ifsc_code']['valid']:
            validation_results['ifsc_code']['message'] = "IFSC code format invalid (should be 11 alphanumeric characters)"
    
    # Date validation
    date_str = str(data.get('date', ''))
    if date_str and date_str != 'N/A':
        validation_results['date']['valid'] = bool(re.fullmatch(DATE_PATTERN, date_str))
        if validation_results['date']['valid']:
            try:
                # Try to parse as MM/DD/YYYY first (common in bills), then DD/MM/YYYY
                parts = date_str.split('/')
                if len(parts) == 3:
                    month, day, year = map(int, parts)
                    # Check if it's a valid date in MM/DD/YYYY format
                    if month <= 12 and day <= 31:
                        datetime(year=year, month=month, day=day)
                    else:
                        # Try DD/MM/YYYY format
                        day, month, year = map(int, parts)
                        datetime(year=year, month=month, day=day)
            except ValueError:
                validation_results['date']['valid'] = False
                validation_results['date']['message'] = "Invalid date (should be MM/DD/YYYY or DD/MM/YYYY and a valid date)"
        else:
            validation_results['date']['message'] = "Date format invalid (should be MM/DD/YYYY or DD/MM/YYYY)"
    
    # Amount validation
    amount = data.get('amount', 'N/A')
    if amount != 'N/A':
        try:
            amount_num = int(amount)
            validation_results['amount']['valid'] = amount_num > 0
            if not validation_results['amount']['valid']:
                validation_results['amount']['message'] = "Amount should be positive"
        except (ValueError, TypeError):
            validation_results['amount']['valid'] = False
            validation_results['amount']['message'] = "Amount should be a valid number"
    
    return validation_results

# --- Document Type Detection ---
def detect_document_type(image: Image) -> str:
    """Detect if the document is a cheque or bill using AI"""
    try:
        if image.mode == 'RGBA':
            image = image.convert('RGB')
            
        img_byte_arr = BytesIO()  
        image.save(img_byte_arr, format='JPEG', quality=70)  
        encoded_image = base64.b64encode(img_byte_arr.getvalue()).decode('utf-8')
        
        detection_prompt = """
        Analyze this image and determine if it's a:
        1. "cheque" - Bank cheque/check with elements like payee line, account details, signature line
        2. "bill" - Invoice/receipt/bill with vendor details, items, amounts, tax information
        3. "unknown" - Neither a cheque nor a bill
        
        Respond with just one word: "cheque", "bill", or "unknown"
        """
        
        body = {  
            "anthropic_version": "bedrock-2023-05-31",  
            "max_tokens": 10,  
            "temperature": 0.1,  
            "messages": [  
                {  
                    "role": "user",  
                    "content": [  
                        {"type": "text", "text": detection_prompt},  
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
        
        response = invoke_model_with_retry("anthropic.claude-3-haiku-20240307-v1:0", body)  
        doc_type = response['content'][0]['text'].strip().lower()
        
        if "cheque" in doc_type:
            return "cheque"
        elif "bill" in doc_type:
            return "bill"
        else:
            return "unknown"
            
    except Exception as e:
        st.error(f"Document type detection failed: {str(e)}")
        return "unknown"

# --- Bill Extraction Functions ---
def extract_bill_data(image: Image) -> Dict:  
    """Send bill image to Claude 3 Haiku and parse response"""  
    try:  
        # Convert image to RGB if it's RGBA
        if image.mode == 'RGBA':
            image = image.convert('RGB')
            
        img_byte_arr = BytesIO()  
        image.save(img_byte_arr, format='JPEG', quality=70)  
        
        if img_byte_arr.tell() > 5 * 1024 * 1024:  
            st.warning("Image too large, applying aggressive compression")  
            img_byte_arr = BytesIO()  
            image.save(img_byte_arr, format='JPEG', quality=30)  
        
        encoded_image = base64.b64encode(img_byte_arr.getvalue()).decode('utf-8') 
        
        # First check if this is a valid bill image
        validation_prompt = """
        Is this image a bill/invoice/receipt? Respond with just 'yes' or 'no'.
        Look for key bill elements: vendor/company name, invoice number, date, 
        item details, amounts, tax information, etc. If multiple of these elements are missing,
        it's likely not a valid bill image.
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
        
        validation_response = invoke_model_with_retry("anthropic.claude-3-haiku-20240307-v1:0", validation_body)  
        
        validation_text = validation_response['content'][0]['text'].strip().lower()
        
        if "no" in validation_text:
            return {"error": "Invalid bill image. Please upload a valid bill/invoice/receipt."}
        
        prompt = """  
        Analyze this bill/invoice image and extract the following details in EXACTLY this JSON format:  
        {  
            "vendor_name": "Company/Vendor Name",  
            "bill_number": "Invoice/Bill Number",  
            "date": "MM/DD/YYYY or DD/MM/YYYY format as shown",  
            "total_amount": "Total amount with decimal (e.g., 182.40)",  
            "tax_amount": "Tax/GST amount with decimal (e.g., 12.50)",  
            "gst_number": "GST Number/Tax ID",  
            "vendor_phone": "Vendor Phone Number",  
            "vendor_email": "Vendor Email Address",  
            "customer_name": "Customer/Bill To Name",  
            "payment_method": "Payment Method (Cash/Card/UPI/etc.)",
            "currency": "Currency symbol if visible (₹, $, €, etc.) or best guess based on location indicators"  
        }  

        CRITICAL INSTRUCTIONS FOR AMOUNT EXTRACTION:  
        1. Locate the total amount and tax amounts clearly  
        2. Include decimal places (e.g., 182.40, not 18240)  
        3. If amount cannot be determined, use "N/A"  
        4. Extract the amount exactly as shown, preserving decimal formatting
        5. For currency, look for currency symbols in the document or deduce from:
           - GST numbers (India = ₹)
           - Phone number formats (Indian vs US patterns)
           - Email domains (.in = ₹, .com could be $)
           - Company names (Pvt Ltd = ₹, Inc/Corp = $)

        IMPORTANT:  
        1. Return ONLY the JSON object  
        2. Do not include any additional text or explanations  
        3. Keep decimal precision for all amounts  
        4. Extract date exactly as shown (MM/DD/YYYY or DD/MM/YYYY)  
        """  
        
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
        
        response = invoke_model_with_retry("anthropic.claude-3-haiku-20240307-v1:0", body)  
        
        response_text = response['content'][0]['text'].strip()  
        
        start_idx = response_text.find('{')  
        end_idx = response_text.rfind('}') + 1  
        if start_idx == -1 or end_idx == 0:  
            raise ValueError("No JSON object found in response")  
            
        response_text = response_text[start_idx:end_idx]  
        result = json.loads(response_text)  
        
        # Clean amount fields
        for amount_field in ["total_amount", "tax_amount"]:
            if amount_field in result and result[amount_field] != "N/A":  
                amount_str = str(result[amount_field])  
                # Remove currency symbols and spaces, but keep decimal point
                cleaned_amount = re.sub(r'[₹$Rs,\s]', '', amount_str)
                
                try:
                    # Parse as float to handle decimal amounts
                    if cleaned_amount and '.' in cleaned_amount:
                        amount_value = float(cleaned_amount)
                        result[amount_field] = f"{amount_value:.2f}"
                    elif cleaned_amount and cleaned_amount.replace('.', '').isdigit():
                        amount_value = float(cleaned_amount)
                        result[amount_field] = f"{amount_value:.2f}"
                    else:
                        result[amount_field] = "N/A"
                except (ValueError, TypeError):
                    result[amount_field] = "N/A"
        
        required_fields = ["vendor_name", "bill_number", "date", "total_amount",   
                        "tax_amount", "gst_number", "vendor_phone", "vendor_email",
                        "customer_name", "payment_method", "currency"]  
        for field in required_fields:  
            if field not in result:  
                result[field] = "N/A"  
        
        # Currency detection - use AI result or fallback to rule-based detection
        if result.get("currency", "N/A") == "N/A" or not result.get("currency"):
            result["currency"] = detect_currency_from_bill_data(result)
        
        # Validate and clean currency symbol
        detected_currency = result.get("currency", "₹")
        if detected_currency not in ["₹", "$", "€", "£", "¥"]:
            # If AI returned text description, convert to symbol
            currency_map = {
                "rupee": "₹", "rupees": "₹", "inr": "₹", "rs": "₹",
                "dollar": "$", "dollars": "$", "usd": "$",
                "euro": "€", "euros": "€", "eur": "€",
                "pound": "£", "pounds": "£", "gbp": "£",
                "yen": "¥", "jpy": "¥"
            }
            detected_currency_lower = detected_currency.lower().strip()
            result["currency"] = currency_map.get(detected_currency_lower, detect_currency_from_bill_data(result))
        
        return result  
        
    except json.JSONDecodeError as e:  
        st.error(f"Failed to parse JSON response: {str(e)}")  
        st.text(f"Raw response: {response_text}")  
        return None  
    except Exception as e:  
        st.error(f"Bill extraction failed: {str(e)}")  
        return None

def validate_bill_data(data: Dict) -> Dict:
    """Apply rule-based validation to extracted bill data"""
    validation_results = {
        "vendor_name": {"valid": False, "message": ""},
        "bill_number": {"valid": False, "message": ""},
        "gst_number": {"valid": False, "message": ""},
        "vendor_phone": {"valid": False, "message": ""},
        "vendor_email": {"valid": False, "message": ""},
        "date": {"valid": False, "message": ""},
        "total_amount": {"valid": False, "message": ""}
    }
    
    # Vendor name validation
    if data.get('vendor_name', 'N/A') != 'N/A':
        vendor_name = str(data['vendor_name']).strip()
        validation_results['vendor_name']['valid'] = len(vendor_name) >= 2
        if not validation_results['vendor_name']['valid']:
            validation_results['vendor_name']['message'] = "Vendor name too short"
    
    # Bill number validation
    bill_num = str(data.get('bill_number', ''))
    if bill_num and bill_num != 'N/A':
        validation_results['bill_number']['valid'] = bool(re.fullmatch(BILL_NUMBER_PATTERN, bill_num))
        if not validation_results['bill_number']['valid']:
            validation_results['bill_number']['message'] = "Bill number format invalid (should be 5-20 alphanumeric characters)"
    
    # GST number validation
    gst = str(data.get('gst_number', ''))
    if gst and gst != 'N/A':
        validation_results['gst_number']['valid'] = bool(re.fullmatch(GST_NUMBER_PATTERN, gst))
        if not validation_results['gst_number']['valid']:
            validation_results['gst_number']['message'] = "GST number format invalid"
    
    # Phone validation
    phone = str(data.get('vendor_phone', ''))
    if phone and phone != 'N/A':
        # Clean phone number for validation
        cleaned_phone = re.sub(r'[\s\-\(\)]', '', phone)
        validation_results['vendor_phone']['valid'] = bool(re.fullmatch(PHONE_PATTERN, phone)) and len(cleaned_phone) >= 10
        if not validation_results['vendor_phone']['valid']:
            validation_results['vendor_phone']['message'] = "Phone number format invalid"
    
    # Email validation
    email = str(data.get('vendor_email', ''))
    if email and email != 'N/A':
        validation_results['vendor_email']['valid'] = bool(re.fullmatch(EMAIL_PATTERN, email))
        if not validation_results['vendor_email']['valid']:
            validation_results['vendor_email']['message'] = "Email format invalid"
    
    # Date validation
    date_str = str(data.get('date', ''))
    if date_str and date_str != 'N/A':
        validation_results['date']['valid'] = bool(re.fullmatch(DATE_PATTERN, date_str))
        if validation_results['date']['valid']:
            try:
                # Try to parse as MM/DD/YYYY first (common in bills), then DD/MM/YYYY
                parts = date_str.split('/')
                if len(parts) == 3:
                    month, day, year = map(int, parts)
                    # Check if it's a valid date in MM/DD/YYYY format
                    if month <= 12 and day <= 31:
                        datetime(year=year, month=month, day=day)
                    else:
                        # Try DD/MM/YYYY format
                        day, month, year = map(int, parts)
                        datetime(year=year, month=month, day=day)
            except ValueError:
                validation_results['date']['valid'] = False
                validation_results['date']['message'] = "Invalid date (should be MM/DD/YYYY or DD/MM/YYYY and a valid date)"
        else:
            validation_results['date']['message'] = "Date format invalid (should be MM/DD/YYYY or DD/MM/YYYY)"
    
    # Amount validation
    amount = data.get('total_amount', 'N/A')
    if amount != 'N/A':
        try:
            amount_num = int(amount)
            validation_results['total_amount']['valid'] = amount_num > 0
            if not validation_results['total_amount']['valid']:
                validation_results['total_amount']['message'] = "Amount should be positive"
        except (ValueError, TypeError):
            validation_results['total_amount']['valid'] = False
            validation_results['total_amount']['message'] = "Amount should be a valid number"
    
    return validation_results

def detect_currency_from_bill_data(data: Dict) -> str:
    """Detect currency based on extracted bill data"""
    # Check for Indian indicators
    indian_indicators = 0
    us_indicators = 0
    
    # GST number indicates India
    gst_number = str(data.get('gst_number', ''))
    if gst_number != 'N/A' and re.match(GST_NUMBER_PATTERN, gst_number):
        indian_indicators += 3
    
    # Check phone number patterns
    phone = str(data.get('vendor_phone', ''))
    if phone != 'N/A':
        # Clean phone for pattern matching
        cleaned_phone = re.sub(r'[\s\-\(\)]', '', phone)
        
        # Check Indian phone patterns
        if any(re.match(pattern, phone) for pattern in INDIAN_PHONE_PATTERNS):
            indian_indicators += 2
        elif any(re.match(pattern, phone) for pattern in US_PHONE_PATTERNS):
            us_indicators += 2
    
    # Check email domain for Indian indicators
    email = str(data.get('vendor_email', ''))
    if email != 'N/A':
        if '.in' in email.lower() or 'gov.in' in email.lower():
            indian_indicators += 1
        elif '.com' in email.lower() or '.org' in email.lower():
            us_indicators += 0.5  # Less specific
    
    # Check vendor name for Indian companies/government
    vendor_name = str(data.get('vendor_name', '')).lower()
    if 'gem' in vendor_name or 'government' in vendor_name or 'pvt' in vendor_name or 'ltd' in vendor_name:
        indian_indicators += 1
    elif 'inc' in vendor_name or 'corp' in vendor_name or 'llc' in vendor_name:
        us_indicators += 1
    
    # Determine currency based on indicators
    if indian_indicators > us_indicators:
        return '₹'
    elif us_indicators > indian_indicators:
        return '$'
    else:
        return '₹'  # Default to INR if unclear

def cross_validate_results(claude_result: Dict, sonnet_result: Dict) -> Tuple[Dict, float]:
    """Single model verification - no cross-validation possible"""
    if not claude_result:
        return {}, 0.0
    
    # Removed dual verification - using single model only
    return {}, 85.0  # Fixed confidence for single model verification

def calculate_automated_accuracy(claude_result: Dict, sonnet_result: Dict, validation_results: Dict) -> float:
    """Calculate automated accuracy score using only rule-based validation"""
    if not claude_result:
        return 0.0
    
    # Only use rule-based validation since we don't have dual verification
    rule_based_score = 0
    if validation_results:
        valid_fields = sum(1 for field in validation_results.values() if field['valid'])
        total_fields = len(validation_results)
        rule_based_score = (valid_fields / total_fields) * 100 if total_fields > 0 else 0
    
    return rule_based_score

def display_bill_result(image: Image, result: Dict, index: int, sonnet_result: Dict, validation_results: Dict) -> None:  
    """Display results for a single bill with automated accuracy verification"""  
    with st.container():  
        st.markdown(f'<div class="bill-container">', unsafe_allow_html=True)  
        
        col1, col2 = st.columns(2)  
        with col1:
            st.markdown('<div class="document-type-badge bill-badge">BILL/INVOICE</div>', unsafe_allow_html=True)
            st.image(image, caption=f"Bill {index+1}", use_container_width=True)
        
        with col2:  
            # Calculate and display automated accuracy using rule-based validation only
            automated_accuracy = calculate_automated_accuracy(result, None, validation_results)
            
            st.markdown(f"""  
            <div class="accuracy-meter">  
                <div style="font-weight: bold; margin-bottom: 5px;">Rule-Based Validation Score</div>  
                <div style="background: #f0f0f0; border-radius: 10px; height: 20px;">  
                    <div style="background: #2e86c1; width: {automated_accuracy}%; height: 100%; border-radius: 10px;  
                        text-align: center; color: white; font-size: 12px; line-height: 20px;">  
                        {automated_accuracy:.1f}%  
                    </div>  
                </div>  
                <div class="accuracy-value" style="text-align: center; margin-top: 5px;">  
                    {automated_accuracy:.1f}% Validation Passed  
                </div>  
            </div>  
            """, unsafe_allow_html=True)  

            # Display results in table format  
            table_data = {  
                "Field": ["Vendor Name", "Bill Number", "Date", "Total Amount", "Tax Amount",  
                        "GST Number", "Vendor Phone", "Vendor Email", "Customer Name", "Payment Method"],  
                "Extracted Value": [  
                    str(result.get("vendor_name", "N/A")),  
                    str(result.get("bill_number", "N/A")),  
                    str(result.get("date", "N/A")),  
                    f"{result.get('currency', '₹')}{result.get('total_amount', 'N/A')}" if result.get('total_amount', 'N/A') != 'N/A' else 'N/A',  
                    f"{result.get('currency', '₹')}{result.get('tax_amount', 'N/A')}" if result.get('tax_amount', 'N/A') != 'N/A' else 'N/A',  
                    str(result.get("gst_number", "N/A")),  
                    str(result.get("vendor_phone", "N/A")),  
                    str(result.get("vendor_email", "N/A")),  
                    str(result.get("customer_name", "N/A")),  
                    str(result.get("payment_method", "N/A"))  
                ]
            }
            
            df = pd.DataFrame(table_data)  
            st.table(df)  
        
        st.markdown('</div>', unsafe_allow_html=True)

def display_cheque_result(image: Image, result: Dict, index: int, sonnet_result: Dict, validation_results: Dict) -> None:  
    """Display results for a single cheque with automated accuracy verification"""  
    with st.container():  
        st.markdown(f'<div class="cheque-container">', unsafe_allow_html=True)  
        
        col1, col2 = st.columns(2)  
        with col1:
            st.markdown('<div class="document-type-badge cheque-badge">CHEQUE</div>', unsafe_allow_html=True)
            st.image(image, caption=f"Cheque {index+1}", use_container_width=True)
        
        with col2:  
            # Calculate and display automated accuracy using rule-based validation only
            automated_accuracy = calculate_automated_accuracy(result, None, validation_results)
            
            st.markdown(f"""  
            <div class="accuracy-meter">  
                <div style="font-weight: bold; margin-bottom: 5px;">Rule-Based Validation Score</div>  
                <div style="background: #f0f0f0; border-radius: 10px; height: 20px;">  
                    <div style="background: #2e86c1; width: {automated_accuracy}%; height: 100%; border-radius: 10px;  
                        text-align: center; color: white; font-size: 12px; line-height: 20px;">  
                        {automated_accuracy:.1f}%  
                    </div>  
                </div>  
                <div class="accuracy-value" style="text-align: center; margin-top: 5px;">  
                    {automated_accuracy:.1f}% Validation Passed  
                </div>  
            </div>  
            """, unsafe_allow_html=True)  

            # Display results in table format  
            table_data = {  
                "Field": ["Bank Name", "Account Holder", "Account Number", "Amount",  
                        "IFSC Code", "Date", "Signature Present"],  
                "Extracted Value": [  
                    str(result.get("bank", "N/A")),  
                    str(result.get("account_holder", "N/A")),  
                    str(result.get("account_number", "N/A")),  
                    str(result.get("amount", "N/A")),  
                    str(result.get("ifsc_code", "N/A")),  
                    str(result.get("date", "N/A")),  
                    "Yes" if result.get("has_signature", False) else "No"  
                ]
            }
            
            df = pd.DataFrame(table_data)  
            st.table(df)  
        
        st.markdown('</div>', unsafe_allow_html=True)

def to_excel(all_results: List[Dict], all_sonnet_results: List[Dict], all_validations: List[Dict], doc_types: List[str]) -> bytes:  
    """Convert all results to Excel bytes including automated verification data for both cheques and bills"""  
    output = BytesIO()  
    
    # Separate data by document type
    cheque_data = []
    bill_data = []
    
    for i, (result, sonnet_result, validation, doc_type) in enumerate(zip(all_results, all_sonnet_results, all_validations, doc_types)):  
        # Handle case where sonnet_result might be None
        if sonnet_result:
            discrepancies, _ = cross_validate_results(result, sonnet_result)
        else:
            discrepancies = {}
            
        automated_accuracy = calculate_automated_accuracy(result, sonnet_result, validation)
        
        if doc_type == "cheque":
            row_data = {  
                "Cheque No.": len(cheque_data) + 1,  
                "Bank Name": str(result.get("bank", "N/A")),  
                "Account Holder": str(result.get("account_holder", "N/A")),  
                "Account Number": str(result.get("account_number", "N/A")),  
                "Amount": str(result.get("amount", "N/A")),  
                "IFSC Code": str(result.get("ifsc_code", "N/A")),  
                "Date": str(result.get("date", "N/A")),  
                "Signature Present": "Yes" if result.get("has_signature", False) else "No",
                "Rule-Based Accuracy": f"{automated_accuracy:.1f}%",
                "Bank Valid": "Yes" if validation.get("bank", {}).get("valid", False) else "No",
                "Account Number Valid": "Yes" if validation.get("account_number", {}).get("valid", False) else "No",
                "IFSC Valid": "Yes" if validation.get("ifsc_code", {}).get("valid", False) else "No",
                "Date Valid": "Yes" if validation.get("date", {}).get("valid", False) else "No",
                "Amount Valid": "Yes" if validation.get("amount", {}).get("valid", False) else "No"
            }
            
            # Add discrepancy information for cheques
            if sonnet_result:
                for field in ["bank", "account_holder", "account_number", "amount", "ifsc_code", "date"]:
                    row_data[f"{field} Matches"] = "Yes" if field not in discrepancies else "No"
            else:
                for field in ["bank", "account_holder", "account_number", "amount", "ifsc_code", "date"]:
                    row_data[f"{field} Matches"] = "N/A"
            
            cheque_data.append(row_data)
        
        elif doc_type == "bill":
            row_data = {  
                "Bill No.": len(bill_data) + 1,  
                "Vendor Name": str(result.get("vendor_name", "N/A")),  
                "Bill Number": str(result.get("bill_number", "N/A")),  
                "Date": str(result.get("date", "N/A")),  
                "Total Amount": f"{result.get('currency', '₹')}{result.get('total_amount', 'N/A')}" if result.get('total_amount', 'N/A') != 'N/A' else 'N/A',  
                "Tax Amount": f"{result.get('currency', '₹')}{result.get('tax_amount', 'N/A')}" if result.get('tax_amount', 'N/A') != 'N/A' else 'N/A',  
                "GST Number": str(result.get("gst_number", "N/A")),  
                "Vendor Phone": str(result.get("vendor_phone", "N/A")),  
                "Vendor Email": str(result.get("vendor_email", "N/A")),  
                "Customer Name": str(result.get("customer_name", "N/A")),  
                "Payment Method": str(result.get("payment_method", "N/A")),
                "Currency": str(result.get("currency", "₹")),
                "Rule-Based Accuracy": f"{automated_accuracy:.1f}%",
                "Vendor Name Valid": "Yes" if validation.get("vendor_name", {}).get("valid", False) else "No",
                "Bill Number Valid": "Yes" if validation.get("bill_number", {}).get("valid", False) else "No",
                "GST Number Valid": "Yes" if validation.get("gst_number", {}).get("valid", False) else "No",
                "Phone Valid": "Yes" if validation.get("vendor_phone", {}).get("valid", False) else "No",
                "Email Valid": "Yes" if validation.get("vendor_email", {}).get("valid", False) else "No",
                "Date Valid": "Yes" if validation.get("date", {}).get("valid", False) else "No",
                "Amount Valid": "Yes" if validation.get("total_amount", {}).get("valid", False) else "No"
            }
            
            bill_data.append(row_data)
    
    # Create Excel with separate sheets for cheques and bills
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:  
        if cheque_data:
            cheque_df = pd.DataFrame(cheque_data)
            cheque_df.to_excel(writer, index=False, sheet_name='ChequeData')
        
        if bill_data:
            bill_df = pd.DataFrame(bill_data)
            bill_df.to_excel(writer, index=False, sheet_name='BillData')
    
    return output.getvalue()

def upload_to_s3(file_bytes: bytes, s3_key: str, content_type: str = 'image/jpeg') -> str:
    """Upload file bytes to S3 and return public URL"""
    try:
        s3.put_object(
            Bucket=S3_BUCKET_NAME,
            Key=s3_key,
            Body=file_bytes,
            ContentType=content_type
        )
        return f"s3://{S3_BUCKET_NAME}/{s3_key}"
    except Exception as e:
        st.error(f"Failed to upload to S3: {str(e)}")
        return None

def upload_excel_to_s3(excel_bytes: bytes) -> str:
    """Upload Excel file to S3 and return URL"""
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        s3_key = f"excel_reports/cheque_report_{timestamp}.xlsx"
        
        s3.put_object(
            Bucket=S3_BUCKET_NAME,
            Key=s3_key,
            Body=excel_bytes,
            ContentType='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        return f"s3://{S3_BUCKET_NAME}/{s3_key}"
    except Exception as e:
        st.error(f"Failed to upload Excel to S3: {str(e)}")
        return None

def crop_signature_area(image: Image, cheque_id: str) -> str:
    """Crop slightly higher bottom-right corner of cheque image and upload to S3"""
    # Convert to RGB if needed
    if image.mode == 'RGBA':
        image = image.convert('RGB')
        
    width, height = image.size
    left = int(width * 0.75)
    top = int(height * 0.57)
    right = width
    bottom = int(height * 0.92)
    signature = image.crop((left, top, right, bottom))
    
    # Save to bytes instead of local file
    img_byte_arr = BytesIO()
    signature.save(img_byte_arr, format='JPEG')
    img_bytes = img_byte_arr.getvalue()
    
    # Generate unique timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    # Upload to S3 with unique identifier
    s3_key = f"signatures/signature_{timestamp}_{cheque_id}.jpg"
    s3_url = upload_to_s3(img_bytes, s3_key)
    return s3_url

def reset_session_state():
    """Completely reset the session state to initial values"""
    # Clear all existing session state keys
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    
    # Reinitialize the essential session state variables
    st.session_state.update({
        'all_results': [],
        'document_images': [],
        'validation_results': [],
        'document_types': [],
        's3_urls': [],
        'processed_files': set(),
        'file_uploader_key': str(datetime.now().timestamp())  # This will force the file uploader to reset
    })

# --- Main UI ---  
st.markdown('<div class="header">Document Information Extractor - Cheques & Bills</div>', unsafe_allow_html=True)  

# File Upload Section  
uploaded_files = st.file_uploader(  
    "📁 Upload document images - Cheques & Bills (JPEG, PNG)",  
    type=["jpg", "jpeg", "png"],  
    accept_multiple_files=True,  
    key=st.session_state.get('file_uploader_key', 'initial_uploader')  
)

if uploaded_files:
    # Initialize session state if not exists
    if 'all_results' not in st.session_state:
        st.session_state.all_results = []
        st.session_state.document_images = []
        st.session_state.validation_results = []
        st.session_state.document_types = []
        st.session_state.s3_urls = []
        st.session_state.processed_files = set()  # Track processed files
    
    # Get the set of currently uploaded files
    current_files = {file.name for file in uploaded_files}
    
    # Find new files that haven't been processed
    new_files = [file for file in uploaded_files if file.name not in st.session_state.processed_files]
    
    if new_files:
        with st.spinner(f"🔍 Analyzing {len(new_files)} new documents with AI verification..."):
            for i, uploaded_file in enumerate(new_files):
                try:
                    img = Image.open(uploaded_file)
                    # Convert to RGB if needed
                    if img.mode == 'RGBA':
                        img = img.convert('RGB')
                    
                    # Add longer delay between documents to avoid rate limiting
                    if i > 0:  # Don't wait before the first request
                        delay = 5.0 + random.uniform(2.0, 4.0)  # 7-9 second delay between documents
                        st.info(f"⏳ Waiting {delay:.1f} seconds between documents to avoid rate limits...")
                        time.sleep(delay)
                    
                    # Detect document type first
                    doc_type = detect_document_type(img)
                    
                    if doc_type == "unknown":
                        st.error(f"❌ {uploaded_file.name}: Could not identify as cheque or bill. Please upload valid documents.")
                        st.session_state.processed_files.add(uploaded_file.name)
                        continue
                    
                    # Process based on document type
                    if doc_type == "cheque":
                        # Extract cheque data
                        claude_result = extract_cheque_data(img)
                        
                        # Check if the result contains an error message (invalid image)
                        if claude_result and "error" in claude_result:
                            st.error(f"❌ {uploaded_file.name}: {claude_result['error']}")
                            st.session_state.processed_files.add(uploaded_file.name)
                            continue
                        
                        # Validate cheque data
                        validation = validate_cheque_data(claude_result)
                        
                        # Generate unique ID
                        doc_id = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{i}_{claude_result.get('account_number', 'unknown')}"
                        
                        # Save to S3
                        img_byte_arr = BytesIO()
                        img.save(img_byte_arr, format='JPEG')
                        doc_s3_key = f"processed/cheque_{doc_id}.jpg"
                        doc_s3_url = upload_to_s3(img_byte_arr.getvalue(), doc_s3_key)
                        
                        # Crop and save signature to S3
                        sig_s3_url = crop_signature_area(img, doc_id)
                        
                        # Store data
                        st.session_state.all_results.append(claude_result)
                        st.session_state.document_images.append(img)
                        st.session_state.validation_results.append(validation)
                        st.session_state.document_types.append("cheque")
                        st.session_state.s3_urls.append({
                            "document": doc_s3_url,
                            "signature": sig_s3_url
                        })
                    
                    elif doc_type == "bill":
                        # Extract bill data
                        claude_result = extract_bill_data(img)
                        
                        # Check if the result contains an error message (invalid image)
                        if claude_result and "error" in claude_result:
                            st.error(f"❌ {uploaded_file.name}: {claude_result['error']}")
                            st.session_state.processed_files.add(uploaded_file.name)
                            continue
                        
                        # Validate bill data
                        validation = validate_bill_data(claude_result)
                        
                        # Generate unique ID
                        doc_id = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{i}_{claude_result.get('bill_number', 'unknown')}"
                        
                        # Save to S3
                        img_byte_arr = BytesIO()
                        img.save(img_byte_arr, format='JPEG')
                        doc_s3_key = f"processed/bill_{doc_id}.jpg"
                        doc_s3_url = upload_to_s3(img_byte_arr.getvalue(), doc_s3_key)
                        
                        # Store data
                        st.session_state.all_results.append(claude_result)
                        st.session_state.document_images.append(img)
                        st.session_state.validation_results.append(validation)
                        st.session_state.document_types.append("bill")
                        st.session_state.s3_urls.append({
                            "document": doc_s3_url,
                            "signature": None  # Bills don't have signatures
                        })
                    
                    # Mark file as processed
                    st.session_state.processed_files.add(uploaded_file.name)
                
                except Exception as e:  
                    st.error(f"Error processing document {i+1}: {str(e)}")
                    # Still mark as processed to avoid infinite reprocessing attempts
                    st.session_state.processed_files.add(uploaded_file.name)
    
    # Display results if available  
    if st.session_state.all_results:  
        # Document selection dropdown  
        document_options = []
        for i, (result, doc_type) in enumerate(zip(st.session_state.all_results, st.session_state.document_types)):
            if doc_type == "cheque":
                display_name = f"Cheque {i+1} - {result.get('account_holder', 'Unknown')} (₹{result.get('amount', 'N/A')})"
            else:  # bill
                currency = result.get('currency', '₹')
                display_name = f"Bill {i+1} - {result.get('vendor_name', 'Unknown')} ({currency}{result.get('total_amount', 'N/A')})"
            document_options.append(display_name)
        
        selected_document = st.selectbox(  
            "📋 Select Document to View Details:",  
            options=document_options,  
            index=0  
        )  
        
        selected_index = document_options.index(selected_document)
        selected_doc_type = st.session_state.document_types[selected_index]
        
        # Display result based on document type
        if selected_doc_type == "cheque":
            display_cheque_result(  
                st.session_state.document_images[selected_index],  
                st.session_state.all_results[selected_index],  
                selected_index,
                None,
                st.session_state.validation_results[selected_index]
            )
        else:  # bill
            display_bill_result(  
                st.session_state.document_images[selected_index],  
                st.session_state.all_results[selected_index],  
                selected_index,
                None,
                st.session_state.validation_results[selected_index]
            )
        
        # Summary statistics
        cheque_count = st.session_state.document_types.count("cheque")
        bill_count = st.session_state.document_types.count("bill")
        st.success(f"✅ Successfully processed {len(st.session_state.all_results)} documents: {cheque_count} cheques, {bill_count} bills")  
        
        # Action buttons  
        col1, col2 = st.columns(2)  
        
        with col1:  
            # Create empty sonnet results list to match the length of all_results
            empty_sonnet_results = [None] * len(st.session_state.all_results)
            
            excel_file = to_excel(
                st.session_state.all_results,
                empty_sonnet_results,
                st.session_state.validation_results,
                st.session_state.document_types
            )  
            
            # Upload Excel to S3 when generating
            excel_s3_url = upload_excel_to_s3(excel_file)
            
            st.download_button(  
                label="📥 Download All Data (Excel)",  
                data=excel_file,  
                file_name="document_data_with_verification.xlsx",  
                mime="application/vnd.ms-excel"  
            )  
        
        with col2:  
            if st.button("🔄 Clear All Data", key="clear_btn"):  
                reset_session_state()
                st.rerun()