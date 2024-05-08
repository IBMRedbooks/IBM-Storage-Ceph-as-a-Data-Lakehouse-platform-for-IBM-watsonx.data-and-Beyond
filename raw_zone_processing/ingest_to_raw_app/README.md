# README - CSV Processing Application

## Overview
This Flask application is meant only for example pourpuses, it processes CSV files stored in an AWS S3 bucket. It determines whether the CSV files contain personal information or any legal conflict in it's transactions and takes appropriate actions such as classifying the data, tagging the S3 objects, uploading modified versions, and applying legal holds when necessary.

## Features
- **Personal Information Detection**: Scans CSV content for patterns indicative of personal information such as Social Security Numbers or Credit Card details.
- **Data Tagging**: Tags S3 objects with `red` for personal data or `green` for non-personal data.
- **Legal Hold**: Checks for rows with a column set to "legal" and enables S3 object lock legal hold on the object, indicating a legal conflict.
- **Secure AWS Role Access**: Utilizes AWS Security Token Service (STS) to assume roles securely with web identity federation for accessing S3 objects.

## Prerequisites
- Ceph Account with access to S3, STS, and permissions for object tagging and legal holds.
- Python 3.6 or higher installed.
- Flask and Boto3 libraries installed. You can install them using pip:
- Properly configured AWS credentials on the host machine or in your deployment environment that can assume the specified roles.

## Environment Variables
Ensure the following environment variables are set before running the application:
- `SOURCE_ROLE_ARN`: The ARN of the AWS IAM role for reading S3 objects.
- `DESTINATION_ROLE_ARN`: The ARN of the AWS IAM role for writing to S3.
- `OIDC_PROVIDER_URL`: The URL of the OIDC provider.
- `OIDC_CLIENT_ID`: The client ID for the OIDC authentication.
- `OIDC_CLIENT_SECRET`: The client secret for OIDC authentication.
- `OIDC_USERNAME`: The username for OIDC authentication.
- `OIDC_PASSWORD`: The password for OIDC authentication.
- `S3_ENDPOINT_URL`: The custom endpoint URL for S3 services.
- `STS_ENDPOINT_URL`: The endpoint URL for the AWS STS service.

## Running the Application
1. Set up the necessary environment variables as described above.
2. Navigate to the script directory and run the Flask application using:
3. python process_ingest_to_raw.py
4. The application will start a server usually accessible via `http://localhost:8080`.

## Usage
- The Applications expects a CloudEvent payload sent from a Kakfa topic,The Kafka topic is populated with events from S3 bucket notifications, it expects a POST request to `http://localhost:8080` with a CloudEvent JSON payload containing the S3 bucket name and object key. The server processes the specified CSV file according to the logic implemented.
- Access `http://localhost:8080/healthz` to check the health of the application, responding with "Health OK" if running properly.

## Security Considerations
- Ensure that the OIDC credentials are secured and not hard-coded in the source files.
- Restrict IAM roles and policies to the minimum necessary permissions for operation.


