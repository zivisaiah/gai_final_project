"""
Admin Panel Component for Streamlit
Provides conversation analytics, agent performance monitoring, and system metrics visualization
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import json
import time
from collections import defaultdict, Counter
import sys
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from app.modules.agents.core_agent import AgentDecision
from app.modules.agents.scheduling_advisor import SchedulingDecision
from app.modules.agents.info_advisor import InfoResponse


class AdminPanel:
    """Admin panel for monitoring and analytics."""
    
    def __init__(self):
        """Initialize the admin panel."""
        self.setup_session_state()
    
    def setup_session_state(self):
        """Initialize session state variables for admin panel."""
        if 'admin_analytics' not in st.session_state:
            st.session_state.admin_analytics = {
                'conversation_logs': [],
                'agent_performance': defaultdict(list),
                'system_metrics': defaultdict(list),
                'user_feedback': [],
                'error_logs': []
            }
    
    def log_conversation_event(self, event_type: str, data: Dict):
        """Log a conversation event for analytics."""
        timestamp = datetime.now()
        event = {
            'timestamp': timestamp,
            'event_type': event_type,
            'data': data,
            'session_id': st.session_state.get('session_id', 'unknown')
        }
        st.session_state.admin_analytics['conversation_logs'].append(event)
        
        # Keep only last 1000 events to prevent memory issues
        if len(st.session_state.admin_analytics['conversation_logs']) > 1000:
            st.session_state.admin_analytics['conversation_logs'] = \
                st.session_state.admin_analytics['conversation_logs'][-1000:]
    
    def log_agent_performance(self, agent_name: str, decision: str, 
                            confidence: float, response_time: float):
        """Log agent performance metrics."""
        timestamp = datetime.now()
        performance_data = {
            'timestamp': timestamp,
            'agent': agent_name,
            'decision': decision,
            'confidence': confidence,
            'response_time': response_time
        }
        st.session_state.admin_analytics['agent_performance'][agent_name].append(performance_data)
        
        # Keep only last 500 entries per agent
        for agent in st.session_state.admin_analytics['agent_performance']:
            if len(st.session_state.admin_analytics['agent_performance'][agent]) > 500:
                st.session_state.admin_analytics['agent_performance'][agent] = \
                    st.session_state.admin_analytics['agent_performance'][agent][-500:]
    
    def log_system_metrics(self, metric_type: str, value: float, metadata: Dict = None):
        """Log system performance metrics."""
        timestamp = datetime.now()
        metric_data = {
            'timestamp': timestamp,
            'metric_type': metric_type,
            'value': value,
            'metadata': metadata or {}
        }
        st.session_state.admin_analytics['system_metrics'][metric_type].append(metric_data)
        
        # Keep only last 200 entries per metric
        for metric in st.session_state.admin_analytics['system_metrics']:
            if len(st.session_state.admin_analytics['system_metrics'][metric]) > 200:
                st.session_state.admin_analytics['system_metrics'][metric] = \
                    st.session_state.admin_analytics['system_metrics'][metric][-200:]
    
    def display_conversation_analytics(self):
        """Display conversation analytics dashboard."""
        st.subheader("📊 Conversation Analytics")
        
        logs = st.session_state.admin_analytics['conversation_logs']
        
        if not logs:
            st.info("No conversation data available yet. Start a conversation to see analytics.")
            return
        
        # Create metrics overview
        col1, col2, col3, col4 = st.columns(4)
        
        # Count different types of events
        event_counts = Counter(log['event_type'] for log in logs)
        decision_counts = Counter(
            log['data'].get('decision', 'unknown') 
            for log in logs if log['event_type'] == 'agent_decision'
        )
        
        with col1:
            st.metric("Total Interactions", len(logs))
        
        with col2:
            st.metric("INFO Requests", decision_counts.get('INFO', 0))
        
        with col3:
            st.metric("Schedule Attempts", decision_counts.get('SCHEDULE', 0))
        
        with col4:
            st.metric("Conversations Ended", decision_counts.get('END', 0))
        
        # Decision distribution chart
        if decision_counts:
            col1, col2 = st.columns(2)
            
            with col1:
                fig_decisions = px.pie(
                    values=list(decision_counts.values()),
                    names=list(decision_counts.keys()),
                    title="Agent Decision Distribution"
                )
                fig_decisions.update_layout(height=400)
                st.plotly_chart(fig_decisions, use_container_width=True)
            
            with col2:
                # Timeline of decisions
                df_logs = pd.DataFrame([
                    {
                        'timestamp': log['timestamp'],
                        'decision': log['data'].get('decision', 'unknown'),
                        'event_type': log['event_type']
                    }
                    for log in logs if log['event_type'] == 'agent_decision'
                ])
                
                if not df_logs.empty:
                    # Group by hour and decision type
                    df_logs['hour'] = df_logs['timestamp'].dt.floor('H')
                    decision_timeline = df_logs.groupby(['hour', 'decision']).size().reset_index(name='count')
                    
                    fig_timeline = px.bar(
                        decision_timeline,
                        x='hour',
                        y='count',
                        color='decision',
                        title="Decision Timeline (by Hour)"
                    )
                    fig_timeline.update_layout(height=400)
                    st.plotly_chart(fig_timeline, use_container_width=True)
        
        # Recent conversation events table
        st.subheader("Recent Events")
        recent_logs = logs[-20:]  # Last 20 events
        
        if recent_logs:
            df_recent = pd.DataFrame([
                {
                    'Time': log['timestamp'].strftime('%H:%M:%S'),
                    'Event': log['event_type'],
                    'Decision': log['data'].get('decision', 'N/A'),
                    'Agent': log['data'].get('agent_type', 'N/A'),
                    'Reasoning': log['data'].get('reasoning', 'N/A')[:50] + '...' if log['data'].get('reasoning', '') else 'N/A'
                }
                for log in reversed(recent_logs)
            ])
            st.dataframe(df_recent, use_container_width=True)
    
    def display_agent_performance(self):
        """Display agent performance monitoring."""
        st.subheader("🤖 Agent Performance Monitoring")
        
        performance_data = st.session_state.admin_analytics['agent_performance']
        
        if not any(performance_data.values()):
            st.info("No agent performance data available yet.")
            return
        
        # Agent performance metrics
        col1, col2 = st.columns(2)
        
        with col1:
            # Response time analysis
            all_response_times = []
            agent_names = []
            
            for agent, metrics in performance_data.items():
                for metric in metrics:
                    all_response_times.append(metric['response_time'])
                    agent_names.append(agent)
            
            if all_response_times:
                df_response = pd.DataFrame({
                    'agent': agent_names,
                    'response_time': all_response_times
                })
                
                fig_response = px.box(
                    df_response,
                    x='agent',
                    y='response_time',
                    title="Response Time Distribution by Agent"
                )
                fig_response.update_layout(height=400)
                st.plotly_chart(fig_response, use_container_width=True)
        
        with col2:
            # Confidence scores
            all_confidence = []
            agent_names_conf = []
            
            for agent, metrics in performance_data.items():
                for metric in metrics:
                    if metric['confidence'] is not None:
                        all_confidence.append(metric['confidence'])
                        agent_names_conf.append(agent)
            
            if all_confidence:
                df_confidence = pd.DataFrame({
                    'agent': agent_names_conf,
                    'confidence': all_confidence
                })
                
                fig_confidence = px.histogram(
                    df_confidence,
                    x='confidence',
                    color='agent',
                    title="Confidence Score Distribution",
                    nbins=20
                )
                fig_confidence.update_layout(height=400)
                st.plotly_chart(fig_confidence, use_container_width=True)
        
        # Agent performance summary table
        st.subheader("Agent Performance Summary")
        summary_data = []
        
        for agent, metrics in performance_data.items():
            if metrics:
                response_times = [m['response_time'] for m in metrics]
                confidences = [m['confidence'] for m in metrics if m['confidence'] is not None]
                
                summary_data.append({
                    'Agent': agent,
                    'Total Calls': len(metrics),
                    'Avg Response Time (s)': f"{sum(response_times)/len(response_times):.2f}",
                    'Min Response Time (s)': f"{min(response_times):.2f}",
                    'Max Response Time (s)': f"{max(response_times):.2f}",
                    'Avg Confidence': f"{sum(confidences)/len(confidences):.2f}" if confidences else "N/A",
                    'Last Active': max(m['timestamp'] for m in metrics).strftime('%H:%M:%S')
                })
        
        if summary_data:
            df_summary = pd.DataFrame(summary_data)
            st.dataframe(df_summary, use_container_width=True)
    
    def display_system_metrics(self):
        """Display system metrics visualization."""
        st.subheader("⚙️ System Metrics")
        
        metrics_data = st.session_state.admin_analytics['system_metrics']
        
        if not any(metrics_data.values()):
            st.info("No system metrics available yet.")
            return
        
        # System metrics overview
        metric_types = list(metrics_data.keys())
        
        if len(metric_types) >= 2:
            col1, col2 = st.columns(2)
            
            # Display first two metrics as time series
            for i, (metric_type, data) in enumerate(list(metrics_data.items())[:2]):
                with col1 if i == 0 else col2:
                    if data:
                        df_metric = pd.DataFrame([
                            {
                                'timestamp': entry['timestamp'],
                                'value': entry['value']
                            }
                            for entry in data
                        ])
                        
                        fig_metric = px.line(
                            df_metric,
                            x='timestamp',
                            y='value',
                            title=f"{metric_type.title()} Over Time"
                        )
                        fig_metric.update_layout(height=300)
                        st.plotly_chart(fig_metric, use_container_width=True)
        
        # System health indicators
        st.subheader("System Health Indicators")
        health_cols = st.columns(4)
        
        # Calculate health metrics
        current_time = datetime.now()
        recent_threshold = current_time - timedelta(minutes=5)
        
        # Recent activity indicator
        recent_logs = [
            log for log in st.session_state.admin_analytics['conversation_logs']
            if log['timestamp'] > recent_threshold
        ]
        
        with health_cols[0]:
            st.metric("Recent Activity (5m)", len(recent_logs))
        
        with health_cols[1]:
            error_count = len(st.session_state.admin_analytics['error_logs'])
            st.metric("Error Count", error_count)
        
        with health_cols[2]:
            # Calculate average response time
            all_metrics = []
            for agent_metrics in st.session_state.admin_analytics['agent_performance'].values():
                all_metrics.extend(agent_metrics)
            
            if all_metrics:
                avg_response_time = sum(m['response_time'] for m in all_metrics) / len(all_metrics)
                st.metric("Avg Response Time", f"{avg_response_time:.2f}s")
            else:
                st.metric("Avg Response Time", "N/A")
        
        with health_cols[3]:
            # System uptime (session duration)
            if 'session_start_time' in st.session_state:
                uptime = current_time - st.session_state.session_start_time
                hours = uptime.total_seconds() / 3600
                st.metric("Session Uptime", f"{hours:.1f}h")
            else:
                st.session_state.session_start_time = current_time
                st.metric("Session Uptime", "0.0h")
    
    def display_export_controls(self):
        """Display conversation export functionality."""
        st.subheader("📁 Export & Data Management")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("📊 Export Analytics Data"):
                self.export_analytics_data()
        
        with col2:
            if st.button("💬 Export Conversations"):
                self.export_conversation_data()
        
        with col3:
            if st.button("🧹 Clear Analytics Data"):
                if st.session_state.get('confirm_clear', False):
                    self.clear_analytics_data()
                    st.session_state.confirm_clear = False
                    st.success("Analytics data cleared!")
                    st.rerun()
                else:
                    st.session_state.confirm_clear = True
                    st.warning("Click again to confirm data clearing")
    
    def export_analytics_data(self):
        """Export analytics data to downloadable format."""
        try:
            analytics_data = st.session_state.admin_analytics
            
            # Convert datetime objects to strings for JSON serialization
            export_data = {}
            for key, value in analytics_data.items():
                if isinstance(value, dict):
                    export_data[key] = {}
                    for subkey, subvalue in value.items():
                        export_data[key][subkey] = self._serialize_for_export(subvalue)
                else:
                    export_data[key] = self._serialize_for_export(value)
            
            # Create downloadable JSON
            json_str = json.dumps(export_data, indent=2, default=str)
            
            st.download_button(
                label="Download Analytics JSON",
                data=json_str,
                file_name=f"recruitment_analytics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json"
            )
            
        except Exception as e:
            st.error(f"Error exporting analytics data: {e}")
    
    def export_conversation_data(self):
        """Export conversation logs in CSV format."""
        try:
            logs = st.session_state.admin_analytics['conversation_logs']
            
            if not logs:
                st.warning("No conversation data to export")
                return
            
            # Convert to DataFrame
            df_export = pd.DataFrame([
                {
                    'timestamp': log['timestamp'],
                    'event_type': log['event_type'],
                    'decision': log['data'].get('decision', ''),
                    'agent_type': log['data'].get('agent_type', ''),
                    'reasoning': log['data'].get('reasoning', ''),
                    'session_id': log['session_id']
                }
                for log in logs
            ])
            
            # Convert to CSV
            csv_str = df_export.to_csv(index=False)
            
            st.download_button(
                label="Download Conversations CSV",
                data=csv_str,
                file_name=f"conversations_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
            
        except Exception as e:
            st.error(f"Error exporting conversation data: {e}")
    
    def clear_analytics_data(self):
        """Clear all analytics data."""
        st.session_state.admin_analytics = {
            'conversation_logs': [],
            'agent_performance': defaultdict(list),
            'system_metrics': defaultdict(list),
            'user_feedback': [],
            'error_logs': []
        }
    
    def _serialize_for_export(self, obj):
        """Helper method to serialize objects for export."""
        if isinstance(obj, list):
            return [self._serialize_for_export(item) for item in obj]
        elif isinstance(obj, dict):
            return {key: self._serialize_for_export(value) for key, value in obj.items()}
        elif isinstance(obj, datetime):
            return obj.isoformat()
        else:
            return obj
    
    def display_admin_panel(self):
        """Display the complete admin panel."""
        st.title("🛠️ Admin Panel")
        
        # Create tabs for different sections
        tab1, tab2, tab3, tab4 = st.tabs([
            "📊 Analytics", 
            "🤖 Agent Performance", 
            "⚙️ System Metrics", 
            "📁 Export & Data"
        ])
        
        with tab1:
            self.display_conversation_analytics()
        
        with tab2:
            self.display_agent_performance()
        
        with tab3:
            self.display_system_metrics()
        
        with tab4:
            self.display_export_controls()


def create_admin_panel() -> AdminPanel:
    """Factory function to create admin panel instance."""
    return AdminPanel() 