# -*- coding: utf-8 -*-
"""
Created on Sun Jan  8 15:28:03 2023

@author: hunte
"""
import streamlit as st
import pandas as pd
import runSims as sims

st.title('Optimal PLayer Degrees of Seperation')

#get data from upload
dat = st.sidebar.file_uploader('Upload CSV Player Data Here')
df = pd.read_csv(dat)
