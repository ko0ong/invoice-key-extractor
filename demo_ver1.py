import streamlit as st
from pyparsing import empty
from datetime import datetime

import openai
import os
import yaml
import requests
from PIL import Image
from io import BytesIO
import base64
import fitz
from image_converter import file_to_base64_image
from prompt import load_prompt
import pandas as pd


auth_path = yaml.safe_load(open('/Users/kong/Desktop/Codes/auth.yml', encoding='utf-8'))
os.environ["OPENAI_API_KEY"] = auth_path['OpenAI']['key']

# img_path = '/Users/kong/Desktop/OCR/01-1.정식개방데이터/Training/01.원천데이터/TS_물류_1.상업송장_INV01/IMG_OCR_6_T_NV_000002.png'
# img = file_to_base64_image(img_path)
# img_name = img_path.split('/')[-1]
# excel_path = 'invoice_inference.xlsx'

client = openai.OpenAI()

prompt_file_path = "prompt.txt"
prompt = load_prompt(prompt_file_path)
prompt_file_path2 = "prompt2.txt"
prompt2 = load_prompt(prompt_file_path2)
prompt_file_path3 = "prompt3.txt"
prompt3 = load_prompt(prompt_file_path3)


st.set_page_config(layout="wide")

# 사이드바 
st.markdown(
    """
    <style>
    [data-testid="stSidebar"] {
        background-color: #f0f0f0;
    }
    </style>
    """,
    unsafe_allow_html=True
)

with st.sidebar:
    st.image('logo.png', width=300)
    st.title('MSBA Capstone Project')
    st.write("")
    st.text_input("API Key를 입력해주세요.")
    st.write("")
    st.write("")
    st.write("")
    st.title('사용법')
    st.write("")
    st.markdown('''
    1. 상업송장 이미지를 업로드해주세요.\n
    2. 추출된 값이 잘못되었다면,<br>"Edit"을 누르고 수정해주세요.\n
    3. 수정을 완료 후,<br>"Save Changes"을 눌러 저장해주세요.<br>재수정도 가능합니다.\n
    4. 정확하게 추출이 되었다면,<br>"Next"을 눌러 출력 단계로 이동하세요.
    ''', unsafe_allow_html=True)

def main():
    st.title('상업송장 요소 추출')
    st.write("")

    st.markdown('''
    ###### 상업송장에서 필요한 정보를 위치에 관계없이 자동으로 추출하는 프로세스를 지원합니다. \n
    ###### 상업송장 이미지를 입력하시면, 값이 구조화된 엑셀 템플릿 또는 엑셀 템플릿에 직접 추가하는 코드를 출력 받을 수 있습니다.
    ''')
    
    st.markdown("<hr style='border: 1.5px solid #4d4d4d; margin-top: 10px; margin-bottom: 50px;'>", unsafe_allow_html=True)

    st.markdown('##### 상업송장 이미지를 업로드 해주세요.')
    img_file = st.file_uploader('pdf, png, jpg, jpeg 형식만 업로드 가능합니다.', type=['pdf', 'png', 'jpg', 'jpeg'])

    table_style = """
    <style>
    thead th {
        text-align: center !important;
        background-color: #f0f0f0;
        font-weight: bold;
    }
    tbody td {
        text-align: center;
    }
    </style>
    """

    if img_file is not None and 'gpt_response' not in st.session_state:
        with st.spinner('분석 요청 중 입니다. 잠시만 기다려주세요.'):
            img = file_to_base64_image(img_file)
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

            st.session_state['gpt_response'] = response.choices[0].message.content
            st.session_state['edit_mode'] = False
            st.session_state['save_mode'] = False
            st.session_state['next_mode'] = False

    if 'gpt_response' in st.session_state:
        st.success('이미지 분석 완료!')

        col1, col2 = st.columns([1, 2])

        with col1:
            st.image(img_file, use_column_width=True)

        with col2:
            generated_code = st.session_state['gpt_response']
            generated_code = generated_code.replace("python\n", "")
            generated_code = generated_code.replace("```", "")
            pd.options.display.float_format = '{:.2f}'.format
            exec(generated_code, globals())

            updated_header_df = header_df.copy()
            updated_inline_df = inline_df.copy()

            if 'updated_header_df' not in st.session_state:
                st.session_state['updated_header_df'] = header_df.copy()

            if 'updated_inline_df' not in st.session_state:
                st.session_state['updated_inline_df'] = inline_df.copy()

            if not st.session_state.edit_mode and not st.session_state.save_mode:
                st.markdown("#### Header Elements")
                if 'header_df' in globals():
                    st.markdown(table_style, unsafe_allow_html=True)  
                    st.table(header_df)
                else:
                    st.error('header_df가 정의되지 않았습니다.')
                
                st.markdown("#### Inline Elements")
                if 'inline_df' in globals():
                    st.markdown(table_style, unsafe_allow_html=True)
                    st.table(inline_df)
                else:
                    st.error('inline_df가 정의되지 않았습니다.')
                
                # st.write('''
                # 혹시 데이터가 잘못 추출되었다면, Edit 버튼을 클릭하여 직접 데이터를 수정해주세요.\n
                # 데이터가 정확하게 추출되었다면, Next 버튼을 클릭하여 다음 단계를 진행해주세요.
                # ''')
                empty1, but1, emtpy2, but2, empty3 = st.columns([0.2, 0.2, 0.2, 0.2, 0.2])
                with but1:
                    if st.button('Edit', key='edit_button'):
                        st.session_state.edit_mode = True

                with but2:
                    if st.button('Next', key='next_button'):
                        st.session_state.next_mode = True

            if st.session_state.edit_mode:
                st.write("수정할 데이터를 입력하세요:")
                for col in header_df.columns:
                    updated_header_df[col][0] = st.text_input(f"Edit {col} (Header)", st.session_state['updated_header_df'][col][0])

                for idx in range(len(inline_df)):
                    for col in inline_df.columns:
                        if inline_df[col].dtype == "object":
                            updated_inline_df.at[idx, col] = st.text_input(f"Edit {col} (row {idx+1})", st.session_state['updated_inline_df'].at[idx, col])
                        else:
                            updated_inline_df.at[idx, col] = st.number_input(f"Edit {col} (row {idx+1})", value=float(st.session_state['updated_inline_df'].at[idx, col]))

                if st.button('Save Changes'):
                    st.session_state.edit_mode = False  
                    st.session_state.save_mode = True 
                    st.session_state['updated_header_df'] = updated_header_df
                    st.session_state['updated_inline_df'] = updated_inline_df
                    st.success("Changes saved successfully!")

            if st.session_state.save_mode:
                st.markdown("<hr style='border: 1px solid #f0f0f0; margin-top: 20px; margin-bottom: px20;'>", unsafe_allow_html=True)
                st.markdown("#### Updated Header Elements")
                st.markdown(table_style, unsafe_allow_html=True)  
                st.table(st.session_state['updated_header_df'])
                st.markdown("#### Updated Inline Elements")
                st.markdown(table_style, unsafe_allow_html=True)  
                st.table(st.session_state['updated_inline_df'])
                
                st.markdown("<hr style='border: 1px solid #f0f0f0; margin-top: 20px; margin-bottom: px20;'>", unsafe_allow_html=True)
                st.markdown("#### Original Header Elements")
                st.markdown(table_style, unsafe_allow_html=True)  
                st.table(header_df)
                st.markdown("#### Original Inline Elements")
                st.markdown(table_style, unsafe_allow_html=True)  
                st.table(inline_df)
                st.markdown("<hr style='border: 1px solid #f0f0f0; margin-top: 20px; margin-bottom: px20;'>", unsafe_allow_html=True)
                
                empty1, but1, emtpy2, but2, empty3 = st.columns([0.2, 0.2, 0.2, 0.2, 0.2])
                with but1:
                    if st.button('Edit', key='edit_button_after_save'):
                        st.session_state.edit_mode = True
                        st.session_state.save_mode = False  

                with but2:
                    if st.button('Next', key='next_button_after_save'):
                        st.session_state.next_mode = True    
                    

if __name__ == "__main__":
    main()
