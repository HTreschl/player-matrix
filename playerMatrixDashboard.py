# -*- coding: utf-8 -*-
"""
Created on Sun Jan  8 15:28:03 2023

@author: hunte
"""
import streamlit as st
import pandas as pd
import runSims as sims
import playerMatrixDashboardController as controller

#instantiate
st.title('Optimal PLayer Degrees of Seperation')
#initial data caching
st.session_state.key = 'sim results'
st.session_state.key = 'input data'
st.session_state.key = 'lineups'
st.session_state.key = 'player matches'
st.session_state.key = 'relationships data'
st.session_state.key = 'sim count'

#initial tab layout
data_tab, sims_tab, relationships_tab = st.tabs(['Import Projections','Run Sims', 'Explore Relationships'])


#get data from upload
with data_tab:
    dat = st.file_uploader('Upload CSV Player Data Here')

if dat is not None:
    df = pd.read_excel(dat)
    st.session_state['input data'] = df
    with data_tab:
        st.dataframe(st.session_state['input data'])
    
#sims tab
with sims_tab:    
    count = int(st.number_input('How many sims to run?'))    
    sims_button = st.button('Run Sims')
    
if sims_button:
    sims_results,lineups = sims.standard_sims(df, 'nfl', count, fpts_col_name='avg fpts', ceil_column = 'avg ceil', floor_column = 'avg floor', include_correlations=True)
    st.session_state['sim results'] = sims_results
    st.session_state['lineups'] = lineups
    st.session_state['sim count'] = count
    with sims_tab:
        st.subheader('Sims Results')
        st.dataframe(st.session_state['sim results'])
else:
    with sims_tab:
        st.subheader('Sims Results')
        st.dataframe(st.session_state['sim results']) 
    
#relationships tab
with relationships_tab:
    player_options = list(st.session_state['sim results'].index)
    selected_players = set(st.multiselect('Players to Include', options = player_options))
    if len(selected_players) > 0:
        filtered_players = controller.lineup_parser(st.session_state['lineups'], selected_players)
        tot_matching_lineups = list(filtered_players.loc[filtered_players['Name']==list(selected_players)[0], ['Count']]['Count'])[0]
        filtered_players = filtered_players[filtered_players['Name'].isin(selected_players)==False]
        filtered_players['% of Filtered Lineups'] = (filtered_players['Count']/tot_matching_lineups)*100
        filtered_players['% of Total Lineups'] = (filtered_players['Count']/st.session_state['sim count'])*100
        filtered_players = filtered_players.set_index('Name')
        st.session_state['relationships data'] = filtered_players
        st.dataframe(st.session_state['relationships data'])      
    
