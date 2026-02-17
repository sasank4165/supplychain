# UI Components

This directory contains all Streamlit UI components for the Supply Chain AI Assistant.

## Components

### 1. login_page.py
Authentication interface with username/password form.

**Features:**
- Username and password input
- Integration with AuthManager
- Session creation on successful login
- Error handling for invalid credentials
- Session state management

**Functions:**
- `render_login_page()`: Render login form
- `show_login_page()`: Display login page with state management
- `logout()`: Handle user logout
- `is_authenticated()`: Check authentication status
- `get_current_user()`: Get current user object
- `get_session_id()`: Get current session ID

### 2. main_app.py
Main application interface with persona selector and query input.

**Features:**
- Persona selector dropdown
- Query text input with 1000 character limit
- Integration with query orchestrator
- Loading indicators during query processing
- Example queries for each persona
- Clear history functionality

**Functions:**
- `render_main_interface()`: Render main UI
- `show_loading_indicator()`: Display loading state
- `get_persona_icon()`: Get icon for persona
- `show_example_queries()`: Display example queries
- `get_example_query()`: Get clicked example query

### 3. results_display.py
Query results display with table and chart visualizations.

**Features:**
- Formatted query results display
- DataFrame visualization with sorting/filtering
- Automatic chart generation (bar, line)
- Summary statistics
- CSV export functionality
- Metadata display (SQL queries, tool calls)
- Error message display

**Functions:**
- `display_query_response()`: Display complete query response
- `display_data()`: Display data with appropriate visualization
- `display_dataframe()`: Display DataFrame with export
- `create_visualizations()`: Create automatic charts
- `display_metadata()`: Display additional information
- `display_error()`: Display error messages

### 4. cost_dashboard.py
Cost tracking dashboard with service breakdown.

**Features:**
- Per-query cost display
- Daily cost tracking
- Monthly cost estimates
- Cost breakdown by service (Bedrock, Redshift, Lambda)
- Token usage tracking
- Cost distribution visualization

**Functions:**
- `display_cost_dashboard()`: Display full cost dashboard
- `display_cost_breakdown()`: Display service breakdown
- `display_service_breakdown()`: Display individual service costs
- `display_monthly_estimate()`: Display monthly projections
- `display_query_cost()`: Display single query cost
- `display_cost_summary_sidebar()`: Compact sidebar display

### 5. conversation_sidebar.py
Conversation history with clickable past queries.

**Features:**
- Last 10 interactions display
- Clickable queries to re-run
- Timestamp display
- Clear history functionality
- Cache statistics display
- Cache management (clear cache)

**Functions:**
- `display_conversation_sidebar()`: Display sidebar with history
- `display_history_list()`: Display list of interactions
- `display_history_item()`: Display single interaction
- `display_cache_stats_sidebar()`: Display cache metrics
- `display_full_conversation_history()`: Display full history in main area
- `get_rerun_query()`: Get query to re-run
- `show_conversation_tips()`: Display usage tips

### 6. app.py (Main Entry Point)
Main application that ties all components together.

**Features:**
- Application initialization
- Component orchestration
- Session state management
- Authentication flow
- Main layout with sidebar
- Error handling
- Logging integration

**Functions:**
- `initialize_app()`: Initialize all components
- `main()`: Main application function

## Usage

### Running the Application

```bash
# From the mvp directory
streamlit run app.py
```

### Configuration

The application uses `config.yaml` for configuration. Key settings:

```yaml
app:
  name: Supply Chain AI Assistant
  session_timeout: 3600

auth:
  users_file: mvp/auth/users.json

cache:
  enabled: true
  max_size: 1000
  default_ttl: 300

cost:
  enabled: true
  log_file: logs/cost_tracking.log
```

### Session State Variables

The application uses Streamlit session state to manage:

- `authenticated`: Boolean indicating if user is logged in
- `session_id`: Current session ID
- `user`: Current user object
- `current_persona`: Selected persona
- `query_history`: List of past queries and responses
- `is_loading`: Loading state indicator
- `app_initialized`: Application initialization flag

### Component Dependencies

```
app.py
├── login_page.py
│   ├── auth_manager.py
│   └── session_manager.py
├── main_app.py
│   └── query_orchestrator.py
├── results_display.py
├── cost_dashboard.py
│   └── cost_tracker.py
└── conversation_sidebar.py
    └── query_orchestrator.py
```

## Customization

### Adding New Personas

1. Update `business_metrics.py` with new persona
2. Add persona to user's authorized list in `users.json`
3. Add persona description in `main_app.py`
4. Add example queries in `main_app.py`

### Customizing Visualizations

Edit `results_display.py`:
- `create_visualizations()`: Add new chart types
- `display_dataframe()`: Customize table display
- `create_summary_stats()`: Add custom statistics

### Customizing Cost Display

Edit `cost_dashboard.py`:
- `display_cost_breakdown()`: Modify service breakdown
- `display_monthly_estimate()`: Adjust estimation logic
- `format_cost()`: Change cost formatting

## Troubleshooting

### Login Issues
- Check `users.json` exists and has valid users
- Verify password hashes are correct
- Check session timeout settings

### Query Processing Issues
- Verify AWS credentials are configured
- Check orchestrator initialization
- Review logs in `logs/app.log`

### Display Issues
- Clear browser cache
- Check Streamlit version compatibility
- Verify all dependencies are installed

### Cost Tracking Issues
- Verify cost tracker is enabled in config
- Check cost log file permissions
- Review cost calculation settings

## Development

### Adding New UI Components

1. Create new file in `mvp/ui/`
2. Import required dependencies
3. Create display functions
4. Import in `app.py`
5. Add to main layout

### Testing UI Components

```python
# Test individual components
import streamlit as st
from ui.login_page import render_login_page

# Run component in isolation
if __name__ == "__main__":
    render_login_page(auth_manager, session_manager)
```

### Styling

Streamlit uses custom CSS for styling. Add custom styles in `app.py`:

```python
st.markdown("""
<style>
.custom-class {
    color: blue;
}
</style>
""", unsafe_allow_html=True)
```

## Best Practices

1. **Session State**: Always check if variables exist before accessing
2. **Error Handling**: Wrap UI operations in try-except blocks
3. **Loading States**: Show loading indicators for long operations
4. **User Feedback**: Provide clear success/error messages
5. **Responsive Design**: Use columns for responsive layouts
6. **Performance**: Cache expensive operations with `@st.cache_data`

## Future Enhancements

- [ ] Add data export in multiple formats (Excel, JSON)
- [ ] Add advanced filtering and search
- [ ] Add user preferences and settings
- [ ] Add dark mode support
- [ ] Add multi-language support
- [ ] Add keyboard shortcuts
- [ ] Add query templates
- [ ] Add data visualization customization
