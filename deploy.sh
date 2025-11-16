#!/bin/bash
set -e

export DOCKER_BUILDKIT=1

echo "Building and pushing xcom-automation to Digital Ocean Container Registry..."

# Build with cache from the latest image
docker compose build --build-arg BUILDKIT_INLINE_CACHE=1 xcom-automation

# Push the image to the registry
docker compose push xcom-automation

echo "✅ Build and push completed successfully!"
echo "📦 Image: registry.digitalocean.com/mmazurovsky-registry/xcom-automation"
echo ""
echo "Next steps:"
echo "1. Go to Digital Ocean App Platform"
echo "2. Create/update app to use this container image"
echo "3. Configure environment variables at OS level (same as your .env file)"
echo "4. Set health check endpoint to: /health"
echo "5. Deploy!"
