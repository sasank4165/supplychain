# Database Migration Scripts

This directory contains scripts for migrating the Supply Chain AI system from Redshift Serverless (MVP) to Amazon Athena (Production).

## Overview

The migration process transforms the database layer from Redshift Serverless to Athena while maintaining data integrity and minimizing downtime.

## Prerequisites

### AWS Permissions

Ensure your AWS credentials have the following permissions:

**Redshift Data API**:
- `redshift-data:ExecuteStatement`
- `redshift-data:DescribeStatement`
- `redshift-data:GetStatementResult`

**S3**:
- `s3:PutObject`
- `s3:GetObject`
- `s3:ListBucket`

**Athena**:
- `athena:StartQueryExecution`
- `athena:GetQueryExecution`
- `athena:GetQueryResults`

**Glue**:
- `glue:CreateDatabase`
- `glue:CreateTable`
- `glue:GetDatabase`
- `glue:GetTable`

### Python Dependencies

```bash
pip install boto3 pyyaml pandas
```

### Configuration

1. Copy the migration configuration template:
```bash
cp config.migration.yaml config.yaml
```

2. Update the configuration with your AWS account details:
   - S3 bucket name
   - IAM role ARN
   - AWS account ID
   - Region

## Migration Scripts

### 1. migrate_redshift_to_athena.py

Main migration orchestration script that handles the complete migration process.

**Usage**:
```bash
# Full migration with validation
python scripts/migrate_redshift_to_athena.py --config config.yaml --validate

# Migration without validation
python scripts/migrate_redshift_to_athena.py --config config.yaml

# Create Athena tables only (skip export)
python scripts/migrate_redshift_to_athena.py --config config.yaml --skip-export
```

**What it does**:
1. Exports all tables from Redshift to S3 in Parquet format
2. Creates Glue Catalog database
3. Creates Athena external tables pointing to S3 data
4. Validates row counts (if --validate flag is used)
5. Generates migration report

**Output**:
```
================================================================================
REDSHIFT TO ATHENA MIGRATION
================================================================================
Start Time: 2026-02-17 10:00:00

STEP 1: Exporting data from Redshift to S3...
--------------------------------------------------------------------------------
  Exporting product... ✓ (150 rows)
  Exporting warehouse_product... ✓ (450 rows)
  Exporting sales_order_header... ✓ (1,250 rows)
  Exporting sales_order_line... ✓ (3,750 rows)
  Exporting purchase_order_header... ✓ (800 rows)
  Exporting purchase_order_line... ✓ (2,400 rows)

STEP 2: Creating Athena database and tables...
--------------------------------------------------------------------------------
  ✓ Database 'supply_chain_athena' created
  Creating table product... ✓
  Creating table warehouse_product... ✓
  Creating table sales_order_header... ✓
  Creating table sales_order_line... ✓
  Creating table purchase_order_header... ✓
  Creating table purchase_order_line... ✓

STEP 3: Validating data integrity...
--------------------------------------------------------------------------------
  Validating row counts...
    product: Redshift=150, Athena=150 ✓
    warehouse_product: Redshift=450, Athena=450 ✓
    sales_order_header: Redshift=1,250, Athena=1,250 ✓
    sales_order_line: Redshift=3,750, Athena=3,750 ✓
    purchase_order_header: Redshift=800, Athena=800 ✓
    purchase_order_line: Redshift=2,400, Athena=2,400 ✓

  ✓ All tables validated successfully

================================================================================
MIGRATION REPORT
================================================================================
Start Time:  2026-02-17 10:00:00
End Time:    2026-02-17 10:05:23
Duration:    323.45 seconds

Table Summary:
--------------------------------------------------------------------------------
  product                   | Redshift:        150 | Athena:        150 | passed
  warehouse_product         | Redshift:        450 | Athena:        450 | passed
  sales_order_header        | Redshift:      1,250 | Athena:      1,250 | passed
  sales_order_line          | Redshift:      3,750 | Athena:      3,750 | passed
  purchase_order_header     | Redshift:        800 | Athena:        800 | passed
  purchase_order_line       | Redshift:      2,400 | Athena:      2,400 | passed

✓ Migration completed successfully with no errors
================================================================================
```

## Step-by-Step Migration Process

### Phase 1: Pre-Migration

1. **Backup Current Data**
```bash
# Create backup of Redshift data
python scripts/migrate_redshift_to_athena.py --config config.yaml
```

2. **Verify S3 Bucket**
```bash
aws s3 ls s3://your-bucket-name/supply-chain-data/
```

3. **Test Athena Access**
```bash
aws athena start-query-execution \
  --query-string "SELECT 1" \
  --result-configuration "OutputLocation=s3://your-bucket-name/athena-results/"
```

### Phase 2: Migration Execution

1. **Run Migration Script**
```bash
python scripts/migrate_redshift_to_athena.py --config config.yaml --validate
```

2. **Verify Migration**
```bash
# Check Glue Catalog
aws glue get-tables --database-name supply_chain_athena

# Test Athena query
aws athena start-query-execution \
  --query-string "SELECT COUNT(*) FROM supply_chain_athena.product" \
  --query-execution-context "Database=supply_chain_athena" \
  --result-configuration "OutputLocation=s3://your-bucket-name/athena-results/"
```

### Phase 3: Application Update

1. **Update Configuration**
```yaml
# config.yaml
database:
  type: athena  # Changed from 'redshift'
```

2. **Restart Application**
```bash
# If running locally
streamlit run app.py

# If running on EC2/SageMaker
sudo systemctl restart supply-chain-app
```

3. **Test Queries**
- Login to application
- Test queries for each persona
- Verify results match expected data

### Phase 4: Validation

1. **Run Parallel Testing**
```bash
# Test same queries on both databases
python scripts/validate_migration.py --config config.yaml
```

2. **Monitor Performance**
- Compare query response times
- Check cost per query
- Verify cache hit rates

3. **User Acceptance Testing**
- Have users test all workflows
- Collect feedback
- Address any issues

### Phase 5: Cutover

1. **Switch to Athena**
- Update production configuration
- Deploy updated application
- Monitor for errors

2. **Keep Redshift Running**
- Maintain Redshift for 7 days as backup
- Monitor for any issues
- Be ready to rollback if needed

3. **Decommission Redshift**
```bash
# After 7 days of successful Athena operation
aws redshift-serverless delete-workgroup --workgroup-name supply-chain-mvp
```

## Troubleshooting

### Issue: UNLOAD fails with permission error

**Solution**: Verify IAM role has S3 write permissions
```bash
aws iam get-role-policy --role-name RedshiftS3Role --policy-name S3Access
```

### Issue: Athena query fails with "Table not found"

**Solution**: Verify Glue Catalog table exists
```bash
aws glue get-table --database-name supply_chain_athena --name product
```

### Issue: Row count mismatch

**Solution**: 
1. Check for data in S3
```bash
aws s3 ls s3://your-bucket-name/supply-chain-data/product/ --recursive
```

2. Run MSCK REPAIR TABLE
```sql
MSCK REPAIR TABLE supply_chain_athena.product;
```

3. Re-run validation

### Issue: Slow Athena queries

**Solution**:
1. Check data partitioning
2. Optimize query patterns
3. Use columnar format (Parquet)
4. Consider data compression

## Rollback Procedure

If migration fails or issues are discovered:

1. **Immediate Rollback**
```yaml
# config.yaml
database:
  type: redshift  # Change back to redshift
```

2. **Restart Application**
```bash
streamlit run app.py
```

3. **Verify Redshift Still Has Data**
```bash
python scripts/verify_redshift_data.py
```

4. **Investigate Issues**
- Review migration logs
- Check error messages
- Identify root cause

5. **Fix and Retry**
- Address issues
- Re-run migration
- Validate thoroughly

## Cost Considerations

### Redshift Serverless Costs
- **Base**: $0.36 per RPU-hour
- **8 RPUs 24/7**: ~$260/month

### Athena Costs
- **Query**: $5 per TB scanned
- **100 GB/day**: ~$150/month
- **Storage**: S3 standard pricing

### Migration Costs
- **Data Transfer**: Free (same region)
- **S3 Storage**: ~$2.30 per 100 GB/month
- **One-time**: Minimal

## Best Practices

1. **Test in Development First**
   - Run migration in dev environment
   - Validate all queries work
   - Measure performance differences

2. **Schedule During Low Usage**
   - Minimize user impact
   - Allow time for validation
   - Have rollback plan ready

3. **Monitor Closely**
   - Watch error rates
   - Check query performance
   - Track costs

4. **Communicate with Users**
   - Notify of maintenance window
   - Provide status updates
   - Collect feedback

5. **Document Everything**
   - Record issues encountered
   - Document solutions
   - Update runbooks

## Support

For issues or questions:
1. Check troubleshooting section above
2. Review migration logs in `logs/migration.log`
3. Consult AWS documentation
4. Contact engineering team

## References

- [AWS Redshift UNLOAD Documentation](https://docs.aws.amazon.com/redshift/latest/dg/r_UNLOAD.html)
- [AWS Athena Documentation](https://docs.aws.amazon.com/athena/)
- [AWS Glue Catalog Documentation](https://docs.aws.amazon.com/glue/latest/dg/catalog-and-crawler.html)
- [Migration Guide](../MIGRATION_GUIDE.md)
