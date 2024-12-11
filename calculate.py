import tiktoken
from PIL import Image

def calculate_token_cost(prompt, response):
    encoding = tiktoken.get_encoding("cl100k_base")
    encoding = tiktoken.encoding_for_model("gpt-4o-2024-08-06")

    prompt_token = len(encoding.encode(prompt))
    response_token = len(encoding.encode(response))

    prompt_cost = round(prompt_token/1000000*2.5,8)
    response_cost = round(response_token/1000000*10,8)

    return prompt_cost, response_cost


def calculate_image_cost(image_path):
    with Image.open(image_path) as img:
        image_width, image_height = img.size

    PRICE_PER_MILLION_TOKENS = 2.50  # 1M tokens당 $2.50
    TOKENS_PER_TILE = 170
    BASE_TOKENS = 85

    min_side = min(image_width, image_height)
    scaling_factor = 768 / min_side
    resized_width = int(image_width * scaling_factor)
    resized_height = int(image_height * scaling_factor)
    num_tiles_width = (resized_width + 511) // 512
    num_tiles_height = (resized_height + 511) // 512
    total_tiles = num_tiles_width * num_tiles_height

    total_tokens = BASE_TOKENS + total_tiles * TOKENS_PER_TILE
    price_per_token = PRICE_PER_MILLION_TOKENS / 1_000_000
    total_price = round(total_tokens * price_per_token, 8)

    return total_price