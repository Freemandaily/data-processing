import os
import sys
import time
import pandas as pd
import streamlit as st

def add_to_csv(tweeted_token:dict)->None:
    tweeted_token = { date:value for date,value in tweeted_token.items() if value}
    if tweeted_token:
        if 'Influencer_data' not in st.session_state:
            st.session_state['Influencer_data'] = { }
            st.toast('Adding Tweeted Token Data To Cvs File!')
            print('Adding Tweeted Token Data To Cvs File!')
            time.sleep(3)
    else:
        Error_message = {'Error':'Tokens  Contains Invalid Price','Message':'Adding Tweeted Token Data To Cvs File!'}
        return Error_message

    # construct the columns and rows
    formated_data = []
    
    for date,info in tweeted_token.items():
        for token_address,token_data in info.items():
            # put here in function
            collect_data(token_data,token_address)
            formated_data.append(st.session_state['Influencer_data'])
            
    new_entry = pd.DataFrame(formated_data)
    return new_entry

def collect_data(token_data,token_address):
    try:
        del st.session_state['Influencer_data']['Address']
    except:
        pass
    for token_key,value in token_data.items():
        st.session_state['Influencer_data'][token_key] = value
    st.session_state['Influencer_data']['Address'] = token_address
