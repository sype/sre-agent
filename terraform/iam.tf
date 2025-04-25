# Create the MCP-access-role
resource "aws_iam_role" "mcp_access_role" {
  name = "MCP-access-role"
  
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Federated = "arn:aws:iam::${var.aws_account_id}:oidc-provider/${module.eks.oidc_provider}"
        }
        Action = "sts:AssumeRoleWithWebIdentity"
        Condition = {
          StringEquals = {
            "${module.eks.oidc_provider}:sub" = "system:serviceaccount:sre-agent:mcp-kubernetes-sa",
            "${module.eks.oidc_provider}:aud" = "sts.amazonaws.com"
          }
        }
      }
    ]
  })

  tags = {
    Name = "MCP-access-role"
  }
}

# Create policy for the MCP-access-role to access the target EKS cluster
resource "aws_iam_policy" "mcp_access_policy" {
  name        = "mcp-access-policy"
  description = "Policy for MCP-access-role to access the target EKS cluster"
  
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = "eks:DescribeCluster"
        Resource = var.target_cluster_arn
      }
    ]
  })
}

# Attach the policy to the role
resource "aws_iam_role_policy_attachment" "mcp_access_policy_attachment" {
  role       = aws_iam_role.mcp_access_role.name
  policy_arn = aws_iam_policy.mcp_access_policy.arn
}

# Create an IAM user group for SRE agent access
resource "aws_iam_group" "sre_agent_group" {
  name = "sre-agent"
}

# Create a policy for the SRE agent group
resource "aws_iam_policy" "sre_agent_policy" {
  name        = "sre-agent-policy"
  description = "Policy for SRE agent to access EKS clusters"
  
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = [
          "eks:DescribeCluster",
          "eks:ListClusters"
        ]
        Resource = "*"
      }
    ]
  })
}

# Attach the policy to the group
resource "aws_iam_group_policy_attachment" "sre_agent_policy_attachment" {
  group      = aws_iam_group.sre_agent_group.name
  policy_arn = aws_iam_policy.sre_agent_policy.arn
} 
