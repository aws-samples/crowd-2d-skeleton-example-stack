# Crowd 2D Skeleton Component Example Stack
This repository contains the code to deploy the needed infrastructure
to carry out [crowd-2d-skeleton](https://github.com/aws-samples/sagemaker-ground-truth-crowd-2d-skeleton-component/tree/main)
labeling jobs. This architecture can also be used as a reference for how Amazon
Ground Truth custom UIs can be deployed and used.

## Infrastructure Overview
![crowd_2d_skeleton_example_stack.jpeg](docs%2Fcrowd_2d_skeleton_example_stack.jpeg)
Below will describe what each component of the architecture is used for.
### Amazon S3 bucket
The Amazon S3 bucket will be used for:
* Storing the [custom worker task template](https://docs.aws.amazon.com/sagemaker/latest/dg/sms-custom-templates-step2.html) (also known as the custom UI template)
* Storing the [crowd-2d-skeleton.js](https://github.com/aws-samples/sagemaker-ground-truth-crowd-2d-skeleton-component/releases/) component code
* Storing the images for the labeling job
* Storing the [manifest files](https://docs.aws.amazon.com/sagemaker/latest/dg/sms-input-data-input-manifest.html) for the labeling job

A bucket policy will be added to the bucket to restrict the created Origin Access
Identity to only be able to access the [crowd-2d-skeleton.js](https://github.com/aws-samples/sagemaker-ground-truth-crowd-2d-skeleton-component/releases/)
component code. All other objects in the bucket will remain private.

### CloudFront Distribution
The [Amazon CloudFront Distribution](https://aws.amazon.com/cloudfront/) will be
used to host the [crowd-2d-skeleton.js](https://github.com/aws-samples/sagemaker-ground-truth-crowd-2d-skeleton-component/releases/)
JavaScript code which will be accessed via the custom labeling user UI. The
Amazon CloudFront Distribution will be assigned an Origin Access Identity which
will allow the Amazon CloudFront Distribution to access the crowd-2d-skeleton.js
residing in the Amazon S3 bucket.

### Pre-Annotation Lambda
The pre-annotation lambda will process line items from the input manifest file
before the manifest data is injected into the custom UI template.For
more information on pre-annotation lambda functions see:
[Processing with AWS Lambda](https://docs.aws.amazon.com/sagemaker/latest/dg/sms-custom-templates-step3-lambda-requirements.html)

### Post-Annotation Lambda
The post-annotation lambda will process the labeling results after all labelers
have finished labeling or the labeling job has expired. This lambda is
responsible for formatting the data for the labeling job output results. For
more information on post-annotation lambda functions see:
[Processing with AWS Lambda](https://docs.aws.amazon.com/sagemaker/latest/dg/sms-custom-templates-step3-lambda-requirements.html)

### SageMaker Ground Truth Role
This role is created to give the Amazon SageMaker Ground Truth labeling job the
ability to invoke the lambda functions and to read the S3 objects (i.e. images,
manifest files, and custom UI template) in the Amazon
S3 Bucket.


## Repository Structure
The key components of the repository are listed below
```
.
├── cdk/
│   ├── ground_truth_templates                <-- custom UI template
│   ├── libs
│   ├── post_annotation_lambda                <-- Post-annotation code
│   ├── pre_annotation_lambda                 <-- Pre-annotation code
│   └── crowd_2d_skeletong_example_stack.py   <-- CDK details of the stack
├── docs                                      <-- images for the documentation
├── scripts                                   <-- Post deployment scripts & example job launching scripts
└── app.py                                    <-- CDK entry point
```

## Build and Deploy the Stack
###  Prerequisites

* [Python 3.9+](https://www.python.org/downloads/release/python-390/)
* [AWS Account](https://aws.amazon.com/)
* [AWS Cloud Development Kit (AWS CDK)](https://docs.aws.amazon.com/cdk/v2/guide/home.html)
* [AWS SageMaker Ground Truth Private Workforce](https://docs.aws.amazon.com/sagemaker/latest/dg/sms-workforce-create-private-console.html)

#### Python Setup
This project is set up like a standard Python project.  The initialization
process also creates a virtualenv within this project, stored under the `.venv`
directory.  To create the virtualenv it assumes that there is a `python3`
(or `python` for Windows) executable in your path with access to the `venv`
package. If for any reason the automatic creation of the virtualenv fails,
you can create the virtualenv manually.

To manually create a virtualenv on MacOS and Linux:

```
$ python -m venv .venv
```

After the init process completes and the virtualenv is created, you can use the following
step to activate your virtualenv.

```
$ source .venv/bin/activate
```

If you are a Windows platform, you would activate the virtualenv like this:

```
% .venv\Scripts\activate.bat
```

Once the virtualenv is activated, you can install the required dependencies.

```
$ pip install -r requirements.txt
```

# Deployment Steps
This repository assumes that you have used the [AWS Cloud Development Kit (CDK)](https://docs.aws.amazon.com/cdk/)
before. If this is your first CDK project, you may want to familiarize your self
by reading the CDK documentation which can be found here: [AWS Cloud Development Kit ](https://docs.aws.amazon.com/cdk/).

## Step 1: Prepare the CDK stack
Simply run:
```
$ cdk synth
```
## Step 2: Deploy the CDK stack
To deploy the CDK stack run:
```
$ cdk deploy
```
## Step 3: Run post deployment script
Not all deployment steps can be done in CDK. In our case, we need to update the
HTML UI template to point the newly hosted JavaScript which was deployed in the
previous step. To handle the post deployment steps the post deployment script
should be run. Activate your python environment and run:
```
$ python scripts/post_deployment_script.py
```

## Step 4 (optional): Create Labeling Job
Once the previous steps have completed, you can create labeling jobs using the
created infrastructure. For examples on how to do this programmatically,
see `scripts/create_example_labeling_job.py`


### Other Useful commands

 * `cdk ls`          list all stacks in the app
 * `cdk synth`       emits the synthesized CloudFormation template
 * `cdk deploy`      deploy this stack to your default AWS account/region
 * `cdk diff`        compare deployed stack with current state
 * `cdk docs`        open CDK documentation
 * `cdk destroy`     Destroy the stack


# Developer Setup
See [CONTRIBUTING](CONTRIBUTING.md#security-issue-notifications) for more information.

Install the pre-commit hooks
```shell
pip install pre-commit
```
```shell
pre-commit install
```

## License

This library is licensed under the MIT-0 License. See the LICENSE file.