import streamlit as st
from pyparsing import empty
from datetime import datetime

import openai
import io
import fitz
import os
import yaml
from PIL import Image
from io import BytesIO
import base64
from image_converter import file_to_base64_image, encode_image
from prompt import load_prompt
import pandas as pd


auth_path = yaml.safe_load(open('/Users/kong/Desktop/Codes/auth.yml', encoding='utf-8'))
os.environ["OPENAI_API_KEY"] = auth_path['OpenAI']['key']
client = openai.OpenAI()

prompt_file_path = "prompt.txt"
prompt = load_prompt(prompt_file_path)
prompt_file_path2 = "prompt2.txt"
prompt2 = load_prompt(prompt_file_path2)

def extract_elements(img):
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
    return response.choices[0].message.content

def structured_elements(first_response):   
    messages_list = [
        {"role": "system", "content": prompt2},
        {"role": "user", "content": first_response}        
    ]
    response = client.chat.completions.create(
        model='gpt-4o-2024-08-06',
        messages=messages_list
    )
    return response.choices[0].message.content

st.set_page_config(page_title="Invoice Key Extractor", page_icon="📝", layout="wide")
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
    1. 상업송장 이미지를 업로드해주세요.<br>pdf, png, jpg, jpeg 형식만 가능합니다.\n
    2. 추출된 값이 잘못되었다면,<br>"Edit"을 누르고 수정해주세요.\n
    3. 수정을 완료 후,<br>"Save Changes"을 눌러 저장해주세요.<br>재수정도 가능합니다.\n
    4. 정확하게 추출이 되었다면,<br>"Download"를 눌러<br>출력 단계로 이동하세요.
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
    
    img_files = st.file_uploader('pdf, png, jpg, jpeg 형식만 업로드 가능합니다.', type=['pdf', 'png', 'jpg', 'jpeg'], accept_multiple_files=True)

    if img_files:
        tabs = st.tabs([f"Document {i+1}" for i in range(len(img_files))])
        for i, img_file in enumerate(img_files):
            with tabs[i]:
                st.subheader(f"Document {i+1}: {img_file.name}")

                if f'gpt_response_{i}' not in st.session_state:
                    with st.spinner('분석 요청 중 입니다. 잠시만 기다려주세요.'):
                        img = file_to_base64_image(img_file)
                        first_response = extract_elements(img)
                        structured_code = structured_elements(first_response)

                        st.session_state[f'gpt_response_{i}'] = structured_code
                        st.session_state[f'edit_mode_{i}'] = False
                        st.session_state[f'save_mode_{i}'] = False
                        st.session_state[f'next_mode_{i}'] = False
                
                if f'gpt_response_{i}' in st.session_state:
                    st.success('이미지 분석 완료!')

                col1, col2 = st.columns([1, 2])
                with col1:
                    st.image(img_file, use_column_width=True)

                with col2:
                    if f'gpt_response_{i}' in st.session_state:
                        generated_code = st.session_state[f'gpt_response_{i}']
                        generated_code = generated_code.replace("python\n", "").replace("```", "")
                        exec(generated_code, globals())

                        updated_header_df = header_df.copy()
                        updated_inline_df = inline_df.copy()

                        if f'updated_header_df_{i}' not in st.session_state:
                            st.session_state[f'updated_header_df_{i}'] = header_df.copy()
                        if f'updated_inline_df_{i}' not in st.session_state:
                            st.session_state[f'updated_inline_df_{i}'] = inline_df.copy()

                        if not st.session_state[f'edit_mode_{i}'] and not st.session_state[f'save_mode_{i}']:
                            st.markdown("#### Header Elements")
                            st.markdown(table_style, unsafe_allow_html=True)
                            if 'header_df' in globals():
                                st.table(header_df)
                            else:
                                st.error('header_df가 정의되지 않았습니다.')
                            
                            st.markdown("#### Inline Elements")
                            st.markdown(table_style, unsafe_allow_html=True)
                            if 'inline_df' in globals():
                                st.table(inline_df)
                            else:
                                st.error('inline_df가 정의되지 않았습니다.')
                            
                            empty1, but1, emtpy2, but2, empty3 = st.columns([2, 1, 1, 1, 2])
                            with but1:
                                if st.button('Edit', key=f'edit_button_{i}'):
                                    st.session_state[f'edit_mode_{i}'] = True
                                    st.session_state[f'save_mode_{i}'] = False
                                    st.session_state[f'next_mode_{i}'] = False 

                            with but2:
                                if st.button('Download', key=f'next_button_{i}'):
                                    st.session_state[f'next_mode_{i}'] = True
                                    st.session_state[f'edit_mode_{i}'] = False

                    if f'updated_header_df_{i}' not in st.session_state:
                        st.session_state[f'updated_header_df_{i}'] = updated_header_df.copy()
                    if f'updated_inline_df_{i}' not in st.session_state:
                        st.session_state[f'updated_inline_df_{i}'] = updated_inline_df.copy()

                    if st.session_state[f'edit_mode_{i}'] and not st.session_state[f'next_mode_{i}']:
                        st.write("수정할 데이터를 입력하세요:")

                        st.session_state[f'updated_header_df_{i}']['Invoice Number'][0] = st.text_input(f"Invoice Number (Header)", st.session_state[f'updated_header_df_{i}']['Invoice Number'][0])
                        st.session_state[f'updated_header_df_{i}']['Invoice Date'][0] = st.text_input(f"Invoice Date (Header)", st.session_state[f'updated_header_df_{i}']['Invoice Date'][0])
                        st.session_state[f'updated_header_df_{i}']['Sender Name'][0] = st.text_input(f"Sender Name (Header)", st.session_state[f'updated_header_df_{i}']['Sender Name'][0])
                        st.session_state[f'updated_header_df_{i}']['Invoice Amount'][0] = st.text_input(f"Invoice Amount (Header)", st.session_state[f'updated_header_df_{i}']['Invoice Amount'][0])
                        st.session_state[f'updated_header_df_{i}']['Currency Code'][0] = st.text_input(f"Currency Code (Header)", st.session_state[f'updated_header_df_{i}']['Currency Code'][0])

                        for idx in range(len(updated_inline_df)):
                            st.session_state[f'updated_inline_df_{i}'].at[idx, 'Product'] = st.text_input(f"Product (row {idx+1})", st.session_state[f'updated_inline_df_{i}'].at[idx, 'Product'])
                            st.session_state[f'updated_inline_df_{i}'].at[idx, 'Unit Quantity'] = st.text_input(f"Unit Quantity (row {idx+1})", st.session_state[f'updated_inline_df_{i}'].at[idx, 'Unit Quantity'])
                            st.session_state[f'updated_inline_df_{i}'].at[idx, 'Unit'] = st.text_input(f"Unit (row {idx+1})", st.session_state[f'updated_inline_df_{i}'].at[idx, 'Unit'])
                            st.session_state[f'updated_inline_df_{i}'].at[idx, 'Unit Price'] = st.text_input(f"Unit Price (row {idx+1})", st.session_state[f'updated_inline_df_{i}'].at[idx, 'Unit Price'])
                            st.session_state[f'updated_inline_df_{i}'].at[idx, 'HS Code'] = st.text_input(f"HS Code (row {idx+1})", st.session_state[f'updated_inline_df_{i}'].at[idx, 'HS Code'])
                            st.session_state[f'updated_inline_df_{i}'].at[idx, 'Total Amount'] = st.text_input(f"Total Amount (row {idx+1})", st.session_state[f'updated_inline_df_{i}'].at[idx, 'Total Amount'])

                        if st.button('Save Changes', key=f'save_button_{i}'):
                            st.session_state[f'edit_mode_{i}'] = False  
                            st.session_state[f'save_mode_{i}'] = True
                            st.success("Changes saved successfully!")
                    
                    if st.session_state[f'save_mode_{i}']:
                        st.markdown("<hr style='border: 1px solid #f0f0f0; margin-top: 20px; margin-bottom: px20;'>", unsafe_allow_html=True)
                        st.markdown("#### Updated Header Elements")
                        st.markdown(table_style, unsafe_allow_html=True)  
                        st.table(st.session_state[f'updated_header_df_{i}'])
                        st.markdown("#### Updated Inline Elements")
                        st.markdown(table_style, unsafe_allow_html=True)  
                        st.table(st.session_state[f'updated_inline_df_{i}'])
                        
                        st.markdown("<hr style='border: 1px solid #f0f0f0; margin-top: 20px; margin-bottom: px20;'>", unsafe_allow_html=True)
                        st.markdown("#### Original Header Elements")
                        st.markdown(table_style, unsafe_allow_html=True)  
                        st.table(header_df)
                        st.markdown("#### Original Inline Elements")
                        st.markdown(table_style, unsafe_allow_html=True)  
                        st.table(inline_df)
                        st.markdown("<hr style='border: 1px solid #f0f0f0; margin-top: 20px; margin-bottom: px20;'>", unsafe_allow_html=True)
                        
                        empty1, but1, emtpy2, but2, empty3 = st.columns([2, 1, 1, 1, 2])
                        with but1:
                            if st.button('Edit', key=f'edit_button_after_save_{i}'):
                                st.session_state[f'edit_mode_{i}'] = True
                                st.session_state[f'save_mode_{i}'] = False
                                st.session_state[f'next_mode_{i}'] = False  

                        with but2:
                            if st.button('Download', key=f'next_button_after_save_{i}'):
                                st.session_state[f'next_mode_{i}'] = True
                                st.session_state[f'edit_mode_{i}'] = False          

                if st.session_state[f'next_mode_{i}'] and not st.session_state[f'edit_mode_{i}']:
                    repeated_header_df = pd.concat([st.session_state[f'updated_header_df_{i}']] * len(st.session_state[f'updated_inline_df_{i}']), ignore_index=True)
                    merged_df = pd.concat([repeated_header_df, st.session_state[f'updated_inline_df_{i}']], axis=1)

                    st.markdown("#### Final Output Preview")
                    st.table(merged_df)

                    output = io.BytesIO()
                    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                        merged_df.to_excel(writer, index=False, sheet_name='Final Output')
                    xlsx_data = output.getvalue()
                    csv_data = merged_df.to_csv(index=False).encode('utf-8')

                    empty1, but1, empty2, but2, empty3 = st.columns([2, 1, 1, 1, 2])
                    with but1:
                        st.download_button(
                            label="Download Excel",
                            data=xlsx_data,
                            file_name=f"final_output_{i+1}.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                        )
                    with but2:
                        st.download_button(
                            label="Download CSV",
                            data=csv_data,
                            file_name=f"final_output_{i+1}.csv",
                            mime="text/csv"
                        )

if __name__ == "__main__":
    main()
