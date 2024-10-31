import streamlit as st
from sqlalchemy import URL,create_engine, text
import plotly.express as px
import pandas as pd
from datetime import date,timedelta
import pmdarima as pm
from sympy import Point
st.set_page_config(layout="wide")

import boto3
AWS_ACCESS_KEY = 'AKIA4HJUEW2NTPPWSE4N'
AWS_SECRET_KEY = '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'
bucket_name = 'agrounicor'
file1_key = 'datos/VistaBI.csv'
file2_key = 'datos/vista_insumos.csv'
s3 = boto3.client('s3', aws_access_key_id=AWS_ACCESS_KEY, aws_secret_access_key=AWS_SECRET_KEY)
response = s3.get_object(Bucket=bucket_name, Key=file2_key)
content = response['Body'].read().decode('utf-8')
filas = content.split('\n')
datos = []
for fila in filas:
    datos.append(fila.split(','))
df = pd.DataFrame(datos[1:])
encabezados = ['id','departamento_nombre','departamento_id','municipio_nombre','municipio_id','producto_id','producto_nombre','valor','fechapublicacion','presentacion']
df.columns = encabezados
df['fechapublicacion'] = pd.to_datetime(df['fechapublicacion'])
df['valor'] = df['valor'].astype(float)


with st.sidebar:
    dep = st.selectbox('Seleccionar departamento',df['departamento_nombre'].unique())
    filtro_departamento = 'departamento_nombre=="%s"'% dep
    muni = st.selectbox('Seleccionar municipio',df.query(filtro_departamento)['municipio_nombre'].unique())
    filtro_municipio = 'municipio_nombre=="%s"'% muni
    filtro_de_mu = filtro_departamento+' and '+filtro_municipio
    prod = st.selectbox('Seleccionar producto',df.query(filtro_de_mu)['producto_nombre'].unique())
    filtro_producto = 'producto_nombre=="%s"'% prod
    filtro_de_mu_pr = filtro_de_mu +' and '+filtro_producto
    pres = st.selectbox('Seleccionar Presentacion',df.query(filtro_de_mu_pr)['presentacion'].unique())
    filtro_pres = 'presentacion=="%s"'% pres
    filtro_de_mu_pr = filtro_de_mu +' and '+filtro_producto+' and '+filtro_pres
    #st.write('ok')
unano = date.today()
hoy = date.today()
unano -= timedelta(days=365)
col1, col2, col3, col4 = st.columns(4)
with col1:
    fi = st.date_input("Fecha Inicio", unano)
with col2:
    ff = st.date_input("Fecha Final", hoy)
with col3:
    option = st.selectbox('Frecuencia de los datos',('Mensual','Quincenal','Semanal'))
with col4:
    number = st.number_input('Cantidad %s a predecir'%option, 1, 10, 1)

if option == 'Mensual':
    frecuencia = 'M'
elif option == 'Quincenal':
    frecuencia = '15D'
else:
    frecuencia = 'W'
df = df.query(filtro_de_mu_pr)
df = df.loc[df["fechapublicacion"].between(str(fi),str(ff))]


if len(df)==0:
    st.subheader('No hay datos para mostrar')
else:
    df.set_index('fechapublicacion', inplace=True)
    df = df['valor']
    dff = df.copy()
    #df = df.asfreq(frecuencia, method='ffill')
    df = df.resample(frecuencia).mean().fillna(0)


    model = pm.auto_arima(df)
    pred = model.predict(n_periods=number)
    tpre = pd.DataFrame(pred)


    tpre.rename(columns={0:'Predicción'}, inplace=True)
    minimos_mensuales = dff.resample(frecuencia).min()
    max_mensuales = dff.resample(frecuencia).max()
    tpre['Minimo'] = df.min()#minimos_mensuales.tail(1).values[0]
    tpre['Maximo'] = df.max()#max_mensuales.tail(1).values[0]

    tpre = tpre.transpose()
    lista = []
    for i in range(len(pred)+1):
        if i == 0:
            lista.append([df.tail(1).index.values[0],df.tail(1).values[0]])
        else:
            lista.append([pred.index.values[i-1],pred[i-1]])
    pred = pd.DataFrame(lista)
    pred.set_index(0, inplace=True)
    df = pd.DataFrame(df)
    df['grupo']='Historico'
    pred['grupo']='Prediccion'
    pred.rename(columns={1:'valor'}, inplace=True)
    total = pd.concat([df,pred], axis=0)
    total2 = total.copy()
    total2.rename(columns={'valor':'Precio'}, inplace=True)
    total2 = total2.rename_axis('Fecha', axis='index')
    #st.dataframe(total2, use_container_width=True)
    import plotly.graph_objects as go
    fig = go.Figure()
    st.header(prod+' en '+pres)
    fig = px.line(total2,
                x=total2.index,
                y='Precio',
                color='grupo',
                symbol='grupo',
                title='Gráfica con la prediccion %s de precios de insumos' % option,
                color_discrete_map={'Historico': 'green', 'Prediccion': 'blue'}).update_traces(mode='markers+lines', line={'width':4})



    fig.add_trace(go.Scatter(x=max_mensuales.index, y=max_mensuales,mode='lines',name='Maximo')).update_traces(mode='markers+lines', line={'width':2})
    fig.add_trace(go.Scatter(x=minimos_mensuales.index, y=minimos_mensuales,mode='lines',name='Minimo')).update_traces(mode='markers+lines', line={'width':2})



    st.plotly_chart(fig, use_container_width=True)
    st.subheader('Información general')
    tpre = tpre.T
    #st.dataframe(tpre, use_container_width=True)


    col1, col2, col3 = st.columns(3)
    with col1:
        st.write("")
    with col2:
        with st.container():
            col1, col2 = st.columns(2)
            col1.metric("Precio Predición", '$'+str('{:,}'.format(round(tpre['Predicción'].values[0],1))), "")
            col2.metric("Precio Maximo", '$'+str('{:,}'.format(round(tpre['Maximo'].values[0]))), "")
            col11, col12 = st.columns(2)
            col11.metric("Precio Minimo", '$'+str('{:,}'.format(round(tpre['Minimo'].values[0]))), "")
    with col3:
        st.write("")


#st.subheader('Soporte de la predicción')
#st.write(model.summary())
#st.subheader('Datos historicos y predicción')
#st.dataframe(total, use_container_width=True)
