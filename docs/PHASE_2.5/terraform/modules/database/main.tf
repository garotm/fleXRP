# RDS Configuration
resource "aws_db_instance" "main" {
  identifier        = "${var.environment}-flexrp-db"
  engine            = "postgres"
  engine_version    = var.postgres_version
  instance_class    = var.instance_class
  allocated_storage = var.allocated_storage
  
  multi_az               = true
  db_subnet_group_name   = aws_db_subnet_group.main.name
  vpc_security_group_ids = [aws_security_group.rds.id]

  backup_retention_period = 7
  backup_window          = "03:00-04:00"
  maintenance_window     = "Mon:04:00-Mon:05:00"

  # ... more configurations
} 