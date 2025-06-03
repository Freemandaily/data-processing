import os
import sys,logging
import time
import pandas as pd
import streamlit as st

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] - %(message)s'
)

def add_to_csv(tweeted_token:dict)->None:
    logging.info('Foramating Data for Display')
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

    
    id = 0
    for date,info in tweeted_token.items():
        for token_address,token_data in info.items():
            data = collect_data(token_data,token_address,id)
            formated_data.append(data)
        id +=1
        
    for influencer_data in formated_data:
        score = 0
        for data_key,data_value in influencer_data.items():
            if data_key.split('_')[-1] == 'Score':
                score += int(data_value)
        influencer_data['Total_Score'] = score

    new_entry = pd.DataFrame(formated_data)
    return new_entry

def collect_data(token_data,token_address,id):
    if token_data['username']+str(id) not in st.session_state['Influencer_data']:
        st.session_state['Influencer_data'][token_data['username']+str(id)] = { }
    try:
        del st.session_state['Influencer_data'][token_data['username']+str(id)]['Address']
        del st.session_state['Influencer_data'][token_data['username']+str(id)]['Tweet_Url'] 
        del st.session_state['Influencer_data'][token_data['username']+str(id)]['Total_Score']  
    except:
        pass
    for token_key,value in token_data.items():
        st.session_state['Influencer_data'][token_data['username']+str(id)][token_key] = value
    
    st.session_state['Influencer_data'][token_data['username']+str(id)]['Address'] = token_address

    try:
        st.session_state['Influencer_data'][token_data['username']+str(id)]['Tweet_Url'] = f"https://x.com/{token_data['username']+str(id)}/status/{token_data['Tweet_id']}"
        del st.session_state['Influencer_data'][token_data['username']+str(id)]['Tweet_id']
    except Exception as e:
        pass
    data = st.session_state['Influencer_data'][token_data['username']+str(id)]
    return data
