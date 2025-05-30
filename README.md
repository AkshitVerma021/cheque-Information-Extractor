# ChequeAI - Document Information Extractor

An AI-powered document information extraction application that processes both **bank cheques** and **bills/invoices** using Amazon Bedrock's Claude AI models. The application provides automated verification, rule-based validation, and dual-model cross-verification for enhanced accuracy.

## 🆕 New Features

### Bill/Invoice Extraction
- **Automatic Document Type Detection**: AI identifies whether uploaded images are cheques or bills
- **Comprehensive Bill Data Extraction**: Vendor details, amounts, tax information, contact details
- **Bill-Specific Validation**: GST number, email, phone number format validation
- **Dual Processing**: Separate Excel sheets for cheques and bills

### Enhanced UI
- **Multi-Document Support**: Upload and process both cheques and bills in the same session
- **Document Type Badges**: Clear visual indicators for document types
- **Smart Document Selection**: Organized dropdown with document-specific information
- **Real-time Statistics**: Shows count of processed cheques and bills

## 📋 Supported Document Types

### Bank Cheques
Extracts the following information:
- Bank Name
- Account Holder Name
- Account Number
- Amount (numerical and written)
- IFSC Code
- Date
- Signature Presence

### Bills/Invoices
Extracts the following information:
- Vendor/Company Name
- Bill/Invoice Number
- Date
- Total Amount
- Tax/GST Amount
- GST Number
- Vendor Phone Number
- Vendor Email Address
- Customer Name
- Payment Method

## 🚀 Features

### Core Capabilities
- **Multi-Model AI Processing**: Uses both Claude 3 Haiku and Claude 3 Sonnet for enhanced accuracy
- **Automated Document Type Detection**: Intelligently identifies cheques vs bills
- **Real-time Processing**: Immediate extraction with progress tracking
- **Batch Processing**: Handle multiple documents simultaneously
- **Cross-Model Verification**: Compare results between different AI models
- **Rule-Based Validation**: Format validation for specific fields (IFSC, GST, email, phone)

### Data Management
- **AWS S3 Integration**: Automatic storage of processed documents
- **Excel Export**: Comprehensive reports with separate sheets for different document types
- **Automated Accuracy Scoring**: AI-powered confidence metrics
- **Session Management**: Maintains processing state across interactions

### Security & Reliability
- **Rate Limiting Protection**: Intelligent retry logic with exponential backoff
- **Error Handling**: Graceful failure management
- **Data Validation**: Multiple layers of verification
- **Cloud Storage**: Secure S3 integration for document archival

## 🛠️ Technology Stack

- **Frontend**: Streamlit
- **AI Models**: Amazon Bedrock (Claude 3 Haiku & Sonnet)
- **Cloud Services**: AWS S3, AWS Bedrock
- **Image Processing**: PIL (Python Imaging Library)
- **Data Processing**: Pandas, JSON
- **File Formats**: Excel export with xlsxwriter

## 📊 Validation Rules

### Cheque Validation
- **Bank Names**: Predefined patterns for major Indian banks
- **IFSC Codes**: 11-character alphanumeric format validation
- **Account Numbers**: 9-18 digit validation
- **Dates**: DD/MM/YYYY format with actual date validation
- **Amounts**: Positive number validation

### Bill Validation
- **GST Numbers**: 15-character GST format validation
- **Email Addresses**: RFC-compliant email format validation
- **Phone Numbers**: International and Indian phone number formats
- **Bill Numbers**: Alphanumeric format validation (5-20 characters)
- **Vendor Information**: Length and format validation

## 🔧 Setup Instructions

### Prerequisites
- Python 3.8+
- AWS Account with Bedrock access
- Required Python packages (see requirements.txt)

### Environment Variables
Create a `.env` file with:
```env
AWS_REGION=your-aws-region
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
S3_BUCKET_NAME=your-s3-bucket
```

### Installation
```bash
# Clone the repository
git clone <repository-url>
cd cheque-extractor

# Install dependencies
pip install -r requirements.txt

# Run the application
python -m streamlit run main.py 
```

## 📱 Usage

1. **Upload Documents**: Select cheque images or bill/invoice images (JPEG, PNG)
2. **Automatic Processing**: AI detects document type and extracts information
3. **Review Results**: View extracted data with accuracy scores
4. **Validation Check**: See rule-based validation results
5. **Export Data**: Download comprehensive Excel reports
6. **Cloud Storage**: Documents automatically saved to S3

## 📈 Output Format

### Excel Report Structure
- **ChequeData Sheet**: All cheque information with validation results
- **BillData Sheet**: All bill/invoice information with validation results
- **Verification Metrics**: Dual-model comparison and accuracy scores
- **Validation Status**: Field-by-field validation results

### Data Fields Per Document Type

#### Cheques
- Document identification and banking details
- Amount extraction (numerical and written)
- Signature detection and validation
- Cross-model verification scores

#### Bills/Invoices
- Vendor and customer information
- Financial details (amounts, taxes)
- Contact information validation
- Payment method identification

## 🔍 Accuracy Features

- **Dual Model Verification**: Compare results between Claude Haiku and Sonnet
- **Automated Accuracy Scoring**: Weighted combination of cross-validation and rule-based checks
- **Confidence Metrics**: Real-time accuracy percentages
- **Error Detection**: Identify and flag potential extraction errors

## 📄 File Support

- **Image Formats**: JPEG, PNG
- **Batch Processing**: Multiple files simultaneously
- **Size Optimization**: Automatic compression for large images
- **Quality Preservation**: Maintains extraction accuracy

## 🏗️ Architecture

```
User Upload → Document Type Detection → AI Extraction → Validation → S3 Storage → Excel Export
                     ↓                        ↓              ↓
                 Cheque/Bill            Dual Models     Rule-Based
                 Detection              (Haiku/Sonnet)  Validation
```

## 🔐 Security Considerations

- AWS credentials management via environment variables
- Secure S3 storage with proper access controls
- No local storage of sensitive document data
- Rate limiting to prevent abuse

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📞 Support

For issues, feature requests, or questions:
- Create an issue in the repository
- Check existing documentation
- Review validation rules for field-specific requirements

## 🔄 Version History

- **v2.0**: Added bill/invoice extraction functionality
- **v1.0**: Initial cheque extraction capabilities

---

**Note**: This application requires valid AWS credentials and Bedrock access for Claude AI models. Ensure your AWS account has the necessary permissions for Bedrock and S3 services.

