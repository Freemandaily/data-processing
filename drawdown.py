import streamlit as st
import pandas as pd

if "handles_data" in st.session_state:
    token_data = st.session_state['handles_data']   
else: 
    st.error('Please Run The Main App First ')
    st.stop()

def max_drawdown(token_data,index):
    prices = token_data[index]['prices']
    max_so_far = prices[0]
    max_drawdown  = 0
    
    try:
        for price in prices:
            if price > max_so_far :
                max_so_far = price
            drawadown = (( price - max_so_far) / max_so_far) * 100
            max_drawdown = min(drawadown,max_drawdown)
    except:
        max_drawdown = 0 
        max_price = 0

    return max_drawdown,max_price
def compute_DrawDown(token_data,index):
    data = pd.DataFrame()
    data['Prices (usd)'] = token_data[index]['prices']
    data['Time'] = [0, 5, 10]
    data['max_so_far'] = data['Prices (usd)'].cummax()
    data['Drawdown (%)'] = ((data['Prices (usd)'] - data['max_so_far']) / data['max_so_far']) * 100 
    return data


if 'slide_index' not in st.session_state:
    st.session_state['slide_index'] = 0

def next_slide():
    if st.session_state.slide_index < len(token_data) - 1:
        st.session_state['slide_index'] +=1


def prev_slide():
    if st.session_state.slide_index > 0:
        st.session_state['slide_index'] -=1


current_slide = token_data[st.session_state['slide_index']]
data = compute_DrawDown(token_data,st.session_state['slide_index'])
st.badge(f'DrawDown Run For {current_slide['username']} Tweets ON ${current_slide['token']}',color='green')
st.markdown("**X-axis: Time Interval | **Y-axis**: Prices (USD)")
st.line_chart(data.set_index('Time')['Prices (usd)'],use_container_width=True)
maximium_drawdown,maximium_price = max_drawdown(token_data,st.session_state['slide_index'])
st.badge(f'Peak Price: ${round(maximium_price,4)}',color='green')
st.badge(f'Max Drawdown: {round(maximium_drawdown,3)}%',color='red')
st.dataframe(data[['Prices (usd)','Drawdown (%)']])


col1,col2,col3 = st.columns([1,2,3])
with col1:
    if st.button('Previous',disabled=st.session_state == 0):
        prev_slide()

with col2:
    if st.button('Next',disabled=st.session_state == len(token_data) -1 ):
        next_slide()
        
st.write(f'Slide {st.session_state['slide_index'] + 1} of {len(token_data)}')