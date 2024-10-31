import streamlit as st
from sqlalchemy import URL,create_engine, text
import plotly.express as px
import pandas as pd
from datetime import date,timedelta
import pmdarima as pm
from sympy import Point
st.set_page_config(layout="wide")
url_object = URL.create(
    "postgresql+psycopg2",
    username="userBI",
    password="agroBI@24",
    host="db-agro-dev.c4i55ifg9j6p.us-east-1.rds.amazonaws.com",
    database="agro",
)
df = pd.DataFrame()
try:
    engine = create_engine(url_object)
    sql_query = text('select * from core."vista_BI";')
    df = pd.read_sql(sql_query, engine.connect())
    print(df.columns)
except Exception as e:
    print(str(e))
st.dataframe(df.head())
with st.sidebar:
    dep = st.selectbox('Seleccionar departamento',df['dpto'].unique())
    filtro_departamento = 'dpto=="%s"'% dep
    muni = st.selectbox('Seleccionar municipio',df.query(filtro_departamento)['mpio'].unique())
    filtro_municipio = 'mpio=="%s"'% muni
    filtro_de_mu = filtro_departamento+' and '+filtro_municipio
    prod = st.selectbox('Seleccionar producto',df.query(filtro_de_mu)['subproducto'].unique())
    filtro_producto = 'subproducto=="%s"'% prod
    filtro_de_mu_pr = filtro_de_mu +' and '+filtro_producto
    pres = st.selectbox('Seleccionar presentación',df.query(filtro_producto)['presentacion'].unique())
    filtro_de_mu_pr = filtro_de_mu_pr+' and presentacion=="%s"'%pres
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
df['fecha_creacion'] = pd.to_datetime(df['fecha_creacion'])
df = df.loc[df["fecha_creacion"].between(str(fi),str(ff))]
df = df.sort_values(by='fecha_creacion')


if len(df)==0:
    st.subheader('No hay datos para mostrar')
else:
    df.set_index('fecha_creacion', inplace=True)
    df = df['precio_con_descuento']

    dff = df.copy()
    #df = df.asfreq(frecuencia, method='ffill')
    df = df.resample(frecuencia).mean()

    model = pm.auto_arima(df)
    pred = model.predict(n_periods=number)
    tpre = pd.DataFrame(pred)

    tpre.rename(columns={0:'Predicción'}, inplace=True)
    minimos_mensuales = dff.resample(frecuencia).min()
    max_mensuales = dff.resample(frecuencia).max()
    tpre['Minimo'] = minimos_mensuales.tail(1).values[0]
    tpre['Maximo'] = max_mensuales.tail(1).values[0]

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
    import plotly.graph_objects as go
    fig = go.Figure()

    fig = px.line(total,
                x=total.index,
                y='valor',
                color='grupo',
                symbol='grupo',
                title='Gráfica con la prediccion %s de precios de ofertas' % option, 
                color_discrete_map={'Prediccion': 'blue'}).update_traces(mode='markers+lines', line={'width':4})


    fig.add_trace(go.Scatter(x=df.index, y=df.precio_con_descuento,mode='lines',name='Historico')).update_traces(mode='markers+lines', line={'width':2})
    fig.add_trace(go.Scatter(x=max_mensuales.index, y=max_mensuales,mode='lines',name='Maximo')).update_traces(mode='markers+lines', line={'width':2})
    fig.add_trace(go.Scatter(x=minimos_mensuales.index, y=minimos_mensuales,mode='lines',name='Minimo')).update_traces(mode='markers+lines', line={'width':2})



    st.plotly_chart(fig, use_container_width=True)
    st.subheader('Predicción')
    st.dataframe(tpre, use_container_width=True)

#st.subheader('Soporte de la predicción')
#st.write(model.summary())
#st.subheader('Datos historicos y predicción')
#st.dataframe(total, use_container_width=True)
