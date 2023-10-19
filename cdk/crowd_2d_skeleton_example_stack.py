# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
from os import path

from aws_cdk import (
    Duration,
    RemovalPolicy,
    Stack,
    aws_cloudfront,
    aws_iam,
    aws_lambda,
    aws_s3,
    aws_s3_deployment,
    aws_ssm,
)
from cdk_nag import NagSuppressions
from constructs import Construct


class Crowd2DSkeletonExampleStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        bucket = aws_s3.Bucket(
            self,
            "Bucket",
            block_public_access=aws_s3.BlockPublicAccess.BLOCK_ALL,
            encryption=aws_s3.BucketEncryption.S3_MANAGED,
            enforce_ssl=True,
            auto_delete_objects=True,
            removal_policy=RemovalPolicy.DESTROY,
            cors=[
                aws_s3.CorsRule(
                    allowed_methods=[aws_s3.HttpMethods.GET],
                    allowed_origins=["*"],
                )
            ],
        )

        origin_access_identity = aws_cloudfront.OriginAccessIdentity(
            self, "MyOriginAccessIdentity", comment="comment"
        )

        distribution = aws_cloudfront.CloudFrontWebDistribution(
            self,
            "MyDistribution",
            origin_configs=[
                aws_cloudfront.SourceConfiguration(
                    s3_origin_source=aws_cloudfront.S3OriginConfig(
                        s3_bucket_source=bucket,
                        origin_access_identity=origin_access_identity,
                    ),
                    behaviors=[
                        aws_cloudfront.Behavior(
                            viewer_protocol_policy=aws_cloudfront.ViewerProtocolPolicy.HTTPS_ONLY,
                            is_default_behavior=True,
                        )
                    ],
                )
            ],
        )

        distribution_response_policy = aws_cloudfront.CfnResponseHeadersPolicy(
            self,
            "ResponseHeaderPolicy",
            response_headers_policy_config=aws_cloudfront.CfnResponseHeadersPolicy.ResponseHeadersPolicyConfigProperty(
                name="ResponseHeaderPolicy",
                comment="Policy for JS file share",
                cors_config=aws_cloudfront.CfnResponseHeadersPolicy.CorsConfigProperty(
                    access_control_allow_credentials=False,
                    access_control_allow_headers=aws_cloudfront.CfnResponseHeadersPolicy.AccessControlAllowHeadersProperty(
                        items=["*"]
                    ),
                    access_control_allow_methods=aws_cloudfront.CfnResponseHeadersPolicy.AccessControlAllowMethodsProperty(
                        items=["GET"]
                    ),
                    access_control_allow_origins=aws_cloudfront.CfnResponseHeadersPolicy.AccessControlAllowOriginsProperty(
                        items=["*"]
                    ),
                    origin_override=False,
                ),
            ),
        )

        cfn_distribution = distribution.node.default_child
        cfn_distribution.add_property_override(
            "DistributionConfig.DefaultCacheBehavior.ResponseHeadersPolicyId",
            distribution_response_policy.attr_id,
        )

        # Add a Deny statement for all other requests
        deny_policy = aws_iam.PolicyStatement(
            actions=["s3:GetObject"],
            not_resources=[
                bucket.arn_for_objects(
                    "infrastructure/ground_truth_templates/crowd-2d-skeleton.js"
                )
            ],  # Deny access to all objects
            effect=aws_iam.Effect.DENY,
            principals=[
                aws_iam.CanonicalUserPrincipal(
                    origin_access_identity.cloud_front_origin_access_identity_s3_canonical_user_id
                )
            ],
        )
        bucket.add_to_resource_policy(deny_policy)

        lambda_role = aws_iam.Role(
            self,
            "lambda_role_name",
            assumed_by=aws_iam.CompositePrincipal(
                aws_iam.ServicePrincipal("lambda.amazonaws.com"),
            ),
            managed_policies=[
                aws_iam.ManagedPolicy.from_aws_managed_policy_name(
                    "service-role/AWSLambdaBasicExecutionRole"
                ),
            ],
            inline_policies={
                "S3Access": aws_iam.PolicyDocument(
                    statements=[
                        aws_iam.PolicyStatement(
                            effect=aws_iam.Effect.ALLOW,
                            actions=["s3:ListBucket", "s3:GetObject"],
                            resources=[bucket.bucket_arn],
                        ),
                    ],
                ),
            },
        )

        pre_annotation_lambda = aws_lambda.Function(
            self,
            "pre_annotation_lambda",
            runtime=aws_lambda.Runtime.PYTHON_3_10,
            code=aws_lambda.Code.from_asset(path.join("cdk", "pre_annotation_lambda")),
            handler="lambda_function.lambda_handler",
            timeout=Duration.seconds(30),
        )

        post_annotation_lambda = aws_lambda.Function(
            self,
            "post_annotation_lambda",
            runtime=aws_lambda.Runtime.PYTHON_3_10,
            code=aws_lambda.Code.from_asset(path.join("cdk", "post_annotation_lambda")),
            role=lambda_role,
            handler="lambda_function.lambda_handler",
            timeout=Duration.seconds(30),
        )

        sagemaker_ground_truth_labeling_job_role = aws_iam.Role(
            self,
            "sagemaker-ground-truth-labeling-job-role",
            assumed_by=aws_iam.CompositePrincipal(
                aws_iam.ServicePrincipal("sagemaker.amazonaws.com"),
                aws_iam.ArnPrincipal(lambda_role.role_arn),
            ),
            managed_policies=[
                aws_iam.ManagedPolicy.from_aws_managed_policy_name(
                    "AmazonSageMakerGroundTruthExecution"
                )
            ],
        )

        sagemaker_ground_truth_labeling_job_role.add_to_policy(
            aws_iam.PolicyStatement(
                effect=aws_iam.Effect.ALLOW,
                resources=[bucket.bucket_arn + "/*"],
                actions=["s3:*"],
            )
        )
        sagemaker_ground_truth_labeling_job_role.add_to_policy(
            aws_iam.PolicyStatement(
                effect=aws_iam.Effect.ALLOW,
                resources=[
                    pre_annotation_lambda.function_arn,
                    post_annotation_lambda.function_arn,
                ],
                actions=["lambda:InvokeFunction"],
            )
        )

        # NOTE: changes made to these files after the first deploy will not
        # be reflected in future deployments.
        aws_s3_deployment.BucketDeployment(
            self,
            "crowd-2d-skeleton-template",
            prune=False,
            sources=[aws_s3_deployment.Source.asset("cdk/ground_truth_templates/")],
            destination_bucket=bucket,
            destination_key_prefix="infrastructure/ground_truth_templates/",
        )

        cloudfront_domain_name = distribution.distribution_domain_name
        aws_ssm.StringParameter(
            self,
            "cloudfront_domain_name",
            parameter_name="/crowd_2d_skeleton_example_stack/cloudfront_domain_name",
            string_value=cloudfront_domain_name,
        )

        aws_ssm.StringParameter(
            self,
            "hosted_javascript_url",
            parameter_name="/crowd_2d_skeleton_example_stack/hosted_javascript_url",
            string_value=f"{cloudfront_domain_name}/infrastructure/ground_truth_templates/crowd-2d-skeleton.js",
        )

        aws_ssm.StringParameter(
            self,
            "bucket_name",
            parameter_name="/crowd_2d_skeleton_example_stack/bucket_name",
            string_value=bucket.bucket_name,
        )

        aws_ssm.StringParameter(
            self,
            "pre_annotation_lambda_arn",
            parameter_name="/crowd_2d_skeleton_example_stack/pre_annotation_lambda_arn",
            string_value=pre_annotation_lambda.function_arn,
        )

        aws_ssm.StringParameter(
            self,
            "post_annotation_lambda_arn",
            parameter_name="/crowd_2d_skeleton_example_stack/post_annotation_lambda_arn",
            string_value=post_annotation_lambda.function_arn,
        )

        aws_ssm.StringParameter(
            self,
            "sagemaker_ground_truth_role",
            parameter_name="/crowd_2d_skeleton_example_stack/sagemaker_ground_truth_role",
            string_value=sagemaker_ground_truth_labeling_job_role.role_arn,
        )

        NagSuppressions.add_resource_suppressions(
            bucket,
            [
                {"id": "AwsSolutions-S1", "reason": "Log bucket not available."},
            ],
        )
        NagSuppressions.add_resource_suppressions(
            distribution,
            [
                {"id": "AwsSolutions-CFR3", "reason": "Log bucket not available."},
                {
                    "id": "AwsSolutions-CFR4",
                    "reason": "SSLv2 are not configurable via this API",
                },
                {"id": "AwsSolutions-CFR1", "reason": "No GEO restrictions required"},
                {"id": "AwsSolutions-CFR2", "reason": "No AWS WAF required"},
            ],
        )
