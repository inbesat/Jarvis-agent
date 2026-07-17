from openai import OpenAI

# Connect to your local LM Studio server
client = OpenAI(base_url="http://localhost:1234/v1", api_key="lm-studio")

response = client.chat.completions.create(
  model="local-model", # LM Studio automatically uses whatever model you have loaded
  messages=[{"role": "user", "content": "Hello! Are you ready to be my Jarvis?"}]
)

print(response.choices[0].message.content)