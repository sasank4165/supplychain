"""Login UI components for Streamlit"""
import streamlit as st
from auth_manager import AuthManager
import os

def render_login_page(auth_manager: AuthManager):
    """Render login page"""
    st.title("🔐 Supply Chain Agent Login")
    
    # Create tabs for different actions
    tab1, tab2, tab3 = st.tabs(["Sign In", "Forgot Password", "About"])
    
    with tab1:
        render_sign_in(auth_manager)
    
    with tab2:
        render_forgot_password(auth_manager)
    
    with tab3:
        st.markdown("""
        ## Supply Chain Agentic AI
        
        This application provides AI-powered assistance for supply chain management.
        
        ### Available Roles:
        - **Warehouse Manager**: Inventory optimization and forecasting
        - **Field Engineer**: Logistics and order fulfillment
        - **Procurement Specialist**: Supplier analysis and cost optimization
        
        ### Features:
        - Natural language queries
        - Real-time data analysis
        - Predictive analytics
        - Role-based access control
        
        Contact your administrator for access.
        """)

def render_sign_in(auth_manager: AuthManager):
    """Render sign in form"""
    st.subheader("Sign In")
    
    with st.form("login_form"):
        username = st.text_input("Username", key="login_username")
        password = st.text_input("Password", type="password", key="login_password")
        submit = st.form_submit_button("Sign In")
        
        if submit:
            if not username or not password:
                st.error("Please enter username and password")
                return
            
            with st.spinner("Signing in..."):
                result = auth_manager.sign_in(username, password)
            
            if result.get("success"):
                # Store tokens in session state
                st.session_state.authenticated = True
                st.session_state.access_token = result['access_token']
                st.session_state.id_token = result['id_token']
                st.session_state.refresh_token = result['refresh_token']
                st.session_state.username = result['username']
                st.session_state.email = result['email']
                st.session_state.groups = result['groups']
                st.session_state.persona = result['persona']
                
                st.success(f"Welcome, {result['username']}!")
                st.rerun()
            elif result.get("challenge"):
                st.warning(f"Challenge required: {result['challenge']}")
                if result['challenge'] == 'NEW_PASSWORD_REQUIRED':
                    render_new_password_challenge(auth_manager, result['session'])
            else:
                st.error(f"Login failed: {result.get('error', 'Unknown error')}")

def render_new_password_challenge(auth_manager: AuthManager, session: str):
    """Render new password challenge for first-time login"""
    st.subheader("Change Password")
    st.info("You must change your password before continuing.")
    
    with st.form("new_password_form"):
        new_password = st.text_input("New Password", type="password")
        confirm_password = st.text_input("Confirm Password", type="password")
        submit = st.form_submit_button("Change Password")
        
        if submit:
            if new_password != confirm_password:
                st.error("Passwords do not match")
                return
            
            # Handle password change challenge
            st.info("Password change functionality requires additional implementation")

def render_forgot_password(auth_manager: AuthManager):
    """Render forgot password form"""
    st.subheader("Forgot Password")
    
    if 'reset_code_sent' not in st.session_state:
        st.session_state.reset_code_sent = False
    
    if not st.session_state.reset_code_sent:
        with st.form("forgot_password_form"):
            username = st.text_input("Username", key="forgot_username")
            submit = st.form_submit_button("Send Reset Code")
            
            if submit:
                if not username:
                    st.error("Please enter username")
                    return
                
                result = auth_manager.forgot_password(username)
                if result.get("success"):
                    st.success("Reset code sent to your email")
                    st.session_state.reset_code_sent = True
                    st.session_state.reset_username = username
                    st.rerun()
                else:
                    st.error(f"Error: {result.get('error')}")
    else:
        with st.form("confirm_reset_form"):
            code = st.text_input("Verification Code")
            new_password = st.text_input("New Password", type="password")
            confirm_password = st.text_input("Confirm Password", type="password")
            submit = st.form_submit_button("Reset Password")
            
            if submit:
                if new_password != confirm_password:
                    st.error("Passwords do not match")
                    return
                
                result = auth_manager.confirm_forgot_password(
                    st.session_state.reset_username,
                    code,
                    new_password
                )
                
                if result.get("success"):
                    st.success("Password reset successfully! Please sign in.")
                    st.session_state.reset_code_sent = False
                    del st.session_state.reset_username
                else:
                    st.error(f"Error: {result.get('error')}")

def render_user_profile(auth_manager: AuthManager):
    """Render user profile in sidebar"""
    if not st.session_state.get('authenticated'):
        return
    
    with st.sidebar:
        st.markdown("---")
        st.subheader("👤 User Profile")
        
        # User info
        st.text(f"Username: {st.session_state.username}")
        st.text(f"Email: {st.session_state.email}")
        st.text(f"Role: {st.session_state.persona.replace('_', ' ').title()}")
        
        # Show accessible resources
        with st.expander("Access Permissions"):
            groups = st.session_state.groups
            tables = auth_manager.get_accessible_tables(groups)
            agents = auth_manager.get_accessible_agents(groups)
            
            st.markdown("**Accessible Tables:**")
            for table in tables:
                st.text(f"• {table}")
            
            st.markdown("**Accessible Agents:**")
            for agent in agents:
                st.text(f"• {agent.replace('_', ' ').title()}")
        
        # Change password
        if st.button("Change Password"):
            st.session_state.show_change_password = True
        
        # Sign out
        if st.button("Sign Out"):
            result = auth_manager.sign_out(st.session_state.access_token)
            if result.get("success"):
                # Clear session state
                for key in list(st.session_state.keys()):
                    del st.session_state[key]
                st.rerun()

def render_change_password_dialog(auth_manager: AuthManager):
    """Render change password dialog"""
    if not st.session_state.get('show_change_password'):
        return
    
    st.subheader("Change Password")
    
    with st.form("change_password_form"):
        old_password = st.text_input("Current Password", type="password")
        new_password = st.text_input("New Password", type="password")
        confirm_password = st.text_input("Confirm New Password", type="password")
        
        col1, col2 = st.columns(2)
        with col1:
            submit = st.form_submit_button("Change Password")
        with col2:
            cancel = st.form_submit_button("Cancel")
        
        if cancel:
            st.session_state.show_change_password = False
            st.rerun()
        
        if submit:
            if new_password != confirm_password:
                st.error("Passwords do not match")
                return
            
            result = auth_manager.change_password(
                st.session_state.access_token,
                old_password,
                new_password
            )
            
            if result.get("success"):
                st.success("Password changed successfully!")
                st.session_state.show_change_password = False
                st.rerun()
            else:
                st.error(f"Error: {result.get('error')}")

def check_authentication():
    """Check if user is authenticated"""
    return st.session_state.get('authenticated', False)

def get_current_user():
    """Get current user info"""
    if not check_authentication():
        return None
    
    return {
        "username": st.session_state.get('username'),
        "email": st.session_state.get('email'),
        "persona": st.session_state.get('persona'),
        "groups": st.session_state.get('groups', []),
        "access_token": st.session_state.get('access_token')
    }
