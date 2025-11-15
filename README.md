# AWS Chatterbot

Chatter to you AWS account about your resources and permissions.

## Setup

install packages:
```bash
pip install langchain-core langchain-anthropic boto3 pydantic
```

set api key:
```bash
export ANTHROPIC_API_KEY='your-key-here'
```

configure aws:
```bash
aws configure
```

## Run

```bash
python chatbot.py
```

or

```bash
python3 chatbot.py
```

## Examples

```
question: how many s3 buckets do i have
question: which buckets are public
question: whats in bucket my-bucket
question: what size is ec2 at ip 10.0.1.5
question: what permissions does user bob have
```

## TODO

- [ ] add more aws services (lambda, rds, etc)
- [ ] ec2 locate by name or tags
- [ ] save chat history to file
- [ ] add region support
- [ ] better error messages
