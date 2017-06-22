def create_iam_roles(stack_name, iam_resource, iam_client, s3_bucket_arn, assume_policy_role_document):

    s3_role_name = stack_name + "s3role"

    with open('./templates/S3_INLINE_POLICY_DOCUMENT', 'r') as policy_document_file:
        policy_document = policy_document_file.read().replace('\n', '')

    policy_document = policy_document.replace("{{S3ARN}}", s3_bucket_arn)

    new_s3_role = iam_resource.create_role(RoleName=s3_role_name, AssumeRolePolicyDocument=assume_policy_role_document)

    iam_client.put_role_policy(RoleName=s3_role_name, PolicyName=stack_name, PolicyDocument=policy_document)
