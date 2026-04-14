#!/usr/bin/env bash
# Verify Docker image signatures before deployment.
# Requires: cosign (https://docs.sigstore.dev/cosign/system_config/installation/)
#
# Usage: ./scripts/verify-images.sh

set -euo pipefail

LITELLM_IMAGE="ghcr.io/berriai/litellm:v1.83.3-stable"
LITELLM_KEY="https://raw.githubusercontent.com/BerriAI/litellm/0112e53/cosign.pub"

echo "Verifying LiteLLM image: $LITELLM_IMAGE"
cosign verify --key "$LITELLM_KEY" "$LITELLM_IMAGE"
echo "LiteLLM image signature verified."
