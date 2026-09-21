from langchain_core.language_models import BaseChatModel
from langchain_aws import ChatBedrockConverse

from .config import AWS_REGION,MODEL_ID,BEDROCK_MAX_TOKENS


def get_chat_model(
    *, 
    temperature: float = 0.0, 
    max_tokens: int | None = None
) -> BaseChatModel:
    """ Return a configured bedrock chat model - could be swapped out for any BaseChatModel """

    return ChatBedrockConverse(
        model=MODEL_ID,
        region_name=AWS_REGION, 
        temperature=temperature, 
        max_tokens= max_tokens or BEDROCK_MAX_TOKENS
    )


if __name__ == "__main__":
    reply = get_chat_model().invoke("Reply with a single word: Ready")
    print(reply)