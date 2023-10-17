# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
"""This module defines the Post-Annotation Lambda.

    This lambda is a modified version of the following AWS Sample:
    https://github.com/aws-samples/aws-sagemaker-ground-truth-recipe/blob/master/aws_sagemaker_ground_truth_sample_lambda/annotation_consolidation_lambda.py

    It will run when all the labeling is finished for a labeling job.
    This lambda formats and augments the output of the annotations for the
    labeling job. See
    https://docs.aws.amazon.com/sagemaker/latest/dg/sms-annotation-consolidation.html
    for more details.
"""
import json

from s3_helper import S3Client


def lambda_handler(event, context):
    """This lambda will take all worker responses for the item to be labeled, and output a consolidated annotation.

    Args:
        event: dict, required
            Content of an example event

            {
                "version": "2018-10-16",
                "labelingJobArn": <labelingJobArn>,
                "labelCategories": [<string>],
                "labelAttributeName": <string>,
                "roleArn" : "string",
                "payload": {
                    "s3Uri": <string>
                }
                "outputConfig":"s3://<consolidated_output configured for labeling job>"
             }


            Content of payload.s3Uri
            [
                {
                    "datasetObjectId": <string>,
                    "dataObject": {
                        "s3Uri": <string>,
                        "content": <string>
                    },
                    "annotations": [{
                        "workerId": <string>,
                        "annotationData": {
                            "content": <string>,
                            "s3Uri": <string>
                        }
                   }]
                }
            ]
        context: Lambda Context runtime methods and attributes

    Returns:
        consolidated_output: dict
            AnnotationConsolidation

            [
               {
                    "datasetObjectId": <string>,
                    "consolidatedAnnotation": {
                        "content": {
                            "<labelattributename>": {
                                # ... label content
                            }
                        }
                    }
                }
            ]

        Return doc: https://docs.aws.amazon.com/sagemaker/latest/dg/sms-custom-templates-step3.html
    """

    # Event received
    print("Received event: " + json.dumps(event, indent=2))

    labeling_job_arn = event["labelingJobArn"]
    label_attribute_name = event["labelAttributeName"]

    payload = event["payload"]
    role_arn = event["roleArn"]

    # If you specified a KMS key in your labeling job, you can use the key to write
    # consolidated_output to s3 location specified in outputConfig.
    kms_key_id = None
    if "kmsKeyId" in event:
        kms_key_id = event["kmsKeyId"]

    # Create s3 client object
    s3_client = S3Client(role_arn, kms_key_id)

    # Perform consolidation
    return do_consolidation(labeling_job_arn, payload, label_attribute_name, s3_client)


def do_consolidation(labeling_job_arn, payload, label_attribute_name, s3_client):
    """Formats and augments the output manifest file annotations.

    Args:
        labeling_job_arn: labeling job ARN
        payload:  payload data for consolidation
        label_attribute_name: identifier for labels in output JSON
        s3_client: S3 helper class
    Return:
        output JSON string
    """

    # Extract payload data
    if "s3Uri" in payload:
        s3_ref = payload["s3Uri"]
        payload = json.loads(s3_client.get_object_from_s3(s3_ref))
    print("-" * 80)
    print(payload)
    print("-" * 80)

    # Payload data contains a list of data objects.
    # Iterate over it to consolidate annotations for individual data object.
    consolidated_output = []
    success_count = 0  # Number of data objects that were successfully consolidated
    failure_count = 0  # Number of data objects that failed in consolidation

    # For each datasetObjectId
    for i in range(len(payload)):
        response = None
        try:
            dataset_object_id = payload[i]["datasetObjectId"]
            log_prefix = "[{}] data object id [{}] :".format(
                labeling_job_arn, dataset_object_id
            )
            annotations = payload[i]["annotations"]

            if len(annotations) > 1:
                msg = "Multiple Reviewers for same datasetObjectId is not " "supported "
                print(f"{log_prefix}{msg}")
                raise NotImplementedError(msg)

            annotation = annotations[0]
            worker_id = annotation["workerId"]
            annotation_data = annotation["annotationData"]
            annotation_content = annotation_data.get("content")
            annotation_content = json.loads(annotation_content)

            # Build consolidation response object for an individual data object
            response = {
                "datasetObjectId": dataset_object_id,
                "consolidatedAnnotation": {
                    "content": {
                        label_attribute_name: {
                            "dataset_object_id": dataset_object_id,
                            "data_object_s3_uri": payload[i]["dataObject"]["s3Uri"],
                            "image_file_name": annotation_content["image_name"].split(
                                "?"
                            )[0],
                            "image_s3_location": annotation_content[
                                "image_s3_uri"
                            ].split("?")[0],
                            "original_annotations": json.loads(
                                annotation_content["original_annotations"]
                            ),
                            "updated_annotations": annotation_content[
                                "updated_annotations"
                            ],
                            "worker_id": worker_id,
                            "no_changes_needed": json.loads(
                                annotation_content["no_changes_needed"]
                            ),
                            "was_modified": json.dumps(
                                annotation_content["updated_annotations"]
                            )
                            != json.dumps(annotation_content["original_annotations"]),
                            "total_time_in_seconds": annotation_content.get(
                                "total_time_in_seconds", "null"
                            ),
                        }
                    }
                },
            }

            success_count += 1
            # Append individual data object response to the list of responses.
            if response is not None:
                consolidated_output.append(response)

        except Exception as e:
            failure_count += 1
            print(" Consolidation failed for dataobject {}".format(i))
            print(" error: {}".format(e))

    print(
        f"Consolidation Complete. Success Count {success_count}  Failure Count {failure_count}"
    )

    print(" -- Consolidated Output -- ")
    print(consolidated_output)
    print(" ------------------------- ")
    return consolidated_output
