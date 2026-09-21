import os


os.environ["AWS_PROFILE"] = ""
os.environ["AWS_REGION"] = "us-east-1"
os.environ["BEDROCK_MODEL_ID"] = "test-model"
os.environ["BEDROCK_GUARDRAIL_ID"] = "test-guardrail"
os.environ["BEDROCK_GUARDRAIL_VERSION"] = "1"
os.environ["BEDROCK_KNOWLEDGE_BASE_ID"] = ""
os.environ["BEDROCK_KB_TYPE"] = ""
os.environ["BEDROCK_EMBED_MODEL_ID"] = "test-embedding-model"