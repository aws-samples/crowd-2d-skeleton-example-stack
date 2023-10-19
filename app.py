# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

import aws_cdk as cdk
from aws_cdk import Aspects
from cdk_nag import AwsSolutionsChecks, NagSuppressions

from cdk.crowd_2d_skeleton_example_stack import Crowd2DSkeletonExampleStack
from cdk.libs.utils import download_crowd_2d_skeleton

download_crowd_2d_skeleton()
app = cdk.App()
stack = Crowd2DSkeletonExampleStack(app, "Crowd2DSkeletonExampleStackStack")
Aspects.of(app).add(AwsSolutionsChecks())
NagSuppressions.add_stack_suppressions(
    stack,
    [
        {
            "id": "AwsSolutions-IAM4",
            "reason": "Policy was reviewed and deemed reasonable.",
        },
        {
            "id": "AwsSolutions-IAM5",
            "reason": "Policy was reviewed and deemed reasonable.",
        },
        {
            "id": "AwsSolutions-L1",
            "reason": "Policy was reviewed and deemed reasonable.",
        },
    ],
)
app.synth()
