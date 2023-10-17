# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
import boto3
from botocore.exceptions import ClientError


def update_custom_template_with_the_hosted_javascript_url(
    bucket_name: str, cloudfront_domain_name: str
) -> None:
    """Updates the example template with the created Cloudfront distribution URL.

        This process is needed to update the template to point to the newly
        hosted JavaScript file.

    Args:
        bucket_name: Name of the bucket to upload the updated template
        cloudfront_domain_name: The domain name of the CloudFront distribution.

    Returns:
        None
    """
    input_file_path = "cdk/ground_truth_templates/crowd_2d_skeleton_template.html"

    with open(input_file_path, "r") as input_file:
        file_content = input_file.read()

    string_to_replace = "URL_TO_HOSTED_JS_GOES_HERE"
    replacement_string = f"https://{cloudfront_domain_name}/infrastructure/ground_truth_templates/crowd-2d-skeleton.js"
    modified_content = file_content.replace(string_to_replace, replacement_string)

    try:
        s3_client = boto3.client("s3")
        object_key = (
            "infrastructure/ground_truth_templates/crowd_2d_skeleton_template.html"
        )
        s3_client.put_object(Bucket=bucket_name, Key=object_key, Body=modified_content)

        print(f"Template was updated! Updated: s3://{bucket_name}/{object_key}")

    except Exception as e:
        print(f"Failed to update template in S3 due to {str(e)}")


def read_ssm_parameter(parameter_name: str) -> str:
    """
    Retrieve an AWS Systems Manager Parameter Store (SSM) value.

    Args:
        parameter_name (str): The name of the SSM parameter to retrieve.

    Returns:
        str: The value of the retrieved SSM parameter.

    Raises:
        ClientError: If there is an issue with retrieving the SSM parameter.
    """
    ssm_client = boto3.client("ssm")

    try:
        response = ssm_client.get_parameter(Name=parameter_name, WithDecryption=True)

        parameter_value = response["Parameter"]["Value"]
        return parameter_value

    except ClientError as e:
        raise ClientError(f"Failed to retrieve the SSM parameter: {str(e)}")


def main():
    # Create the values of the resources which were created during the CDK
    # stack creation time.
    bucket_name = read_ssm_parameter("/crowd_2d_skeleton_example_stack/bucket_name")
    cloudfront_domain_name = read_ssm_parameter(
        "/crowd_2d_skeleton_example_stack/cloudfront_domain_name"
    )
    update_custom_template_with_the_hosted_javascript_url(
        bucket_name, cloudfront_domain_name
    )


if __name__ == "__main__":
    main()
