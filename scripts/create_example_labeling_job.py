# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
"""This script creates an example labeling job.

    This script assumes that the supporting infrastructure is already deployed
    and that the example images are downloaded by running
    download_example_images.py. This script requires the labeling workforce arn
    to be passed in.

Example arguments
    python create_example_labeling_job.py \
        "arn:aws:sagemaker:us-west-2:<account #>:workteam/private-crowd/Crowd-2D-Component-Example" \

"""
import argparse
import json
import os
from datetime import datetime

import boto3
from botocore.exceptions import ClientError


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


def main(workteam_arn: str) -> None:
    """Creates an input manifest and launches a Ground Truth labeling job.

    Args:
        workteam_arn: a labeling workforce arn. See
            https://docs.aws.amazon.com/sagemaker/latest/dg/sms-workforce-create-private-console.html
            for more details.

    Returns:

    """
    # Setup/get variables values from our CDK stack
    s3_upload_prefix = "labeling_jobs"
    image_dir = "scripts/images"
    manifest_file_name = "example_manifest.txt"
    s3_bucket_name = read_ssm_parameter("/crowd_2d_skeleton_example_stack/bucket_name")
    pre_annotation_lambda_arn = read_ssm_parameter(
        "/crowd_2d_skeleton_example_stack/pre_annotation_lambda_arn"
    )
    post_annotation_lambda_arn = read_ssm_parameter(
        "/crowd_2d_skeleton_example_stack/post_annotation_lambda_arn"
    )
    ground_truth_role_arn = read_ssm_parameter(
        "/crowd_2d_skeleton_example_stack/sagemaker_ground_truth_role"
    )
    ui_template_s3_uri = f"s3://{s3_bucket_name}/infrastructure/ground_truth_templates/crowd_2d_skeleton_template.html"
    s3_image_upload_prefix = f"{s3_upload_prefix}/images"
    s3_manifest_upload_prefix = f"{s3_upload_prefix}/manifests"
    s3_output_prefix = f"{s3_upload_prefix}/output"

    s3_client = boto3.client("s3")

    # For each image in the image directory lets create a manifest line
    manifest_items = []
    for filename in os.listdir(image_dir):
        if filename.endswith(".jpg") or filename.endswith(".png"):
            img_path = os.path.join(image_dir, filename)
            object_name = os.path.join(s3_image_upload_prefix, filename).replace(
                "\\", "/"
            )

            # upload to s3_bucket
            s3_client.upload_file(img_path, s3_bucket_name, object_name)

            # add it to manifest file
            manifest_items.append(
                {
                    "source-ref": f"s3://{s3_bucket_name}/{object_name}",
                    "annotations": [],
                }
            )

    # Create Manifest file
    manifest_file_contents = "\n".join([json.dumps(mi) for mi in manifest_items])
    with open(manifest_file_name, "w") as file_handle:
        file_handle.write(manifest_file_contents)

    # Upload manifest file
    object_name = os.path.join(s3_manifest_upload_prefix, manifest_file_name).replace(
        "\\", "/"
    )
    s3_client.upload_file(manifest_file_name, s3_bucket_name, object_name)

    # Create labeling job
    client = boto3.client("sagemaker")
    now = int(round(datetime.now().timestamp()))
    response = client.create_labeling_job(
        LabelingJobName=f"crowd-2d-skeleton-example-{now}",
        LabelAttributeName="label-results",
        InputConfig={
            "DataSource": {
                "S3DataSource": {
                    "ManifestS3Uri": f"s3://{s3_bucket_name}/{object_name}"
                },
            },
            "DataAttributes": {},
        },
        OutputConfig={
            "S3OutputPath": f"s3://{s3_bucket_name}/{s3_output_prefix}/",
        },
        RoleArn=ground_truth_role_arn,
        HumanTaskConfig={
            "WorkteamArn": workteam_arn,
            "UiConfig": {"UiTemplateS3Uri": ui_template_s3_uri},
            "PreHumanTaskLambdaArn": pre_annotation_lambda_arn,
            "TaskKeywords": ["example"],
            "TaskTitle": f"Crowd 2D Component Example {now}",
            "TaskDescription": "Crowd 2D Component Example",
            "NumberOfHumanWorkersPerDataObject": 1,
            "TaskTimeLimitInSeconds": 28800,
            "TaskAvailabilityLifetimeInSeconds": 2592000,
            "MaxConcurrentTaskCount": 123,
            "AnnotationConsolidationConfig": {
                "AnnotationConsolidationLambdaArn": post_annotation_lambda_arn
            },
        },
    )
    print(response)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Create a labeling job")
    parser.add_argument("workteam_arn", help="SageMaker Ground Truth workforce arn")
    args = parser.parse_args()
    main(args.workteam_arn)
