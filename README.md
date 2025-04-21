# Cheque Information Extractor

An intelligent application that extracts information from cheque images using Claude 3 AI models.

## Features

- **Dual Model Verification**: Uses both Claude 3 Haiku and Claude 3 Sonnet for cross-verification of extracted data
- **Automated Validation**: Applies banking rules to validate extracted fields
- **Signature Region Extraction**: Automatically crops and saves signature areas
- **Excel Export**: Generate comprehensive reports with validation data
- **S3 Storage Integration**: Save processed images and reports to AWS S3

## Structure

The application follows a modular architecture:

```
Cheque-Extractor/
├── app/
│   ├── models/         # Data structures
│   ├── services/       # External services (AI, S3)
│   ├── validators/     # Data validation
│   ├── utils/          # Utility functions
│   ├── ui/             # UI components
│   └── main.py         # Main application logic
├── config/             # Configuration settings
├── main.py             # Application entry point
└── README.md           # Documentation
```

## Installation

1. Clone the repository
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Create a `.env` file with the following variables:
   ```
   AWS_REGION=your-region
   AWS_ACCESS_KEY_ID=your-access-key
   AWS_SECRET_ACCESS_KEY=your-secret-key
   S3_BUCKET_NAME=your-bucket-name
   ```

## Usage

Run the application:

```
streamlit run main.py
```

## Technology Stack

- **Streamlit**: Web interface
- **AWS Bedrock**: AI model access (Claude 3 Haiku & Sonnet)
- **AWS S3**: Storage for images and reports
- **Python**: Core language
- **Pandas**: Data processing

