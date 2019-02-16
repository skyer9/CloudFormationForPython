# CloudFormation with Python

CloudFormation 과 Python 을 이용하여 AWS App Stack 을 구성하는 방법을 설명합니다.

[여기](https://jeanphix.github.io/2016/06/13/howto-cloudformation-ecs/) 에 있는 강좌를 기반으로 문서를 작성하므로, 
영어에 익숙하신 분은 링크에서 바로 공부할 수도 있습니다.

## Repository([ecr.py](templates/ecr.py))

서비스 스택에 쓰일 샘플 애플리케이션 이미지를 아래 명령으로 생성합니다.

```bash
git clone https://github.com/jeanphix/hello-django-ecs.git hello
cd hello/
sed -i -- 's/2.0.13.1/2.0.17/g' requirements.txt
docker build -t application:0.1 .
docker images
```

아래 명령으로 ECR(Elastic Container Registry) 를 생성할 수 있습니다.

```bash
python cfn.py -c -t ecr
```

아래 명령으로 생성한 애플리케이션 이미지를 레지스트리에 업로드할 수 있습니다.

```bash
# Install AWS CLI
pip install awscli
aws configure

# Login to ECR repository
`aws ecr get-login --region ap-northeast-2 --no-include-email`

# Push the image
docker tag application:0.1 <accountid>.dkr.ecr.<region>.amazonaws.com/skyer9-test-application:0.1
docker push <accountid>.dkr.ecr.<region>.amazonaws.com/skyer9-test-application:0.1
```

## Assets([assets.py](templates/assets.py))

정적 자원을 저장할 S3 스토리지를 생성하고, Route53 을 이용해 도메인을 연동해 주고, CloudFront(CDN) 을 연결합니다.

아래 명령으로 `assets` 템플릿을 스택으로 생성합니다.(create)

```bash
python cfn.py -c -t assets
```

아래 명령으로 변경된 스택을 반영합니다.(update)

```bash
python cfn.py -t assets
```

## Assets([assets_https_enabled.py](templates/assets_https_enabled.py))

AWS ACM(AWS Certificate Manager) 에서 인증서를 생성 또는 등록하면 HTTPS 로 접속할 수 있습니다.

```bash
python cfn.py -c -t assets-https-enabled
python cfn.py -t assets-https-enabled
```

## Network([network.py](templates/network.py))

아래 명령으로 네트워크 레이어를 생성할 수 있습니다.

```bash
python cfn.py -c -t network
python cfn.py -t network
```

## Database([rds.py](templates/rds.py))

아래 명령으로 MySQL 데이타베이스 서버를 구성할 수 있다.

```bash
python cfn.py -c -t rds
python cfn.py -t rds
```

## Cluster([cluster.py](templates/cluster.py))

아래 명령으로 ECS 클러스터를 구성할 수 있다.

```bash
python cfn.py -c -t cluster
python cfn.py -t cluster
```

## Service([ecs.py](templates/ecs.py))

아래 명령으로 ECS 서비스 스택을 구성할 수 있다.

```bash
python cfn.py -c -t ecs
python cfn.py -t ecs
```
