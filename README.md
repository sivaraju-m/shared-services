# Shared Services

A collection of shared utilities and infrastructure components for the AI Trading Machine ecosystem.

## Features

- Logging and error handling utilities
- Cloud infrastructure components (BigQuery, GCS, etc.)
- Configuration management
- Common data structures and utilities

## Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/shared-services.git
cd shared-services

# Install the package
pip install -e .
```

## Usage

```python
# Example: Using the logger
from shared_services.utils.logger import get_logger

logger = get_logger(__name__)
logger.info("This is an information message")
logger.error("This is an error message")

# Example: Using GCS utilities
from shared_services.infrastructure.gcs_utils import upload_to_gcs

upload_to_gcs("my-bucket", "local_file.txt", "remote_path/file.txt")
```

See documentation for more details.
