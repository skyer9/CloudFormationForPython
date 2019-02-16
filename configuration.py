stack_base_name = "skyer9-test"
region_name = "ap-northeast-2"

# for assets
root_domain_name = "10x10.io"

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
