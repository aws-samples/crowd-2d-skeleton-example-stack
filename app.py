# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

import aws_cdk as cdk

from cdk.crowd_2d_skeleton_example_stack import Crowd2DSkeletonExampleStack
from cdk.libs.utils import download_crowd_2d_skeleton

download_crowd_2d_skeleton()
app = cdk.App()
Crowd2DSkeletonExampleStack(app, "Crowd2DSkeletonExampleStackStack")
app.synth()
