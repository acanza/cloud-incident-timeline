# Networking Specification

## Scope

The networking layer must be intentionally simple and cost-aware.

## Resources

Create:

- One VPC.
- Two public subnets in different Availability Zones.
- One Internet Gateway.
- One public route table.
- Public route to `0.0.0.0/0` through the Internet Gateway.
- ALB security group.
- ECS services security group.

Do not create in v0.1:

- NAT Gateway.
- Private subnets.
- VPC endpoints.
- Bastion host.
- VPN.
- Transit Gateway.

## ECS subnet strategy

For v0.1, ECS tasks must run in public subnets with:

```hcl
assign_public_ip = true
```

This is a deliberate decision to avoid NAT Gateway cost.

## Security group rules
### ALB security group

Inbound:

- Allow HTTP 80 from 0.0.0.0/0.

Outbound:

- Allow traffic to ECS service port.

### ECS security group

Inbound:

- Allow application port only from the ALB security group.

Outbound:

- Allow HTTPS 443 to the internet for AWS API calls.
- Allow HTTP/HTTPS as required by the containers.

No inbound traffic from 0.0.0.0/0 should be allowed directly to ECS tasks.
