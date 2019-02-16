from troposphere import (
    Template,
    AWS_REGION,
    GetAtt,
    Join,
    Ref,
    Output,
    Export,
    Sub
)

from troposphere.ec2 import (
    EIP,
    InternetGateway,
    NatGateway,
    Route,
    RouteTable,
    Subnet,
    SubnetRouteTableAssociation,
    VPC,
    VPCGatewayAttachment,
)

from configuration import (
    vpc_cidr,
    public_subnet_cidr,
    loadbalancer_a_subnet_cidr,
    loadbalancer_b_subnet_cidr,
    container_a_subnet_cidr,
    container_b_subnet_cidr,
)

template = Template()

vpc = template.add_resource(VPC(
    "Vpc",
    CidrBlock=vpc_cidr,
))

internet_gateway = template.add_resource(InternetGateway(
    "InternetGateway",
))

template.add_resource(VPCGatewayAttachment(
    "GatewayAttachment",
    VpcId=Ref(vpc),
    InternetGatewayId=Ref(internet_gateway),
))

public_route_table = template.add_resource(RouteTable(
    "PublicRouteTable",
    VpcId=Ref(vpc),
))

public_route = template.add_resource(Route(
    "PublicRoute",
    GatewayId=Ref(internet_gateway),
    DestinationCidrBlock="0.0.0.0/0",
    RouteTableId=Ref(public_route_table),
))

public_subnet = template.add_resource(Subnet(
    "PublicSubnet",
    VpcId=Ref(vpc),
    CidrBlock=public_subnet_cidr,
))

template.add_resource(SubnetRouteTableAssociation(
    "PublicSubnetRouteTableAssociation",
    RouteTableId=Ref(public_route_table),
    SubnetId=Ref(public_subnet),
))

nat_ip = template.add_resource(EIP(
    "NatIp",
    Domain="vpc",
))

nat_gateway = template.add_resource(NatGateway(
    "NatGateway",
    AllocationId=GetAtt(nat_ip, "AllocationId"),
    SubnetId=Ref(public_subnet),
))

loadbalancer_a_subnet = template.add_resource(Subnet(
    "LoadbalancerASubnet",
    VpcId=Ref(vpc),
    CidrBlock=loadbalancer_a_subnet_cidr,
    AvailabilityZone=Join("", [Ref(AWS_REGION), "a"]),
))

template.add_resource(SubnetRouteTableAssociation(
    "LoadbalancerASubnetRouteTableAssociation",
    RouteTableId=Ref(public_route_table),
    SubnetId=Ref(loadbalancer_a_subnet),
))

loadbalancer_b_subnet = template.add_resource(Subnet(
    "LoadbalancerBSubnet",
    VpcId=Ref(vpc),
    CidrBlock=loadbalancer_b_subnet_cidr,
    AvailabilityZone=Join("", [Ref(AWS_REGION), "c"]),
))

template.add_resource(SubnetRouteTableAssociation(
    "LoadbalancerBSubnetRouteTableAssociation",
    RouteTableId=Ref(public_route_table),
    SubnetId=Ref(loadbalancer_b_subnet),
))

private_route_table = template.add_resource(RouteTable(
    "PrivateRouteTable",
    VpcId=Ref(vpc),
))

private_nat_route = template.add_resource(Route(
    "PrivateNatRoute",
    RouteTableId=Ref(private_route_table),
    DestinationCidrBlock="0.0.0.0/0",
    NatGatewayId=Ref(nat_gateway),
))

container_a_subnet = template.add_resource(Subnet(
    "ContainerASubnet",
    VpcId=Ref(vpc),
    CidrBlock=container_a_subnet_cidr,
    AvailabilityZone=Join("", [Ref(AWS_REGION), "a"]),
))

template.add_resource(SubnetRouteTableAssociation(
    "ContainerARouteTableAssociation",
    SubnetId=Ref(container_a_subnet),
    RouteTableId=Ref(private_route_table),
))

container_b_subnet = template.add_resource(Subnet(
    "ContainerBSubnet",
    VpcId=Ref(vpc),
    CidrBlock=container_b_subnet_cidr,
    AvailabilityZone=Join("", [Ref(AWS_REGION), "c"]),
))

template.add_resource(SubnetRouteTableAssociation(
    "ContainerBRouteTableAssociation",
    SubnetId=Ref(container_b_subnet),
    RouteTableId=Ref(private_route_table),
))

template.add_output(Output(
    "VPCId",
    Description="VPCId of the newly created VPC",
    Value=Ref(vpc),
    Export=Export(Sub("${AWS::StackName}-VPCId")),
))

template.add_output(Output(
    "ContainerASubnet",
    Description="Container A Subnet",
    Value=Ref(container_a_subnet),
    Export=Export(Sub("${AWS::StackName}-ContainerASubnet")),
))

template.add_output(Output(
    "ContainerBSubnet",
    Description="Container B Subnet",
    Value=Ref(container_b_subnet),
    Export=Export(Sub("${AWS::StackName}-ContainerBSubnet")),
))

template.add_output(Output(
    "LoadbalancerASubnet",
    Description="Load Balancer A Subnet",
    Value=Ref(loadbalancer_a_subnet),
    Export=Export(Sub("${AWS::StackName}-LoadbalancerASubnet")),
))

template.add_output(Output(
    "LoadbalancerBSubnet",
    Description="Load Balancer B Subnet",
    Value=Ref(loadbalancer_b_subnet),
    Export=Export(Sub("${AWS::StackName}-LoadbalancerBSubnet")),
))


def get():
    return template.to_yaml()
