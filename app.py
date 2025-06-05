from datetime import datetime
import time
import pytz
import streamlit as st
import sys,logging
from TweetData import processor
from priceFeed import token_tweeted_analyzor
from storage import add_to_csv
from TweetData import contractProcessor
import gspread
from gspread_dataframe import set_with_dataframe

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] - %(message)s'
)

class search_state():
    def __init__(self):
        self.search_with = None
search = search_state()


def restore():
       
    if 'download_dataframe' in st.session_state:
        if st.button('Show Previous Data'):
            df_data = st.session_state['download_dataframe']
            st.dataframe(df_data)

            def convert_for_download(df_data):
                return df_data.to_csv().encode("utf-8")
            csv = convert_for_download(df_data)

            
            st.download_button(
                label="Re-Download CSV",
                data=csv,
                file_name="data.csv",
                key=2,
                mime="text/csv",
                icon=":material/download:"
            )
restore() # To fetch previous Data

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
            if None in influencer_data['prices']:
                continue
            handles_data.append(influencer_data)
    if handles_data:
        st.session_state['handles_data'] = handles_data
    else:
        st.error('Cant Compute DrawnDown. Most Prices Are Missing')
        st.stop()

def worksForReload(contracts_input,choose_time,choose_date,first_tweet_minute,follower_threshold):
    try:
        if st.session_state['contracts_input'] != contracts_input:
            try: 
                if 'Search_tweets_Contract' in st.session_state: 
                    del st.session_state['Search_tweets_Contract']

                if 'Search_tweets_Contract_displayed' in st.session_state :
                    del st.session_state['Search_tweets_Contract_displayed']
                
                if 'Influencer_data' in st.session_state:
                    del st.session_state['Influencer_data'] 


                if 'data_frames' in st.session_state:
                    del st.session_state['data_frames']
                    del st.session_state['address_symbol']
                    del st.session_state['token_price_info'] 
            except:
                pass
    except:
        pass
    
    try:
        if st.session_state['choose_time'] != choose_time and st.session_state['choose_time'] != None:
            try: 
                if 'data_frames' in st.session_state:
                    del st.session_state['data_frames']
                    del st.session_state['address_symbol']
                    del st.session_state['token_price_info']  
            except:
                pass
    except:
        pass
    
    try:
        if st.session_state['choose_date'] != choose_date and  st.session_state['choose_date'] != None:
            try: 
                if 'data_frames' in st.session_state:
                    del st.session_state['data_frames']
                    del st.session_state['address_symbol']
                    del st.session_state['token_price_info']  
            except:
                pass
    except:
        pass
    
    try:
        if st.session_state['first_tweet_minute'] != first_tweet_minute:
            if 'Search_tweets_Contract_displayed' in st.session_state :
                del st.session_state['Search_tweets_Contract_displayed']
    except:
        pass

    try:
        if st.session_state['follower_threshold'] != follower_threshold:
            if 'Search_tweets_Contract_displayed' in st.session_state :
                del st.session_state['Search_tweets_Contract_displayed']
    except:
        pass


st.header('Data-Extraction and Processing')
with st.sidebar:
    st.title('Data Configuration')
    username_url = st.text_input('Enter X Handle Or Tweet Url (Https://..\n')
    timeframe = st.selectbox('Choose A TimeFrame',[7,30,90])
    first_tweet_minute = st.slider('First Tweet Minute After Pool Creation',1,60,1) # GeckoTerminal price indexing changes somethings we use this to toggle price searhc time
    follower_threshold =  st.slider('Kols Followers Threshold',700,1000,1000)
    st.divider()
    contracts_input = st.text_area('Enter Contracts',placeholder='4k3Dyjzvzp8eMZWUXbBCjEvwSkkk59S5iCNLY3QrkX6R\n7GCihgDB8fe6KNjn2MYtkzZcRjQy3t9GHdC8uHYmW2hr')
    choose_date = st.date_input(label='Set A Date',value='today')
    choose_time = st.time_input('Set Time',value=None,step=300)
   
    worksForReload(contracts_input,choose_time,choose_date,first_tweet_minute,follower_threshold)
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
def loadsearch(process=None):
    logging.info('Loading Search')
    if search.search_with == 'handle':
        logging.info('Searching With X Handle')
        with st.spinner(f'Loading @{username_url} Handle'):
            userHandler = process.Load_user(username_url,timeframe=timeframe) 
        if 'Error' in userHandler:
            st.error(userHandler['Error'])
            st.stop() 
        
        with st.spinner(f'Processing @{username_url} Tweets'):
            process.fetchTweets()
            tweeted_token_details = process.processTweets()
            return tweeted_token_details
    elif search.search_with == 'link':
        logging.info('Searching With Link')
        with st.spinner(f'Processing  Tweets in Url......'):
            process.search_with_id(username_url)
            tweeted_token_details = process.processTweets()
            return tweeted_token_details
    elif search.search_with == 'Contracts':
        search_option = st.selectbox(
            'Specify How To Search For The Contract',
            ('Search Contracts Onchain','Search Contract From X Data'),
            index=None,
            placeholder='Choose Search Option'
            )
        if search_option == 'Search Contract From X Data':
            logging.info('Search Contract From X Data Activated')
            st.session_state['Search_tweets_Contract'] = 'Search_tweets_Contract'
            if 'data_frames' in st.session_state:
                del st.session_state['data_frames']

            combine_date_time = None
            
        elif search_option == 'Search Contracts Onchain':
            logging.info('Search Contracts Onchain Activated')
            if 'Search_tweets_Contract' in st.session_state: # delete the sessin set to indentify the contract search from x data
                del st.session_state['Search_tweets_Contract']
            
            if 'df_data' in st.session_state:
                del st.session_state['df_data']
            
            
            if choose_date and choose_time:
                st.session_state['choose_date'] = choose_date
                st.session_state['choose_time'] = choose_time
                combine_date_time =  datetime.combine(choose_date,choose_time)
            else:
                st.error('Please Choose Date And Time')
                st.stop()

        if search_option:
            if 'data_frames' not in st.session_state:
                with st.spinner(f'Loading  Contract(s)......'):
                    time.sleep(2)
                    text_inputs  = contracts_input.split('\n')
                    contracts = [text for text in text_inputs if not text.startswith('0x') or len(text) >= 32]
                    if contracts:
                        st.session_state['contracts_input'] = contracts_input # this work with workforload function to enable seamless reload of pge
                        process = contractProcessor(contracts,combine_date_time)
                        st.session_state['process'] = process # to be used when rerun
                    else:
                        st.error('Please Enter Only  Token Contract (32 to 42 char)') 
                        st.stop()   
                    return process
            else:
                process = st.session_state['process']
                return process
        else:
            st.stop()
        
if len(username_url) > 0 and len(contracts_input) > 0:
    search_option = st.selectbox(
        'Multiple Search Input Detected Choose How To Search',
        ('Search Only With X handle/Url','Search With Contracts'),
        index=None,
        placeholder='Choose Search Option'
        )
    if search_option == 'Search Only With X handle/Url':
        logging.info('Search Only With X handle/Url Selected')
        username_url = username_url.upper()
        if username_url.startswith('HTTP'):
            search.search_with = 'link'
        else:
            search.search_with = 'handle'
    elif search_option == 'Search With Contracts':
        logging.info('Search With Contracts Selected')
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

if search.search_with != 'Contracts':
    st.session_state['first_tweet_minute'] = int(first_tweet_minute)
    st.session_state['follower_threshold'] = follower_threshold
    if st.button('Analyse'):
        logging.info('Started Analyzing..')
        if 'tokens_data' in st.session_state:
            del st.session_state['tokens_data']
        if 'Search_tweets_Contract' in st.session_state: # delete the sessin set to indentify the contract search from x data
                del st.session_state['Search_tweets_Contract']

        if 'df_data' in st.session_state:
            del st.session_state['df_data']

        if 'Influencer_data' in st.session_state:
            del st.session_state['Influencer_data'] 

        process = processor()
        tweeted_token_details = loadsearch(process)
        if 'Error' in tweeted_token_details:
            st.error(tweeted_token_details['Error'])
            st.stop()
        else:
            st.toast(f'{search.search_with} Tweets Successfully Processed!')    
        st.session_state['tweeted_token_details'] = tweeted_token_details # setting this so that for custom timeframe uses it

        with st.spinner('Fetching Tweeted Tokens and Price Datas. Please Wait.....'):
            analyzor = token_tweeted_analyzor(tweeted_token_details) # Removed Token choice
            st.session_state['Timeframe'] = 5
        if 'Error' in analyzor:
            st.error(analyzor['Error'])
            st.stop()

        with st.spinner('Storing Tweeted Token(s) Data'):
            df_data = add_to_csv(analyzor)  # Adding the tweeted token to cs file
        if 'Error' in df_data:
            st.error(df_data['Error'])
            st.stop()
        st.success( 'Succesfully Analyzed Tweeted Token(s)',icon="✅")
        time.sleep(1)
        st.session_state['df_data'] = df_data
else:
    st.session_state['first_tweet_minute'] = int(first_tweet_minute)
    st.session_state['follower_threshold'] = follower_threshold
    process = loadsearch()

    if 'data_frames' in st.session_state:
        if st.button('Changed Input?:Rerun'):
            if 'data_frames' in st.session_state:
                del st.session_state['data_frames']
                del st.session_state['address_symbol']
                del st.session_state['token_price_info']
    
    process.fetch_pairs()
    if 'Search_tweets_Contract' not in st.session_state :
        next_timeframe = st.selectbox(
            'Add Timeframe',
            (5,10,15,30),
            #index=None,
            placeholder= 'Select Timeframe',
            accept_new_options=True
        )
    
        if  next_timeframe !=None:
            if isinstance(next_timeframe,str):
                try:
                    hour_minute = next_timeframe.split(':')
                    hours_into_minutes = int(hour_minute[0]) 
                    minute = int(hour_minute[1])
                    next_timeframe = ( hours_into_minutes * 60) + minute
                except:
                    try:
                        next_timeframe = int(next_timeframe)
                    except:
                        st.error('Please Select Valid Timeframe')
                        st.stop()
        
    if 'Search_tweets_Contract' in st.session_state and  'Search_tweets_Contract_displayed' not in st.session_state :
        with st.spinner('Searching Early Tweets Containing Contract.Might Take A While........'):
            process.search_tweets_with_contract()
            process.processTweets()
        with st.spinner('Fetching Tweeted Contract Price Datas. Please Wait.....'):
            tweeted_Token_details = st.session_state['tweeted_token_details'] 
            analyzor = token_tweeted_analyzor(tweeted_Token_details,5)
            st.session_state['Timeframe'] = 5

            if 'Error' in analyzor:
                st.error(analyzor['Error'])
                st.stop()

            with st.spinner('Storing Tweeted Token(s) Datas'):
                df_data = add_to_csv(analyzor)  
            if 'Error' in df_data:
                st.error(df_data['Error'])
                st.stop()
            st.success( 'Succesfully Analyzed Tweeted Token(s)',icon="✅")
            time.sleep(1)
            st.session_state['df_data'] = df_data
    elif 'Search_tweets_Contract' not  in st.session_state :
        process.process_contracts(next_timeframe)
        price_datas = process.contracts_price_data
        process.slide(price_datas,next_timeframe)
    
  
def display(df_data):
    next_timeframe = st.selectbox(
        'Add Timeframe for x',
        (5,10,15,30),
        index=None,
        placeholder= 'Select Timeframe for x',
        accept_new_options=True
    )
    
    if 'displayed' in st.session_state and next_timeframe !=None and  st.session_state['Timeframe'] != next_timeframe:
        st.session_state['Timeframe'] = next_timeframe
        if isinstance(next_timeframe,str):
            try:
                hour_minute = next_timeframe.split(':')
                hours_into_minutes = int(hour_minute[0]) 
                minute = int(hour_minute[1])
                next_timeframe = ( hours_into_minutes * 60) + minute
            except:
                try:
                    next_timeframe = int(next_timeframe)
                except:
                    st.error('Please Select Valid Timeframe')
                    st.stop()

        tweeted_token_details = st.session_state['tweeted_token_details']
        analyzor = token_tweeted_analyzor(tweeted_token_details,int(next_timeframe))
        df_data = add_to_csv(analyzor) 
        st.session_state['df_data'] = df_data
    
    logging.info('Displaying Data')
    st.dataframe(df_data)
    st.session_state['displayed'] = 'yes'
    if 'Search_tweets_Contract' in st.session_state:
        st.session_state['Search_tweets_Contract_displayed'] = 'Search_tweets_Contract_displayed'
    st.session_state['download_dataframe'] = df_data

    def convert_for_download(df_data):
        return df_data.to_csv().encode("utf-8")
    csv = convert_for_download(df_data)
    col = st.columns([1,1])
    with col[0]:
        st.download_button(
            label="Download CSV",
            data=csv,
            file_name="data.csv",
            key=1,
            mime="text/csv",
            icon=":material/download:"
        )
    with col[1]:
        if st.button('Add To Sheet'):
            try:
                gc = gspread.service_account(filename='freeman-461623-154dc403ca64.json')
                spreadSheet = gc.open('TWEEET')
                sheet = spreadSheet.worksheet('Sheet2')
            except:
                st.error('Unable To Add Data To Sheet')
                st.stop()
            last_row = len(sheet.get_all_values()) + 2
            set_with_dataframe(sheet, df_data, row=last_row, include_index=False, resize=True)
            st.toast( 'Succesfully Added Data To Sheet')
        
if 'df_data' in st.session_state: # For displaying the Tweeted data
    display(st.session_state['df_data'])