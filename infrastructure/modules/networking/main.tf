# Naming convention helper
locals {
  name_prefix = "${var.project_name}-${var.environment}"

  common_tags = merge(
    var.tags,
    {
      Project     = var.project_name
      Environment = var.environment
      Terraform   = "true"
    }
  )
}

# Data source to get available AZs in the region
data "aws_availability_zones" "available" {
  state = "available"
}

# VPC
resource "aws_vpc" "main" {
  cidr_block           = var.vpc_cidr
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = merge(
    local.common_tags,
    {
      Name = "${local.name_prefix}-vpc"
    }
  )
}

# Internet Gateway
resource "aws_internet_gateway" "main" {
  vpc_id = aws_vpc.main.id

  tags = merge(
    local.common_tags,
    {
      Name = "${local.name_prefix}-igw"
    }
  )
}

# Public subnets (2 in different AZs)
resource "aws_subnet" "public" {
  count                   = 2
  vpc_id                  = aws_vpc.main.id
  cidr_block              = var.public_subnet_cidrs[count.index]
  availability_zone       = data.aws_availability_zones.available.names[count.index]
  map_public_ip_on_launch = true

  tags = merge(
    local.common_tags,
    {
      Name = "${local.name_prefix}-public-subnet-${count.index + 1}"
      Type = "Public"
    }
  )
}

# Public route table
resource "aws_route_table" "public" {
  vpc_id = aws_vpc.main.id

  tags = merge(
    local.common_tags,
    {
      Name = "${local.name_prefix}-public-rt"
      Type = "Public"
    }
  )
}

# Default route to Internet Gateway
resource "aws_route" "public_igw" {
  route_table_id         = aws_route_table.public.id
  destination_cidr_block = "0.0.0.0/0"
  gateway_id             = aws_internet_gateway.main.id
}

# Route table associations for public subnets
resource "aws_route_table_association" "public" {
  count          = 2
  subnet_id      = aws_subnet.public[count.index].id
  route_table_id = aws_route_table.public.id
}

# Security Group for ALB
# Allows HTTP 80 from anywhere, outbound to ECS services
resource "aws_security_group" "alb" {
  name_prefix = "${local.name_prefix}-alb-"
  vpc_id      = aws_vpc.main.id
  description = "Security group for Application Load Balancer"

  tags = merge(
    local.common_tags,
    {
      Name = "${local.name_prefix}-alb-sg"
    }
  )
}

# ALB SG inbound rule - HTTP from anywhere
resource "aws_vpc_security_group_ingress_rule" "alb_http" {
  security_group_id = aws_security_group.alb.id

  description = "Allow HTTP from anywhere"
  from_port   = 80
  to_port     = 80
  ip_protocol = "tcp"
  cidr_ipv4   = "0.0.0.0/0"

  tags = {
    Name = "allow-http-from-internet"
  }
}

# ALB SG outbound rule - to ECS services on application ports
# Note: This will be updated once we know the exact ECS ports
resource "aws_vpc_security_group_egress_rule" "alb_to_ecs" {
  security_group_id            = aws_security_group.alb.id
  referenced_security_group_id = aws_security_group.ecs.id

  description = "Allow outbound to ECS services"
  from_port   = 0
  to_port     = 65535
  ip_protocol = "tcp"

  tags = {
    Name = "allow-to-ecs-services"
  }
}

# Security Group for ECS services
# Allows inbound only from ALB, outbound for AWS API calls and application needs
resource "aws_security_group" "ecs" {
  name_prefix = "${local.name_prefix}-ecs-"
  vpc_id      = aws_vpc.main.id
  description = "Security group for ECS services"

  tags = merge(
    local.common_tags,
    {
      Name = "${local.name_prefix}-ecs-sg"
    }
  )
}

# ECS SG inbound rule - from ALB on all ports (ALB will route to specific ports)
resource "aws_vpc_security_group_ingress_rule" "ecs_from_alb" {
  security_group_id = aws_security_group.ecs.id

  description                  = "Allow inbound from ALB"
  from_port                    = 0
  to_port                      = 65535
  ip_protocol                  = "tcp"
  referenced_security_group_id = aws_security_group.alb.id

  tags = {
    Name = "allow-from-alb"
  }
}

# ECS SG outbound rule - HTTPS to internet (for AWS API calls)
resource "aws_vpc_security_group_egress_rule" "ecs_https" {
  security_group_id = aws_security_group.ecs.id

  description = "Allow HTTPS to internet for AWS API calls"
  from_port   = 443
  to_port     = 443
  ip_protocol = "tcp"
  cidr_ipv4   = "0.0.0.0/0"

  tags = {
    Name = "allow-https-outbound"
  }
}

# ECS SG outbound rule - HTTP to internet (if needed by containers)
resource "aws_vpc_security_group_egress_rule" "ecs_http" {
  security_group_id = aws_security_group.ecs.id

  description = "Allow HTTP to internet for containers"
  from_port   = 80
  to_port     = 80
  ip_protocol = "tcp"
  cidr_ipv4   = "0.0.0.0/0"

  tags = {
    Name = "allow-http-outbound"
  }
}
