# Cheque Information Extractor - Technical Documentation

## 1. Introduction

The Cheque Information Extractor is an enterprise-grade application designed to automate the extraction and verification of information from bank cheques. Using advanced AI technologies, the application extracts critical data such as account numbers, bank names, dates, and amounts with high accuracy while providing robust validation mechanisms.

### 1.1 Purpose

This application addresses the following business needs:
- Reduce manual data entry from physical cheques
- Minimize human error in cheque processing
- Accelerate financial workflows
- Create systematic digital records of processed cheques
- Securely store cheque data and extracted information

### 1.2 Key Features

- **Dual AI Verification**: Uses two independent AI models (Claude 3 Haiku and Claude 3 Sonnet) to cross-validate extracted information
- **Automated Validation**: Applies banking industry rules to verify field correctness
- **Signature Region Extraction**: Automatically isolates and stores signature areas for further verification or analysis
- **Excel Report Generation**: Creates comprehensive Excel reports of all processed cheques
- **AWS S3 Integration**: Securely stores processed images and reports in the cloud
- **Confidence Scoring**: Applies a confidence score to assess extraction reliability

## 2. System Architecture

### 2.1 Architecture Overview

The application follows a modular architecture pattern with distinct separation of concerns:

```
Cheque-Extractor/
├── app/
│   ├── models/       # Data structures and domain models
│   ├── services/     # Service layer for external integrations (AI, S3)
│   ├── validators/   # Data validation components
│   ├── utils/        # Utility functions and helpers
│   ├── ui/           # User interface components
│   └── main.py       # Main application orchestration
├── config/           # Configuration settings
├── main.py           # Application entry point
└── README.md         # Basic documentation
```

### 2.2 Component Descriptions

#### 2.2.1 Models
Contains data models that represent the domain entities:
- `ChequeData`: Represents extracted cheque information
- `ValidationResult`: Represents field validation results
- `ChequeValidation`: Collection of validation results for a cheque
- `ProcessedCheque`: Complete representation of a processed cheque including image and results

#### 2.2.2 Services
Handles integration with external systems:
- `AIService`: Manages interactions with Claude AI models
- `S3Service`: Manages AWS S3 storage operations

#### 2.2.3 Validators
Provides data validation logic:
- `ChequeValidator`: Validates extracted cheque data against banking rules

#### 2.2.4 Utils
Provides utility functions:
- `SessionManager`: Manages Streamlit session state
- `Processor`: Orchestrates the cheque processing workflow
- `ExportUtils`: Handles export functions like Excel generation

#### 2.2.5 UI
Manages the user interface components:
- `Display`: Controls the rendering of UI elements

## 3. Technical Implementation

### 3.1 AI Models

The application leverages two Claude 3 AI models for information extraction:

- **Claude 3 Haiku**: A fast, efficient model used as the primary extractor
- **Claude 3 Sonnet**: A more powerful model used to cross-validate extraction results

Both models are accessed through AWS Bedrock, which provides a secure and scalable API for AI inference.

### 3.2 Storage

AWS S3 is used for persistent storage of:
- Original cheque images
- Extracted signature regions
- Generated Excel reports

Files are organized in the following S3 folder structure:
- `/processed/` - Full cheque images
- `/signatures/` - Extracted signature regions
- `/excel_reports/` - Generated Excel reports

### 3.3 Data Flow

1. User uploads cheque image(s)
2. Images are validated as legitimate cheques
3. Primary extraction is performed using Claude 3 Haiku
4. Secondary extraction is performed using Claude 3 Sonnet
5. Results are cross-validated for discrepancies
6. Field-level validation is applied using banking rules
7. Confidence score is calculated based on validation results
8. Signature region is extracted and stored separately
9. All data is stored in session state for UI display
10. Excel report is generated and uploaded to S3

## 4. Installation and Configuration

### 4.1 Prerequisites

- Python 3.8 or higher
- AWS account with access to Bedrock and S3
- Appropriate IAM permissions

### 4.2 Installation Steps

1. Clone the repository:
   ```bash
   git clone https://github.com/yourdomain/cheque-extractor.git
   cd cheque-extractor
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Create a `.env` file with the following environment variables:
   ```
   AWS_REGION=your-region
   AWS_ACCESS_KEY_ID=your-access-key
   AWS_SECRET_ACCESS_KEY=your-secret-key
   S3_BUCKET_NAME=your-bucket-name
   ```

### 4.3 Configuration Options

The application's behavior can be configured through several parameters in the `config/config.py` file:

- **AWS Configuration**: Connection details for AWS services
- **Model Configuration**: Model IDs and parameters
- **Validation Patterns**: Regular expressions for validating bank data
- **UI Styling**: CSS styles for the Streamlit interface

## 5. User Guide

### 5.1 Starting the Application

Run the application with the following command:

```bash
streamlit run main.py
```

This will start the Streamlit server and open the application in your default web browser.

### 5.2 Processing Cheques

1. **Upload**: Click the file upload area to select one or more cheque images (JPEG or PNG format)
2. **Processing**: The system will automatically process the uploaded images
3. **Review**: Use the dropdown selector to view individual cheque results
4. **Verification**: Check the automated verification score and field validations
5. **Export**: Download the Excel report containing all extracted information
6. **Reset**: Clear all processed data using the "Clear All Data" button if needed

### 5.3 Understanding the Results

- **Verification Score**: Indicates the confidence level based on cross-validation and rule checks
- **Field Values**: Shows extracted values for each field
- **Field Validation**: Fields are validated against banking rules (not displayed directly)

## 6. Security Considerations

### 6.1 Data Security

- All uploaded images and extracted data are processed in memory
- Persistent storage is exclusively on AWS S3 with appropriate security controls
- No cheque data is stored in databases or logs
- Authentication is managed through AWS credentials

### 6.2 Access Control

- AWS IAM policies should be configured to restrict access to the S3 bucket
- Application access should be controlled through network security measures
- Consider implementing Streamlit authentication for production deployments

## 7. Performance and Scaling

### 7.1 Performance Considerations

- Image compression is automatically applied for large images
- AI model inference times vary based on image complexity
- Processing time increases linearly with the number of uploaded cheques

### 7.2 Scaling Approaches

For high-volume processing:
- Deploy in container environments like Docker/Kubernetes
- Implement job queuing for asynchronous processing
- Consider using AWS Lambda for serverless scaling
- Implement load balancing for multi-user deployments

## 8. Maintenance and Support

### 8.1 Logging

The application uses Streamlit's built-in logging mechanisms. For production, consider implementing more comprehensive logging with:
- Log rotation
- Structured logging
- Centralized log collection
- Error alerting

### 8.2 Common Issues and Troubleshooting

| Issue | Possible Cause | Resolution |
|-------|---------------|------------|
| Invalid cheque image error | Image doesn't contain recognizable cheque elements | Ensure uploaded image is a clear, complete cheque |
| Low confidence score | Poor image quality or unusual cheque format | Try improving image quality or manual data entry |
| AWS connectivity errors | Invalid credentials or network issues | Check AWS credentials and network connectivity |
| Session expiration | Streamlit session timeout | Refresh the application and reupload files |

### 8.3 Support Contact

For technical support or assistance, please contact:
- consulting@bellblazetech.com

## 9. Future Development

Potential enhancements for future versions:

1. **Multi-user support**: User authentication and role-based access control
2. **Batch processing**: Background job processing for large volumes
3. **API Integration**: REST API for integration with other systems
4. **Advanced reporting**: Generate PDF reports with visual elements
5. **Signature verification**: Implement signature matching algorithms
6. **Additional validations**: More sophisticated banking rule validations
7. **Internationalization**: Support for cheques from multiple countries/languages

## 10. License and Legal Information

This application is proprietary software owned by BellBlaze Technologies.
All rights reserved.

## Appendix A: Field Validation Rules

| Field | Validation Rule |
|-------|----------------|
| Bank Name | Must match known bank name patterns |
| Account Number | Must be 9-18 digits |
| IFSC Code | Must follow pattern: [A-Z]{4}0[A-Z0-9]{6} |
| Date | Must be in DD/MM/YYYY format and a valid date |
| Amount | Must be a positive number |

## Appendix B: Troubleshooting Decision Tree

```
Error during cheque processing
├── Image validation fails
│   ├── Check image quality
│   └── Verify image contains cheque elements
├── AWS connection error
│   ├── Check AWS credentials
│   ├── Verify network connectivity
│   └── Check AWS service status
├── Low confidence score
│   ├── Check image quality
│   ├── Check for unusual cheque format
│   └── Verify extracted data manually
└── Application error
    ├── Check log files
    ├── Restart application
    └── Contact technical support
``` 