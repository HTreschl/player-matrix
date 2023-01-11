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
    
