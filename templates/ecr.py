from troposphere import (
    AWS_ACCOUNT_ID,
    AWS_REGION,
    Join,
    Ref,
    Output,
    Template,
    Export, Sub)
from troposphere.ecr import Repository
from awacs.aws import (
    Allow,
    Policy,
    AWSPrincipal,
    Statement,
)
import awacs.ecr as ecr

from configuration import (
    stack_base_name,
)

repository_name = stack_base_name + "-application"

template = Template()

repository = template.add_resource(Repository(
    "ApplicationRepository",
    RepositoryName=repository_name,
    RepositoryPolicyText=Policy(
        Version="2008-10-17",
        Statement=[
            Statement(
                Sid="AllowPushPull",
                Effect=Allow,
                Principal=AWSPrincipal([
                    Join("", [
                        "arn:aws:iam::",
                        Ref(AWS_ACCOUNT_ID),
                        ":root",
                    ]),
                ]),
                Action=[
                    ecr.GetDownloadUrlForLayer,
                    ecr.BatchGetImage,
                    ecr.BatchCheckLayerAvailability,
                    ecr.PutImage,
                    ecr.InitiateLayerUpload,
                    ecr.UploadLayerPart,
                    ecr.CompleteLayerUpload,
                ],
            ),
        ]
    ),
))

template.add_output(Output(
    "RepositoryURL",
    Description="The docker repository URL",
    Value=Join("", [
        Ref(AWS_ACCOUNT_ID),
        ".dkr.ecr.",
        Ref(AWS_REGION),
        ".amazonaws.com/",
        Ref(repository),
    ]),
))

template.add_output(Output(
    "Repository",
    Description="ECR Repository",
    Value=Ref(repository),
    Export=Export(Sub("${AWS::StackName}-Repository")),
))


def get():
    return template.to_yaml()
