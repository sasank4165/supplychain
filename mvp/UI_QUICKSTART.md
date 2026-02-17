# Streamlit UI Quick Start Guide

This guide will help you get the Supply Chain AI Assistant UI up and running.

## Prerequisites

1. **Python 3.11+** installed
2. **AWS credentials** configured (for Bedrock, Redshift, Lambda access)
3. **Virtual environment** set up with dependencies installed
4. **Configuration file** (`config.yaml`) properly configured
5. **User accounts** created in `auth/users.json`

## Quick Start

### 1. Install Dependencies

```bash
cd mvp
pip install -r requirements.txt
```

### 2. Configure the Application

Copy the example configuration:

```bash
cp config.example.yaml config.yaml
```

Edit `config.yaml` with your AWS settings:

```yaml
aws:
  region: us-east-1
  bedrock:
    model_id: anthropic.claude-3-5-sonnet-20241022-v2:0
  redshift:
    workgroup_name: your-workgroup-name
    database: supply_chain_db
  glue:
    database: supply_chain_catalog
  lambda:
    inventory_function: supply-chain-inventory-optimizer
    logistics_function: supply-chain-logistics-optimizer
    supplier_function: supply-chain-supplier-analyzer
```

### 3. Create User Accounts

Create a user account:

```bash
python scripts/create_user.py
```

Or manually edit `auth/users.json`:

```json
{
  "users": [
    {
      "username": "demo_user",
      "password_hash": "$2b$12$...",
      "personas": ["Warehouse Manager", "Field Engineer"],
      "active": true,
      "created_date": "2024-01-01T00:00:00"
    }
  ]
}
```

### 4. Run the Application

```bash
streamlit run app.py
```

The application will open in your browser at `http://localhost:8501`

## First Login

1. Navigate to `http://localhost:8501`
2. Enter your username and password
3. Click "Login"
4. Select your persona from the dropdown
5. Start asking questions!

## Example Queries

### Warehouse Manager
- "Show me products with stock below minimum levels"
- "Calculate reorder points for warehouse WH001"
- "What products are at risk of stockout?"

### Field Engineer
- "Show me orders scheduled for delivery today"
- "Which orders are delayed?"
- "Optimize delivery route for the North region"

### Procurement Specialist
- "Show me top 10 suppliers by order volume"
- "Analyze supplier performance for the last 90 days"
- "Compare costs between suppliers for Electronics"

## UI Features

### Main Interface
- **Persona Selector**: Choose your role (Warehouse Manager, Field Engineer, Procurement Specialist)
- **Query Input**: Enter natural language queries (max 1000 characters)
- **Example Queries**: Click to try pre-built example queries
- **Clear History**: Clear conversation history

### Results Display
- **Formatted Results**: Tables, charts, and text responses
- **Data Export**: Download results as CSV
- **Visualizations**: Automatic bar and line charts
- **Metadata**: View SQL queries and tool calls

### Cost Dashboard
- **Per-Query Cost**: See cost for each query
- **Daily Cost**: Track today's total cost
- **Monthly Estimate**: Projected monthly cost
- **Service Breakdown**: Cost by service (Bedrock, Redshift, Lambda)

### Conversation History
- **Recent Queries**: View last 10 interactions
- **Re-run Queries**: Click to re-run past queries
- **Cache Stats**: View cache hit rate and size
- **Clear Cache**: Clear cached results

## Configuration Options

### Session Timeout

Adjust session timeout in `config.yaml`:

```yaml
app:
  session_timeout: 3600  # 1 hour in seconds
```

### Cache Settings

Configure query caching:

```yaml
cache:
  enabled: true
  max_size: 1000
  default_ttl: 300  # 5 minutes
  dashboard_ttl: 900  # 15 minutes
```

### Cost Tracking

Enable/disable cost tracking:

```yaml
cost:
  enabled: true
  log_file: logs/cost_tracking.log
```

## Troubleshooting

### Cannot Connect to AWS Services

**Problem**: "Unable to connect to Bedrock/Redshift/Lambda"

**Solution**:
1. Check AWS credentials: `aws configure list`
2. Verify IAM permissions for Bedrock, Redshift Data API, Lambda
3. Check region configuration in `config.yaml`

### Login Failed

**Problem**: "Invalid username or password"

**Solution**:
1. Verify user exists in `auth/users.json`
2. Check password hash is correct
3. Ensure user is marked as `active: true`

### Query Processing Errors

**Problem**: "Error processing query"

**Solution**:
1. Check logs in `logs/app.log`
2. Verify AWS resources are deployed (Redshift, Lambda functions)
3. Check Glue Catalog has table definitions
4. Verify sample data is loaded

### UI Not Loading

**Problem**: Blank page or errors in browser

**Solution**:
1. Clear browser cache
2. Check Streamlit version: `streamlit --version`
3. Restart Streamlit: `Ctrl+C` then `streamlit run app.py`
4. Check for port conflicts (default: 8501)

### Cost Tracking Not Working

**Problem**: Costs showing as $0.00

**Solution**:
1. Verify `cost.enabled: true` in config
2. Check cost log file permissions
3. Ensure token usage is being captured from Bedrock responses

## Advanced Usage

### Running on Custom Port

```bash
streamlit run app.py --server.port 8080
```

### Running on Remote Server

```bash
streamlit run app.py --server.address 0.0.0.0 --server.port 8501
```

Access from other machines: `http://<server-ip>:8501`

### Running with HTTPS

For production, use a reverse proxy (nginx) with SSL certificate.

### Running as Background Service

Create a systemd service file:

```ini
[Unit]
Description=Supply Chain AI Assistant
After=network.target

[Service]
Type=simple
User=your-user
WorkingDirectory=/path/to/mvp
ExecStart=/path/to/venv/bin/streamlit run app.py
Restart=always

[Install]
WantedBy=multi-user.target
```

## Performance Tips

1. **Enable Caching**: Keep cache enabled for faster repeated queries
2. **Limit History**: Conversation history limited to 10 interactions
3. **Clear Cache**: Periodically clear cache for fresh data
4. **Monitor Costs**: Watch daily costs to avoid surprises
5. **Use Example Queries**: Pre-built queries are optimized

## Security Considerations

1. **Change Default Passwords**: Update all default user passwords
2. **Use Strong Passwords**: Minimum 8 characters
3. **Secure Config File**: Don't commit `config.yaml` with credentials
4. **Use IAM Roles**: Prefer IAM roles over access keys
5. **Enable HTTPS**: Use SSL in production
6. **Session Timeout**: Keep session timeout reasonable (1 hour)

## Deployment Options

### Local Development
- Run on localhost for development and testing
- No additional costs
- Single user only

### Amazon SageMaker Notebook
- Deploy on ml.t3.medium instance
- Integrated AWS authentication
- Team collaboration support
- Cost: ~$36/month (24/7) or ~$8/month (8 hours/day)

### EC2 Instance
- Deploy on t3.small instance
- Full control over environment
- Custom domain support
- Cost: ~$15/month

See `DEPLOYMENT.md` for detailed deployment instructions.

## Getting Help

- **Documentation**: See `ui/README.md` for component details
- **Logs**: Check `logs/app.log` for errors
- **Configuration**: Review `config.example.yaml` for all options
- **AWS Issues**: Check AWS service status and quotas

## Next Steps

1. ✅ Login and explore the UI
2. ✅ Try example queries for each persona
3. ✅ Review cost tracking and optimize usage
4. ✅ Set up additional user accounts
5. ✅ Configure caching for your use case
6. ✅ Deploy to production environment

Enjoy using the Supply Chain AI Assistant! 🏭
