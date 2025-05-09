import time
import tweepy
import sys
from datetime import timedelta
import datetime
import pytz,re
import json
import streamlit as st

bearerToken =st.secrets['bearer_token']

class processor:
    def __init__(self) -> None: # Default 7 days TimeFrame
        self.client =  tweepy.Client(bearerToken)
        #self.client =  tweepy.Client(bearerToken)
        self.username = None
        self.user = None
        self.user_id = None
        self.timeframe = None
        self.end_date = None
        self.start_date = None
        self.tweets = None
    
    def Load_user(self,username,timeframe=7):
        self.username = username
        self.timeframe = timeframe
        try:
            self.user = self.client.get_user(username=username)
            self.user_id = self.user.data.id
            self.end_date = datetime.datetime.now(pytz.UTC).replace(microsecond=0)
            self.start_date = (self.end_date - timedelta(days=timeframe)).replace(hour=0,minute=0,second=1,microsecond=0)
            st.toast(f'@{username} Handle Successfully Loaded')
            time.sleep(15)
            return {'Success':True}
        except Exception as e:
            time.sleep(2)
            Error_message = {'Error':f'Error: {e}\n.Upgrade Your X Developer Plan or Try Again later'} # handle error according to it error
            return Error_message
        
    
    # Fetching Ticker and contracts contains in the tweet
    def fetchTicker_Contract(self,tweet_text:str) -> dict:
        contract_patterns = r'\b(0x[a-fA-F0-9]{40}|[1-9A-HJ-NP-Za-km-z]{32,44}|T[1-9A-HJ-NP-Za-km-z]{33})\b'
        ticker_partterns = r'\$[A-Za-z0-9_-]+'

        token_details = {
            'ticker_names' : re.findall(ticker_partterns,tweet_text),
            'contracts' : re.findall(contract_patterns,tweet_text) 
        }
        if 'valid contracts' in st.session_state:
            contracts = [contract for contract in token_details['contracts'] if contract.upper() in st.session_state['valid contracts']]
            token_details['contracts'] = contracts
        return token_details

    # Using X API to fetch user tweets
    def fetchTweets(self) -> list:
        # user_tweets =  [{'created_at':'2025-04-22 14:27:35',
        #                 'tweet_text':'ths is the man he said that kills $Ray $Sol $jup'},
        #                 {'created_at':'2025-04-23 14:27:35',
        #                 'tweet_text':'ths is the man he said that kills $bonk $jto'}
        #                 ]
        if self.timeframe == 7:
            request_limit = 1
        else:
            request_limit = 3
        user_tweets = []
        try:
            for response in tweepy.Paginator(self.client.get_users_tweets,
                                            id=self.user_id,
                                            start_time=self.start_date, 
                                            end_time=self.end_date,
                                            exclude='replies',
                                            max_results=100,
                                            limit=request_limit, # consider this
                                            tweet_fields='created_at'):
                
                if response.data:
                    for tweet in response.data:
                        # print(tweet.created_at)
                        # sys.exit()
                        tweet_dict = {
                            'tweet_id':tweet.id,
                            'tweet_text':tweet.text,
                            'created_at':tweet.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                            'username': self.username
                        }
                        user_tweets.append(tweet_dict)
            self.tweets = user_tweets
        except Exception as e:
            Error_message = {'Error':f'Failed To Fetch Tweets Because of  {e}\nUpgrade Your X Developer Plan or Wait For Sometimes'}
            # return Error_message
            self.tweets = Error_message
        
        
    # format the data to a suitable data type
    def Reformat(self,fetched_Token_details:list) -> dict:
        details = {}
        for data in fetched_Token_details:
            details[data['date']] = { 'Token_names': data['token_details']['ticker_names'],
                                       'contracts': data['token_details']['contracts'],
                                       'username':data['username']}
        details = {date: tokenName_contract for date,tokenName_contract in details.items() if tokenName_contract['Token_names'] or tokenName_contract['contracts']}
        if details:
            st.toast('Tweets Containing Token Symbols Found!')
            time.sleep(10)
            print('Tweets Containing Token Symbols Found!')
            return details
        else:
            Error_message = {'Error':'No Tweets Contain Any Token Symbols Or CA.\nAdjust Timeframe and Try Again'}
            time.sleep(7)
            return Error_message
        
    # Start procesing user tweet
    def processTweets(self)->dict: # Entry function
        tweets = self.tweets
        if isinstance(tweets,dict) and 'Error' in tweets:
            return tweets # Error handlig for streamlit
        fetched_Token_details = []
    
        if tweets:
            for tweet in tweets:
                token_details = self.fetchTicker_Contract(tweet['tweet_text'])
                refined_details = {
                    'username':tweet['username'],
                    'token_details': token_details,
                    'date': tweet['created_at']
                }
                fetched_Token_details.append(refined_details)

            tweeted_Token_details = self.Reformat(fetched_Token_details)
            return tweeted_Token_details
        else :
            Error_message = {'Error':f'Not Able To Process {self.username} Tweets! Please check I'}
            return Error_message
        

    

    def Fetch_Id_username_url(self,url): # This  get tweet id and user using the provided url
        url = url.lower()
        print(url)
        if url.startswith('https://x.com/'):
            try:
                tweet_id = url.split('/')[-1]
                username = url.split('/')[-3]
                if len(tweet_id) == 19 and isinstance(int(tweet_id),int):
                    return tweet_id,username #this should update the self.username
                else:
                    raise ValueError('Incorrect Tweet Id')
            except ValueError as e:
                print(f'Make Sure Url Contains Valid Tweet Id ')
                # stoop the program
                st.error(f'Make Sure Url Contains Valid Tweet Id ')
                st.stop()
        else:
            print('Provide A Valid X Url')
            st.error('Provide A Valid X Url')
            st.stop()
            # stop the program
           
        

    def search_with_id(self,url):
        tweet_id,username =  self.Fetch_Id_username_url(url)
        try:
            tweets = self.client.get_tweets(tweet_id,tweet_fields=['created_at'])
            user_tweets = []
            for tweet in tweets.data:
                tweet_dict = {
                    'tweet_text':tweet.text,
                    'created_at':tweet.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                    'username': username
                    }
                user_tweets.append(tweet_dict)
            # return user_tweets
            print(user_tweets)
            self.tweets = user_tweets
        except Exception as e:
            Error_message = {'Error':f'Failed To Fetch Tweets Because of  {e}'} # this Error comes because of invali tweet id , configure correctly
            self.tweets = Error_message
            



    def search_tweet_with_contract(self,text_inputs,start_time):
        user_tweet = [ ]
        try:
            contracts = [text.upper() for text in text_inputs if not text.startswith('0x') and len(text) >= 32]
            if contracts:
                st.session_state['valid contracts'] = contracts # for matching only te searched contract in fetchTicker_Contract()
                for contract in contracts:
                    search = self.client.search_recent_tweets(contract,tweet_fields=['author_id','created_at'],start_time=start_time)
                    if search.data:
                        for search in search.data:
                            user = self.client.get_user(id=search.author_id,user_fields=['username'])
                            username = user.data.username
                            tweet_dict = {
                                'tweet_text':search.text,
                                'created_at':search.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                                'username':username
                            }
                            user_tweet.append(tweet_dict) 
                    else:
                        st.error('No Tweet Contains The Contracts')
                        st.stop()
                self.tweets = user_tweet
            else:
                st.error('Please Enter only Solana Mint Token Contract (32 to 42 char)') 
                st.stop()   
        except Exception as e:
            st.error(f'Error: Issuse is {e}')
            st.stop()


