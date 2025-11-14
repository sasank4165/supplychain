# CDK Infrastructure - Production Ready

## Overview

This CDK application deploys a production-ready, multi-stack infrastructure following AWS Well-Architected Framework principles.

## Architecture Stacks

### 1. NetworkStack
- VPC with 3 AZs (public, private, isolated subnets)
- NAT Gateways for high availability
- VPC Flow Logs for security monitoring
- VPC Endpoints (DynamoDB, Bedrock, S3)
- Security Groups

### 2. SecurityStack
- KMS keys with automatic rotation
- AWS Secrets Manager for configuration
- IAM roles with least privilege

### 3. DataStack
- S3 buckets with encryption and versioning
- Lifecycle policies for cost optimization
- AWS Glue Data Catalog
- Glue Crawler for schema discovery

### 4. SupplyChainAgentStack (Main)
- Lambda functions (3) with VPC, X-Ray tracing
- DynamoDB tables with encryption and PITR
- API Gateway with logging and throttling
- Cognito User Pool with MFA
- CloudWatch Alarms

### 5. MonitoringStack
- SNS topics for alarms
- CloudWatch Dashboard
- Composite alarms

### 6. BackupStack
- AWS Backup vault
- Daily and weekly backup plans
- Cross-region backup (optional)

### 7. WAFStack (Optional)
- AWS WAF Web ACL
- Managed rule sets
- Rate limiting
- Geo-blocking
- SQL injection protection

### 8. CICDStack (Optional)
- CodeCommit repository
- CodeBuild projects
- CodePipeline with stages
- Automated testing and deployment

## Well-Architected Framework Compliance

### Operational Excellence
- ✅ Infrastructure as Code (CDK)
- ✅ Automated deployments (CI/CD)
- ✅ CloudWatch monitoring and alarms
- ✅ Structured logging
- ✅ X-Ray tracing

### Security
- ✅ Encryption at rest (KMS)
- ✅ Encryption in transit (TLS)
- ✅ VPC with private subnets
- ✅ Security groups and NACLs
- ✅ IAM least privilege
- ✅ Secrets Manager
- ✅ WAF protection
- ✅ MFA for users
- ✅ VPC Flow Logs

### Reliability
- ✅ Multi-AZ deployment
- ✅ Auto-scaling (Lambda, DynamoDB)
- ✅ Point-in-time recovery
- ✅ Automated backups
- ✅ Health checks
- ✅ Retry logic
- ✅ Circuit breakers

### Performance Efficiency
- ✅ Serverless architecture
- ✅ ARM64 Lambda (Graviton2)
- ✅ VPC endpoints (reduced latency)
- ✅ DynamoDB on-demand
- ✅ API Gateway caching
- ✅ CloudFront (optional)

### Cost Optimization
- ✅ Pay-per-use pricing
- ✅ S3 lifecycle policies
- ✅ Reserved concurrency limits
- ✅ ARM64 Lambda (20% cheaper)
- ✅ VPC endpoints (no NAT costs)
- ✅ Athena query optimization

### Sustainability
- ✅ Serverless (no idle resources)
- ✅ ARM64 processors (energy efficient)
- ✅ Multi-AZ in single region
- ✅ S3 Intelligent-Tiering

## Deployment

### Prerequisites

```bash
# Install AWS CDK
npm install -g aws-cdk

# Install Python dependencies
pip install -r requirements.txt

# Configure AWS credentials
aws configure
```

### Bootstrap CDK

```bash
# Bootstrap for single account/region
cdk bootstrap aws://ACCOUNT-ID/REGION

# Bootstrap for cross-account/region
cdk bootstrap \
  --cloudformation-execution-policies arn:aws:iam::aws:policy/AdministratorAccess \
  aws://ACCOUNT-ID/us-east-1 \
  aws://ACCOUNT-ID/us-west-2
```

### Deploy All Stacks

```bash
# Set environment
export ENVIRONMENT=prod
export ALARM_EMAIL=ops@example.com

# Deploy all stacks
cdk deploy --all --require-approval never

# Or deploy specific stacks
cdk deploy SupplyChainNetwork-prod
cdk deploy SupplyChainSecurity-prod
cdk deploy SupplyChainData-prod
cdk deploy SupplyChainApp-prod
cdk deploy SupplyChainMonitoring-prod
cdk deploy SupplyChainBackup-prod
```

### Deploy with Context

```bash
# Using context file
cdk deploy --all --context environment=prod

# Using command line
cdk deploy --all \
  --context environment=prod \
  --context alarm_email=ops@example.com \
  --context enable_waf=true
```

### Environment-Specific Deployment

```bash
# Development
cdk deploy --all --context environment=dev

# Staging
cdk deploy --all --context environment=staging

# Production
cdk deploy --all --context environment=prod
```

## Configuration

### cdk.context.json

```json
{
  "environment": "prod",
  "alarm_email": "ops@example.com",
  "enable_waf": true,
  "enable_cicd": false,
  "multi_az": true,
  "enable_xray": true
}
```

### config.py

Edit `config.py` to customize:
- AWS account IDs
- Region preferences
- Resource sizing
- Retention periods
- Feature flags

## Stack Dependencies

```
NetworkStack
    ↓
SecurityStack
    ↓
DataStack
    ↓
SupplyChainAgentStack
    ↓
MonitoringStack
    ↓
BackupStack
```

## Outputs

After deployment, CDK outputs:
- VPC ID
- Security Group IDs
- S3 bucket names
- DynamoDB table names
- Lambda function ARNs
- API Gateway endpoint
- Cognito User Pool ID
- CloudWatch Dashboard URL

## Testing

```bash
# Synthesize CloudFormation templates
cdk synth

# Diff against deployed stack
cdk diff

# List all stacks
cdk list
```

## Cleanup

```bash
# Destroy all stacks
cdk destroy --all

# Destroy specific stack
cdk destroy SupplyChainApp-prod
```

**Note**: Some resources (S3 buckets, DynamoDB tables) have `RETAIN` policy and must be deleted manually.

## Cost Estimation

Use AWS Cost Calculator or:

```bash
# Generate cost estimate
cdk synth > template.yaml
# Upload to AWS Cost Calculator
```

## Monitoring

### CloudWatch Dashboard

Access at: `https://console.aws.amazon.com/cloudwatch/home?region=REGION#dashboards:`

### Alarms

- Lambda errors
- Lambda throttles
- API Gateway 5xx errors
- DynamoDB throttling
- Athena query failures

### Logs

- Lambda: `/aws/lambda/supply-chain-*`
- API Gateway: `/aws/apigateway/supply-chain-*`
- VPC Flow Logs: `/aws/vpc/flowlogs`

## Security Best Practices

1. **Rotate KMS keys**: Automatic rotation enabled
2. **Update dependencies**: Regular security patches
3. **Review IAM policies**: Least privilege principle
4. **Enable MFA**: For all users
5. **Monitor CloudTrail**: Audit all API calls
6. **Scan for vulnerabilities**: Use AWS Inspector
7. **Encrypt everything**: At rest and in transit

## Disaster Recovery

### Backup Strategy

- **RTO**: < 1 hour (redeploy via CDK)
- **RPO**: < 5 minutes (DynamoDB PITR)

### Recovery Steps

1. Deploy to DR region: `cdk deploy --all --context region=us-west-2`
2. Restore DynamoDB from backup
3. Update Route53 to point to DR region
4. Verify application functionality

## Troubleshooting

### Stack Deployment Fails

```bash
# Check CloudFormation events
aws cloudformation describe-stack-events --stack-name STACK-NAME

# Check CDK logs
cdk deploy --verbose
```

### Lambda Timeout

Increase timeout in `config.py`:
```python
lambda_timeout=600
```

### VPC Endpoint Issues

Verify security group allows HTTPS:
```bash
aws ec2 describe-security-groups --group-ids sg-xxx
```

## Support

For issues:
1. Check CloudWatch Logs
2. Review CloudFormation events
3. Verify IAM permissions
4. Check AWS Service Health Dashboard

## References

- [AWS CDK Documentation](https://docs.aws.amazon.com/cdk/)
- [AWS Well-Architected Framework](https://aws.amazon.com/architecture/well-architected/)
- [AWS Best Practices](https://aws.amazon.com/architecture/best-practices/)
