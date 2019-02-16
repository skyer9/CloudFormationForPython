stack_base_name = "skyer9-test"
region_name = "ap-northeast-2"
acm_certificate_arn = "arn:aws:acm:us-east-1:061175447448:certificate/d6c212a8-8871-XXXXXXXXXXXXXXX"
acm_cluster_certificate_arn = "arn:aws:acm:ap-northeast-2:061175447448:certificate/45a14cb8-3da4-4XXXXXXXXXXXXXXX"

# for assets
root_domain_name = "10x10.io"
api_domain_name = "api." + root_domain_name

# for network
vpc_cidr = "10.0.0.0/16"
public_subnet_cidr = "10.0.1.0/24"
loadbalancer_a_subnet_cidr = "10.0.2.0/24"
loadbalancer_b_subnet_cidr = "10.0.3.0/24"
container_a_subnet_cidr = "10.0.10.0/24"
container_b_subnet_cidr = "10.0.11.0/24"

# for database
db_allocated_storage = 5            # 5 giga byte
db_name = "db_app"
db_class = "db.t2.small"
db_user = "appuser"
db_password = "wYIr9zpQIzuVTCqPOpOQV6lQX1MlgM1E"

# for cluster
container_instance_type = "t2.micro"
max_container_instances = 3
desired_container_instances = 3
autoscaling_group_name = "AutoScalingGroup"

# for service
application_revision = ""
secret_key = "LXeKzcTCAr8kkjKsyARmzX5fUD1BQwi8"
web_worker_cpu = 256
web_worker_memory = 500
web_worker_desired_count = 3
deploy_condition = "Deploy"
web_worker_port = "8000"
