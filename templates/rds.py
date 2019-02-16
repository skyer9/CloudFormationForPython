from troposphere import (
    Template,
    ec2,
    rds,
    Ref,
    AWS_STACK_NAME,
    Join,
    GetAtt,
    Output,
    ImportValue,
    Sub,
    Export)

from configuration import (
    stack_base_name,
    container_a_subnet_cidr,
    container_b_subnet_cidr,
    db_allocated_storage,
    db_name,
    db_class,
    db_user,
    db_password,
)

template = Template()

db_security_group = template.add_resource(ec2.SecurityGroup(
    'DatabaseSecurityGroup',
    GroupDescription="Database security group.",
    VpcId=ImportValue(Sub(stack_base_name + '-network-VPCId')),
    SecurityGroupIngress=[
        ec2.SecurityGroupRule(
            IpProtocol="tcp",
            FromPort="3306",
            ToPort="3306",
            CidrIp=container_a_subnet_cidr,
        ),
        ec2.SecurityGroupRule(
            IpProtocol="tcp",
            FromPort="3306",
            ToPort="3306",
            CidrIp=container_b_subnet_cidr,
        ),
    ],
))

db_subnet_group = template.add_resource(rds.DBSubnetGroup(
    "DatabaseSubnetGroup",
    DBSubnetGroupDescription="Subnets available for the RDS DB Instance",
    SubnetIds=[
        ImportValue(Sub(stack_base_name + '-network-ContainerASubnet')),
        ImportValue(Sub(stack_base_name + '-network-ContainerBSubnet'))
    ],
))

db_instance = template.add_resource(rds.DBInstance(
    "MySQL",
    DBName=db_name,
    AllocatedStorage=db_allocated_storage,
    DBInstanceClass=db_class,
    DBInstanceIdentifier=Ref(AWS_STACK_NAME),
    Engine="MySQL",
    EngineVersion="5.6",
    MultiAZ=True,
    StorageType="gp2",
    MasterUsername=db_user,
    MasterUserPassword=db_password,
    DBSubnetGroupName=Ref(db_subnet_group),
    VPCSecurityGroups=[Ref(db_security_group)],
    BackupRetentionPeriod="7",
    DeletionPolicy="Snapshot",
))

template.add_output(Output(
    "JDBCConnectionString",
    Description="JDBC connection string for database",
    Value=Join("", [
        "jdbc:mysql://",
        GetAtt("MySQL", "Endpoint.Address"),
        GetAtt("MySQL", "Endpoint.Port"),
        "/",
        db_name,
    ]),
    Export=Export(Sub("${AWS::StackName}-JDBCConnectionString")),
))

template.add_output(Output(
    "MySQLInstance",
    Description="MySQL Instance",
    Value=Ref(db_instance),
    Export=Export(Sub("${AWS::StackName}-MySQLInstance")),
))


def get():
    return template.to_yaml()
