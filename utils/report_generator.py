import pandas as pd
import matplotlib.pyplot as plt
import io
import base64
import os
from datetime import datetime
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import json
from utils.db_manager import DBManager

class ReportGenerator:
    """Class for generating reports from conversation data"""
    
    def __init__(self, db_manager=None):
        """Initialize with a database manager"""
        self.db_manager = db_manager or DBManager()
        self.report_dir = "data/reports"
        os.makedirs(self.report_dir, exist_ok=True)
    
    def generate_employee_report(self, employee_id, employee_name=None):
        """Generate a report for a specific employee"""
        # Get conversations for this employee
        conversations = self.db_manager.get_employee_conversations(employee_id)
        
        if not conversations:
            return {
                "employee_id": employee_id,
                "employee_name": employee_name,
                "total_conversations": 0,
                "report_date": datetime.now().strftime("%Y-%m-%d"),
                "conversations": []
            }
        
        # If name not provided, use from first conversation
        if not employee_name and conversations:
            employee_name = conversations[0]["employee_name"]
        
        # Extract topics
        topics = {}
        for convo in conversations:
            topic = convo.get("topic", "Uncategorized")
            topics[topic] = topics.get(topic, 0) + 1
        
        # Prepare report data
        report = {
            "employee_id": employee_id,
            "employee_name": employee_name,
            "total_conversations": len(conversations),
            "report_date": datetime.now().strftime("%Y-%m-%d"),
            "topics": topics,
            "conversations": conversations
        }
        
        return report
    
    def generate_admin_report(self, days=30):
        """Generate an administrative report across all employees"""
        # Get overall statistics
        stats = self.db_manager.get_conversation_stats()
        
        # Get conversation trends by date
        trends = self.db_manager.get_conversation_counts_by_date(days)
        
        # Get top employees by conversation count
        top_employees = self.db_manager.get_conversation_counts_by_employee(limit=10)
        
        # Get top topics
        top_topics = self.db_manager.get_top_topics(limit=10)
        
        # Prepare report data
        report = {
            "report_date": datetime.now().strftime("%Y-%m-%d"),
            "date_range": f"Last {days} days",
            "statistics": stats,
            "trends": trends,
            "top_employees": top_employees,
            "top_topics": top_topics
        }
        
        return report
    
    def save_report_to_json(self, report, filename=None):
        """Save a report to a JSON file"""
        if not filename:
            # Generate filename based on report type and date
            if "employee_id" in report:
                filename = f"employee_report_{report['employee_id']}_{report['report_date']}.json"
            else:
                filename = f"admin_report_{report['report_date']}.json"
        
        # Ensure it has .json extension
        if not filename.endswith(".json"):
            filename += ".json"
            
        # Create full path
        file_path = os.path.join(self.report_dir, filename)
        
        # Save to file
        with open(file_path, "w") as f:
            json.dump(report, f, indent=2)
        
        return file_path
    
    def export_conversations_to_csv(self, employee_id=None, filename=None):
        """Export conversations to CSV"""
        if not filename:
            if employee_id:
                filename = f"conversations_{employee_id}_{datetime.now().strftime('%Y%m%d')}.csv"
            else:
                filename = f"all_conversations_{datetime.now().strftime('%Y%m%d')}.csv"
                
        # Create full path
        file_path = os.path.join(self.report_dir, filename)
        
        # Use database manager to export
        return self.db_manager.export_conversations_to_csv(file_path, filter_employee=employee_id)
    
    def plot_conversation_trends(self, trends_data=None, days=30):
        """Generate a plot of conversation trends over time"""
        if trends_data is None:
            # Get trend data from database
            trends_data = self.db_manager.get_conversation_counts_by_date(days)
            
        if not trends_data:
            return None
            
        # Convert to DataFrame
        df = pd.DataFrame(trends_data)
        
        # Create plotly figure
        fig = px.line(
            df, 
            x='day', 
            y='count', 
            title='Conversations Over Time',
            labels={'day': 'Date', 'count': 'Number of Conversations'},
            markers=True
        )
        
        fig.update_layout(
            xaxis_title="Date",
            yaxis_title="Number of Conversations",
            hovermode="x unified"
        )
        
        return fig
    
    def plot_topic_distribution(self, topics_data=None):
        """Generate a plot of conversation topics distribution"""
        if topics_data is None:
            # Get topic data from database
            topics_data = self.db_manager.get_top_topics()
            
        if not topics_data:
            return None
        
        # Convert to DataFrame
        df = pd.DataFrame(topics_data)
        
        # Create plotly figure
        fig = px.pie(
            df, 
            values='count', 
            names='name', 
            title='Conversation Topics',
            hole=0.3
        )
        
        fig.update_traces(textposition='inside', textinfo='percent+label')
        
        return fig
    
    def plot_employee_activity(self, employee_data=None):
        """Generate a plot of conversation activity by employee"""
        if employee_data is None:
            # Get employee data from database
            employee_data = self.db_manager.get_conversation_counts_by_employee()
            
        if not employee_data:
            return None
        
        # Convert to DataFrame
        df = pd.DataFrame(employee_data)
        
        # Create plotly figure
        fig = px.bar(
            df,
            x='employee_name',
            y='count',
            title='Conversations by Employee',
            labels={'employee_name': 'Employee', 'count': 'Number of Conversations'},
            color='count',
            color_continuous_scale=px.colors.sequential.Viridis
        )
        
        fig.update_layout(
            xaxis_title="Employee",
            yaxis_title="Number of Conversations",
            xaxis={'categoryorder':'total descending'}
        )
        
        return fig
    
    def render_streamlit_employee_report(self, employee_id):
        """Render an employee report in Streamlit"""
        # Get report data
        report = self.generate_employee_report(employee_id)
        
        if report["total_conversations"] == 0:
            st.info(f"No conversations found for employee ID: {employee_id}")
            return
        
        # Display employee info
        st.subheader(f"Report for: {report['employee_name']} ({report['employee_id']})")
        st.write(f"Total conversations: {report['total_conversations']}")
        st.write(f"Report generated on: {report['report_date']}")
        
        # Display topics chart if there are topics
        if report["topics"]:
            # Convert topics to format needed for chart
            topics_data = [{"name": k, "count": v} for k, v in report["topics"].items()]
            fig = self.plot_topic_distribution(topics_data)
            if fig:
                st.plotly_chart(fig, use_container_width=True)
        
        # Display conversations
        st.subheader("Conversation History")
        for i, convo in enumerate(report["conversations"]):
            with st.expander(f"Conversation {i+1}: {convo['date_time']} - {convo.get('topic', 'No topic')}"):
                st.write(f"**Question**: {convo['question']}")
                st.write(f"**Answer**: {convo['answer']}")
                if convo.get('summary'):
                    st.write(f"**Summary**: {convo['summary']}")
        
        # Export options
        st.subheader("Export Options")
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("Export to CSV"):
                csv_path = self.export_conversations_to_csv(employee_id)
                with open(csv_path, "rb") as file:
                    st.download_button(
                        label="Download CSV",
                        data=file,
                        file_name=os.path.basename(csv_path),
                        mime="text/csv"
                    )
        
        with col2:
            if st.button("Export to JSON"):
                json_path = self.save_report_to_json(report)
                with open(json_path, "rb") as file:
                    st.download_button(
                        label="Download JSON",
                        data=file,
                        file_name=os.path.basename(json_path),
                        mime="application/json"
                    )
    
    def render_streamlit_admin_report(self):
        """Render an administrative report in Streamlit"""
        # Get report data
        report = self.generate_admin_report()
        
        # Display overall stats
        st.subheader("Overall Statistics")
        stats = report["statistics"]
        
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Conversations", stats["total_conversations"])
        col2.metric("Unique Employees", stats["unique_employees"])
        col3.metric("Last 7 Days", stats["conversations_last_7_days"])
        col4.metric("Avg Answer Length", f"{int(stats['avg_answer_length'])} chars")
        
        # Display trends chart
        st.subheader("Conversation Trends")
        trends_fig = self.plot_conversation_trends(report["trends"])
        if trends_fig:
            st.plotly_chart(trends_fig, use_container_width=True)
        
        # Display topic distribution
        st.subheader("Topic Distribution")
        topics_fig = self.plot_topic_distribution([{"name": t["name"], "count": t["count"]} for t in report["top_topics"]])
        if topics_fig:
            st.plotly_chart(topics_fig, use_container_width=True)
        
        # Display employee activity
        st.subheader("Employee Activity")
        employee_fig = self.plot_employee_activity(report["top_employees"])
        if employee_fig:
            st.plotly_chart(employee_fig, use_container_width=True)
        
        # Export options
        st.subheader("Export Options")
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("Export to CSV"):
                csv_path = self.export_conversations_to_csv()
                with open(csv_path, "rb") as file:
                    st.download_button(
                        label="Download CSV",
                        data=file,
                        file_name=os.path.basename(csv_path),
                        mime="text/csv"
                    )
        
        with col2:
            if st.button("Export to JSON"):
                json_path = self.save_report_to_json(report)
                with open(json_path, "rb") as file:
                    st.download_button(
                        label="Download JSON",
                        data=file,
                        file_name=os.path.basename(json_path),
                        mime="application/json"
                    )

# Example usage
if __name__ == "__main__":
    # Initialize the report generator
    report_gen = ReportGenerator()
    
    # Test generating an employee report
    employee_report = report_gen.generate_employee_report("test")
    print(f"Generated employee report with {employee_report['total_conversations']} conversations")
    
    # Test generating an admin report
    admin_report = report_gen.generate_admin_report()
    print(f"Generated admin report with trends for {len(admin_report['trends'])} days")