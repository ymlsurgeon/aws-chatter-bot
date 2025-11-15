import boto3
import json
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field



class S3Input(BaseModel):
    bucket_name: str = Field(default="", description="bucket name or leave empty")




class S3Tool(BaseTool):
    name: str = "s3_tool"
    description: str = "use this for s3 questions like how many buckets, which are public, whats in a bucket, sizes, etc. put bucket name for specific bucket or leave empty for all"
    args_schema: type[BaseModel] = S3Input
    
    def _run(self, bucket_name: str = "") -> str:
        
        s3 = boto3.client('s3')
        
        
        response = s3.list_buckets()
        buckets = response['Buckets']
        
        
        if bucket_name == "":
            
            output = f"you have {len(buckets)} buckets:\n\n"
            
            
            for b in buckets:
                name = b['Name']
                
                # check if public
                public = False
                try:
                    acl = s3.get_bucket_acl(Bucket=name)
                    grants = acl['Grants']
                    for grant in grants:
                        grantee = grant['Grantee']
                        if grantee.get('Type') == 'Group':
                            uri = grantee.get('URI')
                            if uri:
                                if 'AllUsers' in uri:
                                    public = True
                except:
                    pass
                
                
                try:
                    policy_response = s3.get_bucket_policy(Bucket=name)
                    policy_string = policy_response['Policy']
                    policy = json.loads(policy_string)
                    statements = policy['Statement']
                    for stmt in statements:
                        principal = stmt.get('Principal')
                        effect = stmt.get('Effect')
                        if principal == '*':
                            if effect == 'Allow':
                                public = True
                except:
                    pass
                
                
                file_count = 0
                total_size = 0
                try:
                    objects_response = s3.list_objects_v2(Bucket=name, MaxKeys=1000)
                    if 'Contents' in objects_response:
                        contents = objects_response['Contents']
                        file_count = len(contents)
                        for obj in contents:
                            total_size = total_size + obj['Size']
                except:
                    pass
                
                # convert to mb
                size_mb = total_size / 1024 / 1024
                
                
                if public:
                    output = output + f"- {name}\n"
                    output = output + "  PUBLIC\n"
                else:
                    output = output + f"- {name}\n"
                    output = output + "  private\n"
                output = output + f"  {file_count} files\n"
                output = output + f"  {size_mb:.2f}MB\n\n"
            
            # count public/private
            public_count = 0
            private_count = 0
            
            for b in buckets:
                name = b['Name']
                is_public = False
                
                try:
                    acl = s3.get_bucket_acl(Bucket=name)
                    for g in acl['Grants']:
                        if g['Grantee'].get('Type') == 'Group':
                            if 'AllUsers' in g['Grantee'].get('URI', ''):
                                is_public = True
                except:
                    pass
                
                if is_public:
                    public_count = public_count + 1
                else:
                    private_count = private_count + 1
            
            output = output + f"total: {public_count} public and {private_count} private"
            
            return output
            
        else:
            
            # check if bucket exists and show details
            bucket_exists = False
            for b in buckets:
                if b['Name'] == bucket_name:
                    bucket_exists = True
            
            if not bucket_exists:
                return f"bucket {bucket_name} doesnt exist"
            
            result = f"bucket: {bucket_name}\n\n"
            
            
            is_public = False
            
        
            try:
                acl = s3.get_bucket_acl(Bucket=bucket_name)
                grants = acl['Grants']
                for grant in grants:
                    grantee = grant['Grantee']
                    if grantee.get('Type') == 'Group':
                        uri = grantee.get('URI')
                        if uri and 'AllUsers' in uri:
                            is_public = True
            except:
                pass
            
            
            try:
                policy_response = s3.get_bucket_policy(Bucket=bucket_name)
                policy_string = policy_response['Policy']
                policy_data = json.loads(policy_string)
                for statement in policy_data['Statement']:
                    if statement.get('Principal') == '*' and statement.get('Effect') == 'Allow':
                        is_public = True
            except:
                pass
            
            if is_public:
                result = result + "PUBLIC (anyone can access)\n\n"
            else:
                result = result + "private\n\n"
            
            
            try:
                objects = s3.list_objects_v2(Bucket=bucket_name, MaxKeys=100)
                
                if 'Contents' not in objects:
                    result = result + "empty bucket"
                    return result
                
                files = objects['Contents']
                
                
                total = 0
                for f in files:
                    total = total + f['Size']
                
                total_mb = total / 1024 / 1024
                
                result = result + f"{len(files)} files:\n"
                
                # only show first 20 files
                count = 0
                for file in files:
                    if count >= 20:
                        break
                    
                    name = file['Key']
                    size = file['Size']
                    size_mb = size / 1024 / 1024
                    
                    result = result + f"- {name} ({size_mb:.2f}MB)\n"
                    
                    count = count + 1
                
                if len(files) > 20:
                    remaining = len(files) - 20
                    result = result + f"...and {remaining} more\n"
                
                result = result + f"\ntotal: {total_mb:.2f}MB"
                
            except Exception as e:
                result = result + f"error getting contents: {e}"
            
            return result
    
    def _arun(self, bucket_name: str = "") -> str:
        return self._run(bucket_name)
