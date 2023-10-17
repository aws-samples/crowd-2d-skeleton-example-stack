# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
"""This module defines the pre-annotation Lambda.

    AWS SageMaker invokes this lambda for each item to be labeled. The lambda
    will be given a single manifest file item. The responsibility of this lambda
     is to format input manifest item into the format that the custom UI
     template expects.
"""
import json


def lambda_handler(event, context):
    """Receives and formats manifest item for custom UI template.

        AWS SageMaker invokes this lambda for each item to be labeled. The lambda
        will be given a single manifest file item. The responsibility of this lambda
        is to format input manifest item into the format that the custom UI template expects.

    Args:
        event: Content of event looks something like following
                {
                    "version":"2018-10-16",
                    "labelingJobArn":"<your labeling job ARN>",
                    "dataObject":{
                        <manifest item>
                    }
                }
        context: Lambda Context runtime methods and attributes
                 Context doc: https://docs.aws.amazon.com/lambda/latest/dg/python-context-object.html

    Returns:
        A dictionary containing values which will be used as UI template variables.
        {
           "taskInput":{
                "image_s3_uri": data_object["source-ref"],
                "image_name": data_object["source-ref"].split("/")[-1],
                "annotations": annotations,
                "annotation_issues": data_object["annotation_issues"],
                "initial_values": json.dumps(annotations),
           },
           "isHumanAnnotationRequired":"true"
        }
    """
    print("Pre-Annotation Lambda Triggered")
    data_object = event["dataObject"]  # this comes directly from the manifest file
    annotations = data_object["annotations"]

    taskInput = {
        "image_s3_uri": data_object["source-ref"],
        "initial_values": json.dumps(annotations),
    }
    print("-" * 50)
    print(event["dataObject"])
    print("-" * 50)
    print(taskInput)
    print("-" * 80)
    return {"taskInput": taskInput, "humanAnnotationRequired": "true"}
