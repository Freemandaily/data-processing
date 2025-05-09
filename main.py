import streamlit as st


navi =st.navigation([st.Page('app.py',title='Main App'),st.Page('drawdown.py',title='Drawdown')])


navi.run()
