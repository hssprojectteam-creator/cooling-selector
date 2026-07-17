import streamlit as st
import pandas as pd
import os

# ------------------ 1. BRANDING & PAGE CONFIG ------------------
COMPANY_NAME = "HSS ProService Marketplace" 
BRAND_COLOR = "#269D84"  

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SLIDES_DIR = os.path.join(BASE_DIR, "slides")

st.set_page_config(
    page_title=f"{COMPANY_NAME} | Climate Control Selector", 
    page_icon="❄️", 
    layout="wide"
)

st.markdown(f"""
    <style>
    [data-testid="stHeader"] {{ display: none !important; }}
    #MainMenu {{ visibility: hidden !important; }}
    footer {{ visibility: hidden !important; }}
    .brand-header {{ color: {BRAND_COLOR}; font-weight: bold; margin-bottom: 0px; }}
    div.stButton > button:first-child {{ background-color: {BRAND_COLOR}; color: white; border-radius: 5px; }}
    </style>
    """, unsafe_allow_html=True)

@st.cache_data(ttl=600)
def load_cooling_data():
    df = pd.read_excel("CoolingData.xlsx", sheet_name="CoolingData")
    return df

try:
    df = load_cooling_data()
    
    # ------------------ 2. SIDEBAR CONFIGURATION ------------------
    if os.path.exists("logo.png"):
        st.sidebar.image("logo.png", width="stretch" if hasattr(st.sidebar, "image") else None)
    else:
        st.sidebar.markdown(f"<h2 class='brand-header'>{COMPANY_NAME}</h2>", unsafe_allow_html=True)
        
    st.sidebar.markdown("---")
    st.sidebar.header("Filter Criteria")
    
    know_code = st.sidebar.checkbox("I know the Product Code", key="know_cooling_code")
    
    if know_code:
        search_code = st.sidebar.text_input("Enter Product Code:", placeholder="e.g. 57111")
        filtered_df = df[df["Product Code"].astype(str).str.contains(search_code.strip(), case=False, na=False)] if search_code.strip() else df.iloc[0:0]
    else:
        eq_types = ["All"] + list(df["Equipment Type"].dropna().unique())
        selected_type = st.sidebar.selectbox("Select Equipment Type", eq_types)
        
        min_room = int(df["Target Room Size (m2)"].min()) if not df.empty else 10
        max_room = int(df["Target Room Size (m2)"].max()) if not df.empty else 150
        
        target_size = st.sidebar.slider("Minimum Room Size Capacity (m²)", min_value=min_room, max_value=max_room, step=5, value=min_room)
        
        filtered_df = df.copy()
        if selected_type != "All":
            filtered_df = filtered_df[filtered_df["Equipment Type"] == selected_type]
        filtered_df = filtered_df[filtered_df["Target Room Size (m2)"] >= target_size]

    def reset_filters():
        st.session_state.know_cooling_code = False
        st.session_state.chassis = "All"
        st.session_state.height = 10
    # ------------------ 3. MAIN APP INTERFACE ------------------
    title_html = f"<h1 class='brand-header'>❄️ Climate Control Solution Finder</h1>"
    st.markdown(title_html, unsafe_allow_html=True)
    st.markdown("Filter your site specifications on the left to pull matching product sheets directly from our catalogue presentation.")
    
    st.markdown("<p style='color: #FF4B4B; font-weight: bold; margin-top: 5px; margin-bottom: 5px;'>Please be aware that exact model available will be dependant on supplier</p>", unsafe_allow_html=True)
    st.markdown("---")
    
    # ------------------ 4. DISPLAY MATCHING SLIDES ------------------
    if not filtered_df.empty:
        # Sort values cleanly so smaller capacity equipment surfaces first
        filtered_df = filtered_df.sort_values(by="Target Room Size (m2)")
        
        st.subheader(f"We found {len(filtered_df)} matching solutions:")
        
        for index, row in filtered_df.iterrows():
            slide_num = row["Slide Number"]
            slide_file = f"Slide{slide_num}.png"
            slide_path = os.path.join(SLIDES_DIR, slide_file)
                
            if os.path.exists(slide_path):
                # Renders the physical PowerPoint slide visually onto the canvas
                st.image(slide_path, caption=f"Product Catalogue Info Sheet - Code {row['Product Code']}", width="stretch")
                st.markdown(" ")
            else:
                st.warning(f"Catalogue Sheet image '{slide_file}' could not be located inside the slides folder.")
    else:
        if know_code and not search_code.strip():
            st.info("Please enter a valid HSS Product Code in the sidebar search box.")
        else:
            st.warning("No specific fleet assets match your exact room parameters. Try lowering your room criteria values.")

except Exception as e:
    st.error(f"Error compiling presentation dashboard asset loops. Details: {e}")

