import openai

# 设置 API 密钥
openai.api_key = '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'

# 调用 GPT-3 模型
response = openai.Completion.create(
    engine='text-davinci-003',
    prompt='Once upon a time',
    max_tokens=100
)

# 处理响应结果
generated_text = response['choices'][0]['text']
print(generated_text)
