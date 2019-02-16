from troposphere import (
    AWS_ACCOUNT_ID,
    AWS_REGION,
    Equals,
    GetAtt,
    iam,
    Join,
    logs,
    Not,
    Output,
    Ref,
    Template,
    ImportValue, Sub)

from troposphere.ecs import (
    ContainerDefinition,
    DeploymentConfiguration,
    Environment,
    LoadBalancer,
    LogConfiguration,
    PortMapping,
    Service,
    TaskDefinition,
)

from configuration import (
    stack_base_name,
    application_revision,
    secret_key,
    web_worker_cpu,
    web_worker_memory,
    web_worker_desired_count,
    deploy_condition,
    web_worker_port,
    api_domain_name,
)

repository = ImportValue(Sub(stack_base_name + '-ecr-Repository'))
assets_bucket = ImportValue(Sub(stack_base_name + '-assets-AssetsBucket'))
distribution = ImportValue(Sub(stack_base_name + '-assets-Distribution'))
db_instance = ImportValue(Sub(stack_base_name + '-rds-MySQLInstance'))
jdbc_connection_string = ImportValue(Sub(stack_base_name + '-rds-JDBCConnectionString'))
cluster = ImportValue(Sub(stack_base_name + '-cluster-Cluster'))
application_target_group = ImportValue(Sub(stack_base_name + '-cluster-ApplicationTargetGroup'))

template = Template()

template.add_condition(deploy_condition, Not(Equals(application_revision, "")))

image = Join("", [
    Ref(AWS_ACCOUNT_ID),
    ".dkr.ecr.",
    Ref(AWS_REGION),
    ".amazonaws.com/",
    repository,
    ":",
    application_revision,
])

web_log_group = logs.LogGroup(
    "WebLogs",
    template=template,
    RetentionInDays=365,
    DeletionPolicy="Retain",
)

log_configuration = LogConfiguration(
    LogDriver="awslogs",
    Options={
        'awslogs-group': Ref(web_log_group),
        'awslogs-region': Ref(AWS_REGION),
    }
)

# ECS task
web_task_definition = TaskDefinition(
    "WebTask",
    template=template,
    Condition=deploy_condition,
    ContainerDefinitions=[
        ContainerDefinition(
            Name="WebWorker",
            #  1024 is full CPU
            Cpu=web_worker_cpu,
            Memory=web_worker_memory,
            Essential=True,
            Image=Join("", [
                Ref(AWS_ACCOUNT_ID),
                ".dkr.ecr.",
                Ref(AWS_REGION),
                ".amazonaws.com/",
                repository,
                ":",
                application_revision,
            ]),
            PortMappings=[PortMapping(
                HostPort=0,
                ContainerPort=web_worker_port,
            )],
            LogConfiguration=LogConfiguration(
                LogDriver="awslogs",
                Options={
                    'awslogs-group': Ref(web_log_group),
                    'awslogs-region': Ref(AWS_REGION),
                }
            ),
            Environment=[
                Environment(
                    Name="AWS_STORAGE_BUCKET_NAME",
                    Value=assets_bucket,
                ),
                Environment(
                    Name="CDN_DOMAIN_NAME",
                    Value=distribution,
                ),
                Environment(
                    Name="DOMAIN_NAME",
                    Value=api_domain_name,
                ),
                Environment(
                    Name="PORT",
                    Value=web_worker_port,
                ),
                Environment(
                    Name="SECRET_KEY",
                    Value=secret_key,
                ),
                Environment(
                    Name="DATABASE_URL",
                    Value=jdbc_connection_string,
                ),
            ],
        )
    ],
)

application_service_role = iam.Role(
    "ApplicationServiceRole",
    template=template,
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
                        "elasticloadbalancing:RegisterTargets",
                        "elasticloadbalancing:DeregisterTargets",
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
)

application_service = Service(
    "ApplicationService",
    template=template,
    Cluster=cluster,
    Condition=deploy_condition,
    DeploymentConfiguration=DeploymentConfiguration(
        MaximumPercent=135,
        MinimumHealthyPercent=30,
    ),
    DesiredCount=web_worker_desired_count,
    LoadBalancers=[LoadBalancer(
        ContainerName="WebWorker",
        ContainerPort=web_worker_port,
        TargetGroupArn=application_target_group,
    )],
    TaskDefinition=Ref(web_task_definition),
    Role=Ref(application_service_role),
)

template.add_output(Output(
    "WebLogsGroup",
    Description="Web application log group",
    Value=GetAtt(web_log_group, "Arn")
))


def get():
    return template.to_yaml()
