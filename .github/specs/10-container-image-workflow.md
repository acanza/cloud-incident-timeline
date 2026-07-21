# Container Image Workflow

Terraform is responsible for creating ECR repositories and ECS resources.

Terraform must not build, tag or push Docker images.

For v0.1, container images are built and pushed manually from the developer machine before ECS services are expected to become healthy.

The default tag is `dev`.

Expected workflow:

1. Run Terraform to create ECR repositories.
2. Build Docker images locally.
3. Tag Docker images using the ECR repository URLs and the `dev` tag.
4. Push Docker images to ECR.
5. Run Terraform to create or update ECS services.
6. Validate ECS tasks and ALB health checks.

If ECS services are created before images exist, the tasks may fail with image pull errors. This is expected and should be fixed by pushing the required images to ECR.