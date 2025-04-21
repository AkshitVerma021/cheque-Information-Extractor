# Cheque Information Extractor - User Guide

## Overview

The Cheque Information Extractor is a powerful tool designed to automatically extract and validate information from bank cheques. This user guide provides step-by-step instructions for using the application effectively.

## Getting Started

### Accessing the Application

The application is accessed through a web browser:

1. Open your preferred web browser
2. Navigate to the application URL provided by your administrator
3. If hosted locally, the default address is typically: http://localhost:8501

## Using the Application

### 1. Home Screen

![Home Screen](../assets/home_screen.png)

The home screen consists of:
- Application header
- File upload section
- Information panel

### 2. Uploading Cheques

To upload cheque images for processing:

1. Click on the "Browse files" button in the upload section
2. Select one or more cheque images (supported formats: JPEG, PNG)
3. The system will automatically begin processing the uploaded images
4. A processing indicator will appear during analysis

**Note**: For optimal results, ensure:
- Images are clear and well-lit
- The entire cheque is visible
- The image is properly oriented

### 3. Viewing Extraction Results

Once processing is complete:

1. A dropdown menu will appear with a list of processed cheques
2. Select any cheque from the dropdown to view detailed results
3. The selected cheque image will be displayed on the left
4. Extracted information will be displayed on the right

### 4. Understanding the Verification Score

Each processed cheque receives an automated verification score:

![Verification Score](../assets/verification_score.png)

- **90-100%**: High confidence in extraction accuracy
- **70-89%**: Good confidence, review recommended
- **Below 70%**: Low confidence, careful review required

The score is calculated based on:
- Cross-validation between two AI models
- Field validation against banking rules

### 5. Reviewing Extracted Data

The extracted data table shows:

| Field | Description |
|-------|-------------|
| Bank Name | Name of the bank that issued the cheque |
| Account Holder | Name of the account holder |
| Account Number | Bank account number |
| Amount | Cheque amount in numbers |
| IFSC Code | Indian Financial System Code |
| Date | Date on the cheque (DD/MM/YYYY) |
| Signature Present | Whether a signature was detected |

### 6. Exporting Data

To export the extraction results:

1. Click the "Download All Data (Excel)" button
2. Save the Excel file to your desired location
3. The Excel report contains:
   - All extracted data
   - Verification scores
   - Validation results

### 7. Clearing Data

To clear all processed data and start fresh:

1. Click the "Clear All Data" button
2. Confirm the action if prompted
3. The application will reset, allowing you to upload new cheques

## Tips for Best Results

1. **Image Quality**: Use high-resolution images for better extraction accuracy
2. **Proper Lighting**: Ensure the cheque is well-lit without glare
3. **Complete View**: Make sure the entire cheque is visible in the image
4. **Multiple Cheques**: Process multiple cheques in a single session for efficiency
5. **Verification**: Always review the extracted data, especially for low confidence scores

## Troubleshooting

### Common Issues

| Issue | Solution |
|-------|----------|
| "Invalid cheque image" error | Ensure the image contains a valid cheque with visible fields |
| Low verification score | Try uploading a clearer image of the cheque |
| Fields showing "N/A" | The field may be illegible or missing in the image |
| Upload not working | Check your internet connection and try again |
| Application seems unresponsive | Refresh the browser and try again |

### Getting Help

If you encounter any issues not addressed in this guide, please contact:
- Technical support: consulting@bellblazetech.com

## Security Best Practices

To ensure the security of sensitive financial information:

1. Close the application when not in use
2. Do not share the application URL with unauthorized users
3. Remember that cheque images and data are stored securely in the system
4. Follow your organization's data handling policies

## Glossary

- **IFSC Code**: Indian Financial System Code, a unique code that identifies a bank branch
- **Verification Score**: Confidence level in the accuracy of extracted information
- **Cross-Validation**: Comparing results from two different AI models
- **Validation Rules**: Banking standards used to verify field formats 