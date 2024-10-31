url_object = URL.create("mysql+mysqlconnector",username="adminbi",password="Unicordoba@23",host="ec2-18-221-11-203.us-east-2.compute.amazonaws.com",database="insumos")    
try:
        engine = create_engine(url_object)
        sql_query = text("select * from vista_precios where departamento_id = %s and municipio_id =%s and producto_id = %s" % (
            insumo.departamento_id, insumo.municipio_id, insumo.producto_id))
        df = pd.read_sql(sql_query, engine.connect())
    except Exception as e:
        df = str(e)