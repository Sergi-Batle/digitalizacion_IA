import sqlalchemy, logging, sys
from sqlalchemy import text
from datetime import datetime

conn_string = (
    "mssql+pyodbc://sa:Abc1234@192.168.22.127,56108/MAESTROS_DATACAP?driver=SQL Server"
)

nombre_tabla="ESTADISTICASEXPORTPROVES"


def comprobar_empresa(nif :str):
    try:
        conn = sqlalchemy.create_engine(conn_string)
        query = f"""
            SELECT
            [Nombre]
            FROM [MAESTROS_DATACAP].[dbo].[CamperEmpresas]
            WHERE NIF LIKE '%{nif}%'
            """

        with conn.connect() as connection:
            result = connection.execute(text(query))
            empresa = result.fetchone()
            return empresa[0] if empresa is not None else ""
        
    except Exception as e:    
        logging.error("Error al conectar con la tabla de empresa")
        logging.error(f"Ocurrio un error: {e}")
        logging.error(f"Traceback: {sys.exc_info()}")
        print("Error al conectar con la tabla de empresa")    
        print(f"Ocurrio un error: {e}")
        print(f"Traceback: {sys.exc_info()}")


def comprobar_proveedor(nif: str):
    try:
        conn = sqlalchemy.create_engine(conn_string)
        query = f"""
            SELECT
            [Nombre]
            FROM [MAESTROS_DATACAP].[dbo].[CamperProveedores]
            WHERE NIF LIKE '%{nif}%'
            OR NIFComunitario LIKE '%{nif}%'
            """
        with conn.connect() as connection:
            result = connection.execute(text(query))
            proveedor = result.fetchone()
            return proveedor[0] if proveedor is not None else ""
            
    except Exception as e:
        logging.error("Error al conectar con la tabla de proveedor")    
        logging.error(f"Ocurrio un error: {e}")
        logging.error(f"Traceback: {sys.exc_info()}")
        print("Error al realizar join en la base de datos")    
        print(f"Ocurrio un error: {e}")
        print(f"Traceback: {sys.exc_info()}")


def get_proveedor_empresas(nif: str):
    try:
        conn = sqlalchemy.create_engine(conn_string)
        query = f""" 
                SELECT 
                CE.[Nombre] AS EmpresaNombre,
                CP.[Nombre] AS ProveedorNombre,
                CE.[NIF] AS EmpresaNIF,
                CP.[NIF] AS ProveedorNif,
                CE.[Codigo] AS EmpresaCodigo,
                CP.[Codigo] AS ProveedorCodigo,
                CP.[NifComunitario] AS nifCom
                FROM 
                [MAESTROS_DATACAP].[dbo].[CamperProveedores] AS CP
                INNER JOIN 
                [MAESTROS_DATACAP].[dbo].[CamperEmpresas] AS CE ON CP.[Empresa] = CE.[Codigo]
                WHERE (CP.[NIFComunitario] LIKE '%{nif}%' OR CP.[NIF] LIKE '%{nif}%')
                """
        with conn.connect() as connection:
            result = connection.execute(text(query))
            keys = result.keys()
            rows = []
            result = result.fetchall()

            for row in result:
                row_dict = {key: row[idx] for idx, key in enumerate(keys)}

                if not row_dict.get('ProveedorNif'):
                    row_dict['ProveedorNif'] = row_dict.get('nifCom', row[-1]) 
                
                modified_row = tuple(row_dict[key] for key in keys)
                rows.append(modified_row)
                
            return rows
    except Exception as e:
        logging.error("Error al realizar join en la base de datos")   
        print("Error al realizar join en la base de datos")    
        print(f"Ocurrio un error: {e}")
        print(f"Traceback: {sys.exc_info()}")            


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
                CP.[Codigo] AS ProveedorCodigo,
                CP.[NifComunitario] AS nifCom
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
            row = result.fetchone()
            if row is not None:
                row_dict = {key: row[idx] for idx, key in enumerate(result.keys())}

                if not str(row_dict.get('ProveedorNif')).strip():
                    row_dict['ProveedorNif'] = row_dict.get('nifCom', row[-1]) 
                
                modified_row = tuple(row_dict[key] for key in result.keys())
                
                return modified_row
            return row
        
    except Exception as e:
        logging.error("Error al realizar join en la base de datos")   
        print("Error al realizar join en la base de datos")    
        print(f"Ocurrio un error: {e}")
        print(f"Traceback: {sys.exc_info()}")      


def insert(file_name, num_pag):
    try:
        fecha = datetime.now().strftime(f'%d/%m/%Y %H:%M:%S.%f')[:-3]
        conn = sqlalchemy.create_engine(conn_string)
        query = text(f"""INSERT INTO [MAESTROS_DATACAP].dbo.{nombre_tabla}
                    ([ORIGEN], [DATACREACIO], [LOTDATACAP], [REFERENCIA], [NUMPAG])
                    VALUES ('CAMPERIA', '{fecha}','NO', '{file_name}', {num_pag})""")
        
        with conn.connect() as connection:
            connection.execute(query)    
            connection.commit()
    except Exception as e:
        logging.error("Error al realizar insert en la base de datos") 
        logging.error(f"Ocurrio un error: {e}")
        logging.error(f"Traceback: {sys.exc_info()}")
        print("Error al realizar join en la base de datos")    
        print(f"Ocurrio un error: {e}")
        print(f"Traceback: {sys.exc_info()}")


     
def get_factura_format(empresa: str, proveedor: str):
    try:
        conn = sqlalchemy.create_engine(conn_string)
        query = f""" 
                SELECT DISTINCT
                [FormatFactura]
                ,[Moneda]
                ,[DataCreacio]
                ,[Factura]
                FROM [MAESTROS_DATACAP].[dbo].[CamperProvFact]
                WHERE CodProv = '{proveedor}' 
                AND CodEmpresa = '{empresa}'
                ORDER BY DataCreacio desc
                """
        with conn.connect() as connection:
            result = connection.execute(text(query))
            return result.fetchall()
        
    except Exception as e:
        logging.error("Error al realizar join en la base de datos")    
        logging.error(f"Ocurrio un error: {e}")
        logging.error(f"Traceback: {sys.exc_info()}")
        print("Error al realizar join en la base de datos")    
        print(f"Ocurrio un error: {e}")
        print(f"Traceback: {sys.exc_info()}")