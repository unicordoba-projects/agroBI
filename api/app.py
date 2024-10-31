import pandas as pd
import pmdarima as pm
from flask import Flask, request, jsonify
from sqlalchemy import URL,create_engine, text
import warnings
warnings.filterwarnings("ignore")

app = Flask(__name__)



class Insumo:
    def __init__(self, departamento_id, municipio_id, producto_id, cantidad_prediccion, frecuencia,presentacion):
        self.departamento_id = departamento_id
        self.municipio_id = municipio_id
        self.producto_id = producto_id
        self.cantidad_prediccion = cantidad_prediccion
        self.frecuencia = frecuencia
        self.presentacion = presentacion

@app.route('/')
def home():
    return {'Status': 'Running...'}

@app.route('/insumos', methods=['POST'])
def prediccion_insumo():
    data = request.get_json()
    insumo = Insumo(**data)
    import boto3
    AWS_ACCESS_KEY = 'AKIA4HJUEW2NTPPWSE4N'
    AWS_SECRET_KEY = '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'
    bucket_name = 'agrounicor'
    file2_key = 'datos/vista_insumos.csv'
    s3 = boto3.client('s3', aws_access_key_id=AWS_ACCESS_KEY, aws_secret_access_key=AWS_SECRET_KEY)
    response = s3.get_object(Bucket=bucket_name, Key=file2_key)
    content = response['Body'].read().decode('utf-8')
    filas = content.split('\n')
    datos = []
    for fila in filas:
        datos.append(fila.split(','))
    df = pd.DataFrame(datos[1:])
    #df = pd.read_csv('../datos/vista_insumos.csv')
    encabezados = ['id','departamento_nombre','departamento_id','municipio_nombre','municipio_id','producto_id','producto_nombre','valor','fechapublicacion','presentacion']
    df.columns = encabezados
    df['fechapublicacion'] = pd.to_datetime(df['fechapublicacion'])
    df['valor'] = df['valor'].astype(float)
    sql = 'departamento_id =="'+str(insumo.departamento_id)+'" and municipio_id == "'+str(insumo.municipio_id)+'" and producto_id == "'+str(insumo.producto_id)+'" and presentacion == "'+insumo.presentacion+'"'
    df = df.query(sql)
    df.set_index('fechapublicacion', inplace=True)
    df = df['valor']
    df = df.resample(insumo.frecuencia).mean()
    model = pm.auto_arima(df)
    pred = model.predict(n_periods=insumo.cantidad_prediccion)
    pred = pred.astype(int)
    pred = pred.reset_index(drop=True)
    min_val = str(df.astype(int).min())
    max_val = str(df.astype(int).max())
    return jsonify({
        'Predicciones': pred.values.tolist(),
        'Minimo': min_val,
        'Maximo': max_val
    })

@app.route('/ventas')
def prediccion_ventas():
    return {'Status': 'Running...'}

if __name__ == '__main__':
    app.run(debug=True)