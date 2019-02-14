from troposphere import (
    GetAtt,
    Join,
    Output,
    FindInMap,
    Ref,
    Template,
)
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
)
from configuration import (
    root_domain_name,
)

assets_domain_name = "assets." + root_domain_name

template = Template()

template.set_description(
    "AWS CloudFormation Template to create needed resources for static site "
    "hosting using s3, CloudFront and route53.  It assumes that "
    "you already  have a Hosted Zone registered with Amazon Route 53. "
)

# https://gist.github.com/matalo33/abc6a40858ead3bf63501f48474426c2
template.add_mapping('RegionMap', {
    "us-east-1": {
        "hostedzoneID": "Z3AQBSTGFYJSTF",
        "websiteendpoint": "s3-website-us-east-1.amazonaws.com"
    },
    "us-west-1": {
        "hostedzoneID": "Z2F56UZL2M1ACD",
        "websiteendpoint": "s3-website-us-west-1.amazonaws.com"
    },
    "us-west-2": {
        "hostedzoneID": "Z3BJ6K6RIION7M",
        "websiteendpoint": "s3-website-us-west-2.amazonaws.com"
    },
    "eu-west-1": {
        "hostedzoneID": "Z1BKCTXD74EZPE",
        "websiteendpoint": "s3-website-eu-west-1.amazonaws.com"
    },
    "ap-southeast-1": {
        "hostedzoneID": "Z3O0J2DXBE1FTB",
        "websiteendpoint": "s3-website-ap-southeast-1.amazonaws.com"
    },
    "ap-southeast-2": {
        "hostedzoneID": "Z1WCIGYICN2BYD",
        "websiteendpoint": "s3-website-ap-southeast-2.amazonaws.com"
    },
    "ap-northeast-1": {
        "hostedzoneID": "Z2M4EHUR26P7ZW",
        "websiteendpoint": "s3-website-ap-northeast-1.amazonaws.com"
    },
    "ap-northeast-2": {
        "hostedzoneID": "Z3W03O7B5YMIYP",
        "websiteendpoint": "s3-website.ap-northeast-2.amazonaws.com"
    },
    "sa-east-1": {
        "hostedzoneID": "Z31GFT0UA1I2HV",
        "websiteendpoint": "s3-website-sa-east-1.amazonaws.com"
    },
    "cloudfront": {
        "hostedzoneID": "Z2FDTNDATAQYW2"
    }
})

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

template.add_resource(RecordSetGroup(
    "AssetsDNSName",
    HostedZoneName=Join("", [root_domain_name, "."]),
    Comment="Zone apex alias.",
    RecordSets=[
        RecordSet(
            Name=assets_domain_name,
            Type="A",
            AliasTarget=AliasTarget(
                FindInMap("RegionMap", Ref("AWS::Region"), "hostedzoneID"),
                FindInMap("RegionMap", Ref("AWS::Region"), "websiteendpoint")
            ),
        ),
    ],
))

distribution = template.add_resource(Distribution(
    "AssetsDistribution",
    DistributionConfig=DistributionConfig(
        Aliases=aliases,
        DefaultCacheBehavior=DefaultCacheBehavior(
            TargetOriginId="AssetsBucketOrigin",
            ViewerProtocolPolicy="allow-all",
            ForwardedValues=ForwardedValues(QueryString=False)
        ),
        DefaultRootObject="index_document",
        Origins=[Origin(
            Id="AssetsBucketOrigin",
            DomainName=GetAtt(assets_bucket, "DomainName"),
            CustomOriginConfig=CustomOriginConfig(
                OriginProtocolPolicy="http-only"
            ),
        )],
        Enabled=True,
        PriceClass="PriceClass_100"
    ),
    DependsOn=["AssetsBucket"]
))

template.add_output(Output(
    "WebsiteURL",
    Description="S3 Website URL",
    Value=GetAtt(assets_bucket, "WebsiteURL")
))


def get():
    return template.to_yaml()
