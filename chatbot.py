import os
from langchain_anthropic import ChatAnthropic


from tools.s3_tool import S3Tool
from tools.ec2_tool import GetEC2InstanceSizeTool
from tools.iam_tool import GetIAMUserPermissionsTool
from tools.security_group_tool import GetSecurityGroupInfoTool


# function to ask claude
def ask_claude(question, tools, history=[]):
    """asks claude and lets it use tools"""
    

    llm = ChatAnthropic(
        model="claude-sonnet-4-20250514",
        temperature=0
    )
    

    tool_descriptions = []
    for tool in tools:
        tool_descriptions.append(f"- {tool.name}: {tool.description}")
    
    tools_text = "\n".join(tool_descriptions)
    

    prompt = f"""you are an ai that answers aws questions. you can use tools.

tools:
{tools_text}

to use a tool say:
TOOL: tool_name
INPUT: the input

for s3_tool leave INPUT blank for all buckets or put bucket name for specific bucket.

history:
{history}

question: {question}

think step by step."""
    
    # call claude
    response = llm.invoke(prompt)
    answer = response.content
    

    if "TOOL:" in answer and "INPUT:" in answer:
        lines = answer.split('\n')
        
        tool_name = None
        tool_input = None
        
        for line in lines:
            if line.startswith('TOOL:'):
                tool_name = line.replace('TOOL:', '').strip()
            if line.startswith('INPUT:'):
                tool_input = line.replace('INPUT:', '').strip()
        

        selected_tool = None
        for t in tools:
            if t.name == tool_name:
                selected_tool = t
                break
        

        if selected_tool:
            try:
                if tool_input and tool_input != '':
                    result = selected_tool._run(tool_input)
                else:
                    result = selected_tool._run()
                
                # ask claude again
                follow_up = f"""tool result:
{result}

original question: {question}

answer based on tool result."""
                
                final = llm.invoke(follow_up)
                return final.content
                
            except Exception as e:
                return f"tool error: {e}"
    
    return answer



def main():
    
    print("=" * 60)
    print("AWS Chatbot")
    print("=" * 60)
    print()
    

    if not os.getenv('ANTHROPIC_API_KEY'):
        print("ERROR: set ANTHROPIC_API_KEY")
        print("do: export ANTHROPIC_API_KEY='your-key'")
        return
    
    print("loading tools...")
    

    tools = [
        S3Tool(),
        GetEC2InstanceSizeTool(),
        GetIAMUserPermissionsTool(),
        GetSecurityGroupInfoTool()
    ]
    
    print(f"loaded {len(tools)} tools")
    print("ready")
    print()
    print("examples:")
    print("- how many s3 buckets do i have")
    print("- which buckets are public")
    print("- whats in bucket my-bucket")
    print("- what size is ec2 at ip 10.0.1.5")
    print("- what permissions does user bob have")
    print("- show me security group sg-12345")
    print("- list all security groups")
    print()
    print("type quit to exit")
    print()
    print("=" * 60)
    print()
    

    history = []
    
    
    while True:
        
        try:
            question = input("question: ")
        except KeyboardInterrupt:
            print("\nbye")
            break
        
        question = question.strip()
        
        if question.lower() in ['quit', 'exit', 'q']:
            print("bye")
            break
        
        if question == '':
            continue
        
        print()
        
        try:
            answer = ask_claude(question, tools, history)
            print(answer)
            
            history.append(f"Q: {question}\nA: {answer}")
            
        except Exception as e:
            print(f"error: {e}")
        
        print()
        print("=" * 60)
        print()


if __name__ == "__main__":
    main()
