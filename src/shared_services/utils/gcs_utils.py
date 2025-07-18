# src/ai_trading_machine/utils/gcs_utils.py

from io import BytesIO

import pandas as pd
from google.cloud import storage


def upload_to_gcs(df: pd.DataFrame, bucket: str, destination_blob_name: str):
    """
    Upload DataFrame as Parquet file to GCS bucket.
    """
    client = storage.Client()
    bucket = client.get_bucket(bucket)
    blob = bucket.blob(destination_blob_name)

    buffer = BytesIO()
    df.to_parquet(buffer, index=False)
    buffer.seek(0)

    blob.upload_from_file(buffer, content_type="application/octet-stream")
    print("✅ Uploaded to gs://{bucket.name}/{destination_blob_name}")


def load_cleaned_data(
    ticker: str, start_date: str, end_date: str, bucket: str = "cleaned-data"
) -> pd.DataFrame:
    """
    Download a cleaned Parquet file from GCS and load as DataFrame.
    """
    client = storage.Client()
    bucket_obj = client.get_bucket(bucket)
    filename = "{ticker}_{start_date}_{end_date}.parquet"
    blob = bucket_obj.blob(filename)
    buffer = BytesIO()
    blob.download_to_file(buffer)
    buffer.seek(0)
    df = pd.read_parquet(buffer)
    print("✅ Loaded cleaned data from gs://{bucket}/{filename}")
    return df


def download_from_gcs(
    bucket_name: str, source_blob_name: str, destination_file_path: str = None
):
    """
    Download a file from Google Cloud Storage.

    Args:
        bucket_name: Name of the GCS bucket
        source_blob_name: Name of the blob (file path in GCS)
        destination_file_path: Local path where the file should be saved.
                              If None, returns the file content as bytes.

    Returns:
        If destination_file_path is None, returns the file content as bytes.
        Otherwise, returns None after saving the file to the specified path.
    """
    client = storage.Client()
    bucket = client.get_bucket(bucket_name)
    blob = bucket.blob(source_blob_name)

    if destination_file_path:
        blob.download_to_filename(destination_file_path)
        print(
            f"✅ Downloaded gs://{bucket_name}/{source_blob_name} to {destination_file_path}"
        )
        return None
    else:
        # Download to memory
        content = blob.download_as_bytes()
        print(f"✅ Downloaded gs://{bucket_name}/{source_blob_name} to memory")
        return content
