import streamlit as st
import pandas as pd
import numpy as np

st.title("Hii")

st.write("YOooo")

df = pd.DataFrame({
    'first': [1,2,3,4],
    'second': [5,6,7,8]
})

st.write(df)

chart = pd.DataFrame(
    np.random.randn(20,3), columns=['a','b','c']
)

st.line_chart(chart)

name = st.text_input("Enter your name: ")
age = st.slider("Enter age",1,100,18)
st.write(f"Age: {age}")
if name:
    st.write(f"Hello {name}")