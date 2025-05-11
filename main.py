import logging
from image_producer import list_s3_images
from image_consumer import process_image

# Configure logging
logging.basicConfig(level=logging.INFO)

def main():
    logging.info("Starting pipeline: S3 Image Producer → Consumer")

    # Define the S3 bucket name
    bucket_name = "captcha-mapreduce-data"
    
    max_images = 50  # Limit the number of images to process
    image_count = 0  # Counter to track processed images

    try:
        # Use the list_s3_images function from image_producer to get the image keys
        image_found = False  # Flag to check if images are found
        for image_key in list_s3_images(bucket_name):
            if image_count >= max_images:
                logging.info(f"Processed {max_images} images. Stopping the pipeline.")
                break  # Stop after processing 50 images

            logging.info(f"[Pipeline] Retrieved image: {image_key}")
            image_found = True  # Set flag to True once an image is found

            # Process the image using the function from image_consumer
            process_image(bucket_name, image_key)
            image_count += 1  # Increment the processed image count
        
        if not image_found:
            logging.warning("No images were found in the S3 bucket.")
    
    except Exception as e:
        logging.error(f"Pipeline failed: {e}")

    logging.info("Pipeline finished.")

if __name__ == "__main__":
    main()
