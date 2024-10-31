import pandas as pd
import pmdarima as pm
from fastapi import FastAPI
from pydantic import BaseModel
from sqlalchemy import URL,create_engine, text
import warnings
warnings.filterwarnings("ignore")
app = FastAPI()

url_object = URL.create("mysql+mysqlconnector",username="adminbi",password="Unicordoba@23",host="ec2-18-221-11-203.us-east-2.compute.amazonaws.com",database="insumos")

class Insumo(BaseModel):
    departamento_id : int
    municipio_id: int
    producto_id: int
    cantidad_prediccion: int
    frecuencia: str

@app.get('/')
def Home():
    return {'Stastus':'Running...'}

@app.post('/insumos')
def Prediccion_Insumo(insumo:Insumo):
    df = pd.DataFrame()
    try:
        engine = create_engine(url_object)
        sql_query = text("select * from vista_precios where departamento_id = %s and municipio_id =%s and producto_id = %s"%(insumo.departamento_id,insumo.municipio_id,insumo.producto_id))
        df = pd.read_sql(sql_query, engine.connect())
    except Exception as e:
        df = str(e)
    df.set_index('fechapublicacion', inplace=True)
    df = df['valor']
    df = df.resample(insumo.frecuencia).mean()
    model = pm.auto_arima(df)
    pred = model.predict(n_periods=insumo.cantidad_prediccion)
    pred = pred.astype(int)
    pred = pred.reset_index(drop=True)
    min = str(df.astype(int).min())
    max = str(df.astype(int).max())
    return  {
            'Predicciones':pred.values.tolist(),
            'Minimo':min,
            'Maximo':max
            }

@app.get('/ventas')
def Prediccion_Ventas():
    return {'Stastus':'Running...'}