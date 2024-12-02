# Terraform Workflow Setup

This document outlines the setup and configuration of the Terraform workflow for the fleXRPL project. The workflow includes security scanning, cost estimation, and documentation generation to ensure robust infrastructure management.

## Workflow Overview

The Terraform workflow is designed to automate the following tasks:
1. **Security Scanning**: Uses Checkov to scan Terraform code for security vulnerabilities.
2. **Documentation Generation**: Automatically generates and updates Terraform module documentation using terraform-docs.
3. **Cost Estimation**: Utilizes Infracost to estimate and track infrastructure costs.
4. **Terraform Operations**: Formats, validates, plans, and applies Terraform configurations.

## Workflow Configuration

### Security Scanning

- **Tool**: Checkov
- **Purpose**: Identify security vulnerabilities in Terraform code.
- **Configuration**:
  - Runs on every push and pull request to the `main` branch.
  - Generates a SARIF report for GitHub's Security tab.
  - Soft fails to report issues without blocking the workflow.

### Documentation Generation

- **Tool**: terraform-docs
- **Purpose**: Generate and maintain up-to-date documentation for Terraform modules.
- **Configuration**:
  - Automatically updates `README.md` files in the Terraform directory.
  - Commits changes back to the repository with a descriptive commit message.

### Cost Estimation

- **Tool**: Infracost
- **Purpose**: Estimate and track infrastructure costs.
- **Configuration**:
  - Generates a cost breakdown for Terraform configurations.
  - Posts cost estimates as comments on pull requests.
  - Requires `INFRACOST_API_KEY` to be set in repository secrets.

### Terraform Operations

- **Tools**: Terraform CLI
- **Purpose**: Manage infrastructure as code.
- **Configuration**:
  - Formats and validates Terraform code.
  - Plans and applies changes to infrastructure.
  - Uses GitHub secrets for AWS credentials.

## Prerequisites

1. **GitHub Secrets**:
   - `AWS_ACCESS_KEY_ID`: AWS access key for Terraform operations.
   - `AWS_SECRET_ACCESS_KEY`: AWS secret key for Terraform operations.
   - `INFRACOST_API_KEY`: API key for Infracost cost estimation.

2. **Repository Setup**:
   - Ensure the `infrastructure/terraform` directory is structured correctly.
   - Configure `.terraform-docs.yml` for documentation settings.

This document provides a comprehensive overview of the workflow setup, detailing each component and its purpose. Let me know if you need further customization or additional sections!