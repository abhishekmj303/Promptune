from h2ogpte import H2OGPTE
from dotenv import dotenv_values

# Load environment variables
config = dotenv_values('.env')

client = H2OGPTE(
    address='https://playground.h2ogpte.h2o.ai',
    api_key=config['H20_GPT_KEY'],
)

# Chat with LLM without a collection
chat_session_id = client.create_chat_session()
