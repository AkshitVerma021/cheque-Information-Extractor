from typing import Dict, Optional, Any
from dataclasses import dataclass
from PIL import Image

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
    def from_dict(cls, data: Dict) -> 'ChequeData':
        """Create ChequeData from dictionary"""
        return cls(
            bank=data.get("bank", "N/A"),
            account_holder=data.get("account_holder", "N/A"),
            account_number=data.get("account_number", "N/A"),
            amount=data.get("amount", "N/A"),
            ifsc_code=data.get("ifsc_code", "N/A"),
            date=data.get("date", "N/A"),
            has_signature=data.get("has_signature", False)
        )
    
    def to_dict(self) -> Dict:
        """Convert ChequeData to dictionary"""
        return {
            "bank": self.bank,
            "account_holder": self.account_holder,
            "account_number": self.account_number,
            "amount": self.amount,
            "ifsc_code": self.ifsc_code,
            "date": self.date,
            "has_signature": self.has_signature
        }

@dataclass
class ValidationResult:
    valid: bool
    message: str

@dataclass
class ChequeValidation:
    bank: ValidationResult
    account_number: ValidationResult
    ifsc_code: ValidationResult
    date: ValidationResult
    amount: ValidationResult
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'ChequeValidation':
        """Create ChequeValidation from dictionary"""
        return cls(
            bank=ValidationResult(**data.get("bank", {"valid": False, "message": ""})),
            account_number=ValidationResult(**data.get("account_number", {"valid": False, "message": ""})),
            ifsc_code=ValidationResult(**data.get("ifsc_code", {"valid": False, "message": ""})),
            date=ValidationResult(**data.get("date", {"valid": False, "message": ""})),
            amount=ValidationResult(**data.get("amount", {"valid": False, "message": ""}))
        )
    
    def to_dict(self) -> Dict:
        """Convert ChequeValidation to dictionary"""
        return {
            "bank": {"valid": self.bank.valid, "message": self.bank.message},
            "account_number": {"valid": self.account_number.valid, "message": self.account_number.message},
            "ifsc_code": {"valid": self.ifsc_code.valid, "message": self.ifsc_code.message},
            "date": {"valid": self.date.valid, "message": self.date.message},
            "amount": {"valid": self.amount.valid, "message": self.amount.message}
        }

@dataclass
class ProcessedCheque:
    image: Image.Image
    data: ChequeData
    sonnet_data: ChequeData
    validation: ChequeValidation
    s3_urls: Dict[str, str]
    
    def display_name(self, index: int) -> str:
        """Generate a display name for UI selection"""
        return f"Cheque {index+1} - {self.data.account_holder} (₹{self.data.amount})" 