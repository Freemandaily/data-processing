from datetime import datetime
import time
import pytz
import streamlit as st
import sys
from TweetData import processor
from priceFeed import token_tweeted_analyzor
from storage import add_to_csv



class search_state():
    def __init__(self):
        self.search_with = None

search = search_state()


def data_for_drawDown(tweeted_token):
    tweeted_token = { date:value for date,value in tweeted_token.items() if value}
        

    handles_data = [ ]
    for date ,info in tweeted_token.items():
        for token_address,token_data in info.items():
            influencer_data = {
                'username' :token_data['username'],
                'prices' : [token_data['Price_Tweeted_At'],token_data['price_5m'],token_data['price_10m']],
                'token': token_data['symbol']
            }
            handles_data.append(influencer_data)
    
    st.session_state['handles_data'] = handles_data


st.header('Data-Extraction and Processing')
with st.sidebar:
    st.title('Data Configuration')
    username_url = st.text_input('Enter X Handle Or Tweet Url (Https://..\n')
    timeframe = st.selectbox('Choose A TimeFrame',[7,30,90])
    token_choice = st.radio('Search From',['Strict Token','All Tokens'])
    
    st.divider()
    contracts_input = st.text_area('Enter Contracts',placeholder='4k3Dyjzvzp8eMZWUXbBCjEvwSkkk59S5iCNLY3QrkX6R\n7GCihgDB8fe6KNjn2MYtkzZcRjQy3t9GHdC8uHYmW2hr')
    choose_date = st.date_input(label='Choose A Date',value='today')
    choose_time = st.time_input('Choose Time',value=None,step=300)
    st.divider()
   
    st.subheader('About')
    About = """
    The Analyst module is tool designed to analyse the impact of influencer tweet on a particular solana based token.
    Built wih the focused on the solana blockchain,the tool scans the twitter activities of the specified influencer within a choosen timeframe and extracts,
    symbols and contract Address(CAs) mentioned in the posts then correlate this mentions with the real times price action
    at 5-minute,10-minute and 15-minuts interval to reveal the impact.
    """

    st.write(About)

st.image('data-extract.png')


def loadsearch():
    if search.search_with == 'handle':
        with st.spinner(f'Loading @{username_url} Handle'):
            userHandler = process.Load_user(username_url,timeframe=timeframe) 
        if 'Error' in userHandler:
            st.error(userHandler['Error'])
            st.stop() 
        
        with st.spinner(f'Processing @{username_url} Tweets'):
            process.fetchTweets()
            tweeted_token_details = process.processTweets()
    elif search.search_with == 'link':
        with st.spinner(f'Processing  Tweets in Url......'):
            process.search_with_id(username_url)
            tweeted_token_details = process.processTweets()
    elif search.search_with == 'Contracts':
        if choose_date and choose_time:
            combine = datetime.combine(choose_date,choose_time)
            utc_datetime = combine.replace(tzinfo=pytz.UTC)
            start_time = utc_datetime.isoformat().replace('+00:12',"z")
        else:
            st.error('Please Choose Date And Time')
            st.stop()
        with st.spinner(f'Processing  Tweets Containing The Contracts......'):
            process.search_tweet_with_contract(contracts_input.split('\n'),start_time)
            tweeted_token_details = process.processTweets()
    
    return tweeted_token_details
    
    
        
if len(username_url) > 0 and len(contracts_input) > 0:
    search_option = st.selectbox(
        'Multiple Search Input Detected Choose How To Search',
        ('Search Only With X handle/Url','Search Only With Contracts'),
        index=None,
        placeholder='Choose Search Option'
        )
    if search_option == 'Search Only With X handle/Url':
        username_url = username_url.upper()
        if username_url.startswith('HTTP'):
            search.search_with = 'link'
        else:
            search.search_with = 'handle'
    elif search_option == 'Search Only With Contracts':
        search.search_with = 'Contracts'

elif len(username_url) > 0 and len(contracts_input) == 0:
    username_url = username_url.upper()
    if username_url.startswith('HTTP'):
        search.search_with = 'link'
    else:
        search.search_with = 'handle'
elif len(contracts_input) > 0 and len(username_url) == 0:
    search.search_with = 'Contracts'
else:
    st.error('Please Enter Where To Search From')
    st.stop()



if st.button('Analyse Tweet'):
    process = processor()

    tweeted_token_details = loadsearch()

    if 'Error' in tweeted_token_details:
        st.error(tweeted_token_details['Error'])
        st.stop()
    else:
        st.toast(f'{search.search_with} Tweets Successfully Processed!')  
    # tweeted_token_details = {'2025-04-22 14:27:35':{'Token_names':['$sol','$ray','$wif','$jup'],'contracts':[]}}
    
    # Fetchng tweeted token data
    with st.spinner('Fetching Tweeted Tokens and Price Datas. Please Wait.....'):
        analyzor = token_tweeted_analyzor(tweeted_token_details,token_choice)
    if 'Error' in analyzor:
        st.error(analyzor['Error'])
        st.stop()

    with st.spinner('Storing Tweeted Token(s) Data'):  
        df_data = add_to_csv(analyzor)  # Adding the tweeted token to cs file
    if 'Error' in df_data:
        st.error(df_data['Error'])
        st.stop()
    st.success( 'Succesfully Analyzed Tweeted Token(s)',icon="✅")
    time.sleep(5)
    st.dataframe(df_data)


    def convert_for_download(df_data):
        return df_data.to_csv().encode("utf-8")
    csv = convert_for_download(df_data)
    st.session_state['analyzor'] = analyzor

    
    st.download_button(
        label="Download CSV",
        data=csv,
        file_name="data.csv",
        mime="text/csv",
        icon=":material/download:"
    )

if 'analyzor' in st.session_state:
    if st.button('Check DrawDown'):
        handles_data = data_for_drawDown(st.session_state['analyzor'])
        st.switch_page('drawdown.py')


