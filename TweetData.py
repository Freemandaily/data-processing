from ast import main
import time
from urllib import response
import tweepy
import sys
from datetime import timedelta
import datetime
import pytz,re
import json
import streamlit as st
import asyncio 
import aiohttp
import pandas as pd

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
                            pass
                    # search = self.client.search_recent_tweets(contract,tweet_fields=['author_id','created_at'],start_time=start_time)
                    # if search.data:
                        # for search in search.data:
                        #     user = self.client.get_user(id=search.author_id,user_fields=['username'])
                        #     username = user.data.username
                        #     tweet_dict = {
                        #         'tweet_text':search.text,
                        #         'created_at':search.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                        #         'username':username
                        #     }
                            # user_tweet.append(tweet_dict) 
                    # else:
                    #     st.error('No Tweet Contains The Contracts')
                    #     st.stop()
                self.tweets = user_tweet
            else:
                st.error('Please Enter only Solana Mint Token Contract (32 to 42 char)') 
                st.stop()   
        except Exception as e:
            st.error(f'Error: Issuse is {e}')
            st.stop()



class contractProcessor():
    
   

    def __init__(self,mint_addresses:list,date_time):
        self.mint_addresses = mint_addresses # list
        self.pairs = []
        self.tokens_data = []
        self.date_time = date_time
        self.contracts_price_data = []


        
    async def fetch_ohlc_and_compute(self,session,endpoint_req) -> dict:
        async with session.get(endpoint_req) as response:
            try:
                response_data = await response.json()
                price_data = response_data['data']['attributes']['ohlcv_list']
                removable_index = [0,5]
                price_data = [price for subprice in price_data for index, price in enumerate(subprice) if index not in removable_index]
            
            
                max_so_far = price_data[0]
                max_drawdown  = 0
                max_price = max(price_data)
                min_price = min(price_data)
            except:
                st.error('Please Choose Timeframe Within Token Traded Prices')
                # st.stop()
            
            try:
                for price in price_data:
                    if price > max_so_far :
                        max_so_far = price
                    drawadown = (( price - max_so_far) / max_so_far) * 100
                    max_drawdown = min(drawadown,max_drawdown)
                    
                price_info = {'highest_price': round(max_price,7),
                            'lowest_price':round(min_price,7),
                            'max_drawdown':str(round(max_drawdown,3)) +'%'
                            }
                return price_info
            except Exception as e:
                st.error('Please Choose Timeframe Within Token Traded Pricess')

        

    async def gecko_price_fetch(self,session,pair,five_timeframe_stamp,ten_timeframe_stamp,fifteen_timeframe_stamp) -> dict:
        try:
            task1 = asyncio.create_task(self.fetch_ohlc_and_compute(session,f'https://api.geckoterminal.com/api/v2/networks/solana/pools/{pair}/ohlcv/minute?aggregate=1&before_timestamp={int(five_timeframe_stamp)}&limit=5&currency=usd&token=base'))
            task2 = asyncio.create_task(self.fetch_ohlc_and_compute(session,f'https://api.geckoterminal.com/api/v2/networks/solana/pools/{pair}/ohlcv/minute?aggregate=1&before_timestamp={int(ten_timeframe_stamp)}&limit=10&currency=usd&token=base'))
            task3 = asyncio.create_task(self.fetch_ohlc_and_compute(session,f'https://api.geckoterminal.com/api/v2/networks/solana/pools/{pair}/ohlcv/minute?aggregate=1&before_timestamp={int(fifteen_timeframe_stamp)}&limit=15&currency=usd&token=base'))
            
            five_minutes_task = await task1
            ten_minutes_task = await task2
            fifteen_minutes_task = await task3
            
            pair_data_info = {pair:{ 
                '5m': five_minutes_task,
                '10m': ten_minutes_task,
                '15m': fifteen_minutes_task
            }}
            return pair_data_info
        except Exception as e:
            st.error(f'Please Choose Timeframe Within Token Traded Prices')


    def process_date_time(self,added_minute):
        from datetime import datetime
        combine = self.date_time
        time_object = datetime.strptime(str(combine), "%Y-%m-%d %H:%M:%S")
        processed_date_time = time_object + timedelta(minutes=added_minute)
        added_date_time = processed_date_time.timestamp()
        
        return added_date_time # timestamp

    async def main(self,five_timeframe_stamp,ten_timeframe_stamp,fifteen_timeframe_stamp):
        async with aiohttp.ClientSession() as session:
            task_container = [self.gecko_price_fetch(session,pair,five_timeframe_stamp,ten_timeframe_stamp,fifteen_timeframe_stamp) for pair in self.pairs]
            contracts_price_data = await asyncio.gather(*task_container)
            # print(contracts_price_data)
            self.contracts_price_data = contracts_price_data
            
        for data in self.tokens_data:
            pair = data['pair']
            # print(pair)
            for element in self.contracts_price_data:
                try:
                    element[pair]['address'] = data['address']
                    element[pair]['symbol'] = data['symbol']
                except:
                    pass
        
    
    def process_contracts(self):
        five_timeframe_stamp = self.process_date_time(5)
        ten_timeframe_stamp = self.process_date_time(10)
        fifteen_timeframe_stamp= self.process_date_time(15)
        if 'data_frames' not in st.session_state:
            asyncio.run(self.main(five_timeframe_stamp,ten_timeframe_stamp,fifteen_timeframe_stamp))

    async def pair(self,session,address,pair_endpoint):
        try:
            async with session.get(pair_endpoint) as response:
                try:
                    result = await response.json()
                    pair_address = result['data'][0]['attributes']['address']
                    symbol = result['data'][0]['attributes']['name']
                    token_data = {'address':address,
                                'pair':pair_address,
                                'symbol':symbol}
                    self.pairs.append(pair_address)
                    self.tokens_data.append(token_data)
                except ValueError as e:
                    st.error(f'Check If This Mint Address Is Correct : {e}')
        except :
            st.error('Gecko Rate Limited : Try AGain')

    async def pair_main(self):
        async with aiohttp.ClientSession() as session:
            pairs_container = [self.pair(session,address,f'https://api.geckoterminal.com/api/v2/networks/solana/tokens/{address}/pools?include=base_token&page=1') for address in self.mint_addresses]
            pairs = await asyncio.gather(*pairs_container)

    def fetch_pairs(self):
        if 'data_frames' not in st.session_state:
            asyncio.run(self.pair_main())
            # print('already there')

    def NeededData(self,pricedata):
        for key,value in pricedata.items():
            token_address = value['address']
            symbol = value['symbol'].split('/')[0]
            # st.write(symbol)
            token_price_info = {
                'Info': ['Peak Price','Lowest Price','Max DrawDown'],
                '    5m': [value['5m']['highest_price'],value['5m']['lowest_price'],value['5m']['max_drawdown']],
                '    10m': [value['10m']['highest_price'],value['10m']['lowest_price'],value['10m']['max_drawdown']],
                '    15m': [value['15m']['highest_price'],value['15m']['lowest_price'],value['15m']['max_drawdown']]
            }
        data_frame = pd.DataFrame(token_price_info)
        return data_frame,token_address,symbol
        # st.dataframe(data_frame)

    def slide(self,price_datas):
        # st.write(st.session_state, 'for session from othere ppage')
        if 'data_frames' not in st.session_state:
            st.session_state['data_frames'] = []
            
        if 'address_symbol' not in st.session_state:
            st.session_state['address_symbol'] = []
        try:
            # data_frames = st.session_state['data_frames']
            # address_symbol = st.session_state['address_symbol']
            data_frames = []
            # if 'data_frames' not in st.session_state:
            for pricedata in price_datas:
                data_frame,address,symbol = self.NeededData(pricedata)
                # st.write(address)
                # data_frames.append(data_frame)
                address_sym = [address,symbol ]
                st.session_state['data_frames'].append(data_frame)
                st.session_state['address_symbol'].append(address_sym)
                # address_symbol.append([address,symbol])
            
            if 'slide_index' not in st.session_state:
                st.session_state['slide_index'] = 0

            
            def next_slide():
                if st.session_state.slide_index < len(st.session_state['data_frames']) - 1:
                    
                    st.session_state['slide_index'] +=1

            def prev_slide():
                if st.session_state.slide_index > 0:
                    st.session_state['slide_index'] -=1

            # st.write(st.session_state['slide_index'], 'is slide index')
            # st.write(len(st.session_state['data_frames']),'is len of data frame')
            # st.write(st.session_state['address_symbol'])
            st.badge(f'Token Address : {st.session_state['address_symbol'][st.session_state['slide_index']][0]}',color='violet')
            st.badge(f'Symbol : ${st.session_state['address_symbol'][st.session_state['slide_index']][1]}',color='orange')
            st.dataframe(st.session_state['data_frames'][st.session_state['slide_index']])
            

            col1,col2,col3 = st.columns([1,2,3])
            with col1:
                if st.button('Prev. CA',disabled=st.session_state['slide_index'] == 0):
                    prev_slide()

            with col2:
                if st.button('Next CA',disabled=st.session_state['slide_index'] == len(st.session_state['data_frames']) -1 ):
                    
                    next_slide()
                    
            # st.write(f'Slide {st.session_state['slide_index'] + 1} of {len(st.session_state['data_frames'])}')
        except:
            st.error('Session Ended: Analyze Data Again')
