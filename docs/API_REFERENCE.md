# Cheque Information Extractor - API Reference

This document provides detailed information about the internal APIs of the Cheque Information Extractor application. It serves as a reference for developers who need to understand, maintain, or extend the application's functionality.

## Table of Contents

1. [Data Models](#1-data-models)
2. [AI Service](#2-ai-service)
3. [S3 Service](#3-s3-service)
4. [Validator](#4-validator)
5. [Processor](#5-processor)
6. [Session Manager](#6-session-manager)
7. [Export Utilities](#7-export-utilities)
8. [UI Components](#8-ui-components)
9. [Integration Points](#9-integration-points)

## 1. Data Models

### `ChequeData` Class

Represents extracted information from a cheque.

```python
@dataclass
class ChequeData:
    bank: str
    account_holder: str
    account_number: str
    amount: Any  # Can be int or str ("N/A")
    ifsc_code: str
    date: str
    has_signature: bool
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'ChequeData'
    
    def to_dict(self) -> Dict
```

### `ValidationResult` Class

Represents the validation result for a single field.

```python
@dataclass
class ValidationResult:
    valid: bool
    message: str
```

### `ChequeValidation` Class

Represents validation results for all fields in a cheque.

```python
@dataclass
class ChequeValidation:
    bank: ValidationResult
    account_number: ValidationResult
    ifsc_code: ValidationResult
    date: ValidationResult
    amount: ValidationResult
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'ChequeValidation'
    
    def to_dict(self) -> Dict
```

### `ProcessedCheque` Class

Represents a fully processed cheque with all associated data.

```python
@dataclass
class ProcessedCheque:
    image: Image.Image
    data: ChequeData
    sonnet_data: ChequeData
    validation: ChequeValidation
    s3_urls: Dict[str, str]
    
    def display_name(self, index: int) -> str
```

## 2. AI Service

The `AIService` class handles all interactions with the Claude AI models through AWS Bedrock.

### Key Methods

```python
class AIService:
    def __init__(self)
    
    def _prepare_image(self, image: Image.Image) -> str
    """Convert image to base64 encoded string with compression if needed"""
    
    def _validate_cheque_image(self, encoded_image: str, model_id: str) -> bool
    """Check if the image is a valid cheque"""
    
    def _extract_json_from_response(self, response_text: str) -> Dict
    """Extract JSON from model response text"""
    
    def _clean_extraction_result(self, result: Dict) -> Dict
    """Clean and normalize extraction result"""
    
    def _process_extraction(self, image: Image.Image, model_id: str, prompt: str) -> Optional[Dict]
    """Process image extraction with specified model and prompt"""
    
    def extract_with_haiku(self, image: Image.Image) -> Optional[Dict]
    """Extract cheque data using Claude 3 Haiku"""
    
    def extract_with_sonnet(self, image: Image.Image) -> Optional[Dict]
    """Extract cheque data using Claude 3 Sonnet"""
```

### Usage Example

```python
from app.services.ai_service import AIService
from PIL import Image

# Initialize the service
ai_service = AIService()

# Load an image
image = Image.open("path/to/cheque.jpg")

# Extract data using Haiku model
result = ai_service.extract_with_haiku(image)

# Extract data using Sonnet model for cross-validation
sonnet_result = ai_service.extract_with_sonnet(image)
```

## 3. S3 Service

The `S3Service` class handles interactions with AWS S3 for storage of images and reports.

### Key Methods

```python
class S3Service:
    def __init__(self)
    
    def upload_image(self, image: Image.Image, s3_key: str, content_type: str = 'image/jpeg') -> Optional[str]
    """Upload PIL Image to S3 and return public URL"""
    
    def upload_bytes(self, file_bytes: bytes, s3_key: str, content_type: str) -> Optional[str]
    """Upload bytes to S3 and return public URL"""
    
    def upload_excel(self, excel_bytes: bytes) -> Optional[str]
    """Upload Excel file to S3 and return URL"""
    
    def crop_and_upload_signature(self, image: Image.Image, cheque_id: str) -> Optional[str]
    """Crop signature area from cheque image and upload to S3"""
```

### Usage Example

```python
from app.services.s3_service import S3Service
from PIL import Image

# Initialize service
s3_service = S3Service()

# Upload an image
image = Image.open("path/to/cheque.jpg")
s3_url = s3_service.upload_image(image, "cheques/my_cheque.jpg")

# Extract and upload signature
signature_url = s3_service.crop_and_upload_signature(image, "cheque123")

# Upload an Excel file
with open("report.xlsx", "rb") as f:
    excel_bytes = f.read()
    excel_url = s3_service.upload_excel(excel_bytes)
```

## 4. Validator

The `ChequeValidator` class provides methods for validating cheque data against banking rules.

### Key Methods

```python
class ChequeValidator:
    @staticmethod
    def validate_cheque_data(data: ChequeData) -> ChequeValidation
    """Apply rule-based validation to extracted cheque data"""
    
    @staticmethod
    def cross_validate_results(haiku_result: ChequeData, sonnet_result: ChequeData) -> Tuple[Dict, float]
    """Compare results from Claude Haiku and Claude Sonnet to identify discrepancies"""
    
    @staticmethod
    def calculate_automated_accuracy(haiku_result: ChequeData, sonnet_result: ChequeData, validation_results: ChequeValidation) -> float
    """Calculate automated accuracy score combining cross-validation and rule-based checks"""
```

### Usage Example

```python
from app.validators.cheque_validator import ChequeValidator
from app.models.cheque_data import ChequeData

# Validate data
validation_results = ChequeValidator.validate_cheque_data(cheque_data)

# Cross-validate results from two models
discrepancies, confidence_score = ChequeValidator.cross_validate_results(haiku_result, sonnet_result)

# Calculate overall accuracy
accuracy = ChequeValidator.calculate_automated_accuracy(haiku_result, sonnet_result, validation_results)
```

## 5. Processor

The `ChequeProcessor` class orchestrates the entire processing workflow.

### Key Methods

```python
class ChequeProcessor:
    def __init__(self)
    
    def process_cheque(self, image: Image.Image, file_name: str) -> Optional[ProcessedCheque]
    """Process a single cheque image through the extraction pipeline"""
    
    def process_batch(self, uploaded_files: List) -> List[ProcessedCheque]
    """Process a batch of uploaded cheque images"""
```

### Usage Example

```python
from app.utils.processor import ChequeProcessor
from PIL import Image

# Initialize processor
processor = ChequeProcessor()

# Process a single cheque
image = Image.open("path/to/cheque.jpg")
processed_cheque = processor.process_cheque(image, "cheque.jpg")

# Or process multiple cheques from Streamlit uploaded files
processed_cheques = processor.process_batch(uploaded_files)
```

## 6. Session Manager

The `SessionManager` class handles Streamlit session state management.

### Key Methods

```python
class SessionManager:
    @staticmethod
    def initialize_session()
    """Initialize session state with default values if not already present"""
    
    @staticmethod
    def reset_session()
    """Reset session state to initial values"""
    
    @staticmethod
    def add_processed_cheque(processed_cheque: ProcessedCheque, file_name: str)
    """Add processed cheque to session state"""
    
    @staticmethod
    def get_processed_cheques() -> List[ProcessedCheque]
    """Get list of processed cheques from session state"""
    
    @staticmethod
    def get_processed_files() -> Set[str]
    """Get set of processed file names from session state"""
    
    @staticmethod
    def get_file_uploader_key() -> str
    """Get unique key for file uploader"""
```

### Usage Example

```python
from app.utils.session_manager import SessionManager

# Initialize session
SessionManager.initialize_session()

# Store a processed cheque
SessionManager.add_processed_cheque(processed_cheque, "cheque.jpg")

# Get processed cheques
cheques = SessionManager.get_processed_cheques()

# Reset session
SessionManager.reset_session()
```

## 7. Export Utilities

The `export_utils` module provides functions for exporting processed data.

### Key Functions

```python
def to_excel(processed_cheques: List[ProcessedCheque]) -> Tuple[bytes, str]
"""
Convert processed cheques data to Excel bytes including automated verification data
Returns tuple of (excel_bytes, s3_url)
"""
```

### Usage Example

```python
from app.utils.export_utils import to_excel

# Generate Excel file
excel_bytes, s3_url = to_excel(processed_cheques)

# Use the bytes for download
streamlit.download_button(label="Download Excel", data=excel_bytes, file_name="report.xlsx")
```

## 8. UI Components

The `display` module handles UI rendering.

### Key Functions

```python
def setup_page()
"""Set up Streamlit page with title, logo, and CSS"""

def display_cheque_result(processed_cheque: ProcessedCheque, index: int) -> None
"""Display results for a single cheque with automated accuracy verification"""

def display_action_buttons(excel_bytes: bytes, on_clear, excel_s3_url: Optional[str] = None)
"""Display action buttons for download and clear"""

def display_results(processed_cheques: List[ProcessedCheque], excel_bytes: bytes, on_clear, excel_s3_url: Optional[str] = None)
"""Display the results section including cheque selector and details"""
```

### Usage Example

```python
from app.ui.display import setup_page, display_results

# Setup the page
setup_page()

# Display results
display_results(
    processed_cheques,
    excel_bytes,
    on_clear=lambda: SessionManager.reset_session(),
    excel_s3_url=s3_url
)
```

## 9. Integration Points

### Adding New AI Models

To add a new AI model, extend the `AIService` class:

1. Add a new model ID in `config/config.py`
2. Create a new extraction method in `AIService`

Example:

```python
def extract_with_new_model(self, image: Image.Image) -> Optional[Dict]:
    """Extract cheque data using a new AI model"""
    prompt = """Your custom prompt for the new model"""
    return self._process_extraction(image, NEW_MODEL_ID, prompt)
```

### Supporting New Export Formats

To add new export formats:

1. Create a new function in `export_utils.py`
2. Update the UI to include the new export option

Example:

```python
def to_pdf(processed_cheques: List[ProcessedCheque]) -> bytes:
    """Convert processed cheques data to PDF"""
    # PDF generation code
    return pdf_bytes
```

### Adding New Validation Rules

To add new validation rules:

1. Add new patterns in `config/config.py`
2. Extend the `validate_cheque_data` method in `ChequeValidator`

Example:

```python
# In config.py
MICR_CODE_PATTERN = r'^[0-9]{9}$'

# In ChequeValidator
if data.micr_code and data.micr_code != 'N/A':
    validation_results['micr_code']['valid'] = bool(re.fullmatch(MICR_CODE_PATTERN, data.micr_code))
``` 