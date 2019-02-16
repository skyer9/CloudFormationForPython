from troposphere import (
    GetAtt,
    Join,
    Output,
    Ref,
    Template,
    Export, Sub)
from troposphere.route53 import (
    RecordSetGroup,
    RecordSet,
    AliasTarget,
)
from troposphere.s3 import (
    BucketPolicy,
    WebsiteConfiguration,
    Bucket,
    CorsConfiguration,
    CorsRules,
)
from troposphere.cloudfront import (
    Distribution,
    DistributionConfig,
    ForwardedValues,
    CustomOriginConfig,
    Origin,
    DefaultCacheBehavior,
    ViewerCertificate
)
from configuration import (
    root_domain_name,
    acm_certificate_arn,
)

assets_domain_name = "assets." + root_domain_name

template = Template()

template.set_description(
    "AWS CloudFormation Template to create needed resources for static site(both http and https) "
    "hosting using s3, CloudFront and route53.  It assumes that "
    "you already  have a Hosted Zone registered with Amazon Route 53. "
)

aliases = [assets_domain_name]

assets_bucket = template.add_resource(Bucket(
    "AssetsBucket",
    AccessControl="PublicRead",
    BucketName=assets_domain_name,
    CorsConfiguration=CorsConfiguration(
        CorsRules=[CorsRules(
            AllowedHeaders=["*"],
            AllowedMethods=["GET"],
            AllowedOrigins=["*"],
            ExposedHeaders=["Date"],
            MaxAge=3600
        )],
    ),
    WebsiteConfiguration=WebsiteConfiguration(
        IndexDocument="index.html",
        ErrorDocument="error.html",
        # ErrorDocument="404.html",
    ),
    # 스택 삭제시 S3 는 남긴다.
    DeletionPolicy="Retain",
))

template.add_resource(BucketPolicy(
    "AssetsBucketPolicy",
    Bucket=Ref(assets_bucket),
    PolicyDocument={
        "Statement": [{
            "Sid": "PublicReadForGetBucketObjects",
            "Action": ["s3:GetObject"],
            "Effect": "Allow",
            "Resource": {
                "Fn::Join": ["", [
                    "arn:aws:s3:::",
                    {"Ref": "AssetsBucket"},
                    "/*"
                ]]
            },
            "Principal": "*"
        }]
    }
))

distribution = template.add_resource(Distribution(
    "AssetsDistribution",
    DistributionConfig=DistributionConfig(
        Aliases=aliases,
        Origins=[Origin(
            Id="AssetsBucketOrigin",
            DomainName=GetAtt(assets_bucket, "DomainName"),
            CustomOriginConfig=CustomOriginConfig(
                HTTPPort=80,
                HTTPSPort=443,
                OriginProtocolPolicy="http-only"
            ),
        )],
        ViewerCertificate=ViewerCertificate(
            # 인증키는 미국동부(버지니아 북부) 리전에서 생성한 것만 사용가능하다.
            AcmCertificateArn=acm_certificate_arn,
            SslSupportMethod='sni-only'
        ),
        DefaultCacheBehavior=DefaultCacheBehavior(
            TargetOriginId="AssetsBucketOrigin",
            ViewerProtocolPolicy="allow-all",
            ForwardedValues=ForwardedValues(QueryString=True)
        ),
        DefaultRootObject="index.html",
        Enabled=True,
        PriceClass="PriceClass_All",
        HttpVersion="http2",
    ),
    DependsOn=["AssetsBucket"]
))

template.add_resource(RecordSetGroup(
    "AssetsDNSName",
    HostedZoneName=Join("", [root_domain_name, "."]),
    Comment="Zone apex alias.",
    RecordSets=[
        RecordSet(
            Name=assets_domain_name,
            Type="A",
            AliasTarget=AliasTarget(
                # CloudFront 는 HostedZoneId 가 하나이다.
                HostedZoneId="Z2FDTNDATAQYW2",
                DNSName=GetAtt(distribution, "DomainName")
            ),
        ),
    ],
))

template.add_output(Output(
    "WebsiteURL",
    Description="S3 Website URL",
    Value=GetAtt(assets_bucket, "WebsiteURL"),
))

template.add_output(Output(
    "WebsiteSecureURL",
    Description="S3 Secure Website URL",
    Value=Join("", [
        "https://",
        GetAtt(assets_bucket, "DomainName"),
    ])
))

template.add_output(Output(
    "AssetsDistributionDomainName",
    Description="AssetsDistribution Domain Name",
    Value=GetAtt(distribution, "DomainName")
))

template.add_output(Output(
    "AssetsBucket",
    Description="LoadBalancer of the VPN connected subnet",
    Value=Ref(assets_bucket),
    Export=Export(Sub("${AWS::StackName}-AssetsBucket")),
))

template.add_output(Output(
    "Distribution",
    Description="CloudFront Distribution",
    Value=Ref(distribution),
    Export=Export(Sub("${AWS::StackName}-Distribution")),
))


def get():
    return template.to_yaml()
