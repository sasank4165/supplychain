# Data Setup Guide

## Quick Start

### Option 1: Use Sample Data Generator (Recommended for Testing)

```bash
# Generate sample data
python scripts/generate_sample_data.py --size medium

# Upload to S3
./scripts/upload_data_to_s3.sh

# Create Glue tables
./scripts/create_glue_tables.sh
```

### Option 2: Use Your Own Data

```bash
# 1. Prepare your CSV files
# 2. Upload to S3
# 3. Create Glue tables
# 4. Verify with Athena
```

## Detailed Setup Steps

### Step 1: Prepare S3 Bucket

```bash
# Get data bucket name from CDK output
DATA_BUCKET=$(aws cloudformation describe-stacks \
  --stack-name SupplyChainData-prod \
  --query "Stacks[0].Outputs[?OutputKey=='DataBucketName'].OutputValue" \
  --output text)

echo "Data bucket: $DATA_BUCKET"

# Create folder structure
aws s3api put-object --bucket $DATA_BUCKET --key product/
aws s3api put-object --bucket $DATA_BUCKET --key warehouse_product/
aws s3api put-object --bucket $DATA_BUCKET --key sales_order_header/
aws s3api put-object --bucket $DATA_BUCKET --key sales_order_line/
aws s3api put-object --bucket $DATA_BUCKET --key purchase_order_header/
aws s3api put-object --bucket $DATA_BUCKET --key purchase_order_line/
```

### Step 2: Generate or Prepare Data

#### Option A: Generate Sample Data

```bash
cd supply_chain_agent

# Install dependencies
pip install faker pandas

# Generate data (choose size: small, medium, large)
python scripts/generate_sample_data.py --size medium --output data/

# This creates:
# - data/product.csv (1000 products)
# - data/warehouse_product.csv (5000 records)
# - data/sales_order_header.csv (5000 orders)
# - data/sales_order_line.csv (15000 lines)
# - data/purchase_order_header.csv (2000 orders)
# - data/purchase_order_line.csv (6000 lines)
```

#### Option B: Prepare Your Own Data

Ensure your CSV files match the schema in `DATA_REQUIREMENTS.md`:

```bash
# Validate your data
python scripts/validate_data.py --input your_data/

# This checks:
# - Schema compliance
# - Referential integrity
# - Data quality
# - Date formats
```

### Step 3: Upload Data to S3

```bash
# Upload all CSV files
aws s3 cp data/product.csv s3://$DATA_BUCKET/product/
aws s3 cp data/warehouse_product.csv s3://$DATA_BUCKET/warehouse_product/
aws s3 cp data/sales_order_header.csv s3://$DATA_BUCKET/sales_order_header/
aws s3 cp data/sales_order_line.csv s3://$DATA_BUCKET/sales_order_line/
aws s3 cp data/purchase_order_header.csv s3://$DATA_BUCKET/purchase_order_header/
aws s3 cp data/purchase_order_line.csv s3://$DATA_BUCKET/purchase_order_line/

# Or use the upload script
./scripts/upload_data_to_s3.sh $DATA_BUCKET
```

### Step 4: Create Glue Database

```bash
# Create database
aws glue create-database \
  --database-input '{
    "Name": "aws-gpl-cog-sc-db",
    "Description": "Supply chain data catalog"
  }'

# Verify
aws glue get-database --name aws-gpl-cog-sc-db
```

### Step 5: Create Glue Tables

```bash
# Run table creation script
./scripts/create_glue_tables.sh $DATA_BUCKET

# Or create manually via AWS Console:
# 1. Go to AWS Glue Console
# 2. Navigate to Tables
# 3. Add table
# 4. Use schemas from DATA_REQUIREMENTS.md
```

### Step 6: Verify with Athena

```bash
# Test queries
aws athena start-query-execution \
  --query-string "SELECT COUNT(*) FROM \"aws-gpl-cog-sc-db\".\"product\"" \
  --result-configuration "OutputLocation=s3://$ATHENA_BUCKET/" \
  --query-execution-context "Database=aws-gpl-cog-sc-db"

# Get query results
QUERY_ID=<execution-id-from-above>
aws athena get-query-results --query-execution-id $QUERY_ID
```

Or use Athena Console:

```sql
-- Test each table
SELECT COUNT(*) FROM "aws-gpl-cog-sc-db"."product";
SELECT COUNT(*) FROM "aws-gpl-cog-sc-db"."warehouse_product";
SELECT COUNT(*) FROM "aws-gpl-cog-sc-db"."sales_order_header";
SELECT COUNT(*) FROM "aws-gpl-cog-sc-db"."sales_order_line";
SELECT COUNT(*) FROM "aws-gpl-cog-sc-db"."purchase_order_header";
SELECT COUNT(*) FROM "aws-gpl-cog-sc-db"."purchase_order_line";

-- Test joins
SELECT 
  p.product_code,
  p.short_name,
  wp.warehouse_code,
  wp.physical_stock_su
FROM "aws-gpl-cog-sc-db"."product" p
JOIN "aws-gpl-cog-sc-db"."warehouse_product" wp 
  ON p.product_code = wp.product_code
LIMIT 10;
```

## Data Formats

### CSV Format

```csv
# Header row required
# Comma-separated
# No quotes unless value contains comma
# UTF-8 encoding
# Unix line endings (LF)

product_code,short_name,standard_cost
P001,Widget A,10.50
P002,Widget B,15.75
```

### Parquet Format (Recommended for Production)

```bash
# Convert CSV to Parquet
python scripts/convert_to_parquet.py \
  --input data/ \
  --output data_parquet/

# Upload Parquet files
aws s3 sync data_parquet/ s3://$DATA_BUCKET/
```

Benefits:
- 10x smaller file size
- Faster query performance
- Column-based compression
- Schema embedded

## Data Partitioning (Optional but Recommended)

### Partition by Date

```bash
# Organize data by date
s3://bucket/sales_order_header/year=2024/month=01/day=15/data.csv
s3://bucket/sales_order_header/year=2024/month=01/day=16/data.csv

# Update Glue table with partitions
aws glue create-partition \
  --database-name aws-gpl-cog-sc-db \
  --table-name sales_order_header \
  --partition-input '{
    "Values": ["2024", "01", "15"],
    "StorageDescriptor": {...}
  }'
```

Benefits:
- Faster queries (partition pruning)
- Lower costs (scan less data)
- Easier data management

## Data Updates

### Full Refresh

```bash
# 1. Upload new data with timestamp
aws s3 cp data/product.csv \
  s3://$DATA_BUCKET/product/product_20240115.csv

# 2. Update Glue table location
# 3. Run MSCK REPAIR TABLE (if partitioned)
```

### Incremental Updates

```bash
# 1. Upload delta files
aws s3 cp data/product_delta.csv \
  s3://$DATA_BUCKET/product/delta/20240115/

# 2. Merge with main table (via Athena CTAS or Spark)
```

### Real-time Updates (Advanced)

```bash
# Use AWS Glue Streaming or Kinesis Data Firehose
# Stream data directly to S3 in Parquet format
# Automatic table updates via Glue Crawler
```

## Data Quality Checks

### Automated Validation

```bash
# Run data quality checks
python scripts/validate_data.py \
  --bucket $DATA_BUCKET \
  --database aws-gpl-cog-sc-db

# Checks:
# ✓ Row counts
# ✓ Null values in required fields
# ✓ Referential integrity
# ✓ Date format validation
# ✓ Numeric range validation
# ✓ Duplicate detection
```

### Manual Checks

```sql
-- Check for nulls in required fields
SELECT COUNT(*) 
FROM "aws-gpl-cog-sc-db"."product"
WHERE product_code IS NULL;

-- Check referential integrity
SELECT COUNT(*) 
FROM "aws-gpl-cog-sc-db"."warehouse_product" wp
LEFT JOIN "aws-gpl-cog-sc-db"."product" p 
  ON wp.product_code = p.product_code
WHERE p.product_code IS NULL;

-- Check date formats
SELECT product_code, date_created
FROM "aws-gpl-cog-sc-db"."product"
WHERE date_created < 20000101 OR date_created > 20991231;

-- Check for duplicates
SELECT product_code, COUNT(*)
FROM "aws-gpl-cog-sc-db"."product"
GROUP BY product_code
HAVING COUNT(*) > 1;
```

## Troubleshooting

### Issue: "Table not found"

```bash
# Verify database exists
aws glue get-database --name aws-gpl-cog-sc-db

# Verify table exists
aws glue get-table \
  --database-name aws-gpl-cog-sc-db \
  --name product

# Recreate table if needed
./scripts/create_glue_tables.sh
```

### Issue: "No data returned"

```bash
# Check S3 location
aws s3 ls s3://$DATA_BUCKET/product/

# Verify file format
aws s3 cp s3://$DATA_BUCKET/product/product.csv - | head -5

# Check table location in Glue
aws glue get-table \
  --database-name aws-gpl-cog-sc-db \
  --name product \
  --query "Table.StorageDescriptor.Location"
```

### Issue: "Schema mismatch"

```bash
# Compare actual data with table schema
# Update table schema if needed
aws glue update-table \
  --database-name aws-gpl-cog-sc-db \
  --table-input file://table_definition.json
```

### Issue: "Query timeout"

```bash
# Add partitions to reduce scan size
# Convert to Parquet format
# Optimize file sizes (128MB-1GB per file)
# Use columnar projection in queries
```

## Performance Optimization

### 1. File Format
- Use Parquet instead of CSV
- Compress with Snappy or ZSTD

### 2. File Size
- Optimal: 128MB - 1GB per file
- Avoid many small files
- Combine small files periodically

### 3. Partitioning
- Partition by date (year/month/day)
- Partition by warehouse_code for large datasets
- Limit partitions to < 10,000

### 4. Compression
- Parquet with Snappy: Good balance
- Parquet with ZSTD: Better compression
- CSV with GZIP: Acceptable for small data

### 5. Query Optimization
- Use partition filters
- Select only needed columns
- Use LIMIT for testing
- Create views for common queries

## Cost Optimization

### Storage Costs
- Use S3 Intelligent-Tiering
- Archive old data to Glacier
- Delete temporary files

### Query Costs
- Partition data to reduce scans
- Use Parquet to reduce data scanned
- Cache frequent query results
- Use LIMIT during development

### Data Transfer Costs
- Keep data in same region as Athena
- Use VPC endpoints
- Compress data before upload

## Next Steps

1. Generate or prepare your data
2. Upload to S3
3. Create Glue tables
4. Verify with Athena queries
5. Test with application
6. Monitor query performance
7. Optimize as needed

## References

- [AWS Glue Documentation](https://docs.aws.amazon.com/glue/)
- [Amazon Athena Best Practices](https://docs.aws.amazon.com/athena/latest/ug/performance-tuning.html)
- [Parquet Format](https://parquet.apache.org/)
