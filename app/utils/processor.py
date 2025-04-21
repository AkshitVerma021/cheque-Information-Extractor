from PIL import Image
from typing import Dict, Optional, List
from datetime import datetime
import streamlit as st

from app.models.cheque_data import ChequeData, ProcessedCheque
from app.services.ai_service import AIService
from app.services.s3_service import S3Service
from app.validators.cheque_validator import ChequeValidator
from app.utils.session_manager import SessionManager

class ChequeProcessor:
    """Processor to handle cheque extraction workflow"""
    
    def __init__(self):
        self.ai_service = AIService()
        self.s3_service = S3Service()
    
    def process_cheque(self, image: Image.Image, file_name: str) -> Optional[ProcessedCheque]:
        """Process a single cheque image through the extraction pipeline"""
        try:
            # Extract with both models
            haiku_result_dict = self.ai_service.extract_with_haiku(image)
            
            # Check if the result contains an error message (invalid image)
            if haiku_result_dict and "error" in haiku_result_dict:
                st.error(f"❌ {file_name}: {haiku_result_dict['error']}")
                # Still mark as processed to avoid reprocessing
                return None
                
            sonnet_result_dict = self.ai_service.extract_with_sonnet(image)
            
            # Check if the sonnet result contains an error message
            if sonnet_result_dict and "error" in sonnet_result_dict:
                st.error(f"❌ {file_name}: {sonnet_result_dict['error']}")
                # Still mark as processed to avoid reprocessing
                return None
            
            # Convert dict results to model objects
            haiku_result = ChequeData.from_dict(haiku_result_dict)
            sonnet_result = ChequeData.from_dict(sonnet_result_dict)
            
            # Validate the data
            validation = ChequeValidator.validate_cheque_data(haiku_result)
            
            # Create a unique ID for this cheque
            cheque_id = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{haiku_result.account_number}"
            
            # Save processed files to S3
            cheque_s3_key = f"processed/cheque_{cheque_id}.jpg"
            cheque_s3_url = self.s3_service.upload_image(image, cheque_s3_key)
            
            # Crop and save signature to S3
            sig_s3_url = self.s3_service.crop_and_upload_signature(image, cheque_id)
            
            # Create a processed cheque object
            processed_cheque = ProcessedCheque(
                image=image,
                data=haiku_result,
                sonnet_data=sonnet_result,
                validation=validation,
                s3_urls={
                    "cheque": cheque_s3_url,
                    "signature": sig_s3_url
                }
            )
            
            return processed_cheque
            
        except Exception as e:  
            st.error(f"Error processing cheque {file_name}: {str(e)}")
            return None
    
    def process_batch(self, uploaded_files: List) -> List[ProcessedCheque]:
        """Process a batch of uploaded cheque images"""
        processed_cheques = []
        processed_files = SessionManager.get_processed_files()
        
        # Find new files that haven't been processed
        new_files = [file for file in uploaded_files if file.name not in processed_files]
        
        if new_files:
            with st.spinner(f"🔍 Analyzing {len(new_files)} new cheques with multiple verification methods..."):
                for uploaded_file in new_files:
                    try:
                        img = Image.open(uploaded_file)
                        # Convert to RGB if needed
                        if img.mode == 'RGBA':
                            img = img.convert('RGB')
                            
                        processed_cheque = self.process_cheque(img, uploaded_file.name)
                        
                        if processed_cheque:
                            processed_cheques.append(processed_cheque)
                            SessionManager.add_processed_cheque(processed_cheque, uploaded_file.name)
                        else:
                            # Still mark file as processed to avoid reprocessing
                            SessionManager.get_processed_files().add(uploaded_file.name)
                    
                    except Exception as e:
                        st.error(f"Error processing {uploaded_file.name}: {str(e)}")
                        # Still mark as processed to avoid infinite reprocessing attempts
                        SessionManager.get_processed_files().add(uploaded_file.name)
        
        return SessionManager.get_processed_cheques() 