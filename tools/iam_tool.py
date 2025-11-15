import boto3
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field

class IAMUserInput(BaseModel):
    username: str = Field(description="username")


class GetIAMUserPermissionsTool(BaseTool):
    name: str = "get_iam_user_permissions"
    description: str = "checks iam permissions for a user"
    args_schema: type[BaseModel] = IAMUserInput
    
    def _run(self, username: str) -> str:
        
        iam = boto3.client('iam')
        
        # check user exists
        try:
            user = iam.get_user(UserName=username)
        except:
            return f"user {username} not found"
        
        
        output = f"permissions for {username}:\n\n"
        
        
        try:
            policies_response = iam.list_attached_user_policies(UserName=username)
            policies = policies_response['AttachedPolicies']
            
            if len(policies) > 0:
                output = output + "managed policies:\n"
                for policy in policies:
                    policy_name = policy['PolicyName']
                    policy_arn = policy['PolicyArn']
                    output = output + f"- {policy_name} ({policy_arn})\n"
        except:
            pass
        
        
        try:
            inline_response = iam.list_user_policies(UserName=username)
            inline_policies = inline_response['PolicyNames']
            
            if len(inline_policies) > 0:
                output = output + "\ninline policies:\n"
                for policy_name in inline_policies:
                    output = output + f"- {policy_name}\n"
        except:
            pass
        
        # groups
        try:
            groups_response = iam.list_groups_for_user(UserName=username)
            groups = groups_response['Groups']
            
            if len(groups) > 0:
                output = output + "\ngroups:\n"
                for group in groups:
                    group_name = group['GroupName']
                    output = output + f"- {group_name}\n"
                    
                    
                    try:
                        group_policies = iam.list_attached_group_policies(GroupName=group_name)
                        for policy in group_policies['AttachedPolicies']:
                            output = output + f"  -> {policy['PolicyName']}\n"
                    except:
                        pass
        except:
            pass
        
        
        if output == f"permissions for {username}:\n\n":
            return f"{username} has no permissions"
        
        return output
    
    def _arun(self, username: str) -> str:
        return self._run(username)
