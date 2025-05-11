from confluent_kafka import Producer
import logging
import json
import boto3
import uuid
from datetime import datetime

# Setup logging
logging.basicConfig(level=logging.INFO)

# Initialize S3 and Kafka producer
s3 = boto3.client("s3")

# Kafka producer configuration 
conf = {
    'bootstrap.servers': 'localhost:9092',  # Kafka installed on localhost
}

# Initialize the producer with the configuration
producer = Producer(conf)

def list_s3_images(bucket_name):
    """List image objects from S3 bucket."""
    logging.info(f"Starting to list images from S3 bucket: {bucket_name}")
    paginator = s3.get_paginator('list_objects_v2')
    page_iterator = paginator.paginate(Bucket=bucket_name)
    
    for page in page_iterator:
        if 'Contents' in page:
            for obj in page['Contents']:
                key = obj['Key']
                if key.endswith('.png') or key.endswith('.jpeg'):
                    yield key

def send_image_metadata_to_kafka(image_key, bucket_name):
    """Send image metadata to Kafka topic."""
    metadata = {
        'image_key': image_key,
        'bucket_name': bucket_name,
        'timestamp': str(datetime.utcnow()),
        'uuid': str(uuid.uuid4())  # Generate a unique ID for the image
    }
    logging.info(f"Sending metadata for {image_key} to Kafka.")
    
    # Manually serialize key and value
    producer.produce('image_topic', key=image_key.encode('utf-8'), value=json.dumps(metadata).encode('utf-8'))
    producer.flush()

if __name__ == "__main__":
    bucket_name = "captcha-mapreduce-data"
    for image_key in list_s3_images(bucket_name):
        send_image_metadata_to_kafka(image_key, bucket_name)
