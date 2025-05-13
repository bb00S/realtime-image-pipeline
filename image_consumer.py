from confluent_kafka import Consumer
import logging
import boto3
import json
import cv2
import numpy as np
from datetime import datetime
import meilisearch
import pandas as pd
import matplotlib.pyplot as plt
from tabulate import tabulate

# Logging setup
logging.basicConfig(level=logging.INFO)

# AWS S3 client
s3 = boto3.client("s3")

# Kafka consumer setup
consumer = Consumer({
    'bootstrap.servers': 'localhost:9092',  # Changeable via Docker env
    'group.id': 'image_consumer_group',
    'auto.offset.reset': 'earliest'
})

# MeiliSearch setup
meili_client = meilisearch.Client('http://127.0.0.1:7700')  # Port configurable
index = meili_client.index('image_metadata')

# Image processing control
MAX_IMAGES = 50
processed_images = 0
processed_data = []

def process_image(bucket_name, file_name):
    """Process image using OpenCV and index metadata into MeiliSearch."""
    global processed_images
    if processed_images >= MAX_IMAGES:
        return
    
    try:
        response = s3.get_object(Bucket=bucket_name, Key=file_name)
        img_bytes = response['Body'].read()
        img_array = np.frombuffer(img_bytes, dtype=np.uint8)
        img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)

        if img is not None:
            gray_img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            cv2.imshow('Processed Image', gray_img)
            cv2.waitKey(1)

            metadata = {
                'image_key': file_name,
                'timestamp': str(datetime.utcnow()),
                'size': len(img_bytes),
                'bucket_name': bucket_name,
                'opencv_processing': 'grayscale',
                'file_name': file_name,
                'size_kb': len(img_bytes) / 1024,
            }

            index.add_documents([metadata])
            logging.info(f"Processed {file_name} and indexed metadata.")

            processed_data.append({
                'file_name': file_name,
                'size_kb': len(img_bytes) / 1024,
                'timestamp': str(datetime.utcnow()),
                'image': gray_img
            })

            processed_images += 1
        else:
            logging.warning(f"Image decode failed: {file_name}")

    except Exception as e:
        logging.error(f"Image processing error ({file_name}): {e}")

def query_meilisearch(query):
    """Search metadata using MeiliSearch."""
    try:
        return index.search(query)['hits']
    except Exception as e:
        logging.error(f"MeiliSearch query error: {e}")
        return []

def visualize_terminal_metadata():
    """Visualizes metadata in terminal and plots."""
    if not processed_data:
        logging.warning("No data to visualize.")
        return

    df = pd.DataFrame([{
        "file_name": d["file_name"],
        "size_kb": d["size_kb"],
        "timestamp": d["timestamp"]
    } for d in processed_data])

    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df['hour'] = df['timestamp'].dt.hour

    print("\n Image Metadata Table:\n")
    print(tabulate(df[['file_name', 'size_kb', 'timestamp']], headers='keys', tablefmt='fancy_grid'))

    plt.figure(figsize=(12, 5))
    plt.subplot(1, 2, 1)
    plt.hist(df['size_kb'], bins=10, color='skyblue', edgecolor='black')
    plt.title('Image Size Distribution (KB)')
    plt.xlabel('File Size (KB)')
    plt.ylabel('Frequency')

    plt.subplot(1, 2, 2)
    plt.hist(df['hour'], bins=24, color='salmon', edgecolor='black')
    plt.title('Image Processing Hour Distribution')
    plt.xlabel('Hour')
    plt.ylabel('Frequency')

    plt.tight_layout()
    plt.show()

    images = [d['image'] for d in processed_data if d['image'] is not None]
    if images:
        fig, axs = plt.subplots(1, min(5, len(images)), figsize=(15, 3))
        for i, img in enumerate(images[:5]):
            axs[i].imshow(img)
            axs[i].axis('off')
        plt.suptitle("Sample Images")
        plt.tight_layout()
        plt.show()

def visualize_mapreduce_output(path='output.txt'):
    """Reads and visualizes key-value output from MapReduce result file."""
    try:
        with open(path, 'r') as f:
            lines = f.readlines()

        data = [line.strip().split('\t') for line in lines if '\t' in line]
        df = pd.DataFrame(data, columns=['key', 'value'])
        df['value'] = pd.to_numeric(df['value'], errors='coerce')

        print("\n MapReduce Output (Top 10 rows):\n")
        print(tabulate(df.head(10), headers='keys', tablefmt='fancy_grid'))

        plt.figure(figsize=(10, 5))
        plt.bar(df['key'], df['value'], color='orange', edgecolor='black')
        plt.title('MapReduce Aggregation Output')
        plt.xlabel('Key')
        plt.ylabel('Value')
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.show()
    except Exception as e:
        logging.error(f"Error visualizing MapReduce output: {e}")

def process_all_images():
    """Consume Kafka topic and process images."""
    consumer.subscribe(['image_topic'])

    try:
        while True:
            msg = consumer.poll(timeout=1.0)
            if msg is None:
                continue
            if msg.error():
                logging.error(f"Kafka error: {msg.error()}")
                continue

            metadata = json.loads(msg.value())
            process_image(metadata['bucket_name'], metadata['image_key'])

            if processed_images >= MAX_IMAGES:
                break

    except Exception as e:
        logging.error(f"Kafka processing error: {e}")
    finally:
        consumer.close()

    visualize_terminal_metadata()
    visualize_mapreduce_output('output.txt')  # Change name of the file as needed

if __name__ == "__main__":
    logging.info("Kafka consumer started for image processing.")
    process_all_images()
    cv2.destroyAllWindows()

