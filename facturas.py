import os, glob, json, time, re, sys, logging
from datetime import datetime
import pandas as pd
from ocrDLL import ocr
from IA_API import gen_response
from database import comprobar_cifs, insert
from utils import *
from pypdf import PdfReader
from unidecode import unidecode

useOcr = False
cif_size = (11, 5)

def save_error(input_file_path, text):
    with open(f"lot_100/{input_file_path}", "a") as file:
        file.write(text)


def ini_proceso(data, index):
    try:
        print("Generando json")
        logging.info("Obteniendo datos")
        start_time = time.time()
        response = gen_response(f"{data}", ', '.join(campos))

        end_time = time.time()
        execution_time = end_time - start_time

        response = re.sub(r'(?<!")\s*\/\/[^\n]*', "", response)
        print("response: \n", response)
        datos = json.loads(response)
        datos = {
            unidecode(clave.lower()).replace(" ", "_"): valor 
            for clave, valor in datos.items()
        }
        logging.info(f"Datos obtenidos en {execution_time} segundos")
        print("\nTiempo de generar json: ", execution_time, " segundos")

        datos = clean_json(datos, useOcr)
        print(datos)
        # save_json("result.txt", datos)

        empresa = datos["cif_o_nif_del_cliente"]
        proveedor = datos["cif_del_proveedor"]
        iva_cant = datos["importe_de_iva"]
        base = datos["importe_total_antes_de_impuestos"]
        total = datos["importe_total_de_la_factura"]
        iva_percent = datos["porcentaje_de_iva"]

        # Comprobar importes
        importes = comprobar_importes(total, base, iva_cant, iva_percent)

        if not importes[0] :
            print("Error de importes")
            return False, None

        print("Importes: ", importes) 
        
        fechavenc = ""
        if "fecha_de_caducidad_o_vencimiento" in datos:
            fechavenc = formatear_fecha(datos["fecha_de_caducidad_o_vencimiento"])

        divisa = ""
        if "divisa" in datos:
            divisa = datos["divisa"]

        
        # Comprobar cifs
        if empresa and proveedor:
            dades_emp = comprobar_cifs(empresa, proveedor)

            if dades_emp:
                print("Export")
                print('Empresa: ', empresa)
                print("Proveedor: ", proveedor)

                print(dades_emp)

                datos = [
                    datos["numero_o_codigo_de_factura"], 
                    datos["fecha_de_factura"],
                    dades_emp[0], 
                    dades_emp[1], 
                    dades_emp[2], 
                    dades_emp[3], 
                    dades_emp[4], 
                    dades_emp[5],
                    importes[1][0],
                    importes[1][1], 
                    importes[1][2],
                    importes[1][3],
                    divisa,
                    fechavenc
                ]


                print(datos)
                print("Completado")
                return True, datos
            
            else:
                print("Provando expresion")
                dades_emp = usar_expresion(empresa, proveedor, data, cif_size)
                print(dades_emp)

                if dades_emp:
                    print("Export")
                    print('Empresa: ', dades_emp[1][0])
                    print("Proveedor: ", dades_emp[1][1])

                    datos = [
                        datos["numero_o_codigo_de_factura"], 
                        datos["fecha_de_factura"],
                        dades_emp[1][0], 
                        dades_emp[1][1], 
                        dades_emp[1][2], 
                        dades_emp[1][3], 
                        dades_emp[1][4], 
                        dades_emp[1][5],
                        importes[1][0],
                        importes[1][1], 
                        importes[1][2],
                        importes[1][3],
                        divisa,
                        fechavenc
                    ]

                    return True, datos
                
                else:
                    print("Error")
                    save_error(f"text_error/Error_{index}.txt", data)
                    return False, None
        
        # Se prueba la expresion regular
        else:
            print("Provando expresion")
            dades_emp = usar_expresion(empresa, proveedor, data, cif_size)
            print(dades_emp)

            if dades_emp[0]:
                print("Export")
                print('Empresa: ', dades_emp[1][0])
                print("Proveedor: ", dades_emp[1][1])

                datos = [
                    datos["numero_o_codigo_de_factura"], 
                    datos["fecha_de_factura"],
                    dades_emp[1][0], 
                    dades_emp[1][1], 
                    dades_emp[1][2], 
                    dades_emp[1][3], 
                    dades_emp[1][4], 
                    dades_emp[1][5],
                    importes[1][0],
                    importes[1][1], 
                    importes[1][2],
                    importes[1][3],
                    divisa,
                    fechavenc
                ]

                return True, datos
            
            else:
                print("Error")
                return False, None
            
    
    # Errores de la IA al generar el JSON
    except KeyError as e:
        logging.error("Error de generacion de JSON se volvera a intentar")
        return 'retry', None
    
    except json.decoder.JSONDecodeError as e:
        logging.error("Error de generacion de JSON se volvera a intentar")
        return 'retry', None
    
    # Cualquier otro error lo pasa a Error
    except Exception as e:
        logging.error("Error al obtener datos de pdf")
        logging.error(f"Ocurrio un error: {e}")
        logging.error(f"Traceback: {sys.exc_info()}")
        print(f"Ocurrio un error: {e}")
        print(f"Traceback: {sys.exc_info()}")
        return False, None


def get_pdfs_text(pdfs :list):
    global useOcr
    if len(pdfs) == 0:
        logging.error("No se han encontrado pdfs en origen")
        print("No se han encontrado pdfs en origen")

    index = 0
    tryOcr = []
    try:
        while index < len(pdfs): 
            pdf = pdfs[index]
        
            logging.info(f"Extrayendo texto de '{os.path.basename(pdf)}'")
            text = ""
            reader = PdfReader(pdf)
            pages = len(reader.pages)
            useOcr = False
            page_index = 0
            while page_index < 3 and page_index < pages:
                page = reader.pages[page_index]
                text += page.extract_text()
                page_index += 1
                
            # Comprovar que el Reader devuelve caracteres
            # sino usa OCR 
            if not any(c.isalpha() for c in text):
                copyFile(pdf, error)
                logging.info(f"Archivo '{os.path.basename(pdf)}' enviado a ERROR")
            #     text = ocr(pdf)
            #     useOcr = True

            result = ini_proceso(text, index)
            # Si ocurre un error de IA se vuelve a intentar
            print()
            print("RESULT")
            print()
            print(result)
            if result[0] == "retry":
                pdfs.append(pdf)
                pdfs.pop(index) 
                continue 
                
            elif result[0]:
                datos = result[1]
                print("datos obtenidos")
                print(datos)

            
                numero_factura = datos[0]
                fecha_factura = formatear_fecha(datos[1])

                nombre_empresa = datos[2]
                nombre_proveedor = datos[3]

                cif_empresa = datos[4]
                cif_proveedor = datos[5]
                cod_empresa = datos[6]
                cod_proveedor = datos[7]
                total = datos[8]
                base_imponible = datos[9]
                importe_iva = datos[10]
                percent_iva = datos[11]


                dataentreg = datetime.now().strftime(f'%Y-%m-%d')
                datarec = datetime.now().strftime(f'%Y-%m-%d')

                divisa = str(datos[12]).lower().strip()
                datavenc = datos[13]
                euro_type = ["€", "euros", "euro"]

                if not divisa:
                    divisa = "EUR"

                elif divisa in euro_type:
                    divisa = "EUR"
                else:
                    divisa = "EUR"        

                base_sin_iva = "0,00"
                irpf = "0,00"
                tipo_irpf = "0,00"
                
                base_iva2 = "0,00"
                importe_iva2 = "0,00"
                tipo_iva2 = "0,00"

                base_iva3 = "0,00"
                importe_iva3 = "0,00"
                tipo_iva3 = "0,00"

                archivo = os.path.basename(pdf)

                tipo_registro = "F"
                tipo = "Factura"

                
                csv_line = f"{numero_factura}, {cif_proveedor}, {nombre_proveedor}, {cif_empresa}, {nombre_empresa}, {fecha_factura}, {tipo}, {total}, {divisa}, {base_sin_iva}, {irpf}, {tipo_irpf}, {base_imponible}, {importe_iva}, {percent_iva}, {base_iva2}, {importe_iva2}, {tipo_iva2}, {base_iva3}, {importe_iva3}, {tipo_iva3}, {archivo}, {datavenc}, {dataentreg}, {cod_empresa}, {cod_proveedor}, {datarec}, {tipo_registro}"
                print("csv: ", csv_line)

                write_csv(nombre_archivo_csv, csv_line)

                copyFile(pdf, export)
                logging.info(f"Archivo '{os.path.basename(pdf)}' enviado a EXPORT")
                insert(os.path.basename(pdf), pages)
            # Si da error y no se ha usado OCR se provara con OCR 
            # elif not result[0] and not useOcr:
                # tryOcr.append(pdf)
                # logging.info(f"Archivo {os.path.basename(pdf)} enviado a Error provisional")
            # Si da error y ya se ha usado OCR se manda a error 
            else:
                copyFile(pdf, error)
                logging.info(f"Archivo '{os.path.basename(pdf)}' enviado a ERROR")
            
            index += 1  
        # Pasada con OCR
        # useOcr = True
        # index = 0
        # while index < len(tryOcr):
        #     pdf = tryOcr[index]
        #     logging.info(f"Extrayendo texto de '{os.path.basename(pdf)}'")
        #     text = ocr(pdf)
        #     result = ini_proceso(text, index)

        #     if result == "retry":
        #         tryOcr.append(pdf)
        #         tryOcr.pop(index) 
        #         continue 

        #     elif result[0]:
        #         copyFile(pdf, export)

        #         logging.info(f"Archivo '{os.path.basename(pdf)}' enviado a Export")
        #         insert(os.path.basename(pdf), pages)
        #     else:
        #         copyFile(pdf, error)
        #         logging.info(f"Archivo '{os.path.basename(pdf)}' enviado a ERROR")

        #     index += 1    


    except Exception as e:
        logging.error("Error al obtener texto de pdfs: ")
        logging.error(f"Ocurrio un error: {e}")
        logging.error(f"Traceback: {sys.exc_info()}")
        print("obtener texto de pdfs: ")
        print(f"Ocurrio un error: {e}")
        print(f"Traceback: {sys.exc_info()}")
        index += 1



path = "C:\\camper\\"

excelConfig = os.path.join(path, "config.xlsx")
df_config = pd.read_excel(excelConfig)
origen = df_config["origen"][0]
export = df_config["export"][0]
error = df_config["error"][0]
logs = df_config["logs"][0]


nombre_archivo_csv = 'resultado.csv'


excelPath = os.path.join(origen, "*.xlsx")
pdfPath = os.path.join(origen, "*.pdf")
pdfs = glob.glob(pdfPath)


campos = [
    "numero o codigo de factura",
    "fecha de factura",
    "fecha de caducidad o vencimiento"
    "CIF del proveedor",
    "CIF o NIF del cliente",
    "importe total de la factura",
    "importe total antes de impuestos",
    "importe de iva",
    "porcentaje de iva", 
    "divisa",
]

log_base_name = time.strftime("%d%m%Y", time.localtime())
log_file = os.path.join(logs, f'{log_base_name}.log')
logging.basicConfig(filename=log_file, level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


get_pdfs_text(pdfs)