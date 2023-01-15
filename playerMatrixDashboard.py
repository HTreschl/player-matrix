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
sample_data = pd.read_csv('Sample App Data.csv') #upload sample data
#initial data caching
st.session_state.key = 'sim results'
if 'sim results' not in st.session_state:
    st.session_state['sim results'] = pd.DataFrame()
st.session_state.key = 'input data'
if 'input data' not in st.session_state:
    st.session_state['input data'] = pd.DataFrame()
st.session_state.key = 'lineups'
if 'lineups' not in st.session_state:
    st.session_state['lineups'] = []
st.session_state.key = 'relationships data'
if 'relationships data' not in st.session_state:
    st.session_state['relationships data'] = pd.DataFrame()
st.session_state.key = 'sim count'
if 'sim count' not in st.session_state:
    st.session_state['sim count'] = 1
st.session_state.key = 'correlation dict'
if 'correlation dict' not in st.session_state:
    st.session_state['correlation dict'] = {'QB':{'WR':.66,'TE':.33,'RB':.08, 'Opp_QB':.24}}

#set global constants
has_valid_data = controller.data_checker(st.session_state['input data'])

#initial tab layout and title
st.title('DFS Degrees of Separation')
intro_tab, data_tab, sims_tab, relationships_tab, correlations_tab = st.tabs(['What is this?','Import Projections','Run Sims', 'Explore Relationships', 'Edit Correlations'])


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
                 

#get data from upload, data sample, and example download
with data_tab:
    dat = st.file_uploader('Upload CSV Player Data Here')
    col1,col2 = st.columns(2)
    
    with col1:
        st.download_button('Download a Template', data = sample_data.to_csv().encode('utf-8'), file_name = 'Sample DFS Data.csv')
        st.caption('Replace column values with your own projections. Ceiling, floor, and ownership columns are optional.')
    with col2:
        sample_button = st.button('Use Sample Data')

if sample_button:
    st.session_state['input data'] = sample_data

if dat is not None:
    df = pd.read_csv(dat)
    st.session_state['input data'] = df   
    has_valid_data = controller.data_checker(st.session_state['input data'])

#if valid data exists
if has_valid_data:
    with data_tab:
        st.subheader('Imported Data')
        st.dataframe(st.session_state['input data'])
    
    #sims tab
    with sims_tab:
        st.subheader('Sims Settings')    
        count = int(st.number_input('How many sims to run?'))    
        sims_button = st.button('Run Sims')
        
    if sims_button: #run the sims
        status_bar = st.progress(0)
        sims_results,lineups = sims.standard_sims(st.session_state['input data'], 'nfl', count,correlation_value = st.session_state['correlation dict'], fpts_col_name='Fpts', ceil_column = 'Ceil', floor_column = 'Floor', status_bar=status_bar)
        st.session_state['sim results'] = sims_results
        st.session_state['lineups'] = lineups
        st.session_state['sim count'] = count
        with sims_tab:
            st.subheader('Sims Results')
            st.dataframe(st.session_state['sim results'])
            st.download_button('Download Sims Results', data = st.session_state['sim results'].to_csv().encode('utf-8'), file_name = 'Sim Results.csv')
    else: #persist the results table
        with sims_tab:
            st.subheader('Sims Results')
            st.dataframe(st.session_state['sim results'])
            st.download_button('Download Sims Results', data = st.session_state['sim results'].to_csv().encode('utf-8'), file_name = 'Sim Results.csv')
        
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
            
else: #no valid data
    with data_tab:
        st.subheader('Input data not available or format is incorrect. Upload data or confirm column names match the template')
    with sims_tab:
        st.subheader('Upload data to run sims')
    with relationships_tab: 
        st.subheader('Upload data and run sims to see player relationships')
        
#correlations section
with correlations_tab:
    #order: qb,rb,wr,te,opp qb, opp rb, opp wr, opp te
    corr_dict = st.session_state['correlation dict']
    pos_list = ['QB','RB','WR','TE','Opp QB','Opp RB','Opp WR','Opp TE']
    qb_rb = corr_dict['QB']['RB']
    qb_wr = corr_dict['QB']['WR']
    qb_te = corr_dict['QB']['TE']
    qb_opp_qb = corr_dict['QB']['Opp_QB']
    correlations_array = {'QB':[1,qb_rb,qb_wr,qb_te,qb_opp_qb,qb_opp_qb*qb_rb, qb_opp_qb*qb_wr, qb_opp_qb*qb_te]}
    corr_df = pd.DataFrame(correlations_array, index = pos_list)
    st.dataframe(corr_df)
