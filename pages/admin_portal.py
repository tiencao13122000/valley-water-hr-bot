import streamlit as st
import pandas as pd
import os
import time
from datetime import datetime, timedelta
import json
from utils.user_auth import admin_required, logout_user
from utils.db_manager import DBManager
from utils.report_generator import ReportGenerator

# Custom CSS for styling
st.markdown("""
<style>
    .main-title {
        font-size: 2rem !important;
        margin-bottom: 1rem;
        color: #0078D7;
    }
    
    .header-container {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 1rem;
    }
    
    .card {
        border-radius: 8px;
        background-color: #f8f9fa;
        padding: 1rem;
        margin-bottom: 1rem;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
    }
    
    .metric-container {
        background-color: white;
        border-radius: 8px;
        padding: 1.5rem;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        text-align: center;
    }
    
    .metric-value {
        font-size: 2rem;
        font-weight: bold;
        color: #0078D7;
    }
    
    .metric-label {
        font-size: 1rem;
        color: #505050;
    }
    
    .footer {
        text-align: center;
        padding: 1rem;
        font-size: 0.8rem;
        color: #6c757d;
        margin-top: 2rem;
    }
    
    .filter-container {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 8px;
        margin-bottom: 1rem;
    }
    
    /* Tab styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 24px;
    }
    
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        background-color: transparent;
        border-radius: 4px 4px 0 0;
        color: #0078D7;
        font-size: 14px;
    }
    
    .stTabs [aria-selected="true"] {
        background-color: #E3F2FD;
        border-bottom: 2px solid #0078D7;
    }
</style>
""", unsafe_allow_html=True)

# Initialize components
db_manager = DBManager()
report_generator = ReportGenerator(db_manager)

# Date range selector
def date_range_selector():
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input(
            "Start Date",
            value=datetime.now() - timedelta(days=30),
            max_value=datetime.now()
        )
    with col2:
        end_date = st.date_input(
            "End Date",
            value=datetime.now(),
            min_value=start_date,
            max_value=datetime.now()
        )
    return start_date, end_date

@admin_required
def main():
    # Get admin data from session
    admin_data = st.session_state.employee_data
    
    # Header with logout button
    col1, col2, col3 = st.columns([4, 4, 2])
    with col1:
        st.markdown("<h1 class='main-title'>HR Admin Portal</h1>", unsafe_allow_html=True)
    with col3:
        st.button("Logout", key="logout_btn", on_click=logout_user)
        if st.button("Return to Portal", key="portal_btn"):
            st.switch_page("pages/employee_portal.py")
    
    # Admin info
    st.markdown(f"**Logged in as:** {admin_data['name']} ({admin_data['position']})")
    
    # Tabs for different sections
    tab1, tab2, tab3, tab4 = st.tabs(["Dashboard", "Conversation History", "Employee Reports", "System Management"])
    
    # Tab 1: Dashboard
    with tab1:
        # Get statistics
        stats = db_manager.get_conversation_stats()
        
        st.subheader("Overview")
        
        # Metrics in cards
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown("<div class='metric-container'>", unsafe_allow_html=True)
            st.markdown(f"<div class='metric-value'>{stats['total_conversations']}</div>", unsafe_allow_html=True)
            st.markdown("<div class='metric-label'>Total Conversations</div>", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)
            
        with col2:
            st.markdown("<div class='metric-container'>", unsafe_allow_html=True)
            st.markdown(f"<div class='metric-value'>{stats['unique_employees']}</div>", unsafe_allow_html=True)
            st.markdown("<div class='metric-label'>Unique Employees</div>", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)
            
        with col3:
            st.markdown("<div class='metric-container'>", unsafe_allow_html=True)
            st.markdown(f"<div class='metric-value'>{stats['conversations_last_7_days']}</div>", unsafe_allow_html=True)
            st.markdown("<div class='metric-label'>Last 7 Days</div>", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)
            
        with col4:
            st.markdown("<div class='metric-container'>", unsafe_allow_html=True)
            avg_length = int(stats['avg_answer_length'])
            st.markdown(f"<div class='metric-value'>{avg_length}</div>", unsafe_allow_html=True)
            st.markdown("<div class='metric-label'>Avg Answer Length</div>", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)
        
        # Conversation trends chart
        st.subheader("Conversation Trends")
        trends_fig = report_generator.plot_conversation_trends(days=30)
        if trends_fig:
            st.plotly_chart(trends_fig, use_container_width=True)
        else:
            st.info("No conversation data available for trend analysis.")
        
        # Two charts side by side
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Topic Distribution")
            topics_fig = report_generator.plot_topic_distribution()
            if topics_fig:
                st.plotly_chart(topics_fig, use_container_width=True)
            else:
                st.info("No topic data available.")
        
        with col2:
            st.subheader("Employee Activity")
            employee_fig = report_generator.plot_employee_activity()
            if employee_fig:
                st.plotly_chart(employee_fig, use_container_width=True)
            else:
                st.info("No employee activity data available.")
        
        # Export report button
        st.subheader("Export Dashboard Report")
        if st.button("Generate Admin Report", key="gen_admin_report"):
            with st.spinner("Generating report..."):
                # Generate admin report
                report = report_generator.generate_admin_report(days=30)
                json_path = report_generator.save_report_to_json(report)
                
                # Provide download link
                with open(json_path, "rb") as file:
                    st.download_button(
                        label="Download Report (JSON)",
                        data=file,
                        file_name=os.path.basename(json_path),
                        mime="application/json"
                    )
    
    # Tab 2: Conversation History
    with tab2:
        st.subheader("Conversation History")
        
        # Filters
        st.markdown("<div class='filter-container'>", unsafe_allow_html=True)
        col1, col2, col3 = st.columns([3, 3, 2])
        
        with col1:
            # Date range filter
            date_filter = st.checkbox("Filter by date", value=False)
            if date_filter:
                start_date, end_date = date_range_selector()
        
        with col2:
            # Topic filter
            topics = ["All Topics"] + [topic["name"] for topic in db_manager.get_top_topics(limit=20)]
            selected_topic = st.selectbox("Topic", topics)
        
        with col3:
            # Search filter
            search_term = st.text_input("Search", placeholder="Search conversations...")
        
        st.markdown("</div>", unsafe_allow_html=True)
        
        # Get conversation data
        conversations = db_manager.get_all_conversations(limit=1000)
        
        if not conversations:
            st.info("No conversation data available.")
        else:
            # Apply filters
            filtered_conversations = conversations
            
            # Date filter
            if date_filter:
                filtered_conversations = [
                    c for c in filtered_conversations 
                    if start_date <= datetime.strptime(c['date_time'].split()[0], "%Y-%m-%d").date() <= end_date
                ]
            
            # Topic filter
            if selected_topic != "All Topics":
                filtered_conversations = [
                    c for c in filtered_conversations 
                    if c.get('topic') == selected_topic
                ]
            
            # Search filter
            if search_term:
                search_term = search_term.lower()
                filtered_conversations = [
                    c for c in filtered_conversations 
                    if (search_term in c['question'].lower() or 
                        search_term in c['answer'].lower() or 
                        search_term in c.get('summary', '').lower() or
                        search_term in c['employee_name'].lower())
                ]
            
            # Display filtered conversations
            st.write(f"Showing {len(filtered_conversations)} of {len(conversations)} conversations")
            
            # Convert to DataFrame for display
            if filtered_conversations:
                df = pd.DataFrame([
                    {
                        "ID": c['id'],
                        "Employee": c['employee_name'],
                        "Date": c['date_time'],
                        "Topic": c.get('topic', 'Uncategorized'),
                        "Question": c['question'],
                        "Summary": c.get('summary', 'No summary available')
                    }
                    for c in filtered_conversations
                ])
                
                # Display table
                st.dataframe(
                    df,
                    column_config={
                        "ID": st.column_config.NumberColumn("ID", width="small"),
                        "Employee": st.column_config.TextColumn("Employee", width="medium"),
                        "Date": st.column_config.DatetimeColumn("Date", width="medium", format="MMM DD, YYYY, h:mm a"),
                        "Topic": st.column_config.TextColumn("Topic", width="medium"),
                        "Question": st.column_config.TextColumn("Question", width="large"),
                        "Summary": st.column_config.TextColumn("Summary", width="large")
                    },
                    use_container_width=True,
                    hide_index=True
                )
                
                # Detailed view for selected conversation
                selected_id = st.selectbox("Select conversation for detailed view:", ["None"] + [str(c['id']) for c in filtered_conversations])
                
                if selected_id != "None":
                    selected_id = int(selected_id)
                    # Find selected conversation
                    selected_convo = next((c for c in filtered_conversations if c['id'] == selected_id), None)
                    
                    if selected_convo:
                        st.subheader(f"Conversation #{selected_id} - {selected_convo['employee_name']}")
                        
                        col1, col2, col3 = st.columns([2, 2, 1])
                        col1.markdown(f"**Date:** {selected_convo['date_time']}")
                        col2.markdown(f"**Topic:** {selected_convo.get('topic', 'Uncategorized')}")
                        
                        # Allow topic editing
                        new_topic = col3.text_input("Edit topic:", value=selected_convo.get('topic', ''), key=f"topic_edit_{selected_id}")
                        if new_topic != selected_convo.get('topic', '') and col3.button("Update Topic", key=f"update_topic_{selected_id}"):
                            if db_manager.update_conversation_topic(selected_id, new_topic):
                                st.success("Topic updated successfully!")
                                time.sleep(1)
                                st.rerun()
                            else:
                                st.error("Failed to update topic.")
                        
                        # Display Q&A
                        st.markdown("**Question:**")
                        st.markdown(f"<div class='card'>{selected_convo['question']}</div>", unsafe_allow_html=True)
                        
                        st.markdown("**Answer:**")
                        st.markdown(f"<div class='card'>{selected_convo['answer']}</div>", unsafe_allow_html=True)
                        
                        if selected_convo.get('summary'):
                            st.markdown("**Summary:**")
                            st.markdown(f"<div class='card'>{selected_convo['summary']}</div>", unsafe_allow_html=True)
            else:
                st.info("No conversations match the current filters.")
            
            # Export filtered data
            st.subheader("Export Data")
            if st.button("Export Filtered Data to CSV", key="export_filtered"):
                # Create a temporary file for the filtered data
                temp_file = os.path.join("data", "reports", f"filtered_conversations_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv")
                
                # Convert to DataFrame and save
                df = pd.DataFrame(filtered_conversations)
                df.to_csv(temp_file, index=False)
                
                # Provide download button
                with open(temp_file, "rb") as file:
                    st.download_button(
                        label="Download CSV",
                        data=file,
                        file_name=os.path.basename(temp_file),
                        mime="text/csv"
                    )
    
    # Tab 3: Employee Reports
    with tab3:
        st.subheader("Employee Reports")
        
        # Get unique employees from conversations
        employee_conversations = db_manager.get_conversation_counts_by_employee(limit=1000)
        
        if not employee_conversations:
            st.info("No employee conversation data available.")
        else:
            # Create dropdown of employees
            employee_options = [f"{e['employee_name']} ({e['employee_id']})" for e in employee_conversations]
            employee_options.insert(0, "Select an employee")
            
            selected_employee_option = st.selectbox("Select employee:", employee_options)
            
            if selected_employee_option != "Select an employee":
                # Extract employee ID from selection
                employee_id = selected_employee_option.split("(")[1].split(")")[0]
                
                # Generate and display employee report
                report_generator.render_streamlit_employee_report(employee_id)
    
    # Tab 4: System Management
    with tab4:
        st.subheader("System Management")
        
        # System info card
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.subheader("System Information")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write(f"**Database Path:** {db_manager.db_path}")
            if os.path.exists(db_manager.db_path):
                st.write(f"**Database Size:** {os.path.getsize(db_manager.db_path) / (1024*1024):.2f} MB")
            else:
                st.write("**Database Status:** Not created yet")
            st.write(f"**Admin Account:** {admin_data['name']}")
        
        with col2:
            st.write(f"**Session Start Time:** {st.session_state.get('login_time', 'Unknown')}")
            st.write(f"**Server Time:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        st.markdown("</div>", unsafe_allow_html=True)
        
        # Database management
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.subheader("Database Management")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("Export Full Database", key="export_full_db"):
                if not os.path.exists(db_manager.db_path):
                    st.warning("Database file does not exist yet. No conversations have been recorded.")
                else:
                    with st.spinner("Exporting database..."):
                        export_path = db_manager.export_conversations_to_csv(
                            os.path.join("data", "reports", f"full_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv")
                        )
                        
                        with open(export_path, "rb") as file:
                            st.download_button(
                                label="Download Full Export",
                                data=file,
                                file_name=os.path.basename(export_path),
                                mime="text/csv"
                            )
        
        with col2:
            # Database backup option
            if st.button("Backup Database", key="backup_db"):
                if not os.path.exists(db_manager.db_path):
                    st.warning("Database file does not exist yet. No conversations have been recorded.")
                else:
                    backup_path = f"data/backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
                    
                    # Create backup
                    import shutil
                    try:
                        shutil.copy2(db_manager.db_path, backup_path)
                        st.success(f"Database backed up to {backup_path}")
                    except Exception as e:
                        st.error(f"Backup failed: {e}")
        
        st.markdown("</div>", unsafe_allow_html=True)
        
        # Danger zone
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.subheader("⚠️ Danger Zone", help="These actions cannot be undone")
        
        # Delete conversation
        delete_id = st.number_input("Enter conversation ID to delete:", min_value=1, step=1)
        if st.button("Delete Conversation", key="delete_convo"):
            # Confirm deletion
            if st.checkbox("I understand this action cannot be undone", key="confirm_delete"):
                # Try to delete
                if db_manager.delete_conversation(delete_id):
                    st.success(f"Conversation #{delete_id} deleted successfully.")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error(f"Failed to delete conversation #{delete_id}. It may not exist.")
        
        st.markdown("</div>", unsafe_allow_html=True)
    
    # Footer
    st.markdown("<div class='footer'>© 2025 Valley Water HR Assistant | Developed by Team Sapphire</div>", unsafe_allow_html=True)

if __name__ == "__main__":
    main()