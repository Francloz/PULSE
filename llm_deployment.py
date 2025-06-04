import os
os.environ["HF_HUB_TIMEOUT"] = "30"   # 300 seconds per request
os.environ["HF_HOME"] = "G:\\Models"



from airllm import AutoModel

MAX_LENGTH = 128
# could use hugging face model repo id:
# model = AutoModel.from_pretrained("garage-bAInd/Platypus2-70B-instruct")
model = AutoModel.from_pretrained("Qwen/Qwen2.5-72B-Instruct")

# or use model's local path...
# model = AutoModel.from_pretrained("/home/ubuntu/.cache/huggingface/hub/models--garage-bAInd--Platypus2-70B-instruct/snapshots/b585e74bcaae02e52665d9ac6d23f4d0dbc81a0f")

input_text = [
    'What is the capital of United States?',
    # 'I like',
]

input_tokens = model.tokenizer(input_text,
                               return_tensors="pt",
                               return_attention_mask=False,
                               truncation=True,
                               compression='4bit',  # specify '8bit' for 8-bit block-wise quantization
                               max_length=MAX_LENGTH,
                               padding=False)

generation_output = model.generate(
    input_tokens['input_ids'].cuda(),
    max_new_tokens=20,
    use_cache=True,
    return_dict_in_generate=True)

output = model.tokenizer.decode(generation_output.sequences[0])

print(output)