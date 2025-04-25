# resource "null_resource" "update_aws_auth" {
#   # Trigger this resource when the list of users changes
#   triggers = {
#     users = jsonencode(var.k8s_users)
#   }

#   # Update the aws-auth ConfigMap using eksctl manually
#   provisioner "local-exec" {
#     interpreter = ["/bin/bash", "-c"]
#     command = <<EOF
# # First, ensure we have eksctl installed
# if ! command -v eksctl &> /dev/null; then
#   echo "eksctl not found, please install it to manage the aws-auth ConfigMap"
#   exit 1
# fi

# # For each user, add their mapping
# %{for user in var.k8s_users}
# echo "Adding user ${user.iam_username} to aws-auth ConfigMap..."
# eksctl create iamidentitymapping --cluster "${var.cluster_name}" --region "${var.aws_region}" --arn "arn:aws:iam::${var.aws_account_id}:user/${user.iam_username}" --username "${user.k8s_username}" --group ${join(" --group ", user.groups)} --no-duplicate-arns
# %{endfor}
# EOF
#   }

#   # Ensure this runs after the EKS cluster is fully created
#   depends_on = [module.eks]
# } 
