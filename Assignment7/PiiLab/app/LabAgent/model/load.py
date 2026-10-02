from langchain_aws import ChatBedrockConverse
MODEL_ID = "deepseek.v3.2"


def load_model() -> ChatBedrockConverse:
    """Get Bedrock model client using IAM credentials."""
    return ChatBedrockConverse(model=MODEL_ID, region_name="us-east-1", temperature=0)


