.PHONY: help init fmt validate plan apply destroy clean refresh state-list state-show tf-version show output console graph print-env

# Colors for output
BLUE := \033[0;34m
GREEN := \033[0;32m
RED := \033[0;31m
YELLOW := \033[0;33m
NC := \033[0m # No Color

# Project variables
TERRAFORM_DIR := infrastructure
ENVIRONMENT ?= dev
ENVIRONMENT_DIR := $(TERRAFORM_DIR)/environments/$(ENVIRONMENT)
PLAN_FILE := tfplan

# Check if environment directory exists
ENVIRONMENT_EXISTS := $(shell [ -d "$(ENVIRONMENT_DIR)" ] && echo true || echo false)

## help: Display this help message
help:
	@echo "$(BLUE)Cloud Incident Timeline - Terraform Makefile$(NC)"
	@echo ""
	@echo "Usage: make [target]"
	@echo ""
	@echo "$(GREEN)Core Terraform Commands:$(NC)"
	@grep -E '^## ' $(MAKEFILE_LIST) | grep -v 'hidden' | awk 'BEGIN {FS = ":.*?## "}; {printf "  make %-20s %s\n", $$2, $$3}' | sed 's/hidden://'
	@echo ""
	@echo "$(YELLOW)Environment:$(NC)"
	@echo "  ENVIRONMENT=dev|prod  Set the target environment (default: dev)"
	@echo ""
	@echo "$(YELLOW)Examples:$(NC)"
	@echo "  make fmt validate plan          # Standard workflow (safe)"
	@echo "  make plan ENVIRONMENT=dev       # Plan for dev environment"
	@echo "  make apply                      # Apply changes (requires confirmation)"
	@echo "  make destroy                    # Destroy infrastructure (requires confirmation)"
	@echo ""

## init: Initialize Terraform (downloads providers and sets up backend)
init:
	@echo "$(BLUE)Initializing Terraform for environment: $(ENVIRONMENT)$(NC)"
	@if [ "$(ENVIRONMENT_EXISTS)" = "false" ]; then \
		echo "$(RED)Error: Environment directory not found: $(ENVIRONMENT_DIR)$(NC)"; \
		echo "Available environments: $$(ls -1 $(TERRAFORM_DIR)/environments 2>/dev/null || echo 'none')"; \
		exit 1; \
	fi
	cd $(ENVIRONMENT_DIR) && terraform init

## fmt: Format Terraform code (idempotent)
fmt:
	@echo "$(BLUE)Formatting Terraform code in $(TERRAFORM_DIR)$(NC)"
	cd $(TERRAFORM_DIR) && terraform fmt -recursive -check=false .
	@echo "$(GREEN)✓ Code formatted$(NC)"

## validate: Validate Terraform configuration syntax (no AWS calls)
validate:
	@echo "$(BLUE)Validating Terraform configuration$(NC)"
	cd $(ENVIRONMENT_DIR) && terraform validate
	@echo "$(GREEN)✓ Configuration is valid$(NC)"

## plan: Generate Terraform plan (safe, read-only)
plan: fmt validate
	@echo "$(BLUE)Generating Terraform plan for environment: $(ENVIRONMENT)$(NC)"
	@echo "$(YELLOW)Note: Use 'make apply' to apply these changes$(NC)"
	cd $(ENVIRONMENT_DIR) && terraform plan -out=$(PLAN_FILE)

## apply: Apply Terraform changes (REQUIRES CONFIRMATION)
apply:
	@if [ ! -f "$(ENVIRONMENT_DIR)/$(PLAN_FILE)" ]; then \
		echo "$(YELLOW)Warning: No plan file found. Running plan first...$(NC)"; \
		$(MAKE) plan; \
	fi
	@echo ""
	@echo "$(RED)⚠️  APPLYING CHANGES TO $(ENVIRONMENT) ENVIRONMENT$(NC)"
	@echo "$(RED)This will modify your AWS infrastructure.$(NC)"
	@read -p "Type 'yes' to confirm: " confirm; \
	if [ "$$confirm" = "yes" ]; then \
		echo "$(BLUE)Applying Terraform changes...$(NC)"; \
		cd $(ENVIRONMENT_DIR) && terraform apply $(PLAN_FILE); \
		rm -f $(ENVIRONMENT_DIR)/$(PLAN_FILE); \
		echo "$(GREEN)✓ Infrastructure updated$(NC)"; \
	else \
		echo "$(YELLOW)Apply cancelled$(NC)"; \
		exit 1; \
	fi

## destroy: Destroy all infrastructure (REQUIRES CONFIRMATION - use with caution!)
destroy:
	@echo ""
	@echo "$(RED)⚠️  DESTRUCTION WARNING ⚠️$(NC)"
	@echo "$(RED)This will PERMANENTLY DELETE all infrastructure in $(ENVIRONMENT).$(NC)"
	@echo "$(RED)This action CANNOT be undone easily.$(NC)"
	@echo ""
	@echo "$(YELLOW)Cost-control principle:$(NC) This project can be destroyed after testing."
	@read -p "Type 'destroy-$(ENVIRONMENT)' to confirm: " confirm; \
	if [ "$$confirm" = "destroy-$(ENVIRONMENT)" ]; then \
		cd $(ENVIRONMENT_DIR) && terraform destroy; \
		echo "$(GREEN)✓ Infrastructure destroyed$(NC)"; \
	else \
		echo "$(YELLOW)Destroy cancelled$(NC)"; \
		exit 1; \
	fi

## refresh: Refresh Terraform state from AWS (detects manual changes)
refresh: validate
	@echo "$(BLUE)Refreshing Terraform state...$(NC)"
	cd $(ENVIRONMENT_DIR) && terraform refresh
	@echo "$(GREEN)✓ State refreshed$(NC)"

## state-list: List all resources in Terraform state
state-list:
	@echo "$(BLUE)Resources in state for $(ENVIRONMENT):$(NC)"
	cd $(ENVIRONMENT_DIR) && terraform state list

## state-show: Show detailed state of a resource (usage: make state-show RESOURCE=aws_instance.example)
state-show:
	@if [ -z "$(RESOURCE)" ]; then \
		echo "$(RED)Error: RESOURCE not specified$(NC)"; \
		echo "Usage: make state-show RESOURCE=<resource_address>"; \
		echo "Example: make state-show RESOURCE=aws_instance.web"; \
		exit 1; \
	fi
	@echo "$(BLUE)Showing state for resource: $(RESOURCE)$(NC)"
	cd $(ENVIRONMENT_DIR) && terraform state show $(RESOURCE)

## tf-version: Show Terraform version and provider versions
tf-version:
	@echo "$(BLUE)Terraform Version:$(NC)"
	terraform version
	@echo ""
	@echo "$(BLUE)Provider Configuration (from $(ENVIRONMENT_DIR)):$(NC)"
	@if grep -r "required_providers" $(ENVIRONMENT_DIR) >/dev/null 2>&1; then \
		grep -A 10 "required_providers" $(ENVIRONMENT_DIR)/versions.tf 2>/dev/null || echo "Check versions.tf for provider requirements"; \
	fi

## clean: Remove Terraform temporary files (safe to run)
clean:
	@echo "$(BLUE)Cleaning Terraform temporary files...$(NC)"
	find $(TERRAFORM_DIR) -type d -name ".terraform" -exec rm -rf {} + 2>/dev/null || true
	find $(TERRAFORM_DIR) -name ".terraform.lock.hcl" -delete
	find $(TERRAFORM_DIR) -name "$(PLAN_FILE)" -delete
	@echo "$(GREEN)✓ Cleanup complete$(NC)"

## show: Show current Terraform state (human-readable)
show:
	@echo "$(BLUE)Current state for environment: $(ENVIRONMENT)$(NC)"
	cd $(ENVIRONMENT_DIR) && terraform show

## output: Display Terraform outputs
output:
	@echo "$(BLUE)Outputs for environment: $(ENVIRONMENT)$(NC)"
	cd $(ENVIRONMENT_DIR) && terraform output

## console: Open Terraform console for interactive evaluation
console:
	@echo "$(BLUE)Opening Terraform console for $(ENVIRONMENT)$(NC)"
	cd $(ENVIRONMENT_DIR) && terraform console

## graph: Generate dependency graph (output: graph.png)
graph:
	@echo "$(BLUE)Generating Terraform dependency graph...$(NC)"
	cd $(ENVIRONMENT_DIR) && terraform graph | dot -Tsvg > graph.svg
	@echo "$(GREEN)✓ Graph saved to graph.svg$(NC)"

## .SILENT: Hide commands for cleaner output

print-env:
	@echo "TERRAFORM_DIR: $(TERRAFORM_DIR)"
	@echo "ENVIRONMENT: $(ENVIRONMENT)"
	@echo "ENVIRONMENT_DIR: $(ENVIRONMENT_DIR)"
	@echo "PLAN_FILE: $(PLAN_FILE)"
