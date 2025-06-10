"""
Candidate Registration Form Component
Ensures proper candidate identification before scheduling interviews
"""

import streamlit as st
from typing import Dict, Optional
from datetime import datetime
import re


class CandidateRegistrationForm:
    """
    Registration form component that collects essential candidate information
    before allowing interview scheduling.
    """
    
    def __init__(self):
        self.initialize_registration_state()
    
    def initialize_registration_state(self):
        """Initialize registration state in session."""
        if 'registration_completed' not in st.session_state:
            st.session_state.registration_completed = False
        
        if 'registration_data' not in st.session_state:
            st.session_state.registration_data = {
                'full_name': '',
                'email': '',
                'phone': '',
                'position_interest': '',
                'experience_years': 0,
                'current_status': '',
                'how_heard_about_us': '',
                'registration_timestamp': None
            }
        
        if 'registration_validation' not in st.session_state:
            st.session_state.registration_validation = {
                'is_valid': False,
                'errors': []
            }
    
    def display_registration_form(self) -> bool:
        """
        Display the registration form and return True if completed successfully.
        
        Returns:
            bool: True if registration is complete and valid
        """
        if st.session_state.registration_completed:
            return True
        
        st.subheader("👤 Candidate Registration")
        st.write("Please complete this quick registration before we schedule your interview:")
        
        with st.form("candidate_registration_form"):
            # Personal Information
            st.write("**Personal Information**")
            full_name = st.text_input(
                "Full Name *", 
                value=st.session_state.registration_data['full_name'],
                placeholder="John Doe"
            )
            
            email = st.text_input(
                "Email Address *", 
                value=st.session_state.registration_data['email'],
                placeholder="john.doe@email.com"
            )
            
            phone = st.text_input(
                "Phone Number *", 
                value=st.session_state.registration_data['phone'],
                placeholder="+972-XX-XXX-XXXX"
            )
            
            # Position Information
            st.write("**Position Details**")
            position_interest = st.selectbox(
                "Position of Interest *",
                options=[
                    "",
                    "Python Developer - Backend",
                    "Python Developer - Full Stack", 
                    "Python Developer - Data Science",
                    "Python Developer - DevOps",
                    "Senior Python Developer",
                    "Python Team Lead"
                ],
                index=0 if not st.session_state.registration_data['position_interest'] 
                else ["", "Python Developer - Backend", "Python Developer - Full Stack", 
                     "Python Developer - Data Science", "Python Developer - DevOps",
                     "Senior Python Developer", "Python Team Lead"].index(
                         st.session_state.registration_data['position_interest']
                     ) if st.session_state.registration_data['position_interest'] in [
                         "Python Developer - Backend", "Python Developer - Full Stack", 
                         "Python Developer - Data Science", "Python Developer - DevOps",
                         "Senior Python Developer", "Python Team Lead"
                     ] else 0
            )
            
            experience_years = st.selectbox(
                "Years of Python Experience *",
                options=[0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, "10+"],
                index=st.session_state.registration_data['experience_years'] if isinstance(
                    st.session_state.registration_data['experience_years'], int
                ) else 0
            )
            
            current_status = st.selectbox(
                "Current Employment Status *",
                options=[
                    "",
                    "Currently employed, looking for new opportunities",
                    "Currently unemployed, actively job seeking", 
                    "Student/Recent graduate",
                    "Freelancer/Contractor",
                    "Career change from another field"
                ],
                index=0 if not st.session_state.registration_data['current_status']
                else ["", "Currently employed, looking for new opportunities",
                     "Currently unemployed, actively job seeking", 
                     "Student/Recent graduate", "Freelancer/Contractor",
                     "Career change from another field"].index(
                         st.session_state.registration_data['current_status']
                     ) if st.session_state.registration_data['current_status'] in [
                         "Currently employed, looking for new opportunities",
                         "Currently unemployed, actively job seeking", 
                         "Student/Recent graduate", "Freelancer/Contractor",
                         "Career change from another field"
                     ] else 0
            )
            
            # Optional information
            st.write("**Additional Information (Optional)**")
            how_heard_about_us = st.selectbox(
                "How did you hear about this position?",
                options=[
                    "",
                    "LinkedIn",
                    "Company website", 
                    "Job board (Indeed, Glassdoor, etc.)",
                    "Referral from current employee",
                    "Professional network",
                    "Recruiter contact",
                    "Social media",
                    "Other"
                ],
                index=0
            )
            
            # Form submission
            submitted = st.form_submit_button("Complete Registration", type="primary")
            
            if submitted:
                # Collect form data
                registration_data = {
                    'full_name': full_name.strip(),
                    'email': email.strip().lower(),
                    'phone': phone.strip(),
                    'position_interest': position_interest,
                    'experience_years': experience_years,
                    'current_status': current_status,
                    'how_heard_about_us': how_heard_about_us,
                    'registration_timestamp': datetime.now()
                }
                
                # Validate registration
                validation_result = self.validate_registration(registration_data)
                
                if validation_result['is_valid']:
                    # Save registration data
                    st.session_state.registration_data = registration_data
                    st.session_state.registration_completed = True
                    st.session_state.registration_validation = validation_result
                    
                    # Update candidate info in main session
                    st.session_state.candidate_info.update({
                        'name': registration_data['full_name'],
                        'email': registration_data['email'],
                        'phone': registration_data['phone'],
                        'experience': f"{registration_data['experience_years']} years Python",
                        'interest_level': 'high',  # They completed registration
                        'position': registration_data['position_interest'],
                        'current_status': registration_data['current_status']
                    })
                    
                    st.success("✅ Registration completed successfully!")
                    st.balloons()
                    st.rerun()
                    
                else:
                    # Show validation errors
                    st.session_state.registration_validation = validation_result
                    for error in validation_result['errors']:
                        st.error(f"❌ {error}")
        
        return st.session_state.registration_completed
    
    def validate_registration(self, data: Dict) -> Dict:
        """
        Validate registration data.
        
        Args:
            data: Registration data dictionary
            
        Returns:
            Dict with validation results
        """
        errors = []
        
        # Required field validation
        if not data['full_name'] or len(data['full_name']) < 2:
            errors.append("Full name is required (minimum 2 characters)")
        
        if not data['email']:
            errors.append("Email address is required")
        elif not self._is_valid_email(data['email']):
            errors.append("Please enter a valid email address")
        
        if not data['phone']:
            errors.append("Phone number is required")
        elif not self._is_valid_phone(data['phone']):
            errors.append("Please enter a valid phone number")
        
        if not data['position_interest']:
            errors.append("Please select the position you're interested in")
        
        if data['experience_years'] is None:
            errors.append("Please select your years of Python experience")
        
        if not data['current_status']:
            errors.append("Please select your current employment status")
        
        # Business logic validation
        if (data['position_interest'] and 'Senior' in data['position_interest'] and 
            isinstance(data['experience_years'], int) and data['experience_years'] < 3):
            errors.append("Senior positions typically require 3+ years of experience")
        
        return {
            'is_valid': len(errors) == 0,
            'errors': errors
        }
    
    def _is_valid_email(self, email: str) -> bool:
        """Validate email format."""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    def _is_valid_phone(self, phone: str) -> bool:
        """Validate phone format (basic validation)."""
        # Remove common formatting characters
        clean_phone = re.sub(r'[\s\-\(\)\+]', '', phone)
        # Check if it's at least 8 digits and at most 15 digits
        return clean_phone.isdigit() and 8 <= len(clean_phone) <= 15
    
    def display_registration_summary(self):
        """Display a summary of the completed registration."""
        if not st.session_state.registration_completed:
            return
        
        data = st.session_state.registration_data
        
        st.success("**✅ Registration Complete**")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write(f"**Name:** {data['full_name']}")
            st.write(f"**Email:** {data['email']}")
            st.write(f"**Phone:** {data['phone']}")
        
        with col2:
            st.write(f"**Position:** {data['position_interest']}")
            st.write(f"**Experience:** {data['experience_years']} years")
            st.write(f"**Status:** {data['current_status']}")
        
        if st.button("🔄 Update Registration"):
            st.session_state.registration_completed = False
            st.rerun()
    
    def get_registration_data(self) -> Optional[Dict]:
        """Get the completed registration data."""
        if st.session_state.registration_completed:
            return st.session_state.registration_data
        return None
    
    def is_registration_complete(self) -> bool:
        """Check if registration is complete."""
        return st.session_state.registration_completed


def create_registration_form() -> CandidateRegistrationForm:
    """Factory function to create a registration form instance."""
    return CandidateRegistrationForm() 