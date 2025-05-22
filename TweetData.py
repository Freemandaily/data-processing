from ast import main
from multiprocessing import pool
import time
from urllib import response
import tweepy
import sys
from datetime import datetime,timedelta
import datetime
import pytz,re
import json
import streamlit as st
import asyncio 
import aiohttp
import pandas as pd

# with open('key.json','r') as file:
#     keys = json.load(file)
#     bearerToken =keys['bearerToken']


bearerToken =st.secrets['bearer_token']

class processor:
    def __init__(self) -> None: # Default 7 days TimeFrame
        self.client =  tweepy.Client(bearerToken)
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
            return tweets # Error handling for streamlit
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
        
    # Get tweet id and user using the provided url
    def Fetch_Id_username_url(self,url):
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
                st.error(f'Make Sure Url Contains Valid Tweet Id ')
                st.stop()
        else:
            print('Provide A Valid X Url')
            st.error('Provide A Valid X Url')
            st.stop()

    def search_with_id(self,url):
        tweet_id,username =  self.Fetch_Id_username_url(url)
        try:
            tweets = self.client.get_tweets(tweet_id,tweet_fields=['created_at'])
            user_tweets = []
            for tweet in tweets.data:
                tweet_dict = {
                    'tweet_text':tweet.text,
                    'created_at':tweet.created_at.strftime("%Y-%m-%d %H:%M"),
                    'username': username
                    }
                user_tweets.append(tweet_dict)
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

    def __init__(self,mint_addresses:list,date_time=None):
        self.mint_addresses = mint_addresses # -> list
        self.pairs = []
        self.tokens_data = []
        self.date_time = date_time
        self.contracts_price_data = []
        self.from_timetamp = 0
        self.to_timestamp = 0
        
    
    async def Priceswharehouse(self,session,poolId):
        # headers = {
        #     "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        #     "Accept": "application/json"
        # }

        headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36 Edg/136.0.0.0",
                "Accept": "application/json, text/plain, */*",
                "Accept-Encoding": "gzip, deflate, zstd",
                "Accept-Language": "en-US,en;q=0.9",
                "Origin": "https://www.geckoterminal.com",
                "Referer": "https://www.geckoterminal.com/",
                "Sec-CH-UA": '"Chromium";v="136", "Microsoft Edge";v="136", "Not.A/Brand";v="99"',
                "Sec-CH-UA-Mobile": "?0",
                "Sec-CH-UA-Platform": '"Windows"',
                "Sec-Fetch-Dest": "empty",
                "Sec-Fetch-Mode": "cors",
                "Sec-Fetch-Site": "same-site",
                "Priority": "u=1, i",
                # Note: ":authority" is not needed in requests; it's handled by the HTTP client
            }
        url = f'https://app.geckoterminal.com/api/p1/candlesticks/{poolId}?resolution=1&from_timestamp={self.from_timetamp}&to_timestamp={self.to_timestamp}&for_update=false&currency=usd&is_inverted=false'
        async with session.get(url=url,headers=headers) as response:
                result = await response.json()
                datas = result['data']
                price_data = [value for data in datas for key in ['o','h','l','c'] for value in [data[key]]]
                dates = [value for data in datas for key in ['dt'] for value in [data[key]]]
                """
                This fetch get data from the gecko terminal website,
                so the time is in GMT which is lagging 1 hour . 
                Also i some candle are missing in some chart , 
                below code is used to mitigate it.
                i have to add 1 hour to  the time. 
                i only use the time to check if the candle chart start from the self.from_timestamp
                """
                from datetime import datetime,timedelta
                new_dates_timestamp = [ ]
                for date in dates:
                    dt = datetime.fromisoformat(date.replace('Z', '+00:00'))
                    unix_timestamp = int(dt.timestamp())
                    new_dates_timestamp.append(unix_timestamp)
                return price_data,new_dates_timestamp

    async def fetch_ohlc_and_compute(self,session,poolId,network):
            
            try:
                task_price  = asyncio.create_task(self.Priceswharehouse(session,poolId))
                price_data,new_date_timestamp = await task_price
                """
                This checks if the starting candle timestamp is there
                if the candle is there m  we take only the closing price and discard the candle
                else we keep the candle and start at the open price
                Rem, this is from website api , the data formation varies
                """
                if self.from_timetamp in new_date_timestamp:
                    entry_price = price_data[4]
                    price_data = price_data[4:]
                else:
                    entry_price = price_data[0]
                
                if self.to_timestamp in new_date_timestamp: # Some request gives extra timestamp, i handle it here
                    price_data = price_data[:-4]
                
                close_price = price_data[-1] 
                peak_price = round(max(price_data),7)
                lowest_price = round(min(price_data),7)
                max_so_far = price_data[0]
                max_drawdown  = 0 
                
                percentage_change = str(round(((close_price - entry_price)/entry_price) * 100,3)) + '%'
                entry_to_peak = str(round(((peak_price - entry_price) /entry_price) * 100,3)) +'%' 
            except:
                st.error('Please Choose Timeframe Within Token Traded Prices')
               
            
            try:
                for price in price_data:
                    if price > max_so_far :
                        max_so_far = price
                    drawadown = (( price - max_so_far) / max_so_far) * 100
                    max_drawdown = min(drawadown,max_drawdown)

                price_info = {'Entry_Price': round(entry_price,7),
                            'Price':round(close_price,7),
                            '%_Change':percentage_change,
                            # DrawDown,
                            'Peak_Price':peak_price,
                            '%_Entry_to_Peak': entry_to_peak,
                            'lowest_Price' : lowest_price,
                            'Max_Drawdown': round(max_drawdown,7)
                            }
                return price_info
            except Exception as e:
                st.error('Please Choose Timeframe Within Token Traded Pricess')

   
    async def gecko_price_fetch(self,session,timeframe,poolId,pair=None,network=None) -> dict:
        try:
            task1 = asyncio.create_task(self.fetch_ohlc_and_compute(session,poolId,network)) 
            time_frame_Task = await task1
            if int(timeframe) > 60:
                    hour = str(timeframe //60)
                    minutes = timeframe %60
                    print(f'{hour}:{minutes}m')
                    
                    timeframe = f'{hour}:{minutes}m'  if minutes > 0  else f'{hour}hr(s)' 
            else:
                timeframe = f'{timeframe}m'

            pair_data_info = {pair:{ 
                f'{timeframe}': time_frame_Task
            }}
            return pair_data_info
        except Exception as e:
            st.error(f'Please Choose Timeframe Within Token Traded Prices')

    def process_date_time(self,added_minute):
        from datetime import datetime
        combine = self.date_time
        added_minute = added_minute + 1
        time_object = datetime.strptime(str(combine), "%Y-%m-%d %H:%M:%S")
        processed_date_time = time_object + timedelta(minutes=added_minute) # added 1 beacuse of how gecko terminal fetch price, price begin at the previou timestamp
        from_timestamp = time_object.timestamp()
        to_timestamp = processed_date_time.timestamp()
        self.from_timetamp = int(from_timestamp)
        self.to_timestamp = int(to_timestamp)

    async def main(self,timeframe): 
        async with aiohttp.ClientSession() as session:
            task_container = [self.gecko_price_fetch(session,timeframe,data['poolId'],pair=data['pair'],network=data['network_id']) for data in self.tokens_data]
            contracts_price_data = await asyncio.gather(*task_container)
            self.contracts_price_data = contracts_price_data
            
        for data in self.tokens_data:
            pair = data['pair']
            for element in self.contracts_price_data: # add element[pair][network] = data[network]
                try:
                    element[pair]['address'] = data['address']
                    element[pair]['symbol'] = data['symbol']
                    element[pair]['network'] = data['network_id']
                except:
                    pass
        
    def process_contracts(self,timeframe): 
        self.process_date_time(timeframe)
        asyncio.run(self.main(timeframe))
    
    async def Fetch_PoolId_TokenId(self,session,network_id,pair):
        # headers = {
        #     "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        #     "Accept": "application/json"
        # }

        headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36 Edg/136.0.0.0",
                "Accept": "application/json, text/plain, */*",
                "Accept-Encoding": "gzip, deflate, br, zstd",
                "Accept-Language": "en-US,en;q=0.9",
                "Origin": "https://www.geckoterminal.com",
                "Referer": "https://www.geckoterminal.com/",
                "Sec-CH-UA": '"Chromium";v="136", "Microsoft Edge";v="136", "Not.A/Brand";v="99"',
                "Sec-CH-UA-Mobile": "?0",
                "Sec-CH-UA-Platform": '"Windows"',
                "Sec-Fetch-Dest": "empty",
                "Sec-Fetch-Mode": "cors",
                "Sec-Fetch-Site": "same-site",
                "Priority": "u=1, i",
                # Note: ":authority" is not needed in requests; it's handled by the HTTP client
            }
        url = f"https://app.geckoterminal.com/api/p1/{network_id}/pools/{pair}?include=dex%2Cdex.network.explorers%2Cdex_link_services%2Cnetwork_link_services%2Cpairs%2Ctoken_link_services%2Ctokens.token_security_metric%2Ctokens.token_social_metric%2Ctokens.tags%2Cpool_locked_liquidities&base_token=0"
        async with session.get(url,headers=headers) as response:
           try:
                result = await response.json()
                data = result['data']
                poolId = data['id']
                pairId = result['data']['relationships']['pairs']['data'][0]['id']
                return poolId,pairId
           except Exception as e:
               st.error(f'Issue getting the poolId{e}')

    async  def fetchNetworkId(self,session,address):
        # 
        # headers = {
        #     "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        #     "Accept": "application/json"
        # }
        headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36 Edg/136.0.0.0",
                "Accept": "application/json, text/plain, */*",
                "Accept-Encoding": "gzip, deflate, br, zstd",
                "Accept-Language": "en-US,en;q=0.9",
                "Origin": "https://www.geckoterminal.com",
                "Referer": "https://www.geckoterminal.com/",
                "Sec-CH-UA": '"Chromium";v="136", "Microsoft Edge";v="136", "Not.A/Brand";v="99"',
                "Sec-CH-UA-Mobile": "?0",
                "Sec-CH-UA-Platform": '"Windows"',
                "Sec-Fetch-Dest": "empty",
                "Sec-Fetch-Mode": "cors",
                "Sec-Fetch-Site": "same-site",
                "Priority": "u=1, i",
                # Note: ":authority" is not needed in requests; it's handled by the HTTP client
            }
        url = f'https://app.geckoterminal.com/api/p1/search?query={address}'
        async with session.get(url,headers=headers) as response:
            try:
                result = await response.json()
                data = result['data']['attributes']['pools'][0]
                pair = data['address']
                network_id = data['network']['identifier']
                return network_id
            except Exception as e:
                st.error(f'Unable To Request For Contract Info From GeckoTerminal issue {e}')

    # async def pair(self,session,address,pair_endpoint):
    async def pair(self,session,address):
        try:
            task_id = asyncio.create_task(self.fetchNetworkId(session,address))
            network_id = await task_id
            pair_endpoint = f'https://api.geckoterminal.com/api/v2/networks/{network_id}/tokens/{address}/pools?include=base_token&page=1'
            async with session.get(pair_endpoint) as response:
                try:
                    result = await response.json()
                    pair_address = result['data'][0]['attributes']['address']
                    task_poolId = asyncio.create_task(self.Fetch_PoolId_TokenId(session,network_id,pair_address))
                    poolId,pairId = await task_poolId
                    symbol = result['data'][0]['attributes']['name']
                    token_data = {'address':address,  #add 'network_id' = network_id
                                'pair':pair_address,
                                'symbol':symbol,
                                'network_id':network_id,
                                'poolId': f'{poolId}/{pairId}'}
                    self.pairs.append(pair_address)
                    self.tokens_data.append(token_data)
                except ValueError as e:
                    st.error(f'Check If This Contract Address Is Correct : {e}')
        except Exception as e:
            st.error(f'Check If This Mint Address Is Correct: Unable to fetch Pair Info{e}')
    
    async def pair_main(self):
        async with aiohttp.ClientSession() as session:  
            pairs_container = [self.pair(session,address) for address in self.mint_addresses]
            pairs = await asyncio.gather(*pairs_container)

    def fetch_pairs(self): 
        if 'data_frames' not in st.session_state: # so that slide dont refetch data again
            asyncio.run(self.pair_main())

    def NeededData(self,pricedata,timeframe):
        for key,value in pricedata.items():
            token_address = value['address']
            symbol = value['symbol'].split('/')[0]
            network = value['network']
            if 'token_price_info' not in st.session_state:
                st.session_state['token_price_info'] = {}

            if token_address not in st.session_state['token_price_info']:
                st.session_state['token_price_info'][token_address] = { 
                    'Info': ['Entry Price','Price','% Change','Peak Price','% Entry to Peak','lowest Price','Max Drawdown']
                }

            if int(timeframe) > 60:
                    hour = str(timeframe //60)
                    minutes = timeframe %60
                    print(f'{hour}:{minutes}m')
                    
                    timeframe = f'{hour}:{minutes}m'  if minutes > 0  else f'{hour}hr(s)' 
            else:
                timeframe = f'{timeframe}m'  ;  
            st.session_state['token_price_info'][token_address][f'{timeframe}'] = [value[f'{timeframe}']['Entry_Price'],
                                                                                    value[f'{timeframe}']['Price'],
                                                                                    value[f'{timeframe}']['%_Change'],
                                                                                    value[f'{timeframe}']['Peak_Price'],
                                                                                    value[f'{timeframe}']['%_Entry_to_Peak'],
                                                                                    value[f'{timeframe}']['lowest_Price'],
                                                                                    value[f'{timeframe}']['Max_Drawdown']
                                                                                    ]
        data_frame = pd.DataFrame(st.session_state['token_price_info'][token_address])
        return data_frame,token_address,symbol,network

    def slide(self,price_datas:list,timeframe):
        if 'data_frames' not in st.session_state:
            st.session_state['data_frames'] = { }
            
        if 'address_symbol' not in st.session_state:
            st.session_state['address_symbol'] = []
        try:
            data_frames = []
            for pricedata in price_datas:
                data_frame,address,symbol,network = self.NeededData(pricedata,timeframe)
                address_sym = [address,symbol,network ]
                st.session_state['data_frames'][address] = data_frame
                st.session_state['address_symbol'].append(address_sym)
            if 'slide_index' not in st.session_state:
                st.session_state['slide_index'] = 0
            
            def next_slide():
                if st.session_state.slide_index < len(st.session_state['data_frames']) - 1:
                    st.session_state['slide_index'] +=1

            def prev_slide():
                if st.session_state.slide_index > 0:
                    st.session_state['slide_index'] -=1

            address = st.session_state['address_symbol'][st.session_state['slide_index']][0]
            st.badge(f'Token Address : {st.session_state['address_symbol'][st.session_state['slide_index']][0]}',color='violet')
            st.badge(f'Symbol : ${st.session_state['address_symbol'][st.session_state['slide_index']][1]}',color='orange')
            st.badge(f'Network : {st.session_state['address_symbol'][st.session_state['slide_index']][2]}',color='green')
            st.dataframe(st.session_state['data_frames'][address])

            col1,col2,col3 = st.columns([1,2,3])
            with col1:
                if st.button('Prev. CA',disabled=st.session_state['slide_index'] == 0):
                    prev_slide()
            with col2:
                if st.button('Next CA',disabled=st.session_state['slide_index'] == len(st.session_state['data_frames']) -1 ) :
                    
                    next_slide()
        except:
            st.error('Session Ended: Analyze Data Again')
