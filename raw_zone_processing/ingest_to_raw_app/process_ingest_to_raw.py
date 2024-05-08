import csv
import re
import os
import logging
import requests
import boto3
import time
from flask import Flask, request, jsonify
from cloudevents.http import from_http

# Initialize logging
app = Flask(__name__)
__version__ = "1.2.0"
logging.basicConfig(level=logging.INFO, format=f'%(asctime)s - %(levelname)s - Script Version {__version__} - %(message)s')


def has_personal_info(csv_content):
    patterns = [
        r'\b\d{3}-\d{2}-\d{4}\b',  # Social Security Number (SSN)
        r'\b\d{4}-\d{4}-\d{4}-\d{4}\b',  # Credit Card Number
        r'\b\d{16}\b',  # Another format of Credit Card Number
        r'\b\d{3}\b',  # CVV
    ]

    for pattern in patterns:
        if re.search(pattern, csv_content):
            return True
    return False

def has_legal_issue(csv_content):
    reader = csv.reader(csv_content.splitlines())
    for row in reader:
        if 'legal' in row:
            return True
    return False

def check_environment():
    missing_params = []

    required_env_vars = [
        'SOURCE_ROLE_ARN',
        'DESTINATION_ROLE_ARN',
        'OIDC_PROVIDER_URL',
        'OIDC_CLIENT_SECRET',
        'OIDC_CLIENT_ID',
        'OIDC_USERNAME',
        'OIDC_PASSWORD',
        'S3_ENDPOINT_URL',
        'STS_ENDPOINT_URL'
    ]

    for var in required_env_vars:
        if var not in os.environ:
            missing_params.append(var)

    if missing_params:
        print("Missing environment parameters:")
        for param in missing_params:
            print(f"- {param}")
        logging.error(f"Please set these environment variables and try again.")
        return False
    else:
        return True

def enable_legal_hold(s3, bucket_name, object_key):
    try:
        s3.put_object_legal_hold(
            Bucket=bucket_name,
            Key=object_key,
            LegalHold={'Status': 'ON'}
        )
        logging.info(f"Legal hold enabled on {object_key} due to legal issues.")
    except Exception as e:
        logging.error(f"Error enabling legal hold on {object_key}: {e}")

def read_csv_from_s3(bucket_name, object_key, s3_endpoint_url, sts_client):
    try:
        role_arn = os.getenv('SOURCE_ROLE_ARN')
        role_session_name = 'source_session'
        provider_url = os.getenv('OIDC_PROVIDER_URL')
        client_id = os.getenv('OIDC_CLIENT_ID')
        client_secret = os.getenv('OIDC_CLIENT_SECRET')
        jwt_token = get_jwt_token(provider_url, client_id, client_secret)
        assumed_role = sts_client.assume_role_with_web_identity(
            RoleArn=role_arn,
            RoleSessionName=role_session_name,
            WebIdentityToken=jwt_token
        )

        # Initialize S3 client with temporary credentials
        s3 = boto3.client(
            's3',
            aws_access_key_id=assumed_role['Credentials']['AccessKeyId'],
            aws_secret_access_key=assumed_role['Credentials']['SecretAccessKey'],
            aws_session_token=assumed_role['Credentials']['SessionToken'],
            endpoint_url=s3_endpoint_url
        )

        # Get object from S3
        response = s3.get_object(Bucket=bucket_name, Key=object_key)
        csv_content = response['Body'].read().decode('utf-8')
        return csv_content
    except Exception as e:
        logging.error(f"Error reading CSV from S3: {e}")
        return None

def process_csv_files_in_bucket(bucket_name, object_name, s3_endpoint_url, sts_client, personal_info_bucket, no_personal_info_bucket):
    try:
        # Get temporary credentials using AssumeRoleWithWebIdentity
        role_arn = os.getenv('SOURCE_ROLE_ARN')
        role_session_name = 'source_session'
        provider_url = os.getenv('OIDC_PROVIDER_URL')
        client_id = os.getenv('OIDC_CLIENT_ID')
        client_secret = os.getenv('OIDC_CLIENT_SECRET')
        jwt_token = get_jwt_token(provider_url, client_id, client_secret)
        assumed_role = sts_client.assume_role_with_web_identity(
            RoleArn=role_arn,
            RoleSessionName=role_session_name,
            WebIdentityToken=jwt_token
        )

        # Initialize S3 client with temporary credentials
        s3 = boto3.client(
            's3',
            aws_access_key_id=assumed_role['Credentials']['AccessKeyId'],
            aws_secret_access_key=assumed_role['Credentials']['SecretAccessKey'],
            aws_session_token=assumed_role['Credentials']['SessionToken'],
            endpoint_url=s3_endpoint_url
        )
        object_key = object_name
        if is_processed_object(s3, bucket_name, object_key):
            logging.info(f"Skipping processed object: {object_key}")
            return None
        csv_content = read_csv_from_s3(bucket_name, object_key, s3_endpoint_url, sts_client)
        if csv_content:
            shop_id, _ = object_key.split('_', 1)  # Extract shop ID from filename until first underscore
            csv_content = insert_shop_id_to_csv(csv_content, shop_id)
            if has_personal_info(csv_content):
                destination_bucket = personal_info_bucket
                tag_color = 'red'
            else:
                destination_bucket = no_personal_info_bucket
                tag_color = 'green'
            logging.info(f"Uploading Object To destination bucket: {destination_bucket}")
            upload_csv_to_s3(destination_bucket, object_key, csv_content, s3_endpoint_url, sts_client)
            tag_s3_object(s3, destination_bucket, object_key, tag_color)
            tag_object_as_processed(s3, bucket_name, object_key)
            if has_legal_issue(csv_content):
                enable_legal_hold(s3, bucket_name, object_name)
    except Exception as e:
        logging.error(f"Error processing CSV files in bucket: {e}")

def insert_shop_id_to_csv(csv_content, shop_id):
    rows = csv_content.split('\n')
    for i, row in enumerate(rows):
        if row.strip():  # Skip empty rows
            rows[i] = f"{shop_id},{row}"
    modified_csv_content = '\n'.join(rows)
    modified_csv_content = modified_csv_content.replace('\r', '')
    return modified_csv_content

def upload_csv_to_s3(bucket_name, object_key, csv_content, s3_endpoint_url, sts_client):
    try:
        # Get temporary credentials using AssumeRoleWithWebIdentity
        role_arn = os.getenv('DESTINATION_ROLE_ARN')
        role_session_name = 'destination_session'
        provider_url = os.getenv('OIDC_PROVIDER_URL')
        client_id = os.getenv('OIDC_CLIENT_ID')
        client_secret = os.getenv('OIDC_CLIENT_SECRET')
        jwt_token = get_jwt_token(provider_url, client_id, client_secret)
        assumed_role = sts_client.assume_role_with_web_identity(
            RoleArn=role_arn,
            RoleSessionName=role_session_name,
            WebIdentityToken=jwt_token
        )

        s3 = boto3.client(
            's3',
            aws_access_key_id=assumed_role['Credentials']['AccessKeyId'],
            aws_secret_access_key=assumed_role['Credentials']['SecretAccessKey'],
            aws_session_token=assumed_role['Credentials']['SessionToken'],
            endpoint_url=s3_endpoint_url
        )

        response = s3.put_object(Bucket=bucket_name, Key=object_key, Body=csv_content.encode('utf-8'))
        logging.info(f"Modified CSV uploaded to S3: {object_key}")
    except Exception as e:
        logging.error(f"Error uploading CSV to S3: {e}")

def tag_object_as_processed(s3, bucket_name, object_key):
    try:
        s3.put_object_tagging(
            Bucket=bucket_name,
            Key=object_key,
            Tagging={'TagSet': [{'Key': 'processed', 'Value': 'true'}]}
        )
        logging.info(f"Object tagged as processed: {object_key}")
    except Exception as e:
        logging.error(f"Error tagging object as processed: {e}")

def is_processed_object(s3, bucket_name, object_key):
    try:
        response = s3.get_object_tagging(Bucket=bucket_name, Key=object_key)
        tags = response['TagSet']
        for tag in tags:
            if tag['Key'] == 'processed' and tag['Value'] == 'true':
                return True
        return False
    except s3.exceptions.NoSuchKey:
        return False
    except Exception as e:
        logging.error(f"Error checking if object is processed: {e}")
        return False

def tag_s3_object(s3, bucket_name, object_key, tag_value):
    try:
        logging.info(f"Attempting to tag object {object_key} in {bucket_name} as {tag_value}.")
        s3.put_object_tagging(
            Bucket=bucket_name,
            Key=object_key,
            Tagging={'TagSet': [{'Key': 'DataClassification', 'Value': tag_value}]}
        )
        logging.info(f"Successfully tagged object {object_key} in {bucket_name} as {tag_value}.")
    except Exception as e:
        logging.error(f"Error tagging object {object_key} in {bucket_name} as {tag_value}: {e}")


def get_jwt_token(provider_url, client_id, client_secret):
    username = os.getenv('OIDC_USERNAME')
    password = os.getenv('OIDC_PASSWORD')
    token_endpoint = f"{provider_url}/token"
    
    payload = {
        'grant_type': 'password',
        'client_id': client_id,
        'client_secret': client_secret,
        'username': username,
        'password': password
    }
    
    try:
        response = requests.post(token_endpoint, data=payload)
        response.raise_for_status()
        token_data = response.json()
        return token_data['access_token']
    except Exception as e:
        logging.error(f"Error obtaining JWT token: {e}")
        return None

@app.route('/', methods=['GET', 'POST'])
def trigger_process():
    if request.method == 'GET':
        return 'Health OK', 200
    elif request.method == 'POST':
        try:
            event = from_http(request.headers, request.get_data())
            records = event.data['Records'][0]
            bucket_name = records['s3']['bucket']['name']
            object_name = records['s3']['object']['key']
            logging.info(f"{bucket_name} {object_name}")

            s3_endpoint_url = os.getenv('S3_ENDPOINT_URL')
            sts_endpoint_url = os.getenv('STS_ENDPOINT_URL')
            personal_info_bucket = 'confidential'
            no_personal_info_bucket = 'anonymized'

            sts_client = boto3.client('sts', endpoint_url=sts_endpoint_url)

            process_csv_files_in_bucket(bucket_name, object_name ,s3_endpoint_url, sts_client, personal_info_bucket, no_personal_info_bucket)

            return jsonify({'message': 'CSV processing triggered for POST request'}), 204
        except KeyError as e:
            logging.error(f"Missing key in CloudEvent payload: {e}")
            return jsonify({'error': f'Missing key in CloudEvent payload: {e}'}), 400
        except Exception as e:
            logging.error(f"Error processing POST request: {e}")
            return jsonify({'error': str(e)}), 500

@app.route('/healthz', methods=['GET'])
def health_check():
    return 'Health OK', 200

if __name__ == "__main__":
    if not check_environment():
        exit(1)

    app.run(host='0.0.0.0', port=8080)
