import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# AWS Configuration
AWS_REGION = os.getenv("AWS_REGION")
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME")

# Model Configuration
CLAUDE_SONNET_MODEL_ID = "anthropic.claude-3-sonnet-20240229-v1:0"
CLAUDE_HAIKU_MODEL_ID = "anthropic.claude-3-haiku-20240307-v1:0"

# Validation Patterns
BANK_NAME_PATTERNS = [
    r'STATE BANK OF INDIA', r'SBI', r'HDFC BANK', r'ICICI BANK', 
    r'AXIS BANK', r'PUNJAB NATIONAL BANK', r'PNB', r'CANARA BANK',
    r'BANK OF BARODA', r'BOB', r'UNION BANK OF INDIA'
]

IFSC_CODE_PATTERN = r'^[A-Z]{4}0[A-Z0-9]{6}$'
ACCOUNT_NUMBER_PATTERN = r'^\d{9,18}$'
DATE_PATTERN = r'^\d{2}/\d{2}/\d{4}$'

# CSS Styles
CSS_STYLES = """
<style>  
.header { font-size: 2.5em; color: #2e86c1; text-align: center; padding: 20px; border-bottom: 2px solid #3498db; margin-bottom: 30px; }  
.upload-box { border: 2px dashed #3498db; border-radius: 5px; padding: 20px; text-align: center; }  
.result-box { margin-top: 20px; padding: 20px; border: 1px solid #3498db; border-radius: 5px; background-color: #f8f9fa; }  
.clear-btn { margin-top: 20px; }  
.data-table { width: 100%; margin-top: 20px; }  
.cheque-container { margin-bottom: 30px; padding: 15px; border: 1px solid #eee; border-radius: 5px; }  
.stButton>button, .stDownloadButton>button { background-color: #2e86c1 !important; color: white !important; border: none !important; width: 100%; margin: 5px 0 !important; transition: background-color 0.3s; }  
.stButton>button:hover, .stDownloadButton>button:hover { background-color: #2874a6 !important; }  
.stButton, .stDownloadButton { display: flex; justify-content: center; }  
.accuracy-meter { margin-bottom: 20px; }  
.accuracy-value { font-weight: bold; color: #2e86c1; }  
.discrepancy { color: #e74c3c; font-weight: bold; }  
.validation-pass { color: #27ae60; font-weight: bold; }  
</style>
""" 