import streamlit as st
from PIL import Image

from app.ui.display import setup_page, display_results
from app.utils.session_manager import SessionManager
from app.utils.processor import ChequeProcessor
from app.utils.export_utils import to_excel

def run_app():
    """Run the Cheque Extractor Streamlit App"""
    # Setup page with title, logo and styles
    setup_page()
    
    # Initialize session state
    SessionManager.initialize_session()
    
    # File Upload Section
    uploaded_files = st.file_uploader(
        "📁 Upload cheque images (JPEG, PNG)",
        type=["jpg", "jpeg", "png"],
        accept_multiple_files=True,
        key=SessionManager.get_file_uploader_key()
    )
    
    if uploaded_files:
        # Process cheques
        processor = ChequeProcessor()
        processed_cheques = processor.process_batch(uploaded_files)
        
        if processed_cheques:
            # Generate Excel data and upload to S3
            excel_bytes, s3_url = to_excel(processed_cheques)
            
            # Store S3 URL in session state if needed
            if s3_url and 'excel_s3_url' not in st.session_state:
                st.session_state.excel_s3_url = s3_url
            
            # Display results
            display_results(
                processed_cheques, 
                excel_bytes, 
                on_clear=lambda: SessionManager.reset_session(),
                excel_s3_url=s3_url
            )
    
    # Info about the app
    with st.expander("ℹ️ About this App"):
        st.markdown("""
        ### Cheque Information Extractor
        
        This application extracts information from cheque images using advanced AI models:
        
        - **Double Verification**: Uses two AI models for cross-verification
        - **Export Data**: Download all extracted information as Excel
        - **Signature Extraction**: Automatically extracts and saves signature
        
        For support, please contact consulting@bellblazetech.com
        """)

if __name__ == "__main__":
    run_app() 