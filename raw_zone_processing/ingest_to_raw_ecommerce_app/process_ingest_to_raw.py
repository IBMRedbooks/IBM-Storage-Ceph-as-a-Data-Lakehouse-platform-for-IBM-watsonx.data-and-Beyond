import os
import logging
import boto3
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)
__version__ = "1.2.0"
logging.basicConfig(level=logging.INFO, format=f'%(asctime)s - %(levelname)s - Script Version {__version__} - %(message)s')

def check_environment():
    missing_params = []
    required_env_vars = [
        'SOURCE_ROLE_ARN', 'DESTINATION_ROLE_ARN', 'OIDC_PROVIDER_URL', 'OIDC_CLIENT_SECRET', 'OIDC_CLIENT_ID',
        'OIDC_USERNAME', 'OIDC_PASSWORD', 'S3_ENDPOINT_URL', 'STS_ENDPOINT_URL', 'DESTINATION_BUCKET', 'CIDR_RANGES',
        'AWS_DEFAULT_REGION'
    ]
    for var in required_env_vars:
        if var not in os.environ:
            missing_params.append(var)
    if missing_params:
        logging.error("Missing environment parameters: %s", ', '.join(missing_params))
        return False
    return True

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
    except requests.exceptions.HTTPError as e:
        logging.error(f"HTTP Error obtaining JWT token: {e}, Status Code: {e.response.status_code}")
        return None
    except Exception as e:
        logging.error(f"Error obtaining JWT token: {e}")
        return None

def assume_role_with_web_identity(role_arn, role_session_name, jwt_token):
    sts_client = boto3.client(
        'sts',
        region_name=os.getenv('AWS_DEFAULT_REGION'),
        endpoint_url=os.getenv('STS_ENDPOINT_URL')
    )
    try:
        assumed_role = sts_client.assume_role_with_web_identity(
            RoleArn=role_arn,
            RoleSessionName=role_session_name,
            WebIdentityToken=jwt_token
        )
        return {
            'aws_access_key_id': assumed_role['Credentials']['AccessKeyId'],
            'aws_secret_access_key': assumed_role['Credentials']['SecretAccessKey'],
            'aws_session_token': assumed_role['Credentials']['SessionToken']
        }
    except Exception as e:
        logging.error("Error assuming role with web identity: %s", str(e))
        return None

def initialize_s3_client(role_credentials):
    return boto3.client(
        's3',
        aws_access_key_id=role_credentials['aws_access_key_id'],
        aws_secret_access_key=role_credentials['aws_secret_access_key'],
        aws_session_token=role_credentials['aws_session_token'],
        region_name=os.getenv('AWS_DEFAULT_REGION'),
        endpoint_url=os.getenv('S3_ENDPOINT_URL')
    )

def s3_select_query(bucket_name, object_key, query, s3_client):
    logging.info(f"Executing S3 Select on Bucket: '{bucket_name}', Key: '{object_key}', Query: '{query}'")
    try:
        response = s3_client.select_object_content(
            Bucket=bucket_name,
            Key=object_key,
            ExpressionType='SQL',
            Expression=query,
            InputSerialization={'CSV': {"FileHeaderInfo": "USE"}},
            OutputSerialization={'CSV': {}},
        )
        result_data = ''
        for event in response['Payload']:
            if 'Records' in event:
                result_data += event['Records']['Payload'].decode('utf-8')
            elif 'Stats' in event:
                stats = event['Stats']['Details']
                logging.info(f"Statistics: {stats}")
            elif 'End' in event:
                logging.info("Reached end of the data stream.")
        return result_data
    except Exception as e:
        logging.error("Error during S3 Select: %s", str(e))
        return None

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

@app.route('/', methods=['POST'])
def trigger_processing():
    source_bucket = request.json.get('source_bucket')
    object_key = request.json.get('object_key')
    destination_bucket = os.getenv('DESTINATION_BUCKET')
    cidr_range = os.getenv('CIDR_RANGES')
    provider_url = os.getenv('OIDC_PROVIDER_URL')
    client_id = os.getenv('OIDC_CLIENT_ID')
    client_secret = os.getenv('OIDC_CLIENT_SECRET')
    jwt_token = get_jwt_token(provider_url, client_id, client_secret)
    if not jwt_token:  
        logging.error("Failed to obtain JWT token, cannot proceed with processing.")
        return jsonify({'error': 'Failed to obtain necessary authentication token'})
    source_credentials = assume_role_with_web_identity(os.getenv('SOURCE_ROLE_ARN'), 'sourceSession', jwt_token)
    destination_credentials = assume_role_with_web_identity(os.getenv('DESTINATION_ROLE_ARN'), 'destinationSession', jwt_token)
    s3_source = initialize_s3_client(source_credentials)
    s3_destination = initialize_s3_client(destination_credentials)
    # Construct the S3 Select SQL expression based on CIDR range
    query_parts = cidr_range.split('|')
    condition = " OR ".join([f"ip LIKE '{part}'" for part in query_parts])
    query = f"SELECT * FROM S3Object WHERE NOT ({condition});"
    logging.info(f"Executing S3 Select with query: {query}")
    filtered_data = s3_select_query(source_bucket, object_key, query, s3_source)
    tag_object_as_processed(s3_source, source_bucket, object_key)
    if filtered_data:
        try:
            response = s3_destination.put_object(
                Bucket=destination_bucket,
                Key=object_key,
                Body=filtered_data.encode('utf-8')
            )
            return jsonify({'message': 'Data processed and saved successfully'}), 200
        except Exception as e:
            logging.error("Error saving data to destination bucket: %s", str(e))
            return jsonify({'error': 'Failed to save data'}), 500
    else:
        return jsonify({'message': 'No data to process'}), 404

@app.route('/healthz', methods=['GET'])
def health_check():
    return 'Service is up', 200

if __name__ == "__main__":
    if not check_environment():
        logging.error("Environment setup is incomplete, terminating application.")
        exit(1)
    app.run(host='0.0.0.0', port=8080)

