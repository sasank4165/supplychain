# Quick Start Guide - After Persona Fix

## What Was Fixed
The "Invalid persona" error has been resolved. All three personas are now properly registered and working.

## Start the Application

### On SageMaker
```bash
cd /home/ec2-user/SageMaker/supplychain/mvp/
streamlit run app.py --server.port 8501
```

### On Local Machine
```bash
cd mvp
streamlit run app.py
```

## Login Credentials

| Username | Password | Persona |
|----------|----------|---------|
| `demo_warehouse` | `demo123` | Warehouse Manager |
| `demo_field` | `demo123` | Field Engineer |
| `demo_procurement` | `demo123` | Procurement Specialist |
| `demo_admin` | `demo123` | All personas |

## Test Queries by Persona

### Warehouse Manager
Try these queries:
- "Show me products with low stock"
- "What products need reordering?"
- "Show me inventory levels at warehouse WH001"
- "Which products are out of stock?"

### Field Engineer
Try these queries:
- "Show me today's deliveries"
- "Which orders are overdue?"
- "Show me orders in transit"
- "What orders are pending?"

### Procurement Specialist
Try these queries:
- "Show me pending purchase orders"
- "List all suppliers"
- "Show me late deliveries from suppliers"
- "What is the total spend with each supplier?"

## Verify Everything Works

Run the verification script:
```bash
python mvp/scripts/verify_personas.py
```

You should see:
```
✓ Warehouse Manager
✓ Field Engineer
✓ Procurement Specialist

Total personas registered: 3
```

## Troubleshooting

### If you still see "Invalid persona" error:
1. Stop the Streamlit app (Ctrl+C)
2. Clear browser cache or open in incognito mode
3. Restart the app
4. Login again

### If you see AWS credential errors:
- Make sure you're running on SageMaker with proper IAM role
- Or configure AWS credentials locally

### If you see Redshift/Glue errors:
- Check that your `config.yaml` has correct AWS resource names
- Verify your IAM role has permissions for Redshift Data API and Glue

## What's Next?

Now that personas are working, you can:
1. **Query Data**: Use SQL queries through the natural language interface
2. **Run Optimizations**: Use specialized agents for inventory, logistics, or supplier analysis
3. **View Cost Tracking**: Monitor Bedrock and Redshift costs in the dashboard
4. **Review History**: See past queries in the conversation sidebar

## Need Help?

Check these files:
- `mvp/PERSONA_FIX_SUMMARY.md` - Details about what was fixed
- `mvp/TROUBLESHOOTING_LOGIN.md` - Login troubleshooting
- `mvp/USER_MANAGEMENT.md` - User management guide
- `mvp/README.md` - Full application documentation
