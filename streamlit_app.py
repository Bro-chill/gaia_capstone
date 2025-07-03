import streamlit as st
import requests
import time

# Configuration
API_BASE_URL = "http://localhost:8000"
ANALYZE_ENDPOINT = f"{API_BASE_URL}/analyze-script"
SAVE_ENDPOINT = f"{API_BASE_URL}/save-analysis"

def main():
    st.set_page_config(
        page_title="Script Analyzer",
        page_icon="🎬",
        layout="centered"
    )
    
    st.title("🎬 Film Script Analyzer")
    st.markdown("Upload a PDF script for AI analysis and database storage")
    
    # File upload
    st.header("📄 Upload Script")
    uploaded_file = st.file_uploader(
        "Choose a PDF script file",
        type=['pdf'],
        help="Upload a PDF script file (max 50MB)"
    )
    
    if uploaded_file is not None:
        st.success(f"✅ File uploaded: {uploaded_file.name}")
        st.info(f"📊 File size: {uploaded_file.size:,} bytes")
        
        # Analyze and Save button
        if st.button("🔍 Analyze & Save Script", type="primary"):
            analyze_and_save_script(uploaded_file)

def analyze_and_save_script(uploaded_file):
    """Analyze script and automatically save to database"""
    
    # Progress tracking
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    try:
        # Step 1: Analyze Script
        status_text.text("📤 Uploading and analyzing script...")
        progress_bar.progress(20)
        
        # Prepare file for upload
        files = {"file": (uploaded_file.name, uploaded_file.getvalue(), "application/pdf")}
        
        # Make analysis request
        status_text.text("🤖 AI is analyzing your script...")
        progress_bar.progress(40)
        
        analyze_response = requests.post(ANALYZE_ENDPOINT, files=files, timeout=300)
        
        if analyze_response.status_code != 200:
            # Handle analysis error
            try:
                error_data = analyze_response.json()
                error_msg = error_data.get('detail', 'Unknown error')
            except:
                error_msg = analyze_response.text
            
            st.error(f"❌ Analysis failed: {error_msg}")
            progress_bar.empty()
            status_text.empty()
            return
        
        # Parse analysis result
        analysis_result = analyze_response.json()
        progress_bar.progress(70)
        status_text.text("✅ Analysis complete! Saving to database...")
        
        # Step 2: Save to Database
        save_request = analysis_result.get('save_request')
        
        if not save_request:
            st.error("❌ No save data available from analysis")
            progress_bar.empty()
            status_text.empty()
            return
        
        # Make save request
        save_response = requests.post(
            SAVE_ENDPOINT, 
            json=save_request, 
            timeout=30,
            headers={'Content-Type': 'application/json'}
        )
        
        progress_bar.progress(90)
        
        if save_response.status_code == 201:
            # Success!
            save_result = save_response.json()
            database_id = save_result.get('database_id')
            
            progress_bar.progress(100)
            status_text.text("🎉 Complete!")
            
            # Show success message
            st.success("✅ **Analysis Complete & Saved!**")
            st.info(f"📝 Database ID: {database_id}")
            
            # Show basic stats
            metadata = analysis_result.get('metadata', {})
            col1, col2, col3 = st.columns(3)
            
            with col1:
                processing_time = metadata.get('processing_time_seconds', 0)
                st.metric("Processing Time", f"{processing_time:.1f}s")
            
            with col2:
                api_calls = metadata.get('api_calls_used', 0)
                st.metric("API Calls", api_calls)
            
            with col3:
                file_size = metadata.get('file_size_bytes', 0)
                st.metric("File Size", f"{file_size:,} bytes")
            
            # Clear progress indicators after 2 seconds
            time.sleep(2)
            progress_bar.empty()
            status_text.empty()
            
        else:
            # Save failed
            try:
                error_data = save_response.json()
                error_msg = error_data.get('detail', 'Unknown save error')
            except:
                error_msg = save_response.text
            
            st.error(f"❌ Save failed: {error_msg}")
            st.warning("⚠️ Analysis completed but couldn't save to database")
            progress_bar.empty()
            status_text.empty()
            
    except requests.exceptions.Timeout:
        st.error("⏰ Request timed out. Please try again.")
        progress_bar.empty()
        status_text.empty()
        
    except requests.exceptions.ConnectionError:
        st.error("🔌 Cannot connect to API server. Please check if the server is running.")
        progress_bar.empty()
        status_text.empty()
        
    except Exception as e:
        st.error(f"❌ Unexpected error: {str(e)}")
        progress_bar.empty()
        status_text.empty()

# Simple CSS for better appearance
def add_simple_css():
    st.markdown("""
    <style>
    .stButton > button {
        width: 100%;
        height: 50px;
        font-size: 16px;
    }
    .stMetric {
        text-align: center;
    }
    </style>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    add_simple_css()
    main()