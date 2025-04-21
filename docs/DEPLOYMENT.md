# Cheque Information Extractor - Deployment Guide

This document provides comprehensive instructions for deploying the Cheque Information Extractor application in various environments.

## Deployment Options

The application can be deployed in several ways depending on your infrastructure requirements:

1. **Local Deployment**: Running on a local machine for development or small-scale use
2. **Server Deployment**: Hosting on a dedicated server for team use
3. **Docker Deployment**: Containerized deployment for easier management and scaling
4. **Cloud Deployment**: Hosting on cloud platforms like AWS, Azure, or GCP

## Prerequisites

For all deployment options, you'll need:

- Python 3.8+ installed
- AWS account with Bedrock and S3 access
- Appropriate IAM permissions for Bedrock and S3
- Network access to AWS services

## 1. Local Deployment

### 1.1 Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/your-repo/cheque-extractor.git
   cd cheque-extractor
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Create a `.env` file with AWS credentials:
   ```
   AWS_REGION=your-region
   AWS_ACCESS_KEY_ID=your-access-key
   AWS_SECRET_ACCESS_KEY=your-secret-key
   S3_BUCKET_NAME=your-bucket-name
   ```

### 1.2 Running Locally

Launch the application:
```bash
streamlit run main.py
```

This will start the application and open it in your default web browser at `http://localhost:8501`.

## 2. Server Deployment

For multi-user access, deploy on a server:

### 2.1 Server Setup

1. Provision a server with:
   - Ubuntu 20.04 LTS or newer recommended
   - Minimum 4GB RAM, 2 CPU cores
   - Python 3.8+ installed

2. Clone the repository:
   ```bash
   git clone https://github.com/your-repo/cheque-extractor.git
   cd cheque-extractor
   ```

3. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate
   ```

4. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

5. Create the `.env` file with credentials as in the local setup.

### 2.2 Using systemd for Service Management

Create a systemd service file for automatic startup and management:

1. Create a service file:
   ```bash
   sudo nano /etc/systemd/system/cheque-extractor.service
   ```

2. Add the following content (adjust paths as needed):
   ```
   [Unit]
   Description=Cheque Information Extractor
   After=network.target

   [Service]
   User=your-user
   WorkingDirectory=/path/to/cheque-extractor
   Environment="PATH=/path/to/cheque-extractor/venv/bin"
   ExecStart=/path/to/cheque-extractor/venv/bin/streamlit run main.py --server.port=8501 --server.address=0.0.0.0
   Restart=always
   RestartSec=5

   [Install]
   WantedBy=multi-user.target
   ```

3. Enable and start the service:
   ```bash
   sudo systemctl enable cheque-extractor
   sudo systemctl start cheque-extractor
   ```

4. Check service status:
   ```bash
   sudo systemctl status cheque-extractor
   ```

### 2.3 Reverse Proxy Setup (Optional)

For HTTPS and better security, set up NGINX as a reverse proxy:

1. Install NGINX:
   ```bash
   sudo apt update
   sudo apt install nginx
   ```

2. Create an NGINX configuration:
   ```bash
   sudo nano /etc/nginx/sites-available/cheque-extractor
   ```

3. Add the following configuration:
   ```
   server {
       listen 80;
       server_name your-domain.com;

       location / {
           proxy_pass http://localhost:8501;
           proxy_http_version 1.1;
           proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
           proxy_set_header Host $host;
           proxy_set_header Upgrade $http_upgrade;
           proxy_set_header Connection "upgrade";
           proxy_read_timeout 86400;
       }
   }
   ```

4. Enable the site:
   ```bash
   sudo ln -s /etc/nginx/sites-available/cheque-extractor /etc/nginx/sites-enabled/
   sudo nginx -t
   sudo systemctl restart nginx
   ```

5. Set up SSL with Certbot (recommended):
   ```bash
   sudo apt install certbot python3-certbot-nginx
   sudo certbot --nginx -d your-domain.com
   ```

## 3. Docker Deployment

For containerized deployment:

### 3.1 Dockerfile

Create a `Dockerfile` in the project root:

```dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8501

CMD ["streamlit", "run", "main.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

### 3.2 Building and Running the Docker Image

1. Build the Docker image:
   ```bash
   docker build -t cheque-extractor:latest .
   ```

2. Run the container:
   ```bash
   docker run -p 8501:8501 \
     -e AWS_REGION=your-region \
     -e AWS_ACCESS_KEY_ID=your-access-key \
     -e AWS_SECRET_ACCESS_KEY=your-secret-key \
     -e S3_BUCKET_NAME=your-bucket-name \
     cheque-extractor:latest
   ```

### 3.3 Docker Compose (Optional)

For easier configuration, create a `docker-compose.yml` file:

```yaml
version: '3'

services:
  cheque-extractor:
    build: .
    ports:
      - "8501:8501"
    environment:
      - AWS_REGION=${AWS_REGION}
      - AWS_ACCESS_KEY_ID=${AWS_ACCESS_KEY_ID}
      - AWS_SECRET_ACCESS_KEY=${AWS_SECRET_ACCESS_KEY}
      - S3_BUCKET_NAME=${S3_BUCKET_NAME}
    restart: always
```

Run with Docker Compose:
```bash
docker-compose up -d
```

## 4. Cloud Deployment

### 4.1 AWS Deployment

#### 4.1.1 Using EC2

1. Launch an EC2 instance with Amazon Linux 2 or Ubuntu
2. Follow the server deployment steps above
3. Configure security groups to allow traffic on port 80/443
4. (Optional) Set up an Elastic IP for a static IP address

#### 4.1.2 Using ECS/Fargate

1. Create an ECR repository:
   ```bash
   aws ecr create-repository --repository-name cheque-extractor
   ```

2. Build and push the Docker image:
   ```bash
   aws ecr get-login-password | docker login --username AWS --password-stdin your-account-id.dkr.ecr.region.amazonaws.com
   docker build -t your-account-id.dkr.ecr.region.amazonaws.com/cheque-extractor:latest .
   docker push your-account-id.dkr.ecr.region.amazonaws.com/cheque-extractor:latest
   ```

3. Create a Fargate cluster, task definition, and service using the AWS console or CLI

### 4.2 Azure Deployment

Azure offers several options for deploying containerized applications:

1. Azure App Service:
   - Create a Web App for Containers
   - Point it to your Docker image
   - Configure environment variables for AWS credentials

2. Azure Container Instances:
   - Deploy a container directly
   - Set environment variables for configuration

### 4.3 GCP Deployment

1. Google Cloud Run:
   - Build and push your image to Google Container Registry
   - Deploy using Cloud Run for a serverless container deployment
   - Set environment variables for AWS credentials

## 5. Security Considerations

### 5.1 Credential Management

For production deployments, never store AWS credentials directly in files:

1. Use environment variables passed at runtime
2. Use AWS IAM roles for EC2/ECS when deploying on AWS
3. Use credential management services like:
   - AWS Secrets Manager
   - Azure Key Vault
   - Google Secret Manager

### 5.2 Network Security

1. Always use HTTPS in production
2. Restrict access using firewall rules
3. Consider using a VPN for internal deployments
4. Implement proper authentication mechanisms

### 5.3 AWS IAM Best Practices

1. Create a dedicated IAM user or role with limited permissions
2. Use the principle of least privilege
3. Required permissions:
   - `bedrock:InvokeModel` for Claude models
   - `s3:PutObject`, `s3:GetObject` for the specific S3 bucket

## 6. Scaling Considerations

For high-volume deployments:

1. **Horizontal Scaling**:
   - Deploy behind a load balancer
   - Use multiple instances or containers

2. **Resource Allocation**:
   - Monitor memory usage as image processing can be memory-intensive
   - Adjust container resources based on load

3. **S3 Performance**:
   - Consider S3 transfer acceleration for better upload performance
   - Use S3 standard for most use cases, or S3 IA for less frequently accessed reports

## 7. Monitoring

Set up monitoring for your deployment:

1. **System Monitoring**:
   - CPU/Memory usage
   - Disk space
   - Network traffic

2. **Application Monitoring**:
   - Request/response times
   - Error rates
   - User activity

3. **AWS Service Monitoring**:
   - S3 metrics
   - Bedrock API usage
   - Cost monitoring

## 8. Backup and Disaster Recovery

1. **Database Backups**:
   - The application uses S3 for storage, which is already durable
   - Consider S3 versioning for additional protection

2. **Configuration Backups**:
   - Back up `.env` files and environment variables
   - Use Infrastructure as Code for reproducible deployments

3. **Disaster Recovery Plan**:
   - Document recovery procedures
   - Test restoration procedures periodically

## 9. Troubleshooting

Common deployment issues:

| Issue | Possible Solution |
|-------|-------------------|
| Application won't start | Check environment variables, Python version, and dependencies |
| AWS connectivity issues | Verify credentials and network connectivity to AWS |
| Image upload failures | Check S3 permissions and bucket configuration |
| Performance degradation | Monitor resource usage and scale as needed |

## 10. Maintenance

Regular maintenance tasks:

1. **Updates**:
   - Regularly update dependencies
   - Check for security patches
   - Update AI models when new versions are available

2. **Monitoring**:
   - Review logs regularly
   - Set up alerts for critical errors
   - Monitor usage patterns

3. **Performance Tuning**:
   - Adjust resources based on usage patterns
   - Optimize image processing if needed

## Contact

For deployment support, contact:
consulting@bellblazetech.com 