import os
import sys,logging
import time
import pandas as pd
import streamlit as st

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] - %(message)s'
)

# def filterForNone():


def add_to_csv(tweeted_token:dict)->None:
    logging.info('Foramating Data for Display')
    # print(tweeted_token)
    formated_data = []
    tweeted_token = { date:value for date,value in tweeted_token.items() if value}
    if tweeted_token:
        if 'Influencer_data' not in st.session_state:
            st.session_state['Influencer_data'] = { }
            st.toast('Adding Tweeted Token Data To Cvs File!')
    else:
        logging.error('Tokens  Contains Invalid Price')
        Error_message = {'Error':'Tokens  Contains Invalid Price','Message':'Adding Tweeted Token Data To Cvs File!'}
        return Error_message

    
    for username_Id,info in tweeted_token.items():
        try:
            for token_address,token_data in info.items():
                data = collect_data(username_Id,token_data,token_address)
                formated_data.append(data)
        except:
            pass
        
    for influencer_data in formated_data:
        score = 0
        for data_key,data_value in influencer_data.items():
            if data_key.split('_')[-1] == 'Score':
                score += int(data_value)
        influencer_data['Total_Score'] = score
    
    max_column = 0
    for influencer_call_data in formated_data:
        if len(influencer_call_data) > max_column:
            max_column = len(influencer_call_data) 
        
    formated_data = [influencer_call_data for influencer_call_data in formated_data if len(influencer_call_data) == max_column ]

    new_entry = pd.DataFrame(formated_data)
    return new_entry

def collect_data(username_Id,token_data,token_address):
    if username_Id not in st.session_state['Influencer_data']:
        st.session_state['Influencer_data'][username_Id] = { }
    try:
        del st.session_state['Influencer_data'][username_Id]['Address']
        del st.session_state['Influencer_data'][username_Id]['Tweet_Url'] 
        del st.session_state['Influencer_data'][username_Id]['Total_Score']  
    except:
        pass
    for token_key,value in token_data.items():
        st.session_state['Influencer_data'][username_Id][token_key] = value
    
    st.session_state['Influencer_data'][username_Id]['Address'] = token_address

    try:
        st.session_state['Influencer_data'][username_Id]['Tweet_Url'] = f"https://x.com/{token_data['username']}/status/{token_data['Tweet_id']}"
        del st.session_state['Influencer_data'][username_Id]['Tweet_id']
    except Exception as e:
        pass
    
    data = st.session_state['Influencer_data'][username_Id]
    return data
