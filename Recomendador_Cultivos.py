import streamlit as st
import numpy as np
import pandas as pd
import pickle
from sklearn.ensemble import RandomForestClassifier
from sklearn import metrics
from PIL import Image
import boto3
import os
import warnings
warnings.filterwarnings('ignore')

AWS_ACCESS_KEY = 'AKIA4HJUEW2NTPPWSE4N'
AWS_SECRET_KEY = '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'
bucket_name = 'agrounicor'
file1_key = 'datos/VistaBI.csv'
file2_key = 'datos/vista_insumos.csv'
s3 = boto3.client('s3', aws_access_key_id=AWS_ACCESS_KEY, aws_secret_access_key=AWS_SECRET_KEY)
if not os.path.exists('datos'):
    os.makedirs('datos')
local_file1 = 'datos/VistaBI.csv'
s3.download_file(bucket_name, file1_key, local_file1)
local_file2 = 'datos/vista_insumos.csv'
s3.download_file(bucket_name, file2_key, local_file2)

st.set_page_config(layout="wide")
df = pd.read_csv("Crop_recommendation.csv")
with st.sidebar:
  col1, col2, col3 = st.columns(3)
  N = col1.slider('(N) Nitrógeno',0,140, 90)
  P = col2.slider('(P) Fósforo',5,145, 42)
  K = col3.slider('(K) Potasio',5,205, 43)
  T = st.number_input('Temperatura media del suelo',8.83,43.7,20.8)
  H = st.text_input('Humedad',82)
  ph = st.text_input('Ph (Acida<7; Neutra=7; Basica>7)',6.5)
  R = st.text_input('Precipitacion dependen de la ubicación',202)
  #btn = st.button('Recomendar cultivo')

col1, col2, col3,col4,col5,col6,col7 = st.columns(7)
col1.metric("Nitrógeno", N)
col2.metric("Fósforo", P)
col3.metric("Potasio", K)
col4.metric("Temperatura", T)
col5.metric("Humedad", H)
col6.metric("Precipitacion", R)
col7.metric("Acidez", ph)

loaded_model = pickle.load(open('Model.sav', 'rb'))
data = np.array([[N,P,K,T,H,ph,R]])
prediction = loaded_model.predict(data)
#st.write(prediction)
df_crop = pd.read_excel("crops.xlsx")
crop = df_crop.query('crop_o=="'+prediction[0]+'"')['crop'].values[0]
texto = df_crop.query('crop_o=="'+prediction[0]+'"')['texto'].values[0]
image = Image.open('crop/'+df_crop.query('crop_o=="'+prediction[0]+'"')['image'].values[0])

st.subheader(crop)
col1, col2 = st.columns([2, 3])
col1.image(image, caption=crop)
with col2:
  st.write(texto)
  
st.divider()
#st.subheader('Promedio de variables por cultivos')
#st.dataframe(pd.pivot_table(df,index=['label'],aggfunc='mean'))
#st.subheader('Correlaciones de variables por cultivos')
#st.dataframe(df.iloc[:,0:7].corr())