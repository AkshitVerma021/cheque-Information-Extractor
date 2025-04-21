import re
from datetime import datetime
from typing import Dict, Tuple

from app.models.cheque_data import ChequeData, ChequeValidation, ValidationResult
from config.config import BANK_NAME_PATTERNS, IFSC_CODE_PATTERN, ACCOUNT_NUMBER_PATTERN, DATE_PATTERN

class ChequeValidator:
    @staticmethod
    def validate_cheque_data(data: ChequeData) -> ChequeValidation:
        """Apply rule-based validation to extracted cheque data"""
        validation_results = {
            "bank": {"valid": False, "message": ""},
            "account_number": {"valid": False, "message": ""},
            "ifsc_code": {"valid": False, "message": ""},
            "date": {"valid": False, "message": ""},
            "amount": {"valid": False, "message": ""}
        }
        
        # Bank name validation
        if data.bank != 'N/A':
            bank_name = str(data.bank).upper()
            validation_results['bank']['valid'] = any(re.search(pattern, bank_name) for pattern in BANK_NAME_PATTERNS)
            if not validation_results['bank']['valid']:
                validation_results['bank']['message'] = "Bank name doesn't match known patterns"
        
        # Account number validation
        account_num = str(data.account_number)
        if account_num and account_num != 'N/A':
            validation_results['account_number']['valid'] = bool(re.fullmatch(ACCOUNT_NUMBER_PATTERN, account_num))
            if not validation_results['account_number']['valid']:
                validation_results['account_number']['message'] = "Account number format invalid (should be 9-18 digits)"
        
        # IFSC code validation
        ifsc = str(data.ifsc_code)
        if ifsc and ifsc != 'N/A':
            validation_results['ifsc_code']['valid'] = bool(re.fullmatch(IFSC_CODE_PATTERN, ifsc))
            if not validation_results['ifsc_code']['valid']:
                validation_results['ifsc_code']['message'] = "IFSC code format invalid (should be 11 alphanumeric characters)"
        
        # Date validation
        date_str = str(data.date)
        if date_str and date_str != 'N/A':
            validation_results['date']['valid'] = bool(re.fullmatch(DATE_PATTERN, date_str))
            if validation_results['date']['valid']:
                try:
                    day, month, year = map(int, date_str.split('/'))
                    datetime(year=year, month=month, day=day)
                except ValueError:
                    validation_results['date']['valid'] = False
                    validation_results['date']['message'] = "Invalid date (should be DD/MM/YYYY and a valid date)"
            else:
                validation_results['date']['message'] = "Date format invalid (should be DD/MM/YYYY)"
        
        # Amount validation
        amount = data.amount
        if amount != 'N/A':
            try:
                amount_num = int(amount)
                validation_results['amount']['valid'] = amount_num > 0
                if not validation_results['amount']['valid']:
                    validation_results['amount']['message'] = "Amount should be positive"
            except (ValueError, TypeError):
                validation_results['amount']['valid'] = False
                validation_results['amount']['message'] = "Amount should be a valid number"
        
        return ChequeValidation.from_dict(validation_results)
    
    @staticmethod
    def cross_validate_results(haiku_result: ChequeData, sonnet_result: ChequeData) -> Tuple[Dict, float]:
        """Compare results from Claude Haiku and Claude Sonnet to identify discrepancies"""
        if not haiku_result or not sonnet_result:
            return {}, 0.0
        
        fields = ["bank", "account_holder", "account_number", "amount", "ifsc_code", "date", "has_signature"]
        discrepancies = {}
        matching_fields = 0
        
        for field in fields:
            haiku_val = getattr(haiku_result, field, "N/A")
            sonnet_val = getattr(sonnet_result, field, "N/A")
            
            # Special handling for numeric fields
            if field == "amount":
                haiku_val = str(haiku_val) if haiku_val != "N/A" else "N/A"
                sonnet_val = str(sonnet_val) if sonnet_val != "N/A" else "N/A"
            
            if haiku_val != sonnet_val:
                discrepancies[field] = {
                    "haiku": haiku_val,
                    "sonnet": sonnet_val
                }
            else:
                matching_fields += 1
        
        confidence_score = (matching_fields / len(fields)) * 100
        return discrepancies, confidence_score
    
    @staticmethod
    def calculate_automated_accuracy(haiku_result: ChequeData, sonnet_result: ChequeData, validation_results: ChequeValidation) -> float:
        """Calculate automated accuracy score combining cross-validation and rule-based checks"""
        if not haiku_result:
            return 0.0
        
        # Weightings for different components
        CROSS_VALIDATION_WEIGHT = 0.6
        RULE_BASED_WEIGHT = 0.4
        
        # Get cross-validation score
        _, cross_val_score = ChequeValidator.cross_validate_results(haiku_result, sonnet_result)
        
        # Calculate rule-based validation score
        rule_based_score = 0
        if validation_results:
            validation_dict = validation_results.to_dict()
            valid_fields = sum(1 for field in validation_dict.values() if field['valid'])
            total_fields = len(validation_dict)
            rule_based_score = (valid_fields / total_fields) * 100 if total_fields > 0 else 0
        
        # Combine scores with weights
        combined_score = (cross_val_score * CROSS_VALIDATION_WEIGHT) + (rule_based_score * RULE_BASED_WEIGHT)
        
        return combined_score 