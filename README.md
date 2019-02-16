# CloudFormation with Python

CloudFormation 과 Python 을 이용하여 AWS App Stack 을 구성하는 방법을 설명합니다.

[여기](https://jeanphix.github.io/2016/06/13/howto-cloudformation-ecs/) 에 있는 강좌를 기반으로 문서를 작성하므로, 
영어에 익숙하신 분은 링크에서 바로 공부할 수도 있습니다.

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
