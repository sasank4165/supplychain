# Data Summary for Supply Chain Agentic AI

## Quick Reference

### Required Tables (6)

| Table | Purpose | Min Records | Key Fields |
|-------|---------|-------------|------------|
| **product** | Product master data | 100+ | product_code, short_name, standard_cost, supplier_code1 |
| **warehouse_product** | Inventory levels | 500+ | warehouse_code, product_code, physical_stock_su, minimum_stock_su |
| **sales_order_header** | Sales order master | 500+ | sales_order_number, customer_code, order_date, order_status |
| **sales_order_line** | Sales order details | 1,500+ | sales_order_number, product_code, qty_ordered_su, order_line_status |
| **purchase_order_header** | Purchase order master | 200+ | purchase_order_number, supplier_code, order_date, order_status |
| **purchase_order_line** | Purchase order details | 600+ | purchase_order_number, product_code, qty_ordered, received_qty |

### Data Relationships

```
product (1) ←→ (N) warehouse_product
product (1) ←→ (N) sales_order_line
product (1) ←→ (N) purchase_order_line
supplier (1) ←→ (N) product
supplier (1) ←→ (N) purchase_order_header
warehouse (1) ←→ (N) warehouse_product
warehouse (1) ←→ (N) sales_order_header
customer (1) ←→ (N) sales_order_header
```

## Quick Start Options

### Option 1: Generate Sample Data (Fastest)

```bash
# Install dependencies
pip install faker pandas

# Generate medium dataset
python scripts/generate_sample_data.py --size medium --output data/

# Upload to S3
export DATA_BUCKET="supply-chain-data-ACCOUNT-REGION"
./scripts/upload_data_to_s3.sh $DATA_BUCKET

# Create Glue tables
./scripts/create_glue_tables.sh $DATA_BUCKET

# Verify
aws athena start-query-execution \
  --query-string "SELECT COUNT(*) FROM \"aws-gpl-cog-sc-db\".\"product\"" \
  --result-configuration "OutputLocation=s3://athena-results-bucket/"
```

**Time**: ~10 minutes

### Option 2: Use Your Own Data

```bash
# 1. Prepare CSV files matching schemas in DATA_REQUIREMENTS.md
# 2. Validate data
python scripts/validate_data.py --input your_data/

# 3. Upload to S3
aws s3 sync your_data/ s3://$DATA_BUCKET/

# 4. Create Glue tables
./scripts/create_glue_tables.sh $DATA_BUCKET
```

**Time**: Depends on data volume

### Option 3: Connect to Existing Database

```bash
# Use AWS Glue Crawler to discover schema
aws glue create-crawler \
  --name supply-chain-crawler \
  --role GlueServiceRole \
  --database-name aws-gpl-cog-sc-db \
  --targets '{
    "JdbcTargets": [{
      "ConnectionName": "your-db-connection",
      "Path": "database/schema/%"
    }]
  }'

# Run crawler
aws glue start-crawler --name supply-chain-crawler
```

**Time**: ~30 minutes

## Data Format Requirements

### Date Format
- **Format**: BIGINT as YYYYMMDD
- **Example**: January 15, 2024 = `20240115`
- **Valid Range**: 20000101 to 20991231

### Numeric Fields
- **Quantities**: Non-negative DOUBLE (e.g., 10.5, 100.0)
- **Costs/Prices**: Non-negative DOUBLE with 2 decimals (e.g., 10.50, 99.99)
- **Percentages**: 0-100 range

### Text Fields
- **Codes**: Alphanumeric, no special characters
- **Status**: Predefined values (see below)
- **Descriptions**: UTF-8 text, max 255 chars

### Status Values

**Order Status**: `OPEN`, `PICKING`, `PACKED`, `SHIPPED`, `COMPLETED`, `CANCELLED`

**Stock Status**: `ACTIVE`, `INACTIVE`, `DISCONTINUED`

**Invoice Status**: `PENDING`, `RECEIVED`, `PAID`

## Sample Data Sizes

### Small (Testing)
- Products: 100
- Warehouse-Product: 500
- Sales Orders: 500 (1,500 lines)
- Purchase Orders: 200 (600 lines)
- **Total Records**: ~3,300
- **Storage**: ~5 MB (CSV), ~1 MB (Parquet)
- **Generation Time**: ~30 seconds

### Medium (Development)
- Products: 1,000
- Warehouse-Product: 5,000
- Sales Orders: 5,000 (15,000 lines)
- Purchase Orders: 2,000 (6,000 lines)
- **Total Records**: ~29,000
- **Storage**: ~50 MB (CSV), ~10 MB (Parquet)
- **Generation Time**: ~2 minutes

### Large (Production-like)
- Products: 10,000
- Warehouse-Product: 50,000
- Sales Orders: 50,000 (150,000 lines)
- Purchase Orders: 20,000 (60,000 lines)
- **Total Records**: ~290,000
- **Storage**: ~500 MB (CSV), ~100 MB (Parquet)
- **Generation Time**: ~10 minutes

## Key Metrics by Persona

### Warehouse Manager Needs
- **Inventory Levels**: warehouse_product.physical_stock_su
- **Reorder Points**: warehouse_product.minimum_stock_su
- **Stock Status**: warehouse_product.stock_status
- **Sales Demand**: sales_order_line.qty_ordered_su
- **Lead Times**: warehouse_product.lead_time_daysbigint

### Field Engineer Needs
- **Order Status**: sales_order_header.order_status
- **Delivery Dates**: sales_order_header.pref_del_date
- **Fulfillment**: sales_order_line.picked_qty_su, despatched_qty_su
- **Warehouse**: sales_order_header.warehouse_code
- **Delivery Area**: sales_order_header.del_area_code

### Procurement Specialist Needs
- **Supplier Info**: product.supplier_code1
- **Purchase Orders**: purchase_order_header.*
- **Costs**: product.standard_cost, purchase_order_line.unit_price_oudouble
- **Receipt Status**: purchase_order_line.received_qty_oudouble
- **Lead Times**: warehouse_product.lead_time_daysbigint

## Data Quality Checklist

### Before Upload
- [ ] All required fields populated
- [ ] Dates in YYYYMMDD format
- [ ] No negative quantities/costs
- [ ] Valid status values
- [ ] Referential integrity (product codes exist)
- [ ] No duplicate primary keys
- [ ] UTF-8 encoding
- [ ] CSV with header row

### After Upload
- [ ] All files in S3
- [ ] Glue tables created
- [ ] Athena queries return data
- [ ] Row counts match expectations
- [ ] Joins work correctly
- [ ] No null values in required fields
- [ ] Date ranges are reasonable

## Common Issues & Solutions

### Issue: "No data returned from Athena"
**Solution**: 
```bash
# Check S3 location
aws s3 ls s3://$DATA_BUCKET/product/

# Verify table location
aws glue get-table --database-name aws-gpl-cog-sc-db --name product \
  --query "Table.StorageDescriptor.Location"
```

### Issue: "Schema mismatch"
**Solution**:
```bash
# Recreate table with correct schema
./scripts/create_glue_tables.sh $DATA_BUCKET
```

### Issue: "Referential integrity errors"
**Solution**:
```bash
# Validate data
python scripts/validate_data.py --input data/

# Fix missing references in CSV files
```

### Issue: "Date format errors"
**Solution**:
```python
# Convert dates to YYYYMMDD format
from datetime import datetime
date_str = "2024-01-15"
date_int = int(datetime.strptime(date_str, "%Y-%m-%d").strftime("%Y%m%d"))
# Result: 20240115
```

## Performance Tips

### For Fast Queries
1. **Use Parquet format** (10x faster than CSV)
2. **Partition by date** (year/month/day)
3. **Compress files** (Snappy or ZSTD)
4. **Optimize file sizes** (128MB-1GB per file)
5. **Select only needed columns**

### For Cost Optimization
1. **Use S3 Intelligent-Tiering**
2. **Partition data** to reduce scans
3. **Archive old data** to Glacier
4. **Use LIMIT** during development
5. **Cache frequent queries**

## Example Queries

### Check Data Loaded
```sql
-- Count records in each table
SELECT 'product' as table_name, COUNT(*) as count 
FROM "aws-gpl-cog-sc-db"."product"
UNION ALL
SELECT 'warehouse_product', COUNT(*) 
FROM "aws-gpl-cog-sc-db"."warehouse_product"
UNION ALL
SELECT 'sales_order_header', COUNT(*) 
FROM "aws-gpl-cog-sc-db"."sales_order_header";
```

### Verify Relationships
```sql
-- Check product references
SELECT 
  COUNT(*) as total_warehouse_products,
  COUNT(DISTINCT wp.product_code) as unique_products,
  COUNT(DISTINCT p.product_code) as products_in_master
FROM "aws-gpl-cog-sc-db"."warehouse_product" wp
LEFT JOIN "aws-gpl-cog-sc-db"."product" p 
  ON wp.product_code = p.product_code;
```

### Sample Business Query
```sql
-- Products below minimum stock
SELECT 
  p.product_code,
  p.short_name,
  wp.warehouse_code,
  wp.physical_stock_su,
  wp.minimum_stock_su,
  wp.minimum_stock_su - wp.physical_stock_su as shortage
FROM "aws-gpl-cog-sc-db"."product" p
JOIN "aws-gpl-cog-sc-db"."warehouse_product" wp 
  ON p.product_code = wp.product_code
WHERE wp.physical_stock_su < wp.minimum_stock_su
ORDER BY shortage DESC
LIMIT 10;
```

## Next Steps

1. **Choose data option** (generate, use own, or connect existing)
2. **Follow setup guide** (DATA_SETUP_GUIDE.md)
3. **Verify data loaded** (run example queries)
4. **Test with application** (run Streamlit app)
5. **Monitor performance** (check query times)
6. **Optimize as needed** (convert to Parquet, add partitions)

## Documentation Files

- **DATA_REQUIREMENTS.md** - Detailed schemas and requirements
- **DATA_SETUP_GUIDE.md** - Step-by-step setup instructions
- **scripts/generate_sample_data.py** - Sample data generator
- **scripts/validate_data.py** - Data validation tool
- **scripts/upload_data_to_s3.sh** - S3 upload script
- **scripts/create_glue_tables.sh** - Glue table creation

## Support

For data-related issues:
1. Check DATA_REQUIREMENTS.md for schema details
2. Run validation script: `python scripts/validate_data.py`
3. Verify S3 upload: `aws s3 ls s3://$DATA_BUCKET/`
4. Test Athena queries in AWS Console
5. Check CloudWatch Logs for errors
