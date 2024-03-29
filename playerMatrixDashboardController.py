# -*- coding: utf-8 -*-
"""
Created on Mon Jan  9 15:54:51 2023

@author: hunte
"""
import pandas as pd
import streamlit as st
import Optimizer as opt
import networkx as nx
import plotly.express as px


def createNodeChart3D(data, min_weight=5, scale=2.0, player_filter=[]):
    # Filter data based on player_filter
    data = [d for d in data if set(player_filter).issubset(set(d))]

    # Create an empty graph
    G = nx.Graph()

    # Create a dictionary to store edge weights
    edge_weights = {}

    # Iterate through the data and add edges based on shared elements
    for sublist in data:
        for i, node1 in enumerate(sublist):
            for j, node2 in enumerate(sublist):
                if i < j:
                    edge = (node1, node2)
                    if edge in edge_weights:
                        edge_weights[edge] += 1
                    else:
                        edge_weights[edge] = 1

    # Add edges to the graph with their corresponding weights, but only if weight >= min_weight
    for edge, weight in edge_weights.items():
        if weight >= min_weight:
            G.add_edge(edge[0], edge[1], weight=weight)

    # Extract node positions from the graph
    pos = nx.kamada_kawai_layout(G, scale=scale, dim=3)

    # Create a DataFrame from the node positions
    nodes_df = pd.DataFrame(pos).T
    nodes_df.columns = ['X', 'Y', 'Z']

    # Create an interactive 3D scatter plot using Plotly
    fig = px.scatter_3d(nodes_df, x='X', y='Y', z='Z', text=nodes_df.index)

    # Customize the appearance and interactivity if needed
    fig.update_traces(marker=dict(size=10))

    # Show the interactive plot
    fig.show()

    return G, fig


def lineup_parser(lineups: list, crit: set):
    '''parses a list of lineups based on passed criteria to get the lineups including those players'''
    df = pd.DataFrame(lineups, columns = ['Player','Lineup Score'])
    df = df.explode('Player')
    df['Name'] = [x[0] for x in df['Player']]
    df['Position'] = [x[1] for x in df['Player']]
    df['Team'] = [x[2] for x in df['Player']]
    df = df.drop(columns = ['Player','Lineup Score'])
    df['group'] = df.groupby(df.index)['Name'].apply(list)
    
    flat_lineups = df[df['group'].apply(lambda x: crit.issubset(x))]
    counts = flat_lineups.groupby('Name')['Name'].count()
    counts = pd.DataFrame(counts).rename(columns = {'Name':'Count'}).reset_index().sort_values(by = 'Count', ascending=False)
    return counts


def get_stacks(df, stack, by_col = 'Optimal Ownership'):
    '''given a dataframe of results from sims.mlb.standard sims, returns the most optimal stacks given a stack size'''
    df = df[df['Position']!='SP']  
    prim_df = df.groupby('Team').apply(lambda x: x.sort_values(by = by_col,ascending=False).head(stack)).drop(columns = ['Team']).reset_index()
    top_teams = prim_df.groupby('Team')[by_col].sum().reset_index().sort_values(by = by_col, ascending=False)
    res = top_teams.merge(prim_df, how = 'left', on = 'Team').drop(columns = ['{}_x'.format(by_col)]).rename(columns = {'{}_y'.format(by_col):by_col})
    return res
    
    

@st.cache
def data_checker(df, sport):
    '''checks if the current supplied data is valid'''
    columns = list(df.columns)
    if sport =='NFL':
        expected_columns = ['Name','Team','Opp','Pos','Salary','Fpts']
    elif sport == 'MLB':
        expected_columns = ['Name','Team','Opp','Position','Salary']
    else:
        return False
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

@st.cache
def get_baseline_optimal(df):
    result = opt.NFL(df).standard_optimizer(df, objective_fn_column='Fpts')
    res_df = df[df['Name'].isin(result)]
    return res_df

@st.cache
def parse_lineups(lineups_list):
    '''given a lieups list from the mlb sims, returns a dataframe of the top projected lineups and their characteristics'''
    df = pd.DataFrame(lineups_list, columns = ['Player','Lineup Score'])
    df = df.explode('Player')
    df['Name'] = [x[0] for x in df['Player']]
    df['Position'] = [x[1] for x in df['Player']]
    df['Team'] = [x[2] for x in df['Player']]
    df = df.drop(columns = ['Player'])
    #calculate stack params
    hitters = df[df['Position']!= 'SP']
    groups = hitters.groupby([hitters.index,'Team'])['Position'].count().reset_index()
    groups = groups.groupby('level_0').apply(lambda x: dict(zip(x['Team'],x['Position'])))
    groups = groups.apply(lambda x: {k:v for k,v in sorted(x.items(), key=lambda y:y[1], reverse = True)})
    groups.name= 'Stacks' #set the name to merge
    df = df.merge(groups, how = 'left', left_index=True, right_index = True)
    #get max stack size
    df['Max Size'] = [max(x.values()) for x in df['Stacks']]
    df['Summary'] = [list(x.values()) for x in df['Stacks']]
    return df

@st.cache
def get_lineup_counts(lineups_list):
    '''given a list of lineups from mlb sims, returns a dataframe of the lineup and the number of times it occurred'''
    df = pd.DataFrame(lineups_list, columns = ['Player','Lineup Score'])
    df['Player'] = [';'.join([y[0] +',' + y[2] for y in x]) for x in df['Player']] #player column is a list of lists
    d = df.groupby('Player').count().reset_index()
    return d
    

