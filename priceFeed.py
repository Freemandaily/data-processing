import sys
import time
import requests,json
from datetime import datetime, timedelta
import streamlit as st



with open('key.json','r') as file:
    keys = json.load(file)
    moralis = keys['moralis']

# moralis = st.secrets['moralis_key']

class price_with_interval:
    def __init__(self):
        self.token_interval_prices = []

def fetchPrice(pair,tweetDate,time_frame,timeframe_prices,get_start_price=None): # accepts pair (3) get the price of the token ,
    from_date = tweetDate[:10]
    date_obj = datetime.strptime(from_date, '%Y-%m-%d')
    new_date = date_obj + timedelta(days=1)
    to_date = new_date.strftime('%Y-%m-%d')


    url = f"https://solana-gateway.moralis.io/token/mainnet/pairs/{pair}/ohlcv?timeframe=5min&currency=usd&fromDate={from_date}&toDate={to_date}&limit=1000"

    headers = {
    "Accept": "application/json",
    "X-API-Key": moralis
    }
    try:
        if not timeframe_prices.token_interval_prices:
            response = requests.request("GET", url, headers=headers)
            if response != 200:
                data = response.json()
                Token_Price_datas = data.get('result',[])
                timeframe_prices.token_interval_prices = Token_Price_datas
            else:
                st.error('Requesting Data from Moralis Failed! App Execution Stopped .Please Reload The Page And Try Again')
                st.stop()
        else:
            Token_Price_datas = timeframe_prices.token_interval_prices

        for price_data in Token_Price_datas:
            moralis_date_obj = datetime.fromisoformat(price_data['timestamp'].replace('Z', '+00:00'))
            Moralis_formatted_date = moralis_date_obj.strftime("%Y-%m-%d %H:%M:%S")

            if get_start_price:
                time_frame_time = tweeted_timeframe(tweetDate)
            else:
                time_frame_time = timeFrame(tweetDate,time_frame)

            if Moralis_formatted_date == time_frame_time:
                open = price_data['open']
                high_price = price_data['high']
                low_price = price_data['low']
                close_price = price_data['close']
                return close_price

    except Exception as e:
        st.error('Failed To Fetch Token Price Data! Please Reload The Page because Execution has Terminated')
        st.stop()
    


def timeFrame(tweetDate,time_frame): # Computing  The Timeframe
    date_obj = datetime.strptime(tweetDate, "%Y-%m-%d %H:%M:%S")
    five_min_later = date_obj + timedelta(minutes=time_frame)
    minutes = five_min_later.minute
    seconds = five_min_later.second
    adjustment = timedelta(minutes=(5 - (minutes % 5)) if minutes % 5 > 2 else -(minutes % 5), 
                        seconds=-seconds)
    nearest_interval = five_min_later + adjustment
    time_frame_time = nearest_interval.strftime("%Y-%m-%d %H:%M:%S")
    return time_frame_time

def tweeted_timeframe(tweetDate): # Get the Rounding Time for Price Calculation
    date_obj = datetime.strptime(tweetDate, "%Y-%m-%d %H:%M:%S")

    minutes = date_obj.minute
    seconds = date_obj.second

    if minutes % 5 == 0 and seconds == 0:
        nearest_interval = date_obj
    else:
        minutes_past = minutes % 5
        seconds_total = minutes_past * 60 + seconds
        if seconds_total < 150:  # 2.5 minutes = 150 seconds
            adjustment = timedelta(minutes=-minutes_past, seconds=-seconds)
        else:
            adjustment = timedelta(minutes=(5 - minutes_past), seconds=-seconds)
        
        nearest_interval = date_obj + adjustment
    tweeted_time = nearest_interval.strftime("%Y-%m-%d %H:%M:%S")
    return tweeted_time


def percent_increase(initial_price:str,ending_price:str) -> str:
    try:
        percent = str(round(((ending_price - initial_price) /initial_price ) * 100,2))
        
        if not percent.startswith('-'):
            percent = '+'+ percent + '%'
        else:
            percent = percent + '%'
        return percent
    except:
        return None

def fetchMessage():
    with st.spinner('Analyzing Token Prices. Please Wait....... '):
        time.sleep(3)

# Getting the different price timeframe 
def Tweet_tokenInfoProcessor(jup_token_datas:dict,tweet_token_detail:dict):
    structured_data = {}
    for date , token_fetched in tweet_token_detail.items():
        structured_data[date] = {}

        token_symbol = [symbol[1:].upper() for symbol in token_fetched['Token_names']]
        token_contracts = [contract.upper() for contract in token_fetched['contracts']]
        username  = token_fetched['username']
        
        for jupToken in jup_token_datas:
           
            try:
               
                if jupToken['symbol'].upper() in token_symbol:
                        if 'valid contracts' in st.session_state:
                            if jupToken['address'].upper() not in st.session_state['valid contracts']: # Make sure that only searched contract are matched
                                continue
                        print('Token With Same Symbol Found')
                        timeframe_prices = price_with_interval()
                        pair_address = dexScreener_token_data(jupToken['address']) # Call to get token pair address from dexscreener
                        if 'Error' in pair_address:
                            print(pair_address['Error'])
                            continue
                        structured_data[date][jupToken['address']] = {'pair':pair_address,
                                                                    'symbol':jupToken['symbol'],
                                                                    'username': username} 
                        structured_data[date][jupToken['address']]['Price_Tweeted_At'] = fetchPrice(pair_address,date,5,timeframe_prices,get_start_price='YES')
                        structured_data[date][jupToken['address']]['price_5m'] = fetchPrice(pair_address,date,5,timeframe_prices) # 5 min timeFrame
                        structured_data[date][jupToken['address']]['price_10m'] = fetchPrice(pair_address,date,10,timeframe_prices) 
                        structured_data[date][jupToken['address']]['price_15m'] = fetchPrice(pair_address,date,15,timeframe_prices)
                        structured_data[date][jupToken['address']]['price_5m%Increase'] = percent_increase(structured_data[date][jupToken['address']]['Price_Tweeted_At'],structured_data[date][jupToken['address']]['price_5m'])
                        structured_data[date][jupToken['address']]['price_10m%Increase'] = percent_increase(structured_data[date][jupToken['address']]['Price_Tweeted_At'],structured_data[date][jupToken['address']]['price_10m'])
                        structured_data[date][jupToken['address']]['price_15m%Increase'] = percent_increase(structured_data[date][jupToken['address']]['Price_Tweeted_At'],structured_data[date][jupToken['address']]['price_15m'])
                        timeframe_prices.token_interval_prices = []
            except KeyboardInterrupt :
                Error_message = {'Error':'Application Runs Interrupted','Message':'Fetching Token Price Ranges'}
                return Error_message
        if len(token_contracts) > 0: # Simple checking for contracts list
           for jupToken in jup_token_datas:
                if jupToken['address'].upper() in token_contracts:
                    print('Contract found')
                    timeframe_prices = price_with_interval()
                    pair_address = dexScreener_token_data(jupToken['address']) # Call to get the pair address from dexscreener
                    if 'Error' in pair_address:
                        print(pair_address['Error'])
                        continue
                    structured_data[date][jupToken['address']] = {'pair':pair_address,
                                                              'symbol':jupToken['symbol'],
                                                              'username': username}
                    structured_data[date][jupToken['address']]['Price_Tweeted_At'] = fetchPrice(pair_address,date,5,timeframe_prices,get_start_price='YES')
                    structured_data[date][jupToken['address']]['price_5m'] = fetchPrice(pair_address,date,5,timeframe_prices)
                    structured_data[date][jupToken['address']]['price_10m'] = fetchPrice(pair_address,date,10,timeframe_prices) # 10 Minute Timeframe
                    structured_data[date][jupToken['address']]['price_15m'] = fetchPrice(pair_address,date,15,timeframe_prices)
                    structured_data[date][jupToken['address']]['price_5m%Increase'] = percent_increase(structured_data[date][jupToken['address']]['Price_Tweeted_At'],structured_data[date][jupToken['address']]['price_5m'])
                    structured_data[date][jupToken['address']]['price_10m%Increase'] = percent_increase(structured_data[date][jupToken['address']]['Price_Tweeted_At'],structured_data[date][jupToken['address']]['price_10m'])
                    structured_data[date][jupToken['address']]['price_15m%Increase'] = percent_increase(structured_data[date][jupToken['address']]['Price_Tweeted_At'],structured_data[date][jupToken['address']]['price_15m'])
                    timeframe_prices.token_interval_prices = []
    

    if 'valid contracts' in st.session_state:
        del st.session_state['valid contracts']

    structured_data= { date:value for date,value in structured_data.items() if value}
    if structured_data:
       st.toast('Filtering  Fetched Token Price Data!')
       print('Filtering  Fetched Token Price Data!')
       time.sleep(10)
       return structured_data
    else:
        Error_message = {'Error':'Unable To Fetch Tokens Prices Data\nPlease Check Your Provider Usage eg Moralis!','Message':'Filtering  Fetched Token Price Data!'}
        return Error_message
    
    
# This Function fetches token address by searching with token symbols 
def token_tweeted_analyzor(tweet_token_detail:dict,strict_token='Strict Token')-> dict: 
    print('Fetching Tweeted Token Datas and Price TimeFrames Please Wait..')
    try:
        if strict_token == 'Strict Token':
            tokens_list_url = "https://token.jup.ag/strict"
        else:
            tokens_list_url = "https://token.jup.ag/all"
        

        response = requests.get(tokens_list_url) 
        status = response.status_code
        if status == 200:
            try:
                token_datas = response.json()
                analyzor = Tweet_tokenInfoProcessor(token_datas,tweet_token_detail)

                if 'Error' in analyzor:
                    return analyzor
                # print(analyzor)
                for date in analyzor: # filter
                    analyzor[date] = {
                        key : value for key,value in analyzor[date].items() if value['Price_Tweeted_At'] != None
                    }
                
                return analyzor
               
            except json.JSONDecodeError:
                Error_message = {'Error':"Error in Fetching Token List: Response is not valid JSON",'Message':'Fetching Token List. Please Wait....'}
                return Error_message
            except KeyError as e:
                Error_message = {'Error':f"Error in Fetching Token List:{e}",'Message':'Fetching Token List. Please Wait....'}
                return Error_message
            except TypeError as e:
                Error_message = {'Error':f"Error in Fetching Token List: {e}",'Message':'Fetching Token List. Please Wait....'}
                return Error_message
    except requests.exceptions.ConnectionError:
        Error_message = {'Error':f"Error: Failed to connect to the {strict_token}",'Message':'Fetching Token List. Please Wait....'}
        return Error_message
    except requests.exceptions.Timeout:
        Error_message = {'Error':f"Error: Request timed out for{strict_token}",'Message':'Fetching Token List. Please Wait....'}
        return Error_message
    except requests.exceptions.RequestException as e:
        Error_message = {'Error':f"Error: A network-related error occurred: {e}",'Message':'Fetching Token List. Please Wait....'}
        return Error_message
    except KeyboardInterrupt:
        Error_message = {'Error':'Application Runs Interrupted'}


def dexScreener_token_data(mint_address): # fetches token pairs seaching with token address (2)
    url = f'https://api.dexscreener.com/latest/dex/tokens/{mint_address}'
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        token_data = data.get('pairs',[])
        pair = token_data[0]['pairAddress']
        return pair
    except requests.exceptions.ConnectionError:
        st.error(f'Error :Failed to connect to {url}! App Executin Has Stopped!  Please Reload The Page')
        st.stop()
       #  print(f'Error :Failed to connect to {url}')
    except requests.exceptions.Timeout:
        st.error(f"Error: Request timed out for{url}!. App Executin Has Stopped!  Please Reload The Page")
        st.stop()
        # print(f"Error: Request timed out for{url}")
    except requests.exceptions.RequestException as e:
        st.error(f"Error: A network-related error occurred! App Executin Has Stopped!  Please Reload The Page:")
        st.stop()
        # print(f"Error: A network-related error occurred: {e}")
    except KeyboardInterrupt:
        pass
    except Exception as e:
        Error_message = {'Error':'Token Not Found'}
        return Error_message

