import streamlit as st
import pandas as pd
import os
import re

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
    .calc-container {{ background-color: #f8f9fa; padding: 20px; border-left: 5px solid {BRAND_COLOR}; border-radius: 4px; margin-bottom: 20px; }}
    .calc-result {{ font-size: 20px; font-weight: bold; color: {BRAND_COLOR}; }}
    </style>
    """, unsafe_allow_html=True)

@st.cache_data(ttl=600)
def load_cooling_data():
    # CHANGED: Now references the new 'CoolingData.xlsx' workbook name
    # Reads the first sheet by default. Adjust sheet_name if it is explicitly named.
    try:
        df = pd.read_excel("CoolingData.xlsx", sheet_name="CoolingData")
    except Exception:
        df = pd.read_excel("CoolingData.xlsx", sheet_name=0)
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
        selected_type = "All"
        search_by_criteria = False
    else:
        eq_types = ["All"] + list(df["Equipment Type"].dropna().unique())
        selected_type = st.sidebar.selectbox("Select Equipment Type", eq_types)
        
        min_room = int(df["Target Room Size (m2)"].min()) if not df.empty else 10
        max_room = int(df["Target Room Size (m2)"].max()) if not df.empty else 150
        
        # This slider is active for other types, but overridden if Portable AC is chosen
        target_size = st.sidebar.slider("Minimum Room Size Capacity (m²)", min_value=min_room, max_value=max_room, step=5, value=min_room)
        search_by_criteria = True

    def reset_filters():
        st.session_state.know_cooling_code = False
    # ------------------ 3. MAIN APP INTERFACE ------------------
    title_html = f"<h1 class='brand-header'>❄️ Climate Control Solution Finder</h1>"
    st.markdown(title_html, unsafe_allow_html=True)
    st.markdown("Filter your site specifications on the left to pull matching product sheets directly from our catalogue presentation.")
    
    st.markdown("<p style='color: #FF4B4B; font-weight: bold; margin-top: 5px; margin-bottom: 5px;'>Please be aware that exact model available will be dependant on supplier</p>", unsafe_allow_html=True)
    st.markdown("---")
    
    # Initialize our filter threshold override tracker
    override_active_area = None
    
    # ------------------ DYNAMIC PORTABLE AC CALCULATOR ------------------
    if not know_code and selected_type == "Portable AC":
        st.subheader("🧮 Interactive Sizing Calculator (Slide 4)")
        with st.container():
            st.markdown("<div class='calc-container'>", unsafe_allow_html=True)
            col1, col2, col3 = st.columns(3)
            
            with col1:
                r_length = st.number_input("Room Length (m)", min_value=1.0, max_value=30.0, value=5.0, step=0.5)
            with col2:
                r_width = st.number_input("Room Width (m)", min_value=1.0, max_value=30.0, value=4.0, step=0.5)
            with col3:
                r_height = st.number_input("Ceiling Height (m)", min_value=2.0, max_value=6.0, value=2.5, step=0.1)
                
            room_gain = st.select_slider(
                "Room Sun Exposure / Heat Load Level",
                options=["Low (Good insulation, low glass)", "Medium (Average windows/sun light)", "High (High glass, south facing, hot equipment)"]
            )
            
            calculated_area = r_length * r_width
            calculated_volume = calculated_area * r_height
            
            if "Low" in room_gain:
                factor = 35
            elif "Medium" in room_gain:
                factor = 40
            else:
                factor = 50
                
            required_watts = calculated_volume * factor
            required_kw = required_watts / 1000.0
            required_btu = required_kw * 3412.142
            
            # CHANGED: Assign the calculator area to override the manual slider parameter
            override_active_area = calculated_area
            
            st.markdown(f"""
            <p style='margin-top:10px;'>Calculated Room Floor Area: <b>{calculated_area:.1f} m²</b> | Room Volume: <b>{calculated_volume:.1f} m³</b></p>
            <p class='calc-result'>Estimated Target Requirement: {required_kw:.2f} kW ({required_btu:,.0f} BTU)</p>
            <p style='font-size:12px; color:#269D84; font-style:italic; font-weight:bold;'>💡 Notice: Catalogue listings below are now filtered automatically based on this {calculated_area:.1f} m² output calculation.</p>
            </div>
            """, unsafe_allow_html=True)
            st.markdown("---")

    # ------------------ 4. FILTERING & SEARCH LOGIC ------------------
    filtered_df = df.copy()
    
    if know_code:
        if search_code.strip() != "":
            filtered_df = filtered_df[filtered_df["Product Code"].astype(str).str.contains(search_code.strip(), case=False, na=False)]
        else:
            filtered_df = filtered_df.iloc[0:0]
    else:
        if selected_type != "All":
            filtered_df = filtered_df[filtered_df["Equipment Type"] == selected_type]
            
        # CHANGED: Apply calculator size criteria filter if active, otherwise fallback to sidebar slider node
        if override_active_area is not None:
            filtered_df = filtered_df[filtered_df["Target Room Size (m2)"] >= override_active_area]
        else:
            filtered_df = filtered_df[filtered_df["Target Room Size (m2)"] >= target_size]

    # ------------------ 5. DISPLAY MATCHING SLIDES ------------------
    st.subheader(f"Matching Results ({len(filtered_df)} solutions found)")
    
    if not filtered_df.empty:
        filtered_df = filtered_df.sort_values(by="Target Room Size (m2)")
        actual_folder_files = os.listdir(SLIDES_DIR) if os.path.exists(SLIDES_DIR) else []
        
        for index, row in filtered_df.iterrows():
            slide_num = str(row["Slide Number"]).strip()
            target_pattern = f"slide{slide_num}"
            
            matched_file = None
            for physical_file in actual_folder_files:
                clean_physical = re.sub(r'[\s_]', '', physical_file).lower()
                if target_pattern in clean_physical:
                    matched_file = physical_file
                    break
            
            if matched_file:
                slide_path = os.path.join(SLIDES_DIR, matched_file)
                st.image(slide_path, caption=f"Product Catalogue Info Sheet - Code {row['Product Code']}", width="stretch")
                st.markdown(" ")
            else:
                st.warning(f"Catalogue Sheet image for Slide {slide_num} could not be located inside the 'slides' folder. Please check file names.")
    else:
        if know_code and not search_code.strip():
            st.info("Please enter a valid HSS Product Code in the sidebar search box.")
        else:
            st.warning("No specific solutions match your current area size inputs. Try lowering your room criteria values.")

except Exception as e:
    st.error(f"Error compiling presentation dashboard asset loops. Details: {e}")
