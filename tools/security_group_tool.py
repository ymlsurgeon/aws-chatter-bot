import boto3
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field


class SecurityGroupInput(BaseModel):
    group_id: str = Field(description="security group id (sg-xxxxx) or leave empty for all groups")


class GetSecurityGroupInfoTool(BaseTool):
    name: str = "get_security_group_info"
    description: str = "checks security group information and rules"
    args_schema: type[BaseModel] = SecurityGroupInput
    
    def _run(self, group_id: str = "") -> str:
        
        ec2 = boto3.client('ec2')
        
        try:
            if group_id and group_id.strip():
                # Get specific security group
                response = ec2.describe_security_groups(GroupIds=[group_id.strip()])
            else:
                # Get all security groups
                response = ec2.describe_security_groups()
                
        except Exception as e:
            if "InvalidGroupId" in str(e):
                return f"security group {group_id} not found"
            return f"error getting security groups: {str(e)}"
        
        security_groups = response['SecurityGroups']
        
        if len(security_groups) == 0:
            return "no security groups found"
        
        output = ""
        
        for sg in security_groups:
            sg_id = sg['GroupId']
            sg_name = sg['GroupName']
            description = sg['Description']
            vpc_id = sg.get('VpcId', 'N/A')
            
            output += f"security group: {sg_name} ({sg_id})\n"
            output += f"description: {description}\n"
            output += f"vpc: {vpc_id}\n"
            
            # Inbound rules
            inbound_rules = sg['IpPermissions']
            if len(inbound_rules) > 0:
                output += "inbound rules:\n"
                for rule in inbound_rules:
                    protocol = rule.get('IpProtocol', 'N/A')
                    from_port = rule.get('FromPort', 'N/A')
                    to_port = rule.get('ToPort', 'N/A')
                    
                    if protocol == '-1':
                        port_range = "all ports"
                    elif from_port == to_port:
                        port_range = str(from_port)
                    else:
                        port_range = f"{from_port}-{to_port}"
                    
                    # Sources
                    sources = []
                    
                    # IP ranges
                    for ip_range in rule.get('IpRanges', []):
                        cidr = ip_range['CidrIp']
                        desc = ip_range.get('Description', '')
                        if desc:
                            sources.append(f"{cidr} ({desc})")
                        else:
                            sources.append(cidr)
                    
                    # Security groups
                    for sg_ref in rule.get('UserIdGroupPairs', []):
                        ref_sg_id = sg_ref['GroupId']
                        ref_desc = sg_ref.get('Description', '')
                        if ref_desc:
                            sources.append(f"{ref_sg_id} ({ref_desc})")
                        else:
                            sources.append(ref_sg_id)
                    
                    sources_str = ", ".join(sources) if sources else "no sources"
                    output += f"  - {protocol} {port_range} from {sources_str}\n"
            else:
                output += "inbound rules: none\n"
            
            # Outbound rules
            outbound_rules = sg['IpPermissionsEgress']
            if len(outbound_rules) > 0:
                output += "outbound rules:\n"
                for rule in outbound_rules:
                    protocol = rule.get('IpProtocol', 'N/A')
                    from_port = rule.get('FromPort', 'N/A')
                    to_port = rule.get('ToPort', 'N/A')
                    
                    if protocol == '-1':
                        port_range = "all ports"
                    elif from_port == to_port:
                        port_range = str(from_port)
                    else:
                        port_range = f"{from_port}-{to_port}"
                    
                    # Destinations
                    destinations = []
                    
                    # IP ranges
                    for ip_range in rule.get('IpRanges', []):
                        cidr = ip_range['CidrIp']
                        desc = ip_range.get('Description', '')
                        if desc:
                            destinations.append(f"{cidr} ({desc})")
                        else:
                            destinations.append(cidr)
                    
                    # Security groups
                    for sg_ref in rule.get('UserIdGroupPairs', []):
                        ref_sg_id = sg_ref['GroupId']
                        ref_desc = sg_ref.get('Description', '')
                        if ref_desc:
                            destinations.append(f"{ref_sg_id} ({ref_desc})")
                        else:
                            destinations.append(ref_sg_id)
                    
                    destinations_str = ", ".join(destinations) if destinations else "no destinations"
                    output += f"  - {protocol} {port_range} to {destinations_str}\n"
            else:
                output += "outbound rules: none\n"
            
            output += "\n"
        
        return output.strip()
    
    def _arun(self, group_id: str = "") -> str:
        return self._run(group_id)
