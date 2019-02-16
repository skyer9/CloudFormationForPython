from troposphere import (
    AWS_REGION,
    AWS_STACK_ID,
    AWS_STACK_NAME,
    autoscaling,
    Base64,
    cloudformation,
    FindInMap,
    GetAtt,
    iam,
    Join,
    Output,
    Ref,
    Template,
    ImportValue,
    Sub,
    elasticloadbalancingv2,
    Export)

from troposphere.ec2 import (
    SecurityGroup,
    SecurityGroupRule,
)

from troposphere.ecs import (
    Cluster,
)

from troposphere.elasticloadbalancingv2 import (
    Action,
    Listener,
    LoadBalancer,
    Matcher,
    TargetGroup,
    TargetGroupAttribute,
)

from awacs import ecr

from configuration import (
    stack_base_name,
    container_instance_type,
    web_worker_port,
    max_container_instances,
    desired_container_instances,
    loadbalancer_a_subnet_cidr,
    loadbalancer_b_subnet_cidr,
    acm_cluster_certificate_arn,
    autoscaling_group_name,
)

vpc = ImportValue(Sub(stack_base_name + '-network-VPCId'))
loadbalancer_a_subnet = ImportValue(Sub(stack_base_name + '-network-LoadbalancerASubnet'))
loadbalancer_b_subnet = ImportValue(Sub(stack_base_name + '-network-LoadbalancerBSubnet'))
assets_bucket = ImportValue(Sub(stack_base_name + '-assets-AssetsBucket'))
container_a_subnet = ImportValue(Sub(stack_base_name + '-network-ContainerASubnet'))
container_b_subnet = ImportValue(Sub(stack_base_name + '-network-ContainerBSubnet'))

template = Template()

# https://docs.aws.amazon.com/ko_kr/AmazonECS/latest/developerguide/ecs-optimized_AMI.html
template.add_mapping("ECSRegionMap", {
    "us-east-1": {"AMI": "ami-eca289fb"},
    "us-east-2": {"AMI": "ami-446f3521"},
    "us-west-1": {"AMI": "ami-9fadf8ff"},
    "us-west-2": {"AMI": "ami-7abc111a"},
    "eu-west-1": {"AMI": "ami-a1491ad2"},
    "eu-central-1": {"AMI": "ami-54f5303b"},
    "ap-northeast-1": {"AMI": "ami-9cd57ffd"},
    "ap-northeast-2": {"AMI": "ami-076eb6ae0f9fc6903"},
    "ap-southeast-1": {"AMI": "ami-a900a3ca"},
    "ap-southeast-2": {"AMI": "ami-5781be34"},
})

application_target_group = template.add_resource(TargetGroup(
    'ApplicationTargetGroup',
    VpcId=vpc,
    Matcher=Matcher(
        HttpCode='200-299',
    ),
    Port=80,
    Protocol='HTTP',
    HealthCheckIntervalSeconds=15,
    HealthCheckPath='/health-check',
    HealthCheckProtocol='HTTP',
    HealthCheckTimeoutSeconds=5,
    HealthyThresholdCount=2,
    UnhealthyThresholdCount=8,
    TargetGroupAttributes=[
        TargetGroupAttribute(
            Key='stickiness.enabled',
            Value='true',
        )
    ],
))

load_balancer_security_group = template.add_resource(SecurityGroup(
    "LoadBalancerSecurityGroup",
    GroupDescription="Web load balancer security group.",
    VpcId=vpc,
    SecurityGroupIngress=[
        SecurityGroupRule(
            IpProtocol="tcp",
            FromPort="443",
            ToPort="443",
            CidrIp='0.0.0.0/0',
        ),
    ],
))

application_load_balancer = template.add_resource(LoadBalancer(
    'ApplicationLoadBalancer',
    Subnets=[
        loadbalancer_a_subnet,
        loadbalancer_b_subnet,
    ],
    SecurityGroups=[Ref(load_balancer_security_group)],
))

application_listener = template.add_resource(Listener(
    'ApplicationListener',
    Certificates=[elasticloadbalancingv2.Certificate(
        CertificateArn=acm_cluster_certificate_arn,
    )],
    LoadBalancerArn=Ref(application_load_balancer),
    Protocol='HTTPS',
    Port=443,
    DefaultActions=[Action(
        TargetGroupArn=Ref(application_target_group),
        Type='forward',
    )]
))

# ECS cluster
cluster = template.add_resource(Cluster(
    "Cluster",
))

# ECS container role
container_instance_role = template.add_resource(iam.Role(
    "ContainerInstanceRole",
    AssumeRolePolicyDocument=dict(Statement=[dict(
        Effect="Allow",
        Principal=dict(Service=["ec2.amazonaws.com"]),
        Action=["sts:AssumeRole"],
    )]),
    Path="/",
    Policies=[
        iam.Policy(
            PolicyName="AssetsManagementPolicy",
            PolicyDocument=dict(
                Statement=[dict(
                    Effect="Allow",
                    Action=[
                        "s3:ListBucket",
                    ],
                    Resource=Join("", [
                        "arn:aws:s3:::",
                        assets_bucket,
                    ]),
                ), dict(
                    Effect="Allow",
                    Action=[
                        "s3:*",
                    ],
                    Resource=Join("", [
                        "arn:aws:s3:::",
                        assets_bucket,
                        "/*",
                    ]),
                )],
            ),
        ),
        iam.Policy(
            PolicyName="ECSManagementPolicy",
            PolicyDocument=dict(
                Statement=[dict(
                    Effect="Allow",
                    Action=[
                        "ecs:*",
                        "elasticloadbalancing:*",
                    ],
                    Resource="*",
                )],
            ),
        ),
        iam.Policy(
            PolicyName='ECRManagementPolicy',
            PolicyDocument=dict(
                Statement=[dict(
                    Effect='Allow',
                    Action=[
                        ecr.GetAuthorizationToken,
                        ecr.GetDownloadUrlForLayer,
                        ecr.BatchGetImage,
                        ecr.BatchCheckLayerAvailability,
                    ],
                    Resource="*",
                )],
            ),
        ),
        iam.Policy(
            PolicyName="LoggingPolicy",
            PolicyDocument=dict(
                Statement=[dict(
                    Effect="Allow",
                    Action=[
                        "logs:Create*",
                        "logs:PutLogEvents",
                    ],
                    Resource="arn:aws:logs:*:*:*",
                )],
            ),
        ),
    ]
))

# ECS container instance profile
container_instance_profile = template.add_resource(iam.InstanceProfile(
    "ContainerInstanceProfile",
    Path="/",
    Roles=[Ref(container_instance_role)],
))

container_security_group = template.add_resource(SecurityGroup(
    'ContainerSecurityGroup',
    GroupDescription="Container security group.",
    VpcId=vpc,
    SecurityGroupIngress=[
        # HTTP from web public subnets
        SecurityGroupRule(
            IpProtocol="tcp",
            FromPort=web_worker_port,
            ToPort=web_worker_port,
            CidrIp=loadbalancer_a_subnet_cidr,
        ),
        SecurityGroupRule(
            IpProtocol="tcp",
            FromPort=web_worker_port,
            ToPort=web_worker_port,
            CidrIp=loadbalancer_b_subnet_cidr,
        ),
    ],
))

container_instance_configuration_name = "ContainerLaunchConfiguration"

container_instance_configuration = template.add_resource(autoscaling.LaunchConfiguration(
    container_instance_configuration_name,
    Metadata=autoscaling.Metadata(
        cloudformation.Init(dict(
            config=cloudformation.InitConfig(
                commands=dict(
                    register_cluster=dict(command=Join("", [
                        "#!/bin/bash\n",
                        # Register the cluster
                        "echo ECS_CLUSTER=",
                        Ref(cluster),
                        " >> /etc/ecs/ecs.config\n",
                        # Enable CloudWatch docker logging
                        'echo \'ECS_AVAILABLE_LOGGING_DRIVERS=',
                        '["json-file","awslogs"]\'',
                        " >> /etc/ecs/ecs.config\n",
                    ]))
                ),
                files=cloudformation.InitFiles({
                    "/etc/cfn/cfn-hup.conf": cloudformation.InitFile(
                        content=Join("", [
                            "[main]\n",
                            "stack=",
                            Ref(AWS_STACK_ID),
                            "\n",
                            "region=",
                            Ref(AWS_REGION),
                            "\n",
                        ]),
                        mode="000400",
                        owner="root",
                        group="root",
                    ),
                    "/etc/cfn/hooks.d/cfn-auto-reloader.conf":
                        cloudformation.InitFile(
                            content=Join("", [
                                "[cfn-auto-reloader-hook]\n",
                                "triggers=post.update\n",
                                "path=Resources.%s."
                                % container_instance_configuration_name,
                                "Metadata.AWS::CloudFormation::Init\n",
                                "action=/opt/aws/bin/cfn-init -v ",
                                "         --stack ",
                                Ref(AWS_STACK_NAME),
                                "         --resource %s"
                                % container_instance_configuration_name,
                                "         --region ",
                                Ref("AWS::Region"),
                                "\n",
                                "runas=root\n",
                                ])
                        )
                }),
                services=dict(
                    sysvinit=cloudformation.InitServices({
                        'cfn-hup': cloudformation.InitService(
                            enabled=True,
                            ensureRunning=True,
                            files=[
                                "/etc/cfn/cfn-hup.conf",
                                "/etc/cfn/hooks.d/cfn-auto-reloader.conf",
                            ]
                        ),
                    })
                )
            )
        ))
    ),
    SecurityGroups=[Ref(container_security_group)],
    InstanceType=container_instance_type,
    ImageId=FindInMap("ECSRegionMap", Ref(AWS_REGION), "AMI"),
    IamInstanceProfile=Ref(container_instance_profile),
    UserData=Base64(Join('', [
        "#!/bin/bash -xe\n",
        "yum install -y aws-cfn-bootstrap\n",
        "/opt/aws/bin/cfn-init -v ",
        "         --stack ", Ref(AWS_STACK_NAME),
        "         --resource %s " % container_instance_configuration_name,
        "         --region ", Ref(AWS_REGION), "\n",
        "/opt/aws/bin/cfn-signal -e $? ",
        "         --stack ", Ref(AWS_STACK_NAME),
        "         --resource %s " % container_instance_configuration_name,
        "         --region ", Ref(AWS_REGION), "\n",
        ])),
))

autoscaling_group = template.add_resource(autoscaling.AutoScalingGroup(
    autoscaling_group_name,
    VPCZoneIdentifier=[container_a_subnet, container_b_subnet],
    MinSize=desired_container_instances,
    MaxSize=max_container_instances,
    DesiredCapacity=desired_container_instances,
    LaunchConfigurationName=Ref(container_instance_configuration),
    HealthCheckType="EC2",
    HealthCheckGracePeriod=300,
))

app_service_role = template.add_resource(iam.Role(
    "AppServiceRole",
    AssumeRolePolicyDocument=dict(Statement=[dict(
        Effect="Allow",
        Principal=dict(Service=["ecs.amazonaws.com"]),
        Action=["sts:AssumeRole"],
    )]),
    Path="/",
    Policies=[
        iam.Policy(
            PolicyName="WebServicePolicy",
            PolicyDocument=dict(
                Statement=[dict(
                    Effect="Allow",
                    Action=[
                        "elasticloadbalancing:Describe*",
                        "elasticloadbalancing"
                        ":DeregisterInstancesFromLoadBalancer",
                        "elasticloadbalancing"
                        ":RegisterInstancesWithLoadBalancer",
                        "ec2:Describe*",
                        "ec2:AuthorizeSecurityGroupIngress",
                    ],
                    Resource="*",
                )],
            ),
        ),
    ]
))

template.add_output(Output(
    "LoadBalancerDNSName",
    Description="Loadbalancer DNS",
    Value=GetAtt(application_load_balancer, "DNSName")
))

template.add_output(Output(
    "Cluster",
    Description="Cluster",
    Value=Ref(cluster),
    Export=Export(Sub("${AWS::StackName}-Cluster")),
))

template.add_output(Output(
    "ApplicationTargetGroup",
    Description="Application Target Group",
    Value=Ref(application_target_group),
    Export=Export(Sub("${AWS::StackName}-ApplicationTargetGroup")),
))


def get():
    return template.to_yaml()
