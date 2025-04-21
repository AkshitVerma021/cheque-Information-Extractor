import streamlit as st
import pandas as pd
from typing import List, Dict, Optional
from PIL import Image

from app.models.cheque_data import ChequeData, ChequeValidation, ProcessedCheque
from app.validators.cheque_validator import ChequeValidator

def setup_page():
    """Set up Streamlit page with title, logo, and CSS"""
    from config.config import CSS_STYLES
    
    st.set_page_config(  
        page_title="ChequeAI",  
        page_icon="🏦",  
        layout="wide"  
    )  
    
    # Add logo at the top center  
    col1, col2, col3 = st.columns([1,1,1])  
    with col2:  
        logo = Image.open("logo.png")  # Load logo from same directory  
        st.image(logo, width=600)  
    
    # Apply custom CSS
    st.markdown(CSS_STYLES, unsafe_allow_html=True)  
    
    # Add header
    st.markdown('<div class="header">Cheque-Information-Extractor</div>', unsafe_allow_html=True)  

def display_cheque_result(processed_cheque: ProcessedCheque, index: int) -> None:  
    """Display results for a single cheque with automated accuracy verification"""  
    with st.container():  
        st.markdown(f'<div class="cheque-container">', unsafe_allow_html=True)  
        
        col1, col2 = st.columns(2)  
        with col1:  
            st.image(processed_cheque.image, caption=f"Cheque {index+1}", use_container_width=True)
        
        with col2:  
            # Calculate and display automated accuracy
            discrepancies, confidence_score = ChequeValidator.cross_validate_results(
                processed_cheque.data, 
                processed_cheque.sonnet_data
            )
            automated_accuracy = ChequeValidator.calculate_automated_accuracy(
                processed_cheque.data, 
                processed_cheque.sonnet_data, 
                processed_cheque.validation
            )
            
            st.markdown(f"""  
            <div class="accuracy-meter">  
                <div style="font-weight: bold; margin-bottom: 5px;">Automated Verification Score</div>  
                <div style="background: #f0f0f0; border-radius: 10px; height: 20px;">  
                    <div style="background: #2e86c1; width: {automated_accuracy}%; height: 100%; border-radius: 10px;  
                        text-align: center; color: white; font-size: 12px; line-height: 20px;">  
                        {automated_accuracy:.1f}%  
                    </div>  
                </div>  
                <div class="accuracy-value" style="text-align: center; margin-top: 5px;">  
                    {automated_accuracy:.1f}% Confidence  
                </div>  
            </div>  
            """, unsafe_allow_html=True)  

            # Display results in table format  
            cheque_data = processed_cheque.data
            table_data = {  
                "Field": ["Bank Name", "Account Holder", "Account Number", "Amount",  
                        "IFSC Code", "Date", "Signature Present"],  
                "Extracted Value": [  
                    cheque_data.bank,  
                    cheque_data.account_holder,  
                    cheque_data.account_number,  
                    cheque_data.amount,  
                    cheque_data.ifsc_code,  
                    cheque_data.date,  
                    "Yes" if cheque_data.has_signature else "No"  
                ]
            }  
            
            df = pd.DataFrame(table_data)  
            st.table(df)  
        
        st.markdown('</div>', unsafe_allow_html=True)  

def display_action_buttons(excel_bytes: bytes, on_clear, excel_s3_url: Optional[str] = None):
    """Display action buttons for download and clear"""
    col1, col2 = st.columns(2)  
    
    with col1:  
        st.download_button(  
            label="📥 Download All Data (Excel)",  
            data=excel_bytes,  
            file_name="cheque_data_with_verification.xlsx",  
            mime="application/vnd.ms-excel"  
        )
        
        # We're not showing the S3 URL to the user as requested
        # But we'll still store it in the session state for backend use
        if excel_s3_url and 'excel_s3_url' not in st.session_state:
            st.session_state.excel_s3_url = excel_s3_url
    
    with col2:  
        if st.button("🔄 Clear All Data", key="clear_btn"):  
            on_clear()
            
def display_results(processed_cheques: List[ProcessedCheque], excel_bytes: bytes, on_clear, excel_s3_url: Optional[str] = None):
    """Display the results section including cheque selector and details"""
    if not processed_cheques:
        return
        
    # Cheque selection dropdown
    cheque_options = [
        cheque.display_name(i) for i, cheque in enumerate(processed_cheques)
    ]
    
    selected_cheque = st.selectbox(
        "📋 Select Cheque to View Details:",
        options=cheque_options,
        index=0
    )
    
    selected_index = cheque_options.index(selected_cheque)
    display_cheque_result(processed_cheques[selected_index], selected_index)
    
    st.success(f"✅ Successfully processed {len(processed_cheques)} cheques with automated verification")
    
    # Display action buttons
    display_action_buttons(excel_bytes, on_clear, excel_s3_url) 