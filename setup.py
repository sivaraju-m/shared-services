from setuptools import setup, find_packages

setup(
    name="shared-services",
    version="0.1.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "pandas>=1.5.0",
        "numpy>=1.22.0",
        "google-cloud-bigquery>=3.3.5",
        "google-cloud-storage>=2.7.0",
        "google-cloud-secret-manager>=2.12.6",
        "pyyaml>=6.0",
    ],
    python_requires=">=3.11",
    author="Your Name",
    author_email="your.email@example.com",
    description="Shared utilities and infrastructure components for AI Trading Machine",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/shared-services",
)
