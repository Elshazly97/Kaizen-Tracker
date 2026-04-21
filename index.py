
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import json
import os

# Page configuration
st.set_page_config(
    page_title="Kaizen Action Tracker - EG Integrated Capacity Planning",
    page_icon="📊",
    layout="wide"
)

# Initialize session state
if 'data' not in st.session_state:
    st.session_state.data = None
if 'roi_rate' not in st.session_state:
    st.session_state.roi_rate = 1297.0
if 'meeting_notes' not in st.session_state:
    st.session_state.meeting_notes = []
if 'cbm_data' not in st.session_state:
    st.session_state.cbm_data = None
if 'history' not in st.session_state:
    st.session_state.history = []

# Helper functions
def save_data():
    """Save current data to JSON file"""
    if st.session_state.data is not None:
        data_dict = {
            'actions': st.session_state.data.to_dict('records'),
            'roi_rate': st.session_state.roi_rate,
            'meeting_notes': st.session_state.meeting_notes,
            'cbm_data': st.session_state.cbm_data.to_dict('records') if st.session_state.cbm_data is not None else None,
            'history': st.session_state.history,
            'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        with open('kaizen_data.json', 'w') as f:
            json.dump(data_dict, f, indent=2)
        return True
    return False

def load_saved_data():
    """Load data from JSON file if exists"""
    if os.path.exists('kaizen_data.json'):
        with open('kaizen_data.json', 'r') as f:
            data_dict = json.load(f)
            st.session_state.data = pd.DataFrame(data_dict['actions'])
            st.session_state.roi_rate = data_dict.get('roi_rate', 1297.0)
            st.session_state.meeting_notes = data_dict.get('meeting_notes', [])
            if data_dict.get('cbm_data'):
                st.session_state.cbm_data = pd.DataFrame(data_dict['cbm_data'])
            st.session_state.history = data_dict.get('history', [])
        return True
    return False

def calculate_progress(status):
    """Calculate progress percentage based on status"""
    status_weights = {
        'Completed': 100,
        'In-Progress': 50,
        'Not Started': 0,
        'Cancelled': 0
    }
    return status_weights.get(status, 0)

def calculate_roi(row):
    """Calculate ROI based only on CBMs"""
    try:
        cbm = float(row.get('CBMs Saved', 0) or 0)
        roi = cbm * st.session_state.roi_rate
        return roi
    except:
        return 0

def get_week_number(eta_str):
    """Extract week number from ETA string"""
    try:
        if pd.isna(eta_str) or eta_str == 'TBD':
            return 999
        return int(str(eta_str).replace('WK', '').replace('wk', '').replace('W', ''))
    except:
        return 999

def add_to_history(action_type, details):
    """Add change to history log"""
    st.session_state.history.append({
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'action': action_type,
        'details': details
    })

# Sidebar
st.sidebar.title("🎯 Kaizen Action Tracker")
st.sidebar.markdown("**Event:** EG | Integrated Capacity Planning and Space Readiness")
st.sidebar.markdown("**Quarter:** Q1")
st.sidebar.markdown("---")

# Navigation
page = st.sidebar.radio("Navigation", 
    ["📥 Import Data", "📋 Actions Management", "📊 Overview Dashboard", 
     "🎯 Milestone View", "📝 Meeting Notes", "⚙️ Settings", "📜 Change History"])

# Main content
if page == "📥 Import Data":
    st.title("📥 Import Kaizen Actions Data")
    
    if st.session_state.data is not None:
        st.success(f"✅ Data already loaded: {len(st.session_state.data)} actions")
        if st.button("🔄 Load Different File"):
            st.session_state.data = None
            st.rerun()
    
    if st.session_state.data is None:
        if st.button("📂 Load Previously Saved Data"):
            if load_saved_data():
                st.success("✅ Loaded saved data successfully!")
                st.rerun()
            else:
                st.warning("No saved data found.")
    
    if st.session_state.data is None:
        st.markdown("### Upload Excel File")
        uploaded_file = st.file_uploader("Choose your Kaizen actions Excel file", type=['xlsx', 'xls'])
        
        if uploaded_file:
            try:
                df = pd.read_excel(uploaded_file)
                
                if 'CBMs Saved' not in df.columns:
                    df['CBMs Saved'] = 0.0
                
                if 'Comments' not in df.columns:
                    df['Comments'] = ''
                
                if 'Last Updated' not in df.columns:
                    df['Last Updated'] = datetime.now().strftime('%Y-%m-%d')
                
                st.session_state.data = df
                add_to_history('Data Import', f'Imported {len(df)} actions from Excel')
                save_data()
                st.success(f"✅ Successfully loaded {len(df)} actions!")
                st.rerun()
            except Exception as e:
                st.error(f"Error loading file: {str(e)}")
    
    st.markdown("### Upload CBM Reference Data (Optional)")
    st.info("Upload Gas Tank file with net design CBMs for accurate ROI calculations")
    cbm_file = st.file_uploader("Choose CBM reference file", type=['xlsx', 'xls'], key='cbm_upload')
    
    if cbm_file:
        try:
            cbm_df = pd.read_excel(cbm_file)
            st.session_state.cbm_data = cbm_df
            save_data()
            st.success("✅ CBM reference data loaded!")
            st.dataframe(cbm_df.head())
        except Exception as e:
            st.error(f"Error loading CBM file: {str(e)}")

elif page == "📋 Actions Management":
    st.title("📋 Actions Management")
    
    if st.session_state.data is None:
        st.warning("⚠️ Please import data first from the 'Import Data' page")
    else:
        df = st.session_state.data
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            status_filter = st.multiselect("Filter by Status", 
                options=df['Status'].dropna().unique().tolist(),
                default=df['Status'].dropna().unique().tolist())
        with col2:
            owner_filter = st.multiselect("Filter by Owner",
                options=df['Owner'].dropna().unique().tolist(),
                default=df['Owner'].dropna().unique().tolist())
        with col3:
            site_filter = st.multiselect("Filter by Site",
                options=df['Sites'].dropna().unique().tolist() if 'Sites' in df.columns else [],
                default=df['Sites'].dropna().unique().tolist() if 'Sites' in df.columns else [])
        with col4:
            search = st.text_input("🔍 Search Actions", "")
        
        filtered_df = df.copy()
        if status_filter:
            filtered_df = filtered_df[filtered_df['Status'].isin(status_filter)]
        if owner_filter:
            filtered_df = filtered_df[filtered_df['Owner'].isin(owner_filter)]
        if site_filter and 'Sites' in df.columns:
            filtered_df = filtered_df[filtered_df['Sites'].isin(site_filter)]
        if search:
            filtered_df = filtered_df[filtered_df['Actions'].str.contains(search, case=False, na=False)]
        
        st.markdown(f"**Showing {len(filtered_df)} of {len(df)} actions**")
        
        if st.button("➕ Add New Action"):
            st.session_state.show_add_form = True
        
        if st.session_state.get('show_add_form', False):
            with st.expander("➕ Add New Action", expanded=True):
                with st.form("new_action_form"):
                    col1, col2 = st.columns(2)
                    with col1:
                        new_fishbone = st.text_input("Fishbone Type")
                        new_subject = st.text_input("Subject")
                        new_sites = st.text_input("Sites")
                        new_action = st.text_area("Action Description")
                        new_owner = st.text_input("Owner")
                    with col2:
                        new_improvement = st.text_input("Improvement Assumptions (e.g., 10%-12%)")
                        new_status = st.selectbox("Status", ['Not Started', 'In-Progress', 'Completed', 'Cancelled'])
                        new_eta = st.text_input("ETA (e.g., WK15)")
                        new_capex = st.selectbox("CAPEX Investment Needed", ['Yes', 'No', 'TBD'])
                        new_cbm = st.number_input("CBMs Saved", min_value=0.0, value=0.0)
                    
                    col_submit, col_cancel = st.columns(2)
                    with col_submit:
                        submitted = st.form_submit_button("Add Action", use_container_width=True)
                    with col_cancel:
                        cancelled = st.form_submit_button("Cancel", use_container_width=True)
                    
                    if submitted:
                        new_row = {
                            'Fishbone Type': new_fishbone,
                            'Subject': new_subject,
                            'Sites': new_sites,
                            'Actions': new_action,
                            'Owner': new_owner,
                            'Improvement Assumptions': new_improvement,
                            'Status': new_status,
                            'ETA (in WKs)': new_eta,
                            'CAPEX Investment Needed': new_capex,
                            'CBMs Saved': new_cbm,
                            'Comments': '',
                            'Last Updated': datetime.now().strftime('%Y-%m-%d')
                        }
                        st.session_state.data = pd.concat([st.session_state.data, pd.DataFrame([new_row])], ignore_index=True)
                        add_to_history('Action Added', f'New action: {new_action[:50]}...')
                        save_data()
                        st.session_state.show_add_form = False
                        st.success("✅ Action added successfully!")
                        st.rerun()
                    
                    if cancelled:
                        st.session_state.show_add_form = False
                        st.rerun()
        
        st.markdown("### Actions List")
        for idx, row in filtered_df.iterrows():
            action_preview = str(row['Actions'])[:80] if pd.notna(row['Actions']) else "No description"
            owner_name = str(row['Owner']) if pd.notna(row['Owner']) else "Unassigned"
            status_name = str(row['Status']) if pd.notna(row['Status']) else "Unknown"
            
            with st.expander(f"**{action_preview}...** | Owner: {owner_name} | Status: {status_name}"):
                with st.form(f"edit_form_{idx}"):
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.markdown("**Basic Info**")
                        fishbone = st.text_input("Fishbone Type", value=str(row.get('Fishbone Type', '')), key=f"fishbone_{idx}")
                        subject = st.text_input("Subject", value=str(row.get('Subject', '')), key=f"subject_{idx}")
                        sites = st.text_input("Sites", value=str(row.get('Sites', '')), key=f"sites_{idx}")
                        action = st.text_area("Action", value=str(row.get('Actions', '')), key=f"action_{idx}", height=100)
                    
                    with col2:
                        st.markdown("**Assignment & Progress**")
                        owner = st.text_input("Owner", value=str(row.get('Owner', '')), key=f"owner_{idx}")
                        current_status = row['Status'] if pd.notna(row['Status']) else 'Not Started'
                        status_options = ['Not Started', 'In-Progress', 'Completed', 'Cancelled']
                        status_index = status_options.index(current_status) if current_status in status_options else 0
                        status = st.selectbox("Status", status_options, index=status_index, key=f"status_{idx}")
                        eta = st.text_input("ETA (in WKs)", value=str(row.get('ETA (in WKs)', '')), key=f"eta_{idx}")
                        improvement = st.text_input("Improvement Assumptions", value=str(row.get('Improvement Assumptions', '')), key=f"improvement_{idx}")
                    
                    with col3:
                        st.markdown("**Financial & Comments**")
                        current_capex = str(row.get('CAPEX Investment Needed', 'No'))
                        capex_options = ['Yes', 'No', 'TBD']
                        capex_index = capex_options.index(current_capex) if current_capex in capex_options else 1
                        capex = st.selectbox("CAPEX Investment Needed", capex_options, index=capex_index, key=f"capex_{idx}")
                        cbm_saved = st.number_input("CBMs Saved", value=float(row.get('CBMs Saved', 0)), key=f"cbm_{idx}")
                        comments = st.text_area("Comments", value=str(row.get('Comments', '')), key=f"comments_{idx}", height=100)
                    
                    col_save, col_delete = st.columns([1, 1])
                    with col_save:
                        save_button = st.form_submit_button("💾 Save Changes", use_container_width=True)
                    with col_delete:
                        delete_button = st.form_submit_button("🗑️ Delete Action", use_container_width=True)
                    
                    if save_button:
                        st.session_state.data.at[idx, 'Fishbone Type'] = fishbone
                        st.session_state.data.at[idx, 'Subject'] = subject
                        st.session_state.data.at[idx, 'Sites'] = sites
                        st.session_state.data.at[idx, 'Actions'] = action
                        st.session_state.data.at[idx, 'Owner'] = owner
                        st.session_state.data.at[idx, 'Status'] = status
                        st.session_state.data.at[idx, 'ETA (in WKs)'] = eta
                        st.session_state.data.at[idx, 'Improvement Assumptions'] = improvement
                        st.session_state.data.at[idx, 'CAPEX Investment Needed'] = capex
                        st.session_state.data.at[idx, 'CBMs Saved'] = cbm_saved
                        st.session_state.data.at[idx, 'Comments'] = comments
                        st.session_state.data.at[idx, 'Last Updated'] = datetime.now().strftime('%Y-%m-%d')
                        add_to_history('Action Updated', f'Updated: {action[:50]}...')
                        save_data()
                        st.success("✅ Changes saved!")
                        st.rerun()
                    
                    if delete_button:
                        st.session_state.data = st.session_state.data.drop(idx).reset_index(drop=True)
                        add_to_history('Action Deleted', f'Deleted: {action[:50]}...')
                        save_data()
                        st.success("✅ Action deleted!")
                        st.rerun()
        
        st.markdown("---")
        if st.button("📥 Export to Excel"):
            output_file = f"kaizen_actions_updated_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            st.session_state.data.to_excel(output_file, index=False)
            with open(output_file, 'rb') as f:
                st.download_button(
                    label="⬇️ Download Excel File",
                    data=f,
                    file_name=output_file,
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )

elif page == "📊 Overview Dashboard":
    st.title("📊 Overview Dashboard")
    
    if st.session_state.data is None:
        st.warning("⚠️ Please import data first from the 'Import Data' page")
    else:
        df = st.session_state.data.copy()
        
        df['ROI_USD'] = df.apply(calculate_roi, axis=1)
        df['Progress'] = df['Status'].apply(calculate_progress)
        
        st.markdown("### 🎯 Overall Kaizen Metrics")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            total_actions = len(df)
            st.metric("Total Actions", total_actions)
        
        with col2:
            completed = len(df[df['Status'] == 'Completed'])
            completion_rate = (completed / total_actions * 100) if total_actions > 0 else 0
            st.metric("Completed Actions", f"{completed} ({completion_rate:.1f}%)")
        
        with col3:
            total_roi = df['ROI_USD'].sum()
            st.metric("Total ROI (USD)", f"${total_roi:,.2f}")
        
        with col4:
            avg_progress = df['Progress'].mean()
            st.metric("Overall Progress", f"{avg_progress:.1f}%")
        
        st.markdown("### 📈 Status Distribution")
        col1, col2 = st.columns(2)
        
        with col1:
            status_counts = df['Status'].value_counts()
            fig_status = px.pie(values=status_counts.values, names=status_counts.index,
                               title="Actions by Status",
                               color_discrete_sequence=px.colors.qualitative.Set3)
            st.plotly_chart(fig_status, use_container_width=True)
        
        with col2:
            fig_progress = go.Figure(go.Indicator(
                mode="gauge+number+delta",
                value=avg_progress,
                title={'text': "Overall Progress"},
                delta={'reference': 50},
                gauge={'axis': {'range': [None, 100]},
                       'bar': {'color': "darkblue"},
                       'steps': [
                           {'range': [0, 50], 'color': "lightgray"},
                           {'range': [50, 75], 'color': "gray"}],
                       'threshold': {'line': {'color': "red", 'width': 4}, 'thickness': 0.75, 'value': 90}}))
            st.plotly_chart(fig_progress, use_container_width=True)
        
        st.markdown("### 👥 Performance by POC (Person of Contact)")
        
        poc_stats = df.groupby('Owner').agg({
            'Actions': 'count',
            'Progress': 'mean',
            'ROI_USD': 'sum',
            'Status': lambda x: (x == 'Completed').sum()
        }).reset_index()
        poc_stats.columns = ['Owner', 'Total Actions', 'Avg Progress (%)', 'Total ROI (USD)', 'Completed Actions']
        poc_stats = poc_stats.sort_values('Total ROI (USD)', ascending=False)
        
        def calculate_eta_finish(owner_name):
            owner_actions = df[df['Owner'] == owner_name]
            incomplete = owner_actions[owner_actions['Status'].isin(['Not Started', 'In-Progress'])]
            if len(incomplete) == 0:
                return "All Complete"
            etas = incomplete['ETA (in WKs)'].apply(get_week_number)
            max_eta = etas.max()
            return f"WK{max_eta}" if max_eta < 999 else "TBD"
        
        poc_stats['ETA to Finish All'] = poc_stats['Owner'].apply(calculate_eta_finish)
        
        st.dataframe(poc_stats.style.format({
            'Avg Progress (%)': '{:.1f}%',
            'Total ROI (USD)': '${:,.2f}'
        }), use_container_width=True)
        
        fig_roi = px.bar(poc_stats, x='Owner', y='Total ROI (USD)',
                        title="ROI Contribution by POC",
                        color='Total ROI (USD)',
                        color_continuous_scale='Viridis')
        fig_roi.update_layout(xaxis_tickangle=-45)
        st.plotly_chart(fig_roi, use_container_width=True)
        
        fig_actions = px.bar(poc_stats, x='Owner', y='Total Actions',
                            title="Number of Actions by POC",
                            color='Avg Progress (%)',
                            color_continuous_scale='RdYlGn')
        fig_actions.update_layout(xaxis_tickangle=-45)
        st.plotly_chart(fig_actions, use_container_width=True)
        
        st.markdown("### 💰 Financial Summary")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            completed_roi = df[df['Status'] == 'Completed']['ROI_USD'].sum()
            st.metric("Money Saved (Completed Actions)", f"${completed_roi:,.2f}")
        
        with col2:
            potential_roi = df[df['Status'].isin(['In-Progress', 'Not Started'])]['ROI_USD'].sum()
            st.metric("Potential Savings (Remaining)", f"${potential_roi:,.2f}")
        
        with col3:
            total_cbm = df['CBMs Saved'].sum()
            st.metric("Total CBMs Saved", f"{total_cbm:,.2f}")

elif page == "🎯 Milestone View":
    st.title("🎯 Milestone Tracking")
    
    if st.session_state.data is None:
        st.warning("⚠️ Please import data first from the 'Import Data' page")
    else:
        df = st.session_state.data.copy()
        df['Week_Number'] = df['ETA (in WKs)'].apply(get_week_number)
        df['ROI_USD'] = df.apply(calculate_roi, axis=1)
        
        PRIME_PEAK_WK = 25
        WF26_WK = 46
        
        st.markdown(f"""
        ### 📅 Key Milestones
        - **Prime Peak**: Week {PRIME_PEAK_WK}
        - **White Friday 26**: Week {WF26_WK}
        - **Target**: All actions completed before WF26
        """)
        
        before_prime = df[df['Week_Number'] < PRIME_PEAK_WK]
        between_milestones = df[(df['Week_Number'] >= PRIME_PEAK_WK) & (df['Week_Number'] < WF26_WK)]
        after_wf26 = df[df['Week_Number'] >= WF26_WK]
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("#### Before Prime Peak (WK25)")
            st.metric("Actions", len(before_prime))
            completed_before = len(before_prime[before_prime['Status'] == 'Completed'])
            st.metric("Completed", f"{completed_before}/{len(before_prime)}")
            progress_before = (completed_before / len(before_prime) * 100) if len(before_prime) > 0 else 0
            st.progress(progress_before / 100)
            st.caption(f"{progress_before:.1f}% Complete")
        
        with col2:
            st.markdown("#### Between Milestones (WK25-46)")
            st.metric("Actions", len(between_milestones))
            completed_between = len(between_milestones[between_milestones['Status'] == 'Completed'])
            st.metric("Completed", f"{completed_between}/{len(between_milestones)}")
            progress_between = (completed_between / len(between_milestones) * 100) if len(between_milestones) > 0 else 0
            st.progress(progress_between / 100)
            st.caption(f"{progress_between:.1f}% Complete")
        
        with col3:
            st.markdown("#### After WF26 (>WK46)")
            st.metric("Actions", len(after_wf26))
            if len(after_wf26) > 0:
                st.warning("⚠️ Actions scheduled after target!")
            else:
                st.success("✅ All actions before WF26")
        
        st.markdown("### 📊 Action Timeline")
        
        timeline_data = df[df['Week_Number'] < 999].copy()
        
        fig_timeline = px.scatter(timeline_data, 
                                 x='Week_Number', 
                                 y='Owner',
                                 color='Status',
                                 size='ROI_USD',
                                 hover_data=['Actions', 'ROI_USD'],
                                 title="Actions Timeline by Owner and Status",
                                 color_discrete_map={
                                     'Completed': 'green',
                                     'In-Progress': 'orange',
                                     'Not Started': 'red',
                                     'Cancelled': 'gray'
                                 })
        
        fig_timeline.add_vline(x=PRIME_PEAK_WK, line_dash="dash", line_color="blue",
                              annotation_text="Prime Peak", annotation_position="top")
        fig_timeline.add_vline(x=WF26_WK, line_dash="dash", line_color="purple",
                              annotation_text="White Friday 26", annotation_position="top")
        
        st.plotly_chart(fig_timeline, use_container_width=True)
        
        st.markdown("### ⚠️ Risk Analysis")
        
        current_week = 15
        at_risk = df[(df['Week_Number'] < current_week + 4) & 
                     (df['Status'].isin(['Not Started', 'In-Progress']))]
        
        if len(at_risk) > 0:
            st.warning(f"⚠️ {len(at_risk)} actions at risk (due within 4 weeks and not completed)")
            st.dataframe(at_risk[['Actions', 'Owner', 'Status', 'ETA (in WKs)']], use_container_width=True)
        else:
            st.success("✅ No actions currently at risk")

elif page == "📝 Meeting Notes":
    st.title("📝 Meeting Notes")
    
    st.markdown("### Bi-Weekly Call Notes")
    st.info("Capture general meeting notes and discussions here")
    
    with st.form("new_note_form"):
        note_date = st.date_input("Meeting Date", value=datetime.now())
        note_content = st.text_area("Meeting Notes", height=200)
        attendees = st.text_input("Attendees (comma-separated)")
        
        if st.form_submit_button("💾 Save Note"):
            new_note = {
                'date': note_date.strftime('%Y-%m-%d'),
                'content': note_content,
                'attendees': attendees,
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            st.session_state.meeting_notes.append(new_note)
            add_to_history('Meeting Note Added', f'Note from {note_date}')
            save_data()
            st.success("✅ Note saved!")
            st.rerun()
    
    st.markdown("### Previous Meeting Notes")
    if st.session_state.meeting_notes:
        for i, note in enumerate(reversed(st.session_state.meeting_notes)):
            with st.expander(f"📅 {note['date']} - Meeting Notes"):
                st.markdown(f"**Attendees:** {note['attendees']}")
                st.markdown(f"**Notes:**")
                st.write(note['content'])
                st.caption(f"Added: {note['timestamp']}")
    else:
        st.info("No meeting notes yet. Add your first note above!")

elif page == "⚙️ Settings":
    st.title("⚙️ Settings")

    st.markdown("### 💰 ROI Configuration")
    col1, col2 = st.columns(2)

    with col1:
        new_roi_rate = st.number_input(
            "ROI Rate per CBM (USD/year)",
            min_value=0.0,
            value=st.session_state.roi_rate,
            step=10.0,
            help="Current rate: $1,297 per CBM per year"
        )

        if st.button("Update ROI Rate"):
            st.session_state.roi_rate = new_roi_rate
            add_to_history('Settings Changed', f'ROI rate updated to ${new_roi_rate}')
            save_data()
            st.success(f"✅ ROI rate updated to ${new_roi_rate:,.2f}")

    with col2:
        current_rate = st.session_state.roi_rate
        st.info(f"""Current ROI Rate: ${current_rate:,.2f} per CBM per year

        ROI Formula: Total CBMs × ROI Rate""")

    st.markdown("---")
    st.markdown("### 📊 Data Management")

    if st.session_state.data is not None:
        st.success(f"✅ {len(st.session_state.data)} actions currently loaded")
        st.caption(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

elif page == "📜 Change History":
    st.title("📜 Change History")

    if st.session_state.history:
        st.markdown(f"### Recent Changes ({len(st.session_state.history)} total)")

        for i, change in enumerate(reversed(st.session_state.history[-50:])):
            with st.expander(f"🕐 {change['timestamp']} - {change['action']}"):
                st.write(change['details'])
    else:
        st.info("No changes recorded yet. Changes will appear here as you use the application.")

