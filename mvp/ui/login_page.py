"""
Login Page for Supply Chain AI Assistant

Provides authentication interface with username/password form.
"""

import streamlit as st
from typing import Optional
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from auth.auth_manager import AuthManager, User
from auth.session_manager import SessionManager


def render_login_page(auth_manager: AuthManager, session_manager: SessionManager) -> Optional[tuple[str, User]]:
    """
    Render login page and handle authentication.
    
    Args:
        auth_manager: Authentication manager instance
        session_manager: Session manager instance
        
    Returns:
        Tuple of (session_id, user) if login successful, None otherwise
    """
    # Center the login form
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.title("🏭 Supply Chain AI Assistant")
        st.markdown("---")
        st.subheader("Login")
        
        # Login form
        with st.form("login_form", clear_on_submit=False):
            username = st.text_input(
                "Username",
                placeholder="Enter your username",
                key="login_username"
            )
            
            password = st.text_input(
                "Password",
                type="password",
                placeholder="Enter your password",
                key="login_password"
            )
            
            submit_button = st.form_submit_button("Login", use_container_width=True)
            
            if submit_button:
                if not username or not password:
                    st.error("Please enter both username and password")
                    return None
                
                # Attempt authentication
                user = auth_manager.authenticate(username, password)
                
                if user is None:
                    st.error("Invalid username or password. Please try again.")
                    return None
                
                # Check if user has any personas
                if not user.personas:
                    st.error("Your account has no assigned personas. Please contact your administrator.")
                    return None
                
                # Create session
                session_id = session_manager.create_session(username)
                
                st.success(f"Welcome, {username}!")
                
                # Return session info
                return (session_id, user)
        
        # Help text
        st.markdown("---")
        st.caption("Contact your administrator if you need access or have forgotten your password.")
    
    return None


def show_login_page(auth_manager: AuthManager, session_manager: SessionManager):
    """
    Display login page and manage authentication state.
    
    This function integrates with Streamlit session state to manage login.
    
    Args:
        auth_manager: Authentication manager instance
        session_manager: Session manager instance
    """
    # Initialize session state
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    if 'session_id' not in st.session_state:
        st.session_state.session_id = None
    if 'user' not in st.session_state:
        st.session_state.user = None
    
    # Check if already authenticated
    if st.session_state.authenticated and st.session_state.session_id:
        # Verify session is still valid
        session = session_manager.get_session(st.session_state.session_id)
        if session is None:
            # Session expired
            st.session_state.authenticated = False
            st.session_state.session_id = None
            st.session_state.user = None
            st.warning("Your session has expired. Please login again.")
            st.rerun()
        else:
            # Already authenticated, don't show login page
            return
    
    # Show login page
    result = render_login_page(auth_manager, session_manager)
    
    if result:
        session_id, user = result
        st.session_state.authenticated = True
        st.session_state.session_id = session_id
        st.session_state.user = user
        st.rerun()


def logout(session_manager: SessionManager):
    """
    Handle user logout.
    
    Args:
        session_manager: Session manager instance
    """
    if 'session_id' in st.session_state and st.session_state.session_id:
        session_manager.invalidate_session(st.session_state.session_id)
    
    # Clear session state
    st.session_state.authenticated = False
    st.session_state.session_id = None
    st.session_state.user = None
    st.session_state.current_persona = None
    
    # Clear any other session state variables
    for key in list(st.session_state.keys()):
        if key not in ['authenticated', 'session_id', 'user', 'current_persona']:
            del st.session_state[key]


def is_authenticated() -> bool:
    """
    Check if user is authenticated.
    
    Returns:
        True if authenticated, False otherwise
    """
    return st.session_state.get('authenticated', False)


def get_current_user() -> Optional[User]:
    """
    Get current authenticated user.
    
    Returns:
        User object if authenticated, None otherwise
    """
    return st.session_state.get('user', None)


def get_session_id() -> Optional[str]:
    """
    Get current session ID.
    
    Returns:
        Session ID if authenticated, None otherwise
    """
    return st.session_state.get('session_id', None)
