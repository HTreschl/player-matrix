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
#initial data caching
st.session_state.key = 'sim results'
st.session_state.key = 'input data'
st.session_state.key = 'lineups'
st.session_state['sim results '] = pd.DataFrame()
st.session_state['input data']  = pd.DataFrame()

#initial tab layout
data_tab, sims_tab, explore_tab = st.tabs(['Import Projections','Run Sims', 'Explore Relationships'])


#get data from upload
dat = st.sidebar.file_uploader('Upload CSV Player Data Here')

if dat is not None:
    df = pd.read_excel(dat)
    st.session_state['input data'] = df
    with data_tab:
        st.dataframe(st.session_state['input data'])
    

with sims_tab:    
    count = int(st.sidebar.number_input('How many sims to run?'))    
    sims_button = st.sidebar.button('Run Sims')
    
if sims_button:
    sims_results,lineups = sims.standard_sims(df, 'nfl', count, fpts_col_name='avg fpts', ceil_column = 'avg ceil', floor_column = 'avg floor', include_correlations=True) 
    st.session_state['sim results'] = sims_results
    st.session_state['lineups'] = lineups
    
                
with sims_tab:
    st.subheader('Sims Results')
    st.dataframe(st.session_state['sim results'])
    
