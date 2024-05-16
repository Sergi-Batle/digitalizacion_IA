import sqlalchemy, logging
from sqlalchemy import text
from datetime import datetime


conn_string = (
    "mssql+pyodbc://sa:Abc1234@192.168.22.127,56108/MAESTROS_DATACAP?driver=SQL Server"
)

nombre_tabla="ESTADISTICASEXPORTPROVES"


def check_existe(nif :str):
    return comprobar_empresa(nif) or comprobar_proveedor(nif)


def comprobar_empresa(nif :str):
    try:
        conn = sqlalchemy.create_engine(conn_string)
        query = f"""
            SELECT TOP 1000 [Codigo]
            ,[Nombre]
            ,[NIF]
            ,[Moneda]
            ,[Dirección]
            ,[CodPostal]
            ,[Población]
            ,[Pais]
            FROM [MAESTROS_DATACAP].[dbo].[CamperEmpresas]
            WHERE NIF LIKE '%{nif}'
            """

        with conn.connect() as connection:
            result = connection.execute(text(query))

            return True if result.fetchone() else False
    except:    
        logging.error("Error al conectar con la tabla de empresa")


def comprobar_proveedor(nif: str):
    try:
        conn = sqlalchemy.create_engine(conn_string)
        query = f"""
            SELECT TOP (1000) [Codigo]
            ,[NIFComunitario]
            ,[Empresa]
            ,[Nombre]
            ,[Nombre2]
            ,[NIF]
            ,[NIF2]
            ,[NIF3]
            ,[NIF4]
            ,[NIF5]
            ,[NIF6]
            FROM [MAESTROS_DATACAP].[dbo].[CamperProveedores]
            WHERE NIF LIKE '%{nif}'
            OR NIFComunitario LIKE '%{nif}'
            """
        with conn.connect() as connection:
            result = connection.execute(text(query))

            return True if result.fetchone() else False
    except:
        logging.error("Error al conectar con la tabla de porveedor")    


def comprobar_cifs(empresa: str, proveedor: str):
    try:
        conn = sqlalchemy.create_engine(conn_string)
        query = f""" 
                SELECT 
                CE.[Nombre] AS EmpresaNombre,
                CP.[Nombre] AS ProveedorNombre,
                CE.[NIF] AS EmpresaNIF,
                CP.[NIF] AS ProveedorNif,
                CE.[Codigo] AS EmpresaCodigo,
                CP.[Codigo] AS ProveedorCodigo
            FROM 
                [MAESTROS_DATACAP].[dbo].[CamperProveedores] AS CP
            INNER JOIN 
                [MAESTROS_DATACAP].[dbo].[CamperEmpresas] AS CE ON CP.[Empresa] = CE.[Codigo]
            WHERE 
                ((CP.[NIFComunitario] LIKE '%{proveedor}%' OR CP.[NIF] LIKE '%{proveedor}%') AND 
                CE.[NIF] LIKE '%{empresa}%')
                OR
                ((CP.[NIFComunitario] LIKE '%{empresa}%' OR CP.[NIF] LIKE '%{empresa}%') AND 
                CE.[NIF] LIKE '%{proveedor}%')
                """
        with conn.connect() as connection:
            result = connection.execute(text(query))
            return result.fetchone() 
        
    except:
        logging.error("Error al realizar join en la base de datos")    



def insert(file_name, num_pag):
    fecha = datetime.now().strftime(f'%d/%m/%Y %H:%M:%S.%f')[:-3]
    conn = sqlalchemy.create_engine(conn_string)
    query = text(f"""INSERT INTO [MAESTROS_DATACAP].dbo.{nombre_tabla}
                ([ORIGEN], [DATACREACIO], [LOTDATACAP], [REFERENCIA], [NUMPAG])
                VALUES ('CAMPERIA', '{fecha}','NO', '{file_name}', {num_pag})""")
    
    with conn.connect() as connection:
        connection.execute(query)    
        connection.commit()

     