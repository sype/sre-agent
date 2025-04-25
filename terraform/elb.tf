module "elb" {
  source  = "terraform-aws-modules/elb/aws"
  version = "~> 4.0"

  name = "${var.cluster_name}-elb"

  subnets         = module.vpc.public_subnets
  security_groups = [aws_security_group.elb_sg.id]
  internal        = false

  # Configure the listeners for HTTP and HTTPS
  listener = [
    {
      instance_port     = 30000  # NodePort range - will be assigned by Kubernetes
      instance_protocol = "HTTP"
      lb_port           = 80
      lb_protocol       = "HTTP"
    },
    {
      instance_port     = 30000  # NodePort range - will be assigned by Kubernetes
      instance_protocol = "TCP"
      lb_port           = 443
      lb_protocol       = "TCP"
    }
  ]

  health_check = {
    target              = "TCP:30000"  # Generic TCP check on NodePort range
    interval            = 30
    healthy_threshold   = 2
    unhealthy_threshold = 2
    timeout             = 5
  }

  # We can't directly attach an ELB to an EKS ASG through this module,
  # so we'll set the number_of_instances to 0 here and handle the
  # attachment in a separate resource
  number_of_instances = 0
  instances           = []

  tags = {
    Name = "${var.cluster_name}-elb"
  }
}

# Create a security group for the ELB
resource "aws_security_group" "elb_sg" {
  name        = "${var.cluster_name}-elb-sg"
  description = "Security group for the ELB to access the EKS cluster"
  vpc_id      = module.vpc.vpc_id

  # Allow HTTP access from anywhere
  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
    description = "HTTP access"
  }

  # Allow HTTPS access from anywhere
  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
    description = "HTTPS access"
  }

  # Allow all outbound traffic
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${var.cluster_name}-elb-sg"
  }
}

# Create security group rule to allow ELB to communicate with EKS nodes
resource "aws_security_group_rule" "elb_to_eks" {
  type                     = "ingress"
  from_port                = 0
  to_port                  = 65535
  protocol                 = "tcp"
  source_security_group_id = aws_security_group.elb_sg.id
  security_group_id        = module.eks.node_security_group_id
  description              = "Allow ELB to communicate with EKS nodes"
}

# Create specific security group rule to allow traffic to the NodePort range
resource "aws_security_group_rule" "eks_nodeport_range" {
  type                     = "ingress"
  from_port                = 30000
  to_port                  = 32767
  protocol                 = "tcp"
  source_security_group_id = aws_security_group.elb_sg.id
  security_group_id        = module.eks.node_security_group_id
  description              = "Allow traffic to the Kubernetes NodePort range"
}

# Attach the ELB to the EKS node Auto Scaling Groups
resource "aws_autoscaling_attachment" "eks_nodes_elb_attachment" {
  for_each               = module.eks.eks_managed_node_groups
  autoscaling_group_name = each.value.node_group_autoscaling_group_names[0]
  elb                    = module.elb.elb_id
  
  depends_on = [module.eks]
} 
