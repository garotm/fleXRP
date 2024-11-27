# fleXRP Infrastructure as Code

This directory contains the Terraform configurations for deploying and managing fleXRP's AWS infrastructure.

## Directory Structure

```
terraform/
├── backend/                 # State management configuration
├── environments/           # Environment-specific configurations
│   ├── dev/
│   └── prod/
├── modules/               # Reusable infrastructure modules
│   ├── networking/       # VPC, subnets, routing
│   ├── database/        # RDS instances
│   ├── compute/        # Lambda, ECS/Fargate
│   ├── security/      # IAM, Security Groups, KMS
│   └── monitoring/   # CloudWatch, Alerts
└── README.md
```

## Prerequisites

### Required Tools
```bash
# Terraform (>= 1.0.0)
brew install terraform    # macOS
choco install terraform  # Windows

# AWS CLI (>= 2.0.0)
brew install awscli      # macOS
choco install awscli    # Windows

# Configure AWS CLI
aws configure
```

### AWS Account Requirements
- Administrative access
- Access key and secret key
- Appropriate service quotas
- Cost monitoring enabled

## Getting Started

### 1. Initialize State Backend
```bash
# First, create the S3 bucket and DynamoDB table for state management
cd backend
terraform init
terraform apply

# Expected output will include:
# - S3 bucket name
# - DynamoDB table name
```

### 2. Environment Configuration

#### Development Environment
```bash
# Navigate to dev environment
cd environments/dev

# Create terraform.tfvars file
cat << EOF > terraform.tfvars
environment = "dev"
aws_region = "us-west-2"
vpc_cidr = "10.0.0.0/16"
private_subnets = ["10.0.1.0/24", "10.0.2.0/24"]
public_subnets = ["10.0.101.0/24", "10.0.102.0/24"]
availability_zones = ["us-west-2a", "us-west-2b"]
EOF

# Initialize and apply
terraform init
terraform plan -out=plan.tfplan
terraform apply "plan.tfplan"
```

#### Production Environment
```bash
# Navigate to prod environment
cd environments/prod

# Create terraform.tfvars file
cat << EOF > terraform.tfvars
environment = "prod"
aws_region = "us-west-2"
vpc_cidr = "172.16.0.0/16"
private_subnets = ["172.16.1.0/24", "172.16.2.0/24"]
public_subnets = ["172.16.101.0/24", "172.16.102.0/24"]
availability_zones = ["us-west-2a", "us-west-2b"]
EOF

# Initialize and apply
terraform init
terraform plan -out=plan.tfplan
terraform apply "plan.tfplan"
```

## Module Usage

### Networking Module
```hcl
module "networking" {
  source = "../../modules/networking"
  
  environment        = var.environment
  vpc_cidr          = var.vpc_cidr
  private_subnets   = var.private_subnets
  public_subnets    = var.public_subnets
  availability_zones = var.availability_zones
}
```

### Database Module
```hcl
module "database" {
  source = "../../modules/database"
  
  environment      = var.environment
  instance_class   = "db.t3.medium"
  storage_size     = 100
  multi_az         = true
  subnet_ids       = module.networking.private_subnet_ids
}
```

## State Management

### Handling State Lock
```bash
# If you need to manually release a state lock
aws dynamodb delete-item \
    --table-name terraform-state-lock \
    --key '{"LockID": {"S": "terraform-state"}}'
```

### Importing Existing Resources
```bash
# Import existing resources into state
terraform import aws_s3_bucket.example bucket-name
```

## Common Operations

### Plan Changes
```bash
# Generate execution plan
terraform plan -out=plan.tfplan

# Show planned changes
terraform show plan.tfplan
```

### Apply Changes
```bash
# Apply with auto-approve (use with caution)
terraform apply -auto-approve

# Apply specific plan
terraform apply "plan.tfplan"
```

### Destroy Infrastructure
```bash
# Generate destroy plan
terraform plan -destroy -out=destroy.tfplan

# Execute destroy
terraform apply "destroy.tfplan"
```

## Best Practices

### 1. Version Control
- Commit `.tfvars` files only for shared environments
- Use `.tfvars.example` for templates
- Never commit sensitive data

### 2. State Management
- Always use remote state
- Enable state locking
- Enable state encryption
- Regular state backups

### 3. Security
- Use variables for sensitive data
- Implement least privilege
- Enable audit logging
- Regular security reviews

### 4. Cost Management
- Use cost estimation before apply
- Implement budget alerts
- Regular cost reviews
- Clean up unused resources

## Troubleshooting

### Common Issues

1. State Lock Timeout
```bash
# Clear stuck state lock
aws dynamodb delete-item \
    --table-name terraform-state-lock \
    --key '{"LockID": {"S": "terraform-state"}}'
```

2. Plan/Apply Failures
```bash
# Enable debug logging
export TF_LOG=DEBUG
terraform plan

# Check AWS credentials
aws sts get-caller-identity
```

## Maintenance

### Regular Tasks
1. Update provider versions
2. Review and update module versions
3. Security patches
4. Cost optimization
5. State cleanup

### Updates
```bash
# Update providers
terraform init -upgrade

# Update state
terraform refresh
```

## Support

For infrastructure support:
- Documentation: `/docs/infrastructure`
- Issues: GitHub Issues
- Email: devops@flexrp.com

## Contributing

1. Create feature branch
2. Make changes
3. Test changes
4. Submit pull request
5. Wait for review

## Security

Report security issues to: security@flexrp.com

## License

Copyright (c) 2024 fleXRP. All rights reserved. 