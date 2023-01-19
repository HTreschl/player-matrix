# -*- coding: utf-8 -*-
"""
Created on Mon Jan  9 15:54:51 2023

@author: hunte
"""
import pandas as pd
import streamlit as st


def lineup_parser(lineups, crit):
    '''parses a list of lineups based on passed criteria'''
    rel_lineups = [x for x in lineups if crit.issubset(x)]
    flat_lineups = [x for y in rel_lineups for x in y]
    counts = pd.DataFrame(flat_lineups, columns=['Name']).groupby('Name')['Name'].count()
    counts = pd.DataFrame(counts).rename(columns = {'Name':'Count'}).reset_index().sort_values(by = 'Count', ascending=False)
    return counts

@st.cache
def data_checker(df):
    '''checks if the current supplied data is valid'''
    columns = list(df.columns)
    expected_columns = ['Name','Team','Opp','Pos','Salary','Fpts']
    if (all(x in columns for x in expected_columns)):
        return True
    else:
        return False
    
@st.cache
def parse_correlation_to_df(corr_dict):
    pos_list = ['QB','RB','WR','TE','Opp QB','Opp RB','Opp WR','Opp TE']
    qb_rb = corr_dict['QB']['RB']
    qb_wr = corr_dict['QB']['WR']
    qb_te = corr_dict['QB']['TE']
    opp_qb = corr_dict['QB']['Opp_QB']
    correlations_array = {'QB':[1,qb_rb,qb_wr,qb_te,opp_qb,opp_qb*qb_rb, opp_qb*qb_wr, opp_qb*qb_te],
                          'RB': [qb_rb, 1, qb_rb*qb_wr, qb_rb*qb_te, opp_qb*qb_rb, opp_qb*qb_rb*qb_rb, opp_qb*qb_rb*qb_wr, opp_qb*qb_rb*qb_te],
                          'WR': [qb_wr, qb_wr*qb_rb, 1, qb_wr*qb_te, opp_qb*qb_wr, opp_qb*qb_wr*qb_rb, opp_qb*qb_wr*qb_wr, opp_qb*qb_wr*qb_te],
                          'TE': [qb_te, qb_te*qb_rb, qb_te*qb_wr, 1, opp_qb*qb_te, opp_qb*qb_te*qb_rb, opp_qb*qb_te*qb_wr, opp_qb*qb_wr*qb_te],
                          'Opp QB': [opp_qb,opp_qb*qb_rb, opp_qb*qb_wr, opp_qb*qb_te,1,qb_rb,qb_wr,qb_te],
                          'Opp RB': [opp_qb*qb_rb, opp_qb*qb_rb*qb_rb, opp_qb*qb_rb*qb_wr, opp_qb*qb_rb*qb_te,qb_rb, 1, qb_rb*qb_wr, qb_rb*qb_te],
                          'Opp WR': [opp_qb*qb_wr, opp_qb*qb_wr*qb_rb, opp_qb*qb_wr*qb_wr, opp_qb*qb_wr*qb_te,qb_wr, qb_wr*qb_rb, 1, qb_wr*qb_te],
                          'Opp TE': [opp_qb*qb_te, opp_qb*qb_te*qb_rb, opp_qb*qb_te*qb_wr, opp_qb*qb_wr*qb_te,qb_te, qb_te*qb_rb, qb_te*qb_wr, 1]}
    corr_df = pd.DataFrame(correlations_array, index = pos_list)
    return corr_df

@st.cache
def get_default_correlations():
    return {'QB':{'WR':.66, 'TE':.33, 'RB':.08, 'Opp_QB':.24}}
