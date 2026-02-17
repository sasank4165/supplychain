# Scripts Directory

This directory contains utility scripts for setting up and managing the Supply Chain MVP.

## Available Scripts

### setup_glue_catalog.py

Creates AWS Glue Data Catalog database and table schemas for all 6 supply chain tables.

**Usage:**
```bash
# Basic usage with defaults
python setup_glue_catalog.py

# Specify custom database name and region
python setup_glue_catalog.py --database my_catalog --region us-west-2

# Use specific AWS profile
python setup_glue_catalog.py --profile my-aws-profile
```

**Arguments:**
- `--database`: Glue database name (default: supply_chain_catalog)
- `--region`: AWS region (default: us-east-1)
- `--profile`: AWS profile name (optional)

**Tables Created:**
- product
- warehouse_product
- sales_order_header
- sales_order_line
- purchase_order_header
- purchase_order_line

### generate_sample_data.py

Generates realistic sample data for testing and development.

**Usage:**
```bash
# Generate data and save to CSV files
python generate_sample_data.py --output-dir ./sample_data

# Generate with custom parameters
python generate_sample_data.py --num-products 200 --days 120

# Generate and load directly into Redshift
python generate_sample_data.py \
  --load-redshift \
  --workgroup supply-chain-mvp \
  --database supply_chain_db \
  --region us-east-1
```

**Arguments:**
- `--output-dir`: Output directory for CSV files (default: ./sample_data)
- `--num-products`: Number of products to generate (default: 150)
- `--days`: Number of days of order history (default: 90)
- `--load-redshift`: Load data into Redshift Serverless
- `--workgroup`: Redshift Serverless workgroup name (required with --load-redshift)
- `--database`: Redshift database name (required with --load-redshift)
- `--region`: AWS region (default: us-east-1)

**Generated Data:**
- 150+ products across 8 product groups
- 3 warehouses with inventory levels
- 90 days of sales orders (3-8 orders per day)
- 90 days of purchase orders (2-5 POs per week)

## Setup Workflow

Follow these steps to set up the database and load sample data:

1. **Create Glue Catalog schemas:**
   ```bash
   cd mvp/scripts
   python setup_glue_catalog.py --database supply_chain_catalog
   ```

2. **Generate sample data:**
   ```bash
   python generate_sample_data.py --output-dir ./sample_data
   ```

3. **Review generated CSV files:**
   ```bash
   ls -lh ./sample_data/
   ```

4. **Load data into Redshift:**
   ```bash
   python generate_sample_data.py \
     --load-redshift \
     --workgroup YOUR_WORKGROUP_NAME \
     --database supply_chain_db
   ```

5. **Verify data in Redshift:**
   - Use AWS Console or query editor
   - Run: `SELECT COUNT(*) FROM product;`

## Prerequisites

- Python 3.11+
- AWS credentials configured (via environment variables, AWS CLI, or IAM role)
- Required Python packages (installed via requirements.txt)
- AWS Glue Data Catalog access
- Redshift Serverless workgroup (for data loading)

## Troubleshooting

**Error: "Failed to initialize Redshift client"**
- Check AWS credentials are configured
- Verify region is correct
- Ensure Redshift Serverless workgroup exists

**Error: "Query timeout"**
- Increase timeout with larger datasets
- Check Redshift Serverless is running
- Verify network connectivity

**Error: "Table already exists"**
- This is normal - script will skip existing tables
- To recreate tables, drop them first in Redshift

## Notes

- The Glue Catalog tables are metadata only - actual data is stored in Redshift
- Sample data is randomly generated and realistic but not real
- Data generation is deterministic within a run but varies between runs
- Loading large datasets may take several minutes
