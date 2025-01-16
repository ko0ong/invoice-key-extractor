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

prompt_file_path = "prompt.txt"
prompt = load_prompt(prompt_file_path)
prompt_file_path2 = "prompt2.txt"
prompt2 = load_prompt(prompt_file_path2)

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
    st.write("")
    st.markdown('''
        <div style="text-align: center;">
            <h1>MSBA Capstone Project</h1>
            비전 언어 모델을 활용한<br>
            문서 이미지의 구조화 프로세스 구축
        </div>
    ''', unsafe_allow_html=True)

    st.write("")
    st.write("")
    st.markdown('# API Key 입력', unsafe_allow_html=True)
    my_api = st.text_input("API Key를 입력하고 Enter를 눌러주세요.", type="password")
    my_api = my_api.strip()

    st.write("")
    st.write("")
    st.markdown('# 사용법', unsafe_allow_html=True)
    st.markdown('''
    1. 상업송장 이미지를 업로드해주세요.<br>pdf, png, jpg, jpeg 형식만 가능합니다.\n
    2. 첫 번째 탭에서 모든 문서로부터 추출한<br>값을 병합한 결과를 바로 확인하고<br>다운로드할 수 있습니다.\n
    3. 추출된 값이 잘못되었다면,<br>개별 탭에서 "Edit"을 눌러 수정해주세요.\n
    4. 수정 완료 후,<br>"Save Changes"을 눌러 저장해주세요.\n
    5. 개별 문서도 다운로드 가능합니다.
    6. 첫 번째 탭으로 돌아와서<br>"Update"를 누른 후에 다운로드 하세요.\n
    ''', unsafe_allow_html=True)
  

def main():
    st.title("📝 Commercial Invoice Key Extractor")
    st.write("")

    st.markdown('''
    ##### 상업송장에서 필요한 정보를 위치에 관계없이 자동으로 추출하는 프로세스를 지원합니다. \n
    ##### 상업송장 문서 이미지를 입력하시면, 값이 구조화된 엑셀 템플릿을 다운로드할 수 있습니다.
    ''')

    os.environ["OPENAI_API_KEY"] = st.secrets['OPENAI_API_KEY']
    client = openai.OpenAI()

    def extract_elements(img):
        messages_list = [
            {"role": "system", "content": prompt},
            {"role": "user", "content": [
                {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{img}"}}
            ]}
        ]
        response = client.chat.completions.create(
            model='gpt-4o-2024-11-20',
            messages=messages_list
        )
        return response.choices[0].message.content

    def structured_elements(first_response):   
        messages_list = [
            {"role": "system", "content": prompt2},
            {"role": "user", "content": first_response}        
        ]
        response = client.chat.completions.create(
            model='gpt-4o-2024-11-20',
            messages=messages_list
        )
        return response.choices[0].message.content

    # if my_api:
    #     if not my_api.startswith("sk-"):
    #         st.error("API Key는 'sk-'로 시작해야 합니다. 올바른 API Key를 입력해주세요.")
    #         return
    #     os.environ["OPENAI_API_KEY"] = st.secrets['OPENAI_API_KEY']
    #     client = openai.OpenAI()

    #     def extract_elements(img):
    #         messages_list = [
    #             {"role": "system", "content": prompt},
    #             {"role": "user", "content": [
    #                 {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{img}"}}
    #             ]}
    #         ]
    #         response = client.chat.completions.create(
    #             model='gpt-4o-2024-11-20',
    #             messages=messages_list
    #         )
    #         return response.choices[0].message.content

    #     def structured_elements(first_response):   
    #         messages_list = [
    #             {"role": "system", "content": prompt2},
    #             {"role": "user", "content": first_response}        
    #         ]
    #         response = client.chat.completions.create(
    #             model='gpt-4o-2024-11-20',
    #             messages=messages_list
    #         )
    #         return response.choices[0].message.content

    # else:
    #     st.info("왼쪽에 있는 사이드 바에 API Key를 입력하고 Enter를 눌러주세요.")
    #     return

    st.markdown("<hr style='border: 1.5px solid #4d4d4d; margin-top: 10px; margin-bottom: 50px;'>", unsafe_allow_html=True)
    st.markdown('##### 상업송장 문서 이미지를 업로드 해주세요.')

    img_files = st.file_uploader('pdf, png, jpg, jpeg 형식만 업로드 가능합니다.', type=['pdf', 'png', 'jpg', 'jpeg'], accept_multiple_files=True)

    with st.spinner("요소를 추출하고 있습니다. 잠시만 기다려주세요..."):
        if img_files:
            tabs = st.tabs(["All Documents"] + [f"Document {i+1}" for i in range(len(img_files))])

            if 'all_headers' not in st.session_state:
                st.session_state['all_headers'] = []
            if 'all_inlines' not in st.session_state:
                st.session_state['all_inlines'] = []
            if 'data_changed' not in st.session_state:
                st.session_state['data_changed'] = False

            for i, img_file in enumerate(img_files, start=1):
                with tabs[i]:
                    st.subheader(f"Document {i}: {img_file.name}")

                    if f'gpt_response_{i}' not in st.session_state:
                        with st.spinner('요소를 추출하고 있습니다. 잠시만 기다려주세요...'):
                            img = file_to_base64_image(img_file)
                            first_response = extract_elements(img)
                            if "정보가 제공되지 않다면," in first_response:
                                st.error("손상된 파일을 입력하였습니다. 입력한 이미지 파일을 확인해주세요.")
                                st.stop()  

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
    
                                loc = {}
                                exec(generated_code, globals(), loc)

                                header_df = loc['header_df']
                                inline_df = loc['inline_df']

                                if f'updated_header_df_{i}' not in st.session_state:
                                    st.session_state[f'updated_header_df_{i}'] = header_df.copy()
                                if f'updated_inline_df_{i}' not in st.session_state:
                                    st.session_state[f'updated_inline_df_{i}'] = inline_df.copy()

                                if not st.session_state[f'edit_mode_{i}'] and not st.session_state[f'save_mode_{i}'] and not st.session_state[f'next_mode_{i}']:
                                    st.markdown("#### Header Elements")
                                    st.markdown(table_style, unsafe_allow_html=True)
                                    st.table(header_df)
                                    
                                    st.markdown("#### Inline Elements")
                                    st.markdown(table_style, unsafe_allow_html=True)
                                    st.table(inline_df)

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

                                # Edit 모드
                                if st.session_state[f'edit_mode_{i}'] and not st.session_state[f'next_mode_{i}']:
                                    st.write("수정할 데이터를 입력하세요:")

                                    st.session_state[f'updated_header_df_{i}']['Invoice Number'][0] = st.text_input(f"Invoice Number (Header)", st.session_state[f'updated_header_df_{i}']['Invoice Number'][0])
                                    st.session_state[f'updated_header_df_{i}']['Invoice Date'][0] = st.text_input(f"Invoice Date (Header)", st.session_state[f'updated_header_df_{i}']['Invoice Date'][0])
                                    st.session_state[f'updated_header_df_{i}']['Sender Name'][0] = st.text_input(f"Sender Name (Header)", st.session_state[f'updated_header_df_{i}']['Sender Name'][0])
                                    st.session_state[f'updated_header_df_{i}']['Invoice Amount'][0] = st.text_input(f"Invoice Amount (Header)", st.session_state[f'updated_header_df_{i}']['Invoice Amount'][0])
                                    st.session_state[f'updated_header_df_{i}']['Currency Code'][0] = st.text_input(f"Currency Code (Header)", st.session_state[f'updated_header_df_{i}']['Currency Code'][0])

                                    for idx in range(len(st.session_state[f'updated_inline_df_{i}'])):
                                        st.session_state[f'updated_inline_df_{i}'].at[idx, 'Product'] = st.text_input(f"Product (row {idx})", st.session_state[f'updated_inline_df_{i}'].at[idx, 'Product'])
                                        st.session_state[f'updated_inline_df_{i}'].at[idx, 'Unit Quantity'] = st.text_input(f"Unit Quantity (row {idx})", st.session_state[f'updated_inline_df_{i}'].at[idx, 'Unit Quantity'])
                                        st.session_state[f'updated_inline_df_{i}'].at[idx, 'Unit'] = st.text_input(f"Unit (row {idx})", st.session_state[f'updated_inline_df_{i}'].at[idx, 'Unit'])
                                        st.session_state[f'updated_inline_df_{i}'].at[idx, 'Unit Price'] = st.text_input(f"Unit Price (row {idx})", st.session_state[f'updated_inline_df_{i}'].at[idx, 'Unit Price'])
                                        st.session_state[f'updated_inline_df_{i}'].at[idx, 'HS Code'] = st.text_input(f"HS Code (row {idx})", st.session_state[f'updated_inline_df_{i}'].at[idx, 'HS Code'])
                                        st.session_state[f'updated_inline_df_{i}'].at[idx, 'Total Amount'] = st.text_input(f"Total Amount (row {idx})", st.session_state[f'updated_inline_df_{i}'].at[idx, 'Total Amount'])

                                    if st.button('Save Changes', key=f'save_button_{i}'):
                                        st.session_state[f'edit_mode_{i}'] = False  
                                        st.session_state[f'save_mode_{i}'] = True
                                        st.session_state['data_changed'] = True
                                        st.success("Changes saved successfully!")
                                

                                if st.session_state[f'save_mode_{i}']:
                                    st.markdown("#### Updated Header Elements")
                                    st.markdown(table_style, unsafe_allow_html=True)  
                                    st.table(st.session_state[f'updated_header_df_{i}'])
                                    st.markdown("#### Updated Inline Elements")
                                    st.markdown(table_style, unsafe_allow_html=True)  
                                    st.table(st.session_state[f'updated_inline_df_{i}'])
                                    
                                    st.markdown("#### Original Header Elements")
                                    st.markdown(table_style, unsafe_allow_html=True)  
                                    st.table(header_df)
                                    st.markdown("#### Original Inline Elements")
                                    st.markdown(table_style, unsafe_allow_html=True)  
                                    st.table(inline_df)
                                    
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
                            updated_header_df = st.session_state[f'updated_header_df_{i}']
                            updated_inline_df = st.session_state[f'updated_inline_df_{i}']
                            repeated_header_df = pd.concat([updated_header_df] * len(updated_inline_df), ignore_index=True)
                            merged_df = pd.concat([repeated_header_df, updated_inline_df], axis=1)

                            st.markdown("#### Single Document Output Preview")
                            st.table(merged_df)

                            output = io.BytesIO()
                            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                                merged_df.to_excel(writer, index=False, sheet_name='single')
                            xlsx_data = output.getvalue()
                            csv_data = merged_df.to_csv(index=False).encode('utf-8')

                            empty1, but1, empty2, but2, empty3 = st.columns([2, 1, 1, 1, 2])
                            with but1:
                                st.download_button(
                                    label="Download Excel",
                                    data=xlsx_data,
                                    file_name=f"single_document_output_{i}.xlsx",
                                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                                )
                            with but2:
                                st.download_button(
                                    label="Download CSV",
                                    data=csv_data,
                                    file_name=f"single_document_output_{i}.csv",
                                    mime="text/csv"
                                    )

                    if f'updated_header_df_{i}' in st.session_state and f'updated_inline_df_{i}' in st.session_state:
                        while len(st.session_state['all_headers']) < len(img_files):
                            st.session_state['all_headers'].append(None)
                        while len(st.session_state['all_inlines']) < len(img_files):
                            st.session_state['all_inlines'].append(None)
                        st.session_state['all_headers'][i-1] = st.session_state[f'updated_header_df_{i}']
                        st.session_state['all_inlines'][i-1] = st.session_state[f'updated_inline_df_{i}']

            with tabs[0]:
                all_processed = (len(st.session_state['all_headers']) == len(img_files) and 
                                len(st.session_state['all_inlines']) == len(img_files) and
                                all(h is not None for h in st.session_state['all_headers']) and
                                all(i is not None for i in st.session_state['all_inlines']))

                if all_processed:
                    # if st.session_state['data_changed']:
                    #     st.warning("수정된 사항이 있습니다. 업데이트 하시겠습니까?")
                    #     if st.button("Update"):
                    #         st.session_state['data_changed'] = False

                    merged_all = []
                    for hdf, idf in zip(st.session_state['all_headers'], st.session_state['all_inlines']):
                        repeated_header_df = pd.concat([hdf]*len(idf), ignore_index=True)
                        merged_df = pd.concat([repeated_header_df, idf], axis=1)
                        merged_all.append(merged_df)
                    final_merged = pd.concat(merged_all, ignore_index=True)

                    st.markdown("#### All Documents Output Preview")
                    st.table(final_merged)

                    output = io.BytesIO()
                    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                        final_merged.to_excel(writer, index=False, sheet_name='All')
                    xlsx_data = output.getvalue()
                    csv_data = final_merged.to_csv(index=False).encode('utf-8')

                    empty4, but3, empty5, but4, empty6 = st.columns([2, 1, 1, 1, 2])
                    with but3:
                        st.download_button(
                            label="Download Excel",
                            data=xlsx_data,
                            file_name="all_documents_output.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                        )
                    with but4:
                        st.download_button(
                            label="Download CSV",
                            data=csv_data,
                            file_name="all_documents_output.csv",
                            mime="text/csv"
                        )

if __name__ == "__main__":
    main()
