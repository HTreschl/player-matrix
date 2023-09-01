# -*- coding: utf-8 -*-
"""
Created on Mon Aug 23 18:24:22 2021

@author: Hunter Treschl
"""
import pandas as pd
import pulp
import numpy as np
import math
import os

def get_download_path():
     """Returns the default downloads path for linux or windows"""
     if os.name == 'nt':
         import winreg
         sub_key = r'SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders'
         downloads_guid = '{374DE290-123F-4565-9164-39C4925E467B}'
         with winreg.OpenKey(winreg.HKEY_CURRENT_USER, sub_key) as key:
             location = winreg.QueryValueEx(key, downloads_guid)[0]
         return location
     else:
        return os.path.join(os.path.expanduser('~'), 'downloads')    


class MLB():
    '''MLB Optimizer'''
    '''Columns: Name, Fpts, Position,Team, Salary'''
    
    def __init__(self, df): 
        self.salary_cap = 50000 
        self.roster =['P','P','C','1B','2B','3B','SS','OF','OF','OF']
        self.df = df
        #self.solver = pulp.getSolver('CPLEX_CMD')
        
    def prep_df(self):
        positions = self.df['Position'].apply(lambda x: pd.Series(x.split('/')))
        
        #create dummies for position
        dummies_1 = pd.get_dummies(positions[0])
        dummies_2 = pd.get_dummies(positions[1])
        
        #merge into one set of dummies
        p_dummies = dummies_1.merge(dummies_2, left_index=True, right_index=True)
        pos = ['1B','2B','3B','OF','SS','C']
        for p in pos:
            if p not in [col for col in p_dummies]: #corner case if a position has only players that don't flex
                p_dummies[p] = p_dummies[p+'_x'] + p_dummies[p + '_y']
        p_dummies = p_dummies[pos + ['SP']]
        #merge
        df = self.df.merge(p_dummies, left_index=True, right_index=True)
        
        #create team dummies
        team_dummies = pd.get_dummies(df['Team'], prefix='t')
        df = df.merge(team_dummies, left_index=True, right_index=True)
        
        #opp dummies
        opp_dummies = pd.get_dummies(df['Opp'], prefix = 'o_')
        df = df.merge(opp_dummies, left_index=True, right_index = True)
        
        
        #pitchers and hitters
        df['hitters'] = np.where(df['Position']!='SP', 1, 0)
        df['pitchers'] = np.where(df['Position']=='SP', 1, 0)
        return df
    
    
    def standard_optimizer(self, df, objective_fn_column, stack = None, no_opps = False, return_score = False):
        '''
        
        Parameters
        ----------
        df : dataframe
            generated by prep_df. Columns: Name, Fpts, Position,Team, Salary.
        objective_fn_column : string
            name of column containing objective values.
        five_three : TYPE, optional
            determines whether to 5/3 stack. The default is True.
        no_opps : TYPE, optional
            determines whether pitchers play hitters. The default is False.

        Returns
        -------
        results : dataframe
            the players in the optimized lineup.

        '''        
        #final cleaning
        df = df[df[objective_fn_column].isnull()==False]
        
        #define problem
        prob = pulp.LpProblem('MLB', pulp.LpMaximize)
        
        #create lineup list
        lineup = pulp.LpVariable.dicts('players',df.index, cat='Binary')
        
        #add constraints
        #player count
        prob += pulp.lpSum([lineup[i] for i in df.index]) == 10
        #position constraints
        prob += pulp.lpSum([df['SP'][i]*lineup[i] for i in df.index]) == 2
        prob += pulp.lpSum([df['1B'][i]*lineup[i] for i in df.index]) == 1
        prob += pulp.lpSum([df['2B'][i]*lineup[i] for i in df.index]) == 1
        prob += pulp.lpSum([df['3B'][i]*lineup[i] for i in df.index]) == 1
        prob += pulp.lpSum([df['SS'][i]*lineup[i] for i in df.index]) == 1
        prob += pulp.lpSum([df['OF'][i]*lineup[i] for i in df.index]) == 3
        prob += pulp.lpSum([df['C'][i]*lineup[i] for i in df.index]) == 1
        #salary constraint
        prob += pulp.lpSum([df['Salary'][i] * lineup[i] for i in df.index]) <= 50000

        '''
        #five three stack       
        if stack:
            #determine which teams are stacked 
            teams = set(df['Team'])            
            stack_primary = pulp.LpVariable.dicts('teams_primary',teams, cat='Binary')
            stack_secondary = pulp.LpVariable.dicts('teams_secondary',teams, cat='Binary')
            prob += pulp.lpSum([stack_primary[i] for i in teams]) == 1
            prob += pulp.lpSum([stack_secondary[i] for i in teams]) == 2
            #stack_params = [pulp.LpVariable('stack_{}_{}'.format(x[0],x[1]),cat='Binary') for x in stack]
            #prob += pulp.lpSum([stack_params[i] for i in range(len(stack))]) == 1
            for s_it,s in enumerate(stack):
                for t in teams:
                    sl = df[(df['t_'+t]==1) & (df['hitters']==1)] 
                    #set stack size
                    prob += (s[0]*stack_primary[t]<= pulp.lpSum([sl['hitters'][i]*lineup[i] for i in sl.index]))
                    prob += (s[1]*stack_secondary[t]<= pulp.lpSum([sl['hitters'][i]*lineup[i] for i in sl.index]))
          
        '''    
        if stack:
            teams = set(df['Team'])            
            stack_5 = pulp.LpVariable.dicts('teams_5',teams, cat='Binary')
            stack_3 = pulp.LpVariable.dicts('teams_3',teams, cat='Binary')
            prob += pulp.lpSum([stack_5[i] for i in teams]) == 1
            prob += pulp.lpSum([stack_3[i] for i in teams]) == 2
            stack_1_size = stack[0]
            stack_2_size = stack[1]
            for t in teams:
                sl = df[(df['t_'+t]==1) & (df['hitters']==1)] 
                prob += (stack_1_size*stack_5[t] <= pulp.lpSum([sl['hitters'][i]*lineup[i] for i in sl.index]))
                prob += (stack_2_size*stack_3[t] <= pulp.lpSum([sl['hitters'][i]*lineup[i] for i in sl.index]))
            
        #no opps
        if no_opps:
            hitters = df[(df['t_'+t]==1)&(df['hitters']==1)]
            pitchers = df[(df['o_'+t]==1)&(df['pitchers']==1)] 
            tuples = [(pitcher,hitter) for pitcher in pitchers.index for hitter in hitters.index]
            pulp.lpSum([lineup[t[0]]*lineup[t[1]] for t in tuples]) == 0
    
        #add objective function
        prob.setObjective(pulp.lpSum([df[objective_fn_column][i] * lineup[i] for i in df.index]))
        
        #solve the problem
        prob.solve()
        
        #write to list of playernames
        sln_locs = [int(x.name.split('_')[1]) for x in prob.variables() if x.varValue == 1 and 'teams_' not in x.name]
        slns = df.filter(items = sln_locs, axis = 0)
        if return_score:
            score = slns[objective_fn_column].sum()
            return slns[['Name','Position','Team']].values.tolist(), score
        else:
            return slns[['Name','Position','Team']].values.tolist()
        
    
class NFL():
    
    def __init__(self,df):
        self.df=df[df['Salary'].isnull()==False]
        self.salary = 50000
        self.roster = ['QB','RB','RB','WR','WR','WR','TE','DST']
        self.num_players = 9
        #self.solver = pulp.getSolver('CPLEX_CMD')
        
    def standard_optimizer(self, df, objective_fn_column = 'avg fpts', return_score = False):
        '''returns the top lineup from the given dataframe for the standard contest type
        Columns = Name, Salary, Pos, Team, avg fpts'''

        
        #initial cleanup; get dummy variables for positions and drop nulls in target column
        pos_dummies = pd.get_dummies(df['Pos'])
        df = df.merge(pos_dummies,how='inner', left_index=True, right_index = True).set_index('Name')
        df = df[df[objective_fn_column].isnull() == False]
        
        #define the problem
        prob = pulp.LpProblem('NFL', pulp.LpMaximize)
        
        #create lineup list
        lineup = pulp.LpVariable.dicts('players',df.index, cat='Binary')
        
        #add max player constraint
        prob += pulp.lpSum([lineup[i] for i in df.index]) == 9
        
        #add position contraints
        prob += pulp.lpSum([df['QB'][f]*lineup[f] for f in df.index]) == 1
        prob += pulp.lpSum([df['RB'][f]*lineup[f] for f in df.index]) >= 2
        prob += pulp.lpSum([df['WR'][f]*lineup[f] for f in df.index]) >= 3
        prob += pulp.lpSum([df['TE'][f]*lineup[f] for f in df.index]) >= 1
        prob += pulp.lpSum([df['DST'][f]*lineup[f] for f in df.index]) == 1
        
        #add salary constraint
        prob += pulp.lpSum([df['Salary'][f]*lineup[f] for f in df.index]) <= 50000
        
        #add objective function
        prob.setObjective(pulp.lpSum([df[objective_fn_column][f]*lineup[f] for f in df.index]))
        
        prob.solve()
        
        #write to list of playernames
        sln_locs = [' '.join(x.name.split('_')[1:]) for x in prob.variables() if x.varValue == 1 and 'teams_' not in x.name]
        df = df.reset_index()
        slns = df[df['Name'].isin(sln_locs)]
        if return_score:
            score = slns[objective_fn_column].sum()
            return slns[['Name','Pos','Team']].values.tolist(), score
        else:
            return slns[['Name','Pos','Team']].values.tolist()
        return slns
    
    def showdown_optimizer(self, df, objective_fn_column = 'avg fpts'):
        '''returns the optimal lineup for a showdown slate
        columns = Name, Salary, avg fpts'''
        
        #df = pd.read_csv('showdown test.csv')
        
        #initial cleanup
        df = df[df[objective_fn_column].isnull() == False]
        df = df[df[objective_fn_column]!=0]
        
        #get player dummies to dedupe captain
        df = df.merge(pd.get_dummies(df['Name']), how='inner', left_index=True, right_index=True)
        df = df.set_index('Name')
        players = list(df.index)
        
        #add in the CPT projections
        cpt_df = df.copy().reset_index()
        cpt_df['Name'] = cpt_df['Name'] + ' cpt'
        cpt_df = cpt_df.set_index('Name')
        cpt_df['is cpt'] = 1
        cpt_df['Salary'] = cpt_df['Salary'] *1.5
        cpt_df[objective_fn_column] = cpt_df[objective_fn_column] *1.5
        df = cpt_df.append(df)
        df['is cpt'] = df['is cpt'].fillna(0)
        
        #define the problem and add constraints
        prob = pulp.LpProblem('NFL', pulp.LpMaximize)
        
        #create lineup list
        lineup = pulp.LpVariable.dicts('players',df.index, cat='Binary')
        
        #add max player constraint
        prob += pulp.lpSum([lineup[i] for i in df.index]) == 6
        
        #add position contraints -- captain
        prob += pulp.lpSum([df['is cpt'][f]*lineup[f] for f in df.index]) == 1
        
        #ensure captains can't duplicate other players in the lineup
        for col in players:
            prob += pulp.lpSum([df[col][f]*lineup[f] for f in df.index]) <= 1
        #add salary constraint
        prob += pulp.lpSum([df['Salary'][f]*lineup[f] for f in df.index]) <= 50000
        
        #add objective function
        prob.setObjective(pulp.lpSum([df[objective_fn_column][f]*lineup[f] for f in df.index]))
        
        prob.solve()
        slns = [x.name[8:].replace('_',' ') for x in prob.variables() if x.varValue == 1]
        return slns
    
    def player_constrained_standard_optimizer(self, df, objective_fn_column = 'avg fpts', required_players = []):
        '''returns the top lineup from the given dataframe for the standard contest type
        Columns = Name, Salary, Pos, Team, avg fpts'''

        
        #initial cleanup; get dummy variables for positions and drop nulls in target column
        pos_dummies = pd.get_dummies(df['Pos'])
        df = df.merge(pos_dummies,how='inner', left_index=True, right_index = True)
        player_dummies = pd.get_dummies(df['Name'])
        df = df.merge(player_dummies, how = 'inner', left_index = True, right_index = True)
        df = df[df[objective_fn_column].isnull() == False]
        
        #define the problem
        prob = pulp.LpProblem('NFL', pulp.LpMaximize)
        
        #create lineup list
        lineup = pulp.LpVariable.dicts('players',df.index, cat='Binary')
        
        #add max player constraint
        prob += pulp.lpSum([lineup[i] for i in df.index]) == 9
        
        #add position contraints
        prob += pulp.lpSum([df['QB'][f]*lineup[f] for f in df.index]) == 1
        prob += pulp.lpSum([df['RB'][f]*lineup[f] for f in df.index]) >= 2
        prob += pulp.lpSum([df['WR'][f]*lineup[f] for f in df.index]) >= 3
        prob += pulp.lpSum([df['TE'][f]*lineup[f] for f in df.index]) >= 1
        prob += pulp.lpSum([df['DST'][f]*lineup[f] for f in df.index]) == 1
        
        #add individual player constraints
        for player in required_players:
            prob += pulp.lpSum([df[player][f]*lineup[f] for f in df.index]) == 1
        
        #add salary constraint
        prob += pulp.lpSum([df['Salary'][f]*lineup[f] for f in df.index]) <= 50000
        
        #add objective function
        prob.setObjective(pulp.lpSum([df[objective_fn_column][f]*lineup[f] for f in df.index]))
        
        prob.solve()
        slns = [x.name[8:].replace('_',' ') for x in prob.variables() if x.varValue == 1]
        return slns
        
    def prep_df(self):
        #3placeholder method to match MLB
        if 'Pos' in self.df.columns:
            self.df = self.df.rename(columns = {'Pos':'Position'})
        return self.df
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
    
