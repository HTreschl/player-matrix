# -*- coding: utf-8 -*-
"""
Created on Sun Jan  8 15:28:03 2023

@author: hunte
"""
import streamlit as st
import pandas as pd
import runSims as sims

#instantiate
st.title('Optimal PLayer Degrees of Seperation')
#initial data
df = pd.DataFrame()
sim_results = pd.DataFrame()

#get data from upload
dat = st.sidebar.file_uploader('Upload CSV Player Data Here')

upload_button = st.sidebar.button('Data Uploaded')

if upload_button:
    df = pd.read_excel(dat)
    #show data
with st.expander('Uploaded Data'):
    st.dataframe(df)


count = st.sidebar.number_input('How many sims to run?')
sims_button = st.sidebar.button('Run Sims')
if sims_button:
    sim_results = sims.standard_sims(df, 'nfl', count, fpts_col_name='avg fpts', ceil_column = 'avg ceil', floor_column = 'avg floor', include_correlations=True)        
    
    
with st.expander('Sims Results'):
    st.dataframe(sim_results)
