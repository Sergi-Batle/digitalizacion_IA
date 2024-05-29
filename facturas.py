import os, glob, time, sys, logging
import pandas as pd
from database import insert
from utils import extraer_datos, copyFile, generar_linea_csv, limpiar_texto
from pypdf import PdfReader
from firma import firmar_pdf

path = "C:\\camper\\"
# path = "C:\\Users\\tecnico\\OneDrive - Angel 24\\RPA\\DIG_Camper\\Scripts\\DIG_Camper\\"

ruta_certificat = "C:\\docs\\Cert\\Certificado_de_Camerfirma.pfx"
ruta_clave = "C:\\docs\\Cert\\pwd.txt"


excelConfig = os.path.join(path, "config.xlsx")
df_config = pd.read_excel(excelConfig)
origen = df_config["origen"][0]
export = df_config["export"][0]
error = df_config["error"][0]
logs = df_config["logs"][0]

excelPath = os.path.join(origen, "*.xlsx")
pdfPath = os.path.join(origen, "*.pdf")
pdfs = glob.glob(pdfPath)

nombre_archivo_csv = 'resultado.csv'


log_base_name = time.strftime("%d%m%Y", time.localtime())
log_file = os.path.join(logs, f'{log_base_name}.log')
logging.basicConfig(filename=log_file, level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def gestionar_resultado_datos(result, pdf, paginas, exempt):
    try:
        if result[0] == "retry":
            logging.info(f"Archivo '{os.path.basename(pdf)}' ERROR por GENERACION DE IA se volvera a intentar")
            print("Error de generacion de IA")
            return "retry"
            
        elif result[0]:
            datos = result[1]
            logging.info("datos obtenidos")
            logging.info(datos)

            generar_linea_csv(datos, str(os.path.basename(pdf)).upper(), nombre_archivo_csv, export, exempt)
            firmar_pdf(ruta_certificat, ruta_clave, os.path.abspath(pdf))
            copyFile(pdf, export)
            logging.info(f"Archivo '{os.path.basename(pdf)}' enviado a EXPORT")
            
            insert(os.path.basename(pdf), paginas)

        else:
            copyFile(pdf, error)
            logging.info(f"Archivo {os.path.basename(pdf)}  enviado a ERROR")
            
    except  Exception as e:        
        logging.error("Error al obtener texto de pdfs: ")
        logging.error(f"Ocurrio un error: {e}")
        logging.error(f"Traceback: {sys.exc_info()}")
        print(f"Ocurrio un error: {e}")
        print(f"Traceback: {sys.exc_info()}")     


def get_pdf_text(pdf, all_pages):    
    try: 
        logging.info("")
        logging.info("==============================================")
        logging.info("")
        logging.info(f"Extrayendo texto de '{os.path.abspath(pdf)}'")  
        print(f"Extrayendo texto de '{os.path.basename(pdf)}'")  

        text = ""
        reader = PdfReader(pdf)
        pages = len(reader.pages)
        page_index = 0
        if all_pages:
            while page_index < 2 and page_index < pages:
                page = reader.pages[page_index]
                text += page.extract_text()
                page_index += 1

        else:       
            page = reader.pages[0]
            text = page.extract_text()

        return text, pages    
    
    except Exception as e:
        logging.error("Error al obtener texto de pdfs: ")
        logging.error(f"Ocurrio un error: {e}")
        logging.error(f"Traceback: {sys.exc_info()}")
        print(f"Ocurrio un error: {e}")
        print(f"Traceback: {sys.exc_info()}")            



def main(pdfs):
    try:
        if len(pdfs) == 0:
            logging.error("No se han encontrado pdfs en origen")
            print("No se han encontrado pdfs en origen")

        retry=[]
        for pdf in pdfs:
            exempt = False
            texto_paginas = get_pdf_text(pdf, True)
            text = texto_paginas[0]
            paginas = texto_paginas[1]

            if 'exento' in text.lower() or 'exempt' in text.lower():
                # exempt = True
                copyFile(pdf, error)
                logging.error(f"Archivo '{os.path.basename(pdf)}' enviado a ERROR por EXENTO")
                continue

            # Si no hay texto en el pdf lo manda a ERROR
            if not any(c.isalpha() for c in text):
                copyFile(pdf, error)
                logging.error(f"Archivo '{os.path.basename(pdf)}' enviado a ERROR, no hay texto en el pdf")
                continue

            resultado_datos = extraer_datos(text, campos, exempt)    

            resultado_proceso = gestionar_resultado_datos(resultado_datos, pdf, paginas, exempt)

            if resultado_proceso == "retry":
                retry.append(pdf)
                continue
            else:
                continue    

        # Segunda vuelta de errores de generacion solo con la primera pagina
        if len(retry) != 0:
            for pdf in retry:
                exempt = False
                texto_pagina = get_pdf_text(pdf, False)

                text = limpiar_texto(texto_paginas[0])
                paginas = texto_pagina[1]

                if 'exento' in text.lower() or 'exempt' in text.lower():
                    # exempt = True
                    copyFile(pdf, error)
                    logging.error(f"Archivo '{os.path.basename(pdf)}' enviado a ERROR por EXENTO")
                    continue

                resultado_datos = extraer_datos(text, campos, exempt)    

                resultado_proceso = gestionar_resultado_datos(resultado_datos, pdf, paginas, exempt)

                if resultado_proceso == "retry":
                    logging.info(f"Archivo '{os.path.basename(pdf)}' enviado a ERROR")
                    copyFile(pdf, error)
                else:
                    continue    

    except Exception as e:
        logging.error("Error en el proceso principal: ")
        logging.error(f"Ocurrio un error: {e}")
        logging.error(f"Traceback: {sys.exc_info()}")
        print(f"Ocurrio un error: {e}")
        print(f"Traceback: {sys.exc_info()}")  
    finally:
        logging.info("==============================================")    
        logging.info("")    
        logging.info("                FINALIZADO")    
        logging.info("")    
        logging.info("==============================================")    
                


campos = [
    "numero o codigo de factura",
    "fecha de factura",
    "fecha de caducidad o vencimiento"
    "CIF del proveedor",
    "CIF o NIF del cliente",
    "importe total de la factura",
    "importe total antes de impuestos",
    "importe de iva",
    "porcentaje de iva"
]

main(pdfs)