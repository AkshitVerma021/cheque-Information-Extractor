import pandas as pd
from io import BytesIO
from typing import List, Tuple
from datetime import datetime

from app.models.cheque_data import ProcessedCheque
from app.validators.cheque_validator import ChequeValidator
from app.services.s3_service import S3Service

def to_excel(processed_cheques: List[ProcessedCheque]) -> Tuple[bytes, str]:
    """
    Convert processed cheques data to Excel bytes including automated verification data
    Returns tuple of (excel_bytes, s3_url)
    """
    output = BytesIO()
    
    # Prepare data for Excel
    excel_data = []
    for i, cheque in enumerate(processed_cheques):
        discrepancies, _ = ChequeValidator.cross_validate_results(cheque.data, cheque.sonnet_data)
        automated_accuracy = ChequeValidator.calculate_automated_accuracy(cheque.data, cheque.sonnet_data, cheque.validation)
        
        validation_dict = cheque.validation.to_dict() if cheque.validation else {}
        
        row_data = {
            "Cheque No.": i+1,
            "Bank Name": cheque.data.bank,
            "Account Holder": cheque.data.account_holder,
            "Account Number": cheque.data.account_number,
            "Amount": cheque.data.amount,
            "IFSC Code": cheque.data.ifsc_code,
            "Date": cheque.data.date,
            "Signature Present": "Yes" if cheque.data.has_signature else "No",
            "Automated Accuracy": f"{automated_accuracy:.1f}%",
            "Bank Valid": "Yes" if validation_dict.get("bank", {}).get("valid", False) else "No",
            "Account Number Valid": "Yes" if validation_dict.get("account_number", {}).get("valid", False) else "No",
            "IFSC Valid": "Yes" if validation_dict.get("ifsc_code", {}).get("valid", False) else "No",
            "Date Valid": "Yes" if validation_dict.get("date", {}).get("valid", False) else "No",
            "Amount Valid": "Yes" if validation_dict.get("amount", {}).get("valid", False) else "No"
        }
        
        # Add discrepancy information
        for field in ["bank", "account_holder", "account_number", "amount", "ifsc_code", "date"]:
            row_data[f"{field} Matches"] = "Yes" if field not in discrepancies else "No"
        
        excel_data.append(row_data)
    
    df = pd.DataFrame(excel_data)
    
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='ChequeData')
    
    excel_bytes = output.getvalue()
    
    # Upload to S3
    s3_service = S3Service()
    s3_url = s3_service.upload_excel(excel_bytes)
    
    return excel_bytes, s3_url 