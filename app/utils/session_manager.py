import streamlit as st
from datetime import datetime
from typing import Set, List, Dict
from PIL import Image

from app.models.cheque_data import ChequeData, ChequeValidation, ProcessedCheque

class SessionManager:
    """Manage Streamlit session state for the app"""
    
    @staticmethod
    def initialize_session():
        """Initialize session state with default values if not already present"""
        if 'processed_cheques' not in st.session_state:
            st.session_state.processed_cheques = []
            st.session_state.processed_files = set()
            st.session_state.file_uploader_key = str(datetime.now().timestamp())
    
    @staticmethod
    def reset_session():
        """Reset session state to initial values"""
        # Store keys to preserve
        uploader_key = str(datetime.now().timestamp())
        
        # Clear all existing session state keys
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        
        # Reinitialize with fresh values
        st.session_state.processed_cheques = []
        st.session_state.processed_files = set()
        st.session_state.file_uploader_key = uploader_key
    
    @staticmethod
    def add_processed_cheque(processed_cheque: ProcessedCheque, file_name: str):
        """Add processed cheque to session state"""
        SessionManager.initialize_session()
        st.session_state.processed_cheques.append(processed_cheque)
        st.session_state.processed_files.add(file_name)
    
    @staticmethod
    def get_processed_cheques() -> List[ProcessedCheque]:
        """Get list of processed cheques from session state"""
        SessionManager.initialize_session()
        return st.session_state.processed_cheques
    
    @staticmethod
    def get_processed_files() -> Set[str]:
        """Get set of processed file names from session state"""
        SessionManager.initialize_session()
        return st.session_state.processed_files
    
    @staticmethod
    def get_file_uploader_key() -> str:
        """Get unique key for file uploader"""
        SessionManager.initialize_session()
        return st.session_state.file_uploader_key 