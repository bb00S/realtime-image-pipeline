
# Real-Time Image Processing Pipeline with Kafka, OpenCV & MeiliSearch (AWS Deployment)

## 📌 Project Overview

This project implements a real-time image processing pipeline using **Apache Kafka**, **OpenCV**, and **MeiliSearch**, integrated with **AWS S3, EC2 AND EMR** for deployment and storage. It streams image metadata from Kafka producers, fetches images from AWS S3, processes them using OpenCV, stores structured metadata in MeiliSearch, and provides both **tabular** and **graphical** visualizations of the results.

---

## AWS Infrastructure Setup

### 1. Configure AWS S3 (Image Storage)

1. Go to the [S3 Console](https://eu-north-1.console.aws.amazon.com/s3/home?region=eu-north-1#).
2. Click **"Create bucket"** and give it a unique name (`captcha-mapreduce-data`).
3. Choose the AWS Region closest to you.

<img width="503" alt="Screenshot 2025-04-10 at 16 20 50" src="https://github.com/user-attachments/assets/e1852a10-6c68-43d9-b0b1-fde1e1daab78" />

4. Leave default settings or disable **Block all public access** if needed (not recommended for sensitive data).
5. Upload test images or use your Kafka producer to send image metadata pointing to this bucket.

<img width="503" alt="Screenshot 2025-04-10 at 16 05 21" src="https://github.com/user-attachments/assets/3796f5ba-7816-42c4-9ce9-f429478c9265" />

### 2. Launch & Configure EC2 Instance

1. Go to the [EC2 Console](https://eu-north-1.console.aws.amazon.com/ec2/home?region=eu-north-1#Instances).
2. Launch a new instance using an **Ubuntu** or **Amazon Linux 2 AMI**.

<img width="503" alt="Screenshot 2025-04-10 at 16 23 13" src="https://github.com/user-attachments/assets/039f419a-7e05-4795-81e9-52dd1bf1ac2c" />

3. Choose a free-tier eligible instance type (`t3.micro`).
4. Under **Key pair**, create or select one to SSH into your instance.
5. In **Network Settings → Edit Inbound Rules**, enable:
   - Port `22` (SSH)
   - Port `9092` (Kafka)
   - Port `7700` (MeiliSearch)
   - Port `5000` or `8888` (Flask/Streamlit dashboard if needed)

<img width="503" alt="Screenshot 2025-04-10 at 16 24 24" src="https://github.com/user-attachments/assets/68f27f73-1aac-4470-a84e-472a78c1e413" />

---

### 3. Set Security Groups

- Allow access from anywhere by setting the inbound rules to 0.0.0.0/0 for the required ports 
- Download and secure your `.pem` key file.
- SSH into EC2:

```bash
chmod 400 opencv-key.pem
ssh -i "opencv-key.pem" ec2-user@ip-13.51.6.137
```

---

### 4.EMR Cluster Configuration

1. Go to the [Amazon EMR Console](https://eu-north-1.console.aws.amazon.com/emr/home?region=eu-north-1#/clusters).
2. Click **"Create Cluster"**, then choose the following settings:
   - **Release version**: EMR 6.x
   - **Applications**: Hadoop (required), Spark (optional)
  
<img width="503" alt="Screenshot 2025-04-12 at 10 35 58" src="https://github.com/user-attachments/assets/f0638d01-816d-46e4-b186-38314e2be360" />

   - **Cluster type**: EMR on EC2
   - **Instance count**: 1 Master + 1 Core
   - **Instance type**: `m5.xlarge` or any available option

<img width="503" alt="Screenshot 2025-04-12 at 10 37 02" src="https://github.com/user-attachments/assets/45fd6e5a-ad3f-4bc4-945b-6a7e97f3c909" />

3. Set **EC2 key pair** to the one you created previously (e.g., `opencv-key.pem`).
4. Under **Cluster logs**, choose your existing bucket (`captcha-mapreduce-data`) or create one for storing job logs.


#### SSH Access & Permissions

```bash
chmod 400 /Users/borisborovcanin/Desktop/opencv-key.pem
ssh -i /Users/borisborovcanin/Desktop/opencv-key.pem hadoop@ec2-16-170-228-222.eu-north-1.compute.amazonaws.com
```

#### Upload Data and Scripts to HDFS

```bash
hdfs dfs -put captcha_metadata.csv /user/hadoop/input/
hdfs dfs -put mapper.py /user/hadoop/input/
hdfs dfs -put reducer.py /user/hadoop/input/
hdfs dfs -ls /user/hadoop/input/
```

#### Run Hadoop Streaming Job (HDFS Mode)

```bash
hadoop jar /usr/lib/hadoop-mapreduce/hadoop-streaming.jar \
  -input /user/hadoop/input/captcha_metadata.csv \
  -output /user/hadoop/output \
  -mapper mapper.py \
  -reducer reducer.py \
  -file mapper.py \
  -file reducer.py
```

#### View Output in HDFS

```bash
hdfs dfs -ls /user/hadoop/output/
hdfs dfs -cat /user/hadoop/output/part-00000
```

#### Run Hadoop Streaming Job with S3 Paths

```bash
hadoop jar /usr/lib/hadoop-mapreduce/hadoop-streaming.jar \
  -input s3://captcha-mapreduce-data/data/captcha_metadata.csv \
  -output s3://captcha-mapreduce-data/output/captcha_summary \
  -mapper s3://captcha-mapreduce-data/scripts/mapper.py \
  -reducer s3://captcha-mapreduce-data/scripts/reducer.py \
  -file s3://captcha-mapreduce-data/scripts/mapper.py \
  -file s3://captcha-mapreduce-data/scripts/reducer.py
```

#### Download Output from S3

```bash
aws s3 cp s3://captcha-mapreduce-data/output/captcha_summary/part-00000 ./output.txt
```

#### Identity Job Test

```bash
hadoop jar /usr/lib/hadoop-mapreduce/hadoop-streaming.jar \
  -input /user/hadoop/input/captcha_metadata.csv \
  -output /user/hadoop/output \
  -mapper /bin/cat \
  -reducer /bin/cat
```
---

## Technology Stack

| Component     | Role                                    |
|---------------|------------------------------------------|
| Kafka         | Real-time image metadata streaming       |
| OpenCV        | Image processing & manipulation          |
| MeiliSearch   | Fast metadata indexing & search engine   |
| AWS S3        | Cloud-based image storage                |
| AWS EC2       | Host for Kafka, MeiliSearch, processing  |
| AWS EMR       | Hadoop-based distributed data processing |
| Python        | Main language for all microservices      |
| Matplotlib    | Visual representation of metadata        |
| Tabulate      | Terminal-based tabular views             |

---

## Data Flow

1. **Kafka Producer** sends metadata (e.g., `bucket`, `image_key`, `timestamp`) to Kafka topic.
2. **Kafka Consumer** reads metadata, fetches image from S3, and processes it via OpenCV.
3. **MeiliSearch** indexes metadata (filename, size, timestamp).
4. **Python script** visualizes data in:
   - Terminal tables (`tabulate`)
   - Histograms (`matplotlib`)
   - Image previews (`matplotlib.imshow`)

---

## Implementation Details

### Kafka Producer/Consumer (Python)

- `image_producer.py`: Sends metadata (JSON format) to Kafka topic.
- `image_consumer.py`: Listens to Kafka topic, fetches image, processes it.

### OpenCV Image Processing

- Basic operations: resize, grayscale conversion.
- Extendable with face/object detection or edge detection filters.

### MeiliSearch Indexing

- Metadata is indexed in a `image_metadata` index.
- Indexed fields: `file_name`, `timestamp`, `size_kb`.

```python
meili_client = meilisearch.Client('http://127.0.0.1:7700')
index = meili_client.index('image_metadata')
index.add_documents([metadata])
```

---

## Visual Representation

### Tabular View (Terminal Output)

Displays the following metadata in a formatted table:

- `file_name`
- `size_kb`
- `timestamp`

### Graphical Charts (Matplotlib)

- **Image Size Distribution (Histogram)**
- **Processing Hour Distribution**

### Image Previews (Optional)

Displays a preview of up to 5 processed images using `matplotlib`.

---

## Setup Instructions

### 1. Clone Repository

```bash
git clone https://github.com/ibu-fenms512/2025-group7.git 
```

### 2. Install Python Dependencies

```bash
pip install boto3 opencv-python confluent_kafka pandas matplotlib tabulate meilisearch
```

### 3. Start MeiliSearch

```bash
./meilisearch --http-addr '127.0.0.1:7700'
```

### 4. Start Kafka Locally or via Docker

```bash
# Docker Compose (optional)
docker-compose up -d zookeeper kafka
```

### 5. Run Consumer Service

```bash
python consumer.py
```

---

## Notes

- Use `.env` or AWS credential manager to securely access S3.
- MeiliSearch admin key can be stored in environment variables.
- Consider using Docker to containerize the pipeline.

---

## Author

- **Boris Borovčanin**

