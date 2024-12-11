import pandas as pd
from evaluate import load

def main():
    pre_df = pd.read_csv('elements.csv', index_col=0, encoding='cp949')
    pre_df['img path'] = pre_df['img path'].apply(lambda x: x.split('/')[-1])
    pre_df = pre_df.drop(columns='Unit')
    pre_df['Unit Price'] = pre_df['Unit Price'].astype('str')
    pre_df['Unit Quantity'] = pre_df['Unit Quantity'].astype('str')
    pre_df['HS Code'] = pre_df['HS Code'].astype('str')
    pre_df.loc[pre_df['HS Code']=='nan', 'HS Code'] = '-'
    pre_df['Invoice Date'] = pre_df['Invoice Date'].astype('str')
    pre_df['Invoice Date'] = pre_df['Invoice Date'].apply(lambda x: x.replace('.', '-'))

    def convert_date_format(date_str):
        try:
            parts = date_str.split('-')
            if len(parts) == 3:
                year, month, day = parts
                month = month.zfill(2)
                day = day.zfill(2)
                return f"{year}-{month}-{day}"
            else:
                return None
        except Exception as e:
            return None

    pre_df['Invoice Date'] = pre_df['Invoice Date'].apply(convert_date_format)

    pre_df['Invoice Amount'] = pre_df['Invoice Amount'].apply(lambda x: x.split('.')[0][:-3]+','+x.split('.')[0][-3:]+'.'+x.split('.')[1] if (len(x.split('.')[0]) >= 4) and ',' not in x else x)
    pre_df['Unit Price'] = pre_df['Unit Price'].apply(lambda x: x.split('.')[0][:-3]+','+x.split('.')[0][-3:]+'.'+x.split('.')[1] if (len(x.split('.')[0]) >= 4) and ',' not in x else x)
    pre_df['Total Amount'] = pre_df['Total Amount'].apply(lambda x: x.split('.')[0][:-3]+','+x.split('.')[0][-3:]+'.'+x.split('.')[1] if (len(x.split('.')[0]) >= 4) and ',' not in x else x)
    pre_df['HS Code'] = pre_df['HS Code'].apply(lambda x: x+'0' if (len(x.split('.')[-1])==1) & ('-' not in x) else x)
    pre_df['HS Code'] = pre_df['HS Code'].apply(lambda x: '0'+x if len(x.split('.')[0])==3 else x)
    pre_df['HS Code'] = pre_df['HS Code'].apply(lambda x: '00'+x if len(x.split('.')[0])==2 else x)
    pre_df['Invoice Amount'] = pre_df['Invoice Amount'].apply(lambda x: x+'0' if len(x.split('.')[-1])==1 else x)
    pre_df['Unit Price'] = pre_df['Unit Price'].apply(lambda x: x+'0' if len(x.split('.')[-1])==1 else x)
    pre_df['Total Amount'] = pre_df['Total Amount'].apply(lambda x: x+'0' if len(x.split('.')[-1])==1 else x)
    pre_df = pre_df.rename(columns={'img path':'IMG_ID'})
    pre_df['Sender Name'] = pre_df['Sender Name'].apply(lambda x: x.strip())
    pre_df['Product'] = pre_df['Product'].apply(lambda x: x.strip())
    pre_df = pre_df.fillna('-')
    pre_df['Unit Price'] = pre_df['Unit Price'].astype('str')
    pre_df['Unit Quantity'] = pre_df['Unit Quantity'].astype('str')
    pre_df['Invoice Amount'] = pre_df['Invoice Amount'].astype('str')
    pre_df['Total Amount'] = pre_df['Total Amount'].astype('str')

    gt_df = pd.read_csv('invoice_label.csv', header=1)
    gt_df = gt_df.drop(index=0)
    gt_df = gt_df.drop(columns=['Unnamed: 0'])
    gt_df = gt_df.rename(columns={'Description':'Product'})
    gt_df = gt_df.iloc[:211, :]
    gt_df['Sender Name'] = gt_df['Sender Name'].apply(lambda x: x.strip())
    gt_df['Product'] = gt_df['Product'].apply(lambda x: x.strip())
    gt_df['HS Code'] = gt_df['HS Code'].astype('str')
    gt_df['HS Code'] = gt_df['HS Code'].apply(lambda x: x+'0' if (len(x.split('.')[-1])==1) & ('-' not in x) else x)
    gt_df['Invoice Amount'] = gt_df['Invoice Amount'].apply(lambda x: x+'0' if len(x.split('.')[-1])==1 else x)
    gt_df['Unit Price'] = gt_df['Unit Price'].apply(lambda x: x+'0' if len(x.split('.')[-1])==1 else x)
    gt_df['Total Amount'] = gt_df['Total Amount'].apply(lambda x: x+'0' if len(x.split('.')[-1])==1 else x)
    gt_df.loc[gt_df['HS Code']=='nan', 'HS Code'] = '-'
    gt_df['Unit Price'] = gt_df['Unit Price'].astype('str')
    gt_df['Unit Quantity'] = gt_df['Unit Quantity'].astype('str')
    gt_df['Invoice Amount'] = gt_df['Invoice Amount'].astype('str')
    gt_df['Total Amount'] = gt_df['Total Amount'].astype('str')

    for column in pre_df.columns:
        if column != 'Invoice Date':
            pre_df[column] =  pre_df[column].apply(lambda x: x.strip())
            gt_df[column] =  gt_df[column].apply(lambda x: x.strip())

    cost = pd.read_csv('cost.csv', index_col=0)
    cost['img path'] = cost['img path'].apply(lambda x: x.split('/')[-1])

    exact_match_metric = load("exact_match")    
    exact_match_df = pd.DataFrame(columns=gt_df.columns)
    column_list = pre_df.columns
    for column in column_list:
        exact_match_scores = []
        for gt_value, pred_value in zip(gt_df[column], pre_df[column]):
            score = exact_match_metric.compute(references=[gt_value], predictions=[pred_value])
            exact_match_scores.append(score["exact_match"])
        exact_match_df[column] = exact_match_scores



if __name__ == "__main__":
    main()