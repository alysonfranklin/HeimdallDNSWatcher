# Ingress DNS Manager

## Description

Ingress DNS Manager is a Python application that monitors Ingress events in Kubernetes and manages DNS records in Cloudflare. The application updates or creates CNAME DNS records in Cloudflare based on modifications in Ingresses, using a specific label to manage the proxy status.

## Features

- Monitors creation, modification, and deletion events of Ingress in all namespaces.
- Updates existing DNS records in Cloudflare based on the `app` label and the host name of the Ingress.
- Creates new DNS records in Cloudflare when necessary.
- Deletes DNS records when the associated Ingress is deleted.
- Sets TTL to "Auto" and enables the proxy by default unless specified otherwise through the `proxyEnabled` label.

## Configuration

### Prerequisites

- **Kubernetes Cluster**: The application should be run in a Kubernetes cluster.
- **Cloudflare API Token**: A Cloudflare API token with permissions to manage DNS records.

### Environment Variables

- `CLOUDFLARE_API_TOKEN`: Cloudflare API token.
- `CLOUDFLARE_ZONE_ID`: ID of the DNS zone in Cloudflare.
- `LOG_LEVEL`: Logging level for the application (e.g., `DEBUG`, `INFO`).

### Labels in Ingress

- **`dns: cloudflare`**: Required for the Ingress to be monitored by the application.
- **`app: AppName`**: Used to associate the DNS record with a specific Ingress.
- **`proxyEnabled: true|false`** (optional): Determines if the Cloudflare proxy should be enabled. By default, the proxy is enabled (`true`).

## Deployment

### Docker

Build the Docker image:

```bash
docker build -t ingress-dns-manager .
```

Create a Secret to store the Cloudflare credentials:
```yaml
apiVersion: v1
kind: Secret
metadata:
  name: cloudflare-secrets
  namespace: default
type: Opaque
data:
  CLOUDFLARE_API_TOKEN: <base64_encoded_token>
  CLOUDFLARE_ZONE_ID: <base64_encoded_zone_id>
```

**Note**: Replace <base64_encoded_token> and <base64_encoded_zone_id> with base64 encoded values.

Create a Deployment for the application:
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ingress-dns-manager
  namespace: default
spec:
  replicas: 1
  selector:
    matchLabels:
      app: ingress-dns-manager
  template:
    metadata:
      labels:
        app: ingress-dns-manager
    spec:
      containers:
      - name: ingress-dns-manager
        image: ingress-dns-manager:latest
        env:
        - name: CLOUDFLARE_API_TOKEN
          valueFrom:
            secretKeyRef:
              name: cloudflare-secrets
              key: CLOUDFLARE_API_TOKEN
        - name: CLOUDFLARE_ZONE_ID
          valueFrom:
            secretKeyRef:
              name: cloudflare-secrets
              key: CLOUDFLARE_ZONE_ID
        - name: LOG_LEVEL
          value: "INFO"
        resources:
          limits:
            memory: "256Mi"
            cpu: "500m"
          requests:
            memory: "128Mi"
            cpu: "250m"
```

Apply the manifests in Kubernetes:
```bash
kubectl apply -f cloudflare-secrets.yaml
kubectl apply -f ingress-dns-manager-deployment.yaml
```

## Usage

The application starts monitoring Ingresses as soon as it is started. Ensure that your Ingresses are properly labeled and configured so that the DNS records are managed as expected.

## Contribution

## Contributions are welcome! Feel free to open issues or submit pull requests.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
