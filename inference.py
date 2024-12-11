import openai
import os
import yaml
from PIL import Image
from io import BytesIO
import base64
import fitz
import pandas as pd
import glob
import natsort
from datetime import datetime
import tiktoken
import argparse
from calculate import calculate_token_cost, calculate_image_cost
from prompt import load_prompt
from image_converter import encode_image, file_to_base64_image


def main(glob_path, max_images, extract_csv_path, cost_csv_path):
    auth_path = yaml.safe_load(open('auth.yml', encoding='utf-8'))

    prompt_file_path = "prompt_edit.txt"
    prompt = load_prompt(prompt_file_path)
    prompt_file_path2 = "prompt2_edit.txt"
    prompt2 = load_prompt(prompt_file_path2)

    os.environ["OPENAI_API_KEY"] = auth_path['OpenAI']['key']
    client = openai.OpenAI()

    img_list = natsort.natsorted(glob.glob(glob_path))[:max_images]
    extract_df = pd.DataFrame()
    cost_df = pd.DataFrame()

    for idx, img_path in enumerate(img_list[55:]):
        client = openai.OpenAI()
        img = file_to_base64_image(img_path)

        start_time = datetime.now()
        messages_list = [
                {"role": "system", "content": prompt},
                {"role": "user", "content": [
                    {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{img}"}}
                ]}
            ]
        response = client.chat.completions.create(
            model='gpt-4o-2024-08-06',
            messages=messages_list
        )
        first_response = response.choices[0].message.content        
        messages_list.append({
            "role": "assistant",
            "content": first_response + prompt2
        })         
        response = client.chat.completions.create(
            model='gpt-4o-2024-08-06',
            messages=messages_list
        )
        end_time = datetime.now()
        elapsed_time = (end_time - start_time).total_seconds()

        generated_code = response.choices[0].message.content
        generated_code = generated_code.replace("python\n", "").replace("```", "")
        exec(generated_code, globals())

        if 'header_df' in globals() and 'inline_df' in globals():
            header_df.insert(0, 'img path', img_path)
            header_expanded_df = pd.concat([header_df] * len(inline_df), ignore_index=True)
            merge_df = pd.concat([header_expanded_df, inline_df], axis=1)
            extract_df = pd.concat([extract_df, merge_df])
            
            prompt_cost, response_cost = calculate_token_cost(prompt, first_response)
            prompt_cost2, response_cost2 = calculate_token_cost(prompt2, generated_code)
            image_cost = calculate_image_cost(img_path)
            
            cost_dict = {
                'img path': img_path,
                'cost': (prompt_cost*1330 + response_cost*1330 + prompt_cost2*1330 + response_cost2*1330 + image_cost*1330),
                'time': elapsed_time
            }
            cost_merge_df = pd.DataFrame([cost_dict])
            cost_df = pd.concat([cost_df, cost_merge_df], ignore_index=True)
            
        else:
            print(f"header_df 또는 inline_df가 제대로 생성되지 않았습니다: 이미지 {img_path} index {idx}")
            continue  
    
    extract_df.to_csv(extract_csv_path)
    cost_df.to_csv(cost_csv_path)
    print(f"Extracted data saved to {extract_csv_path}")
    print(f"Cost data saved to {cost_csv_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process images and calculate costs")
    parser.add_argument("--glob_path", type=str, required=True, 
                        help="Glob pattern to specify image files, e.g., '/path/to/images/*.png'")
    parser.add_argument("--max_images", type=int, default=100, 
                        help="Maximum number of images to process (default: 100)")
    parser.add_argument("--extract_csv_path", type=str, required=True, 
                        help="Path to save the extracted data CSV file")
    parser.add_argument("--cost_csv_path", type=str, required=True, 
                        help="Path to save the cost data CSV file")
    args = parser.parse_args()

    main(args.glob_path, args.max_images, args.extract_csv_path, args.cost_csv_path)


#  python script.py --glob_path '/Users/kong/Desktop/OCR/*.png' --max_images 50 --extract_csv_path 'extracted_data.csv' --cost_csv_path 'cost_data.csv'