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
st.title('DFS Degrees of Separation')
sample_data = pd.read_csv('Sample App Data.csv')
#initial data caching
st.session_state.key = 'sim results'
st.session_state.key = 'input data'
st.session_state.key = 'lineups'
st.session_state.key = 'player matches'
st.session_state.key = 'relationships data'
st.session_state.key = 'sim count'

#initial tab layout
intro_tab, data_tab, sims_tab, relationships_tab = st.tabs(['What is this?','Import Projections','Run Sims', 'Explore Relationships'])

#write documentation
with intro_tab:
    st.header('FAQ')
    with st.expander('What does this tool do?'):
        st.write('''The degrees of separation tool allows you to run game simulations using your own player projections and quickly visualize the frequency with which players appear together.
                 For example, if you are building a stack with Allen, you might want to know whether the sims find a 1,2, or 3 receiver stack most frequently in the optimal lineups.
                 The tool also includes the ability to run sims for all players and determine the optimal frequency a player will appear.
                 ''')
    with st.expander('How can this help me?'):
        st.write('''We all know stacking teams and maximizing within-lineup correlation is key to profitably playing DFS. However, there is also a tradeoff for correlation in lineup ceiling. 
                 Let's say you want Mahomes and Kelce in a lineup. It might be tempting to include Smith-Schuster for the correlation, but he might not be the highest projected receiver at
                 that pricepoint. This tool runs the sims and presents the tradeoff between correlation and ceiling.
                 ''')
    with st.expander('How do I use it?'):
        st.write('''For starters, you'll need to upload a csv file with your player projections in the "Import Projections" tab. A schematic sheet is 
                 available for download for example formatting (WIP). Once you've uploaded projections, you can run sims and get the mathematically optimal play rate for each player. 
                 Once you've run the sims, dive into the data in the "explore Relationships" section.
                 ''')
                 

#get data from upload
with data_tab:
    dat = st.file_uploader('Upload CSV Player Data Here')
    st.download_button('Download a Template', data = sample_data.to_csv().encode('utf-8'), file_name = 'Sample DFS Data.csv')

if dat is not None:
    df = pd.read_csv(dat)
    st.session_state['input data'] = df
    with data_tab:
        st.subheader('Imported Data')
        st.dataframe(st.session_state['input data'])
    
#sims tab
with sims_tab:
    st.subheader('Sims Settings')    
    count = int(st.number_input('How many sims to run?'))    
    sims_button = st.button('Run Sims')
    
if sims_button:
    sims_results,lineups = sims.standard_sims(df, 'nfl', count, fpts_col_name='Fpts', ceil_column = 'Ceil', floor_column = 'Floor', include_correlations=True)
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
        st.subheader('Optimal Pairings for {}'.format(', '.join(selected_players)))
        filtered_players = controller.lineup_parser(st.session_state['lineups'], selected_players)
        tot_matching_lineups = list(filtered_players.loc[filtered_players['Name']==list(selected_players)[0], ['Count']]['Count'])[0]
        filtered_players = filtered_players[filtered_players['Name'].isin(selected_players)==False]
        filtered_players['% of Filtered Lineups'] = (filtered_players['Count']/tot_matching_lineups)*100
        filtered_players['% of Total Lineups'] = (filtered_players['Count']/st.session_state['sim count'])*100
        filtered_players = filtered_players.set_index('Name')
        st.session_state['relationships data'] = filtered_players
        st.dataframe(st.session_state['relationships data'])      
    
