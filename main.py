import streamlit as st


navi =st.navigation([st.Page('appv2.py',title='Main App'),st.Page('drawdown.py',title='Drawdown')])


navi.run()