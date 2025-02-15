import streamlit as st
import pandas as pd
import numpy as np

# Title
st.title("Streamlit Crash Course")

# Sidebar
with st.sidebar:
    st.header('st.sidebar')
    st.write('this is a practice area for the Streamlit crash course')

# Header with a divider
st.header('Header looks looks like this', divider='blue')

# Write some Markdown
st.markdown('We can also write markdown \n\n-see Streamlit documentation for emoji codes etc.')

# Structure the page into columns
st.header('st.columns')
col1, col2 = st.columns(2)

# Include a user input slider in column 1
with col1:
    x = st.slider('Choose a value', 1, 10)
# Write the output in column 2
with col2:
    st.write('The Value of :blue[**x**] is', x)

st.header('st.area_chart')
# Throw some data into a dataframe and plot it
chart_data = pd.DataFrame(np.random.randn(20,3))
st.area_chart(chart_data)