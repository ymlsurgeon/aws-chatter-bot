import boto3
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field



class EC2IPInput(BaseModel):
    ip_address: str = Field(description="ip address")



class GetEC2InstanceSizeTool(BaseTool):
    name: str = "get_ec2_instance_size"
    description: str = "finds ec2 info by ip address"
    args_schema: type[BaseModel] = EC2IPInput
    
    def _run(self, ip_address: str) -> str:
        
        ec2 = boto3.client('ec2')
        
        
        response = ec2.describe_instances(
            Filters=[
                {
                    'Name': 'network-interface.addresses.private-ip-address',
                    'Values': [ip_address]
                }
            ]
        )
        
        
        if len(response['Reservations']) == 0:
            response = ec2.describe_instances(
                Filters=[
                    {
                        'Name': 'ip-address',
                        'Values': [ip_address]
                    }
                ]
            )
        
    
        if len(response['Reservations']) == 0:
            return f"no instance found with ip {ip_address}"
        
        # get instance
        reservation = response['Reservations'][0]
        instance = reservation['Instances'][0]
        
        # get info
        instance_id = instance['InstanceId']
        instance_type = instance['InstanceType']
        state = instance['State']['Name']
        
        # get ips
        private_ip = 'N/A'
        if 'PrivateIpAddress' in instance:
            private_ip = instance['PrivateIpAddress']
        
        public_ip = 'N/A'
        if 'PublicIpAddress' in instance:
            public_ip = instance['PublicIpAddress']
        
        # get name
        name = 'no name'
        if 'Tags' in instance:
            tags = instance['Tags']
            for tag in tags:
                if tag['Key'] == 'Name':
                    name = tag['Value']
        
        
        output = "ec2 instance:\n"
        output = output + f"id: {instance_id}\n"
        output = output + f"type: {instance_type}\n"
        output = output + f"state: {state}\n"
        output = output + f"name: {name}\n"
        output = output + f"private ip: {private_ip}\n"
        output = output + f"public ip: {public_ip}"
        
        return output
    
    def _arun(self, ip_address: str) -> str:
        return self._run(ip_address)
