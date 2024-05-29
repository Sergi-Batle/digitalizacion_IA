import os, shutil, re, logging, sys, csv, json, time
from IA_API import gen_response
from database import comprobar_cifs, get_factura_format, get_proveedor_empresas
from datetime import datetime
from unidecode import unidecode

cif_size = (11, 5)


def copyFile(file, procesadosPath):
    source = file
    file_name = os.path.basename(file)
    dest = os.path.join(procesadosPath, file_name)
    num = 0
    while os.path.exists(dest):
        num += 1
        period = file_name.rfind(".")
        if period == -1:
            period = len(file_name)
        new_file = f"{file_name[:period]}({num}){file_name[period:]}"

        dest = os.path.join(procesadosPath, new_file)
    shutil.move(source, dest)


def formatear_iva(numero_str :str):
    numero_str = numero_str.replace(".", "").replace(",", "")
    if len(numero_str) <= 2:
        numero_formateado = numero_str + ".00"
    else:
        numero_formateado = numero_str[:2] + "." + numero_str[2:]
    
    return numero_formateado    


def check_last_three_digits(input_str):
    if len(input_str) < 3:
        return False

    last = input_str[-3:]
    if '.' in last:
        return 'punto'
    elif ',' in last:
        return 'coma'
    else:
        return False


def limpiar_importe(numero: str):
    resultado = check_last_three_digits(numero)
    if resultado == 'punto':
        fragments = numero.rsplit('.', 1)
        numero = fragments[0].replace(',', '').replace('.', '') + '.' + fragments[1]
    elif resultado == 'coma':
        fragments = numero.rsplit(',', 1)
        numero = fragments[0].replace(',', '').replace('.', '') + '.' + fragments[1]
    else:
        numero = numero.replace(',', '').replace('.', '') + '.00'
    
    # Asegurar que el resultado tenga dos decimales
    if '.' in numero:
        partes = numero.split('.')
        if len(partes[1]) == 1:
            numero += '0'
        elif len(partes[1]) == 0:
            numero += '00'
    else:
        numero += '.00'
    
    return numero


def formatear_importes(total, base, iva_cant, iva_percent):
    total = "{:,.5f}".format(total).replace(',', 'X').replace('.', ',').replace('X', '.')
    base = "{:,.2f}".format(base).replace(',', 'X').replace('.', ',').replace('X', '.')
    iva_cant = "{:,.2f}".format(iva_cant).replace(',', 'X').replace('.', ',').replace('X', '.')
    iva_percent = "{:.2f}".format(iva_percent).replace(".", ",")

    return(total, base, iva_cant, iva_percent)


def comprobar_iva_percent(base, iva_cant, iva_percent):
    real_iva = round((round((iva_cant / base),2) * 100),2)

    return iva_percent if iva_percent == real_iva else real_iva



def comprobar_importes(total :str, base :str, iva_cant :str, iva_percent :str, exempt):
    total = limpiar_importe(total)
    base = limpiar_importe(base)
    iva_cant = limpiar_importe(iva_cant)
    iva_percent = limpiar_importe(iva_percent)

    total = float(total)
    base = float(base) 
    iva_cant = float(iva_cant) 
    iva_percent = float(iva_percent)

    print("IVA_PERCENT: ", iva_percent)


    if total == round((base + iva_cant), 2):
        if exempt and iva_percent != 0:
            iva_percent = comprobar_iva_percent(base, iva_cant, iva_percent)
            return True, formatear_importes(total, base, iva_cant, iva_percent)
        else:
            return True, formatear_importes(total, base, iva_cant, iva_percent)
                

    if base >= total and iva_cant != 0:
        base, total = total, base

        if total == round((base + iva_cant), 2):
            if exempt and iva_percent != 0:
                iva_percent = comprobar_iva_percent(base, iva_cant, iva_percent)
                return True, formatear_importes(total, base, iva_cant, iva_percent)
            else:
                return True, formatear_importes(total, base, iva_cant, iva_percent)
        
        else:
            total = base
            base = round((total - iva_cant), 2)
            if iva_cant == round((base * (iva_percent / 100)), 2):
                if exempt and iva_percent != 0:
                    iva_percent = comprobar_iva_percent(base, iva_cant, iva_percent)
                    return True, formatear_importes(total, base, iva_cant, iva_percent)
                else:
                    return True, formatear_importes(total, base, iva_cant, iva_percent)
            
        
    if (total == round(base + (base * (iva_percent / 100)),2)) or (iva_cant == 0 and base != total):
        iva_cant = round(base * (iva_percent / 100), 2)
        if total == round((base + iva_cant), 2):
            if exempt and iva_percent != 0:
                iva_percent = comprobar_iva_percent(base, iva_cant, iva_percent)
                return True, formatear_importes(total, base, iva_cant, iva_percent)
            else:
                return True, formatear_importes(total, base, iva_cant, iva_percent)
                
        
    if iva_cant == round(round((total - iva_cant), 2) * (iva_percent / 100),2):
        base = round((total - iva_cant), 2)
        if exempt and iva_percent != 0:
            iva_percent = comprobar_iva_percent(base, iva_cant, iva_percent)
            return True, formatear_importes(total, base, iva_cant, iva_percent)
        else:
            return True, formatear_importes(total, base, iva_cant, iva_percent)
    

    if iva_cant == round((base * (iva_percent / 100)), 2):
        total = base + iva_cant
        if total == round((base + iva_cant), 2):
            if exempt and iva_percent != 0:
                iva_percent = comprobar_iva_percent(base, iva_cant, iva_percent)
                return True, formatear_importes(total, base, iva_cant, iva_percent)
            else:
                return True, formatear_importes(total, base, iva_cant, iva_percent)

    
    print("Error de importes")
    logging.error("Error de importes:")
    logging.error(f"TOTAL: {total}, BASE: {base}, IVA_CANT: {iva_cant}, IVA_PERCENT {iva_percent}")
    return False, None


def buscar_cifs(palabras: str, cif_size):
    posibles_cifs = []
    for palabra in palabras:
        palabra_limpiada = re.sub(r"[^0-9]", "", palabra)
        
        if palabra_limpiada and (len(palabra_limpiada) <= cif_size[0] and len(palabra_limpiada) >= cif_size[1]):
            posibles_cifs.append(palabra_limpiada)

    return posibles_cifs


def comprobar_abrev(cadena: str) -> str:
    try:
        cadena1 = cadena.replace(".", " ").replace(",", " ")
        chars = ["(", ")"]

        palabras = cadena1.split()
        palabras_filtradas = []

        for palabra in palabras:
            if not any(char in palabra for char in chars):
                palabras_filtradas.append(palabra)
        
        return max(palabras_filtradas, key=len) 
    except ValueError as e:
        print(f"Ocurrió un error: {e}")
        print("CADENA", cadena)
        print("CADENA1", cadena1)
        print("PALABRAS", palabra)
        print("PALABRAS_FILTRADAS", palabras_filtradas)
        return ""


def usar_expresion(cif_1, cif_2, texto :str, cifs_size):
    palabras = texto.split()

    if cif_1 and cif_2:
        result = comprobar_cifs(cif_1, cif_2)
        if result:
            con1 = comprobar_abrev(result[0]).lower() in texto.lower()
            con2 = comprobar_abrev(result[1]).lower() in texto.lower()

            if con1 and con2:
                return True, result


    posibles_cifs = buscar_cifs(palabras, cifs_size)

    for posible_cif in posibles_cifs:
        posibles_empresas = get_proveedor_empresas(posible_cif)
        if posibles_empresas:
            for posible_empresa in posibles_empresas:

                nom_empresa = comprobar_abrev(posible_empresa[0]).lower()
                nom_proveedor = comprobar_abrev(posible_empresa[1]).lower()
                cif_empresa = re.sub(r"[^0-9]", "", posible_empresa[2])
                cif_proveedor = re.sub(r"[^0-9]", "", posible_empresa[3])
                con1 = nom_empresa in texto.lower()
                con2 = nom_proveedor in texto.lower()
                con3 = cif_empresa in texto
                con4 = cif_proveedor in texto

                if con1 and con2 and con3 and con4:
                    return True, comprobar_cifs(cif_empresa, cif_proveedor)
                    
    print("CIFS NO ENCONTRADOS")                
    print()
    logging.error("CIFS NO ECONTRADOS")
    return False, None


def clean_json(datos):
    try:
        datos["cif_del_proveedor"] = re.sub(
            r"[^0-9]", "", str(datos["cif_del_proveedor"])
        )

        datos["cif_o_nif_del_cliente"] = re.sub(
            r"[^0-9]", "", str(datos["cif_o_nif_del_cliente"])
        )

        datos["importe_total_de_la_factura"] = re.sub(
            r"[^0-9,.]", "", str(datos["importe_total_de_la_factura"])
        )
        datos["importe_total_antes_de_impuestos"] = re.sub(
            r"[^0-9,.]", "", str(datos["importe_total_antes_de_impuestos"])
        )
        datos["importe_de_iva"] = re.sub(r"[^0-9,.]", "", str(datos["importe_de_iva"]))
        datos["porcentaje_de_iva"] = re.sub(r"[^0-9,.]", "", str(datos["porcentaje_de_iva"]))

        return datos

    except Exception as e:    
        logging.error("Error al limpiar datos del JSON")
        logging.error(f"Ocurrio un error: {e}")
        logging.error(f"Traceback: {sys.exc_info()}")


# Añade comillas a los valores del json
def add_quotes(match):
    return f'"{match.group(0)}"'


def escribir_linea_csv(nombre_archivo, csv_line, export_dir):
    nombre_archivo = f"{export_dir}/{nombre_archivo}"
    
    with open(nombre_archivo, 'a', newline='', encoding='utf-8') as archivo_csv:
        escritor_csv = csv.writer(archivo_csv, delimiter=';')

        valores = csv_line.split("; ")
        escritor_csv.writerow(valores + [''])


meses = {
    "enero": "01", "ene": "01", "en": "01",
    "febrero": "02", "feb": "02",
    "marzo": "03", "mar": "03",
    "abril": "04", "abr": "04",
    "mayo": "05", "may": "05",
    "junio": "06", "jun": "06",
    "julio": "07", "jul": "07",
    "agosto": "08", "ago": "08",
    "septiembre": "09", "sep": "09",
    "octubre": "10", "oct": "10",
    "noviembre": "11", "nov": "11",
    "diciembre": "12", "dic": "12",
    "january": "01", "jan": "01", "jan": "01",
    "february": "02", "feb": "02", "feb": "02",
    "march": "03", "mar": "03", "mar": "03",
    "april": "04", "apr": "04", "apr": "04",
    "may": "05",
    "june": "06", "jun": "06", "jun": "06",
    "july": "07", "jul": "07", "jul": "07",
    "august": "08", "aug": "08", "aug": "08",
    "september": "09", "sep": "09", "sep": "09",
    "october": "10", "oct": "10", "oct": "10",
    "november": "11", "nov": "11", "nov": "11",
    "december": "12", "dec": "12", "dec": "12"
}

def limpiar_fecha(fecha_str :str):
    chars=["de", "del", ",", "/", ".","-"]
    for char in chars:
        fecha_str = fecha_str.replace(char, " ")
    return fecha_str


def formatear_fecha(fecha_str: str) -> str:
    try:
        fecha_str = limpiar_fecha(fecha_str)
        fecha_str = re.sub(r'\s+', '-', fecha_str)
        
        partes = fecha_str.split("-")
        nuevas_partes = []
        
        for parte in partes:
            contiene_letras = re.search(r'[a-zA-Z]', parte)
            contiene_numeros = re.search(r'\d', parte)

            if contiene_letras and contiene_numeros:
                parte = re.sub(r'[a-zA-Z]', '', parte)
            nuevas_partes.append(parte)
        partes = nuevas_partes
        

        if not re.fullmatch(r'\d+', partes[0]):
            partes[0], partes[1] = partes[1], partes[0]

        partes[0] = re.sub(r'[a-zA-Z]', '', partes[0])    

        if len(partes) != 3:
            return ""
        
        # Convierte el nombre del mes en número si es necesario
        if not re.fullmatch(r'\d+', partes[1]):
            partes[1] = meses.get(partes[1].lower(), "00")
        

        if int(partes[1]) > 12:
            partes[0], partes[1] = partes[1], partes[0]       

        # Intercambia el día y el año si es necesario
        if len(partes[0]) > 2:
            partes[0], partes[2] = partes[2], partes[0]
        
        
        # Añade el prefijo "20" si el año es de dos dígitos
        if len(partes[2]) == 2:
            partes[2] = "20" + partes[2]

        # Une las partes en una cadena nuevamente
        fecha_str = "-".join(partes)
        
        fecha = datetime.strptime(fecha_str, "%d-%m-%Y")
        return fecha.strftime("%Y-%m-%d")
    except:
        logging.error("Error al parsear fecha")
        return ""
  
    

def generar_linea_csv(datos, nombre_pdf, nombre_cvs, export_dir, exempt):
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

    divisa = datos[12]
    datavenc = datos[13]

            
    base_sin_iva = "0,00"
    if exempt and percent_iva == "0,00":
        base_sin_iva = importe_iva
        importe_iva = "0,00"


    irpf = "0,00"
    tipo_irpf = "0,00"
    
    base_iva2 = "0,00"
    importe_iva2 = "0,00"
    tipo_iva2 = "0,00"

    base_iva3 = "0,00"
    importe_iva3 = "0,00"
    tipo_iva3 = "0,00"


    tipo_registro = "F"
    tipo = "Factura"

    csv_line = f"{numero_factura}; {cif_proveedor}; {nombre_proveedor}; {cif_empresa}; {nombre_empresa}; {fecha_factura}; {tipo}; {total}; {divisa}; {base_sin_iva}; {irpf}; {tipo_irpf}; {base_imponible}; {importe_iva}; {percent_iva}; {base_iva2}; {importe_iva2}; {tipo_iva2}; {base_iva3}; {importe_iva3}; {tipo_iva3}; {nombre_pdf}; {datavenc}; {dataentreg}; {cod_empresa}; {cod_proveedor}; {datarec}; {tipo_registro}"
    print("csv: ", csv_line)
    logging.info(f"linea csv: {csv_line}")

    escribir_linea_csv(nombre_cvs, csv_line, export_dir)



def salvar_respuesta(campos, response):
    try:
        campos_format = [campo.lower() for campo in campos]
        lines = [line.strip() for line in response.split("\n")[1:-1]]

        fields_values=[]
        for line in lines:
            for campo_format in campos_format:
                if campo_format in line.lower() and ":" in line:
                    fields_values.append(line.split(":")[1])
                    break

        text = "{"
        if len(fields_values) == len(campos):
            for i in range (len(fields_values)):
                text += f'"{campos[i].replace(" ", "_")}"' + " : " + f'"{str(fields_values[i]).strip()}"' + ","

        text = text[:-1] 
        text += "}"

        parsed = json.loads(text)
        return parsed
    
    except:
        logging.info("No se ha podido salvar la respuesta mal generada")
        print("No se ha podido salvar la respuesta mal generada")
        return False


def solo_numeros(cadena):
    caracteres_validos = {'^', ',', '0', '-', '9', '$', '[', ']'}
    if "[-]" in cadena:
        return False
    for char in cadena:
        if char not in caracteres_validos:
            return False
    return True


def comprobar_n_factura(n_factura, cod_empresa, cod_proveedor, palabras):
    dades = get_factura_format(cod_empresa, cod_proveedor)
   
    if dades is not None and len(dades) != 0:
        only_number=False
        for format in dades:
            format_factura = format[0]
            divisa = format[1]
            logging.info(f"FORMAT FACTURA: {format_factura}")

            if solo_numeros(format_factura):
                only_number=True

            if not only_number:
                if re.match(format_factura, n_factura):
                    logging.info("Numero de factura encontrado")
                    return True, n_factura, divisa
                else:
                    for palabra in palabras:
                        
                        if re.match(format_factura, palabra):
                            print("Numero de factura encontrado")
                            n_factura = palabra
                            logging.info("Numero de factura encontrado")
                            return True, n_factura, divisa

            else:
                if re.match(format_factura, n_factura):
                    logging.info("Numero de factura encontrado")
                    return True, n_factura, divisa
                else:
                    for idx, palabra in enumerate(palabras):
                        if re.match(format_factura, palabra):
                            proxim = palabras[idx-4:idx+4]
                            proxim = [str(item).lower() for item in proxim]
                            if "fact" in proxim or "inv" in proxim or "fatt" in proxim:
                                print("PROXIM: ", proxim)
                                n_factura = palabra
                                logging.info("Numero de factura encontrado")
                                return True, n_factura, divisa                

        print("Numero de factura no encontrado")
        logging.error("Numero de factura no encontrado")
        return False, None, None    
    else:
        print("No se ha encontrado un formato de numero de factura")
        print(n_factura, cod_empresa, cod_proveedor)
        logging.error("No se ha encontrado un formato de numero de factura")
        return False, None, None    



def extraer_datos(data :str, campos, exempt):
    try:
        print("Generando json")
        logging.info("Obteniendo datos")
        start_time = time.time()
        response = str(gen_response(f"{data}", ', '.join(campos)))
        end_time = time.time()
        execution_time = end_time - start_time
        logging.info(f"Respuesta: \n{response}")
        logging.info(f"Datos obtenidos en {execution_time} segundos")
        print("\nTiempo de generar json: ", execution_time, " segundos")
        text="{"
        lines = response.strip().split("\n")[1:-1]
        for line in lines:
            if ":" in line:
                text += line.strip() + "\n"
        text += "}"

        response = re.sub(r'(?<!")\s*(\/\/|%)[^\n]*', "", text).replace("\n", "")
        datos = re.compile(r'(?<=: )(\d+\.\d+|\d+)(?=,|\n)').sub(add_quotes, response)
        datos = json.loads(datos)
        datos = {
            unidecode(clave.lower()).replace(" ", "_"): valor 
            for clave, valor in datos.items()
        }
        
        datos = clean_json(datos)
        print(datos)
        logging.info(datos)

        empresa = datos["cif_o_nif_del_cliente"]
        proveedor = datos["cif_del_proveedor"]
        iva_cant = datos["importe_de_iva"]
        base = datos["importe_total_antes_de_impuestos"]
        total = datos["importe_total_de_la_factura"]
        iva_percent = datos["porcentaje_de_iva"]

        n_factura = datos["numero_o_codigo_de_factura"]

        # Comprobar importes
        importes = comprobar_importes(total, base, iva_cant, iva_percent, exempt)

        if not importes[0]:
            print("Error de importes")
            return False, None
        
        # if float(importes[1][3].replace(",", ".")) > 22.0:
        #     return False, None 


        print("Importes: ", importes) 

        # Comprobar fecha
        fechafact = ""
        if "fecha_de_factura" in datos:
            fechafact = formatear_fecha(datos["fecha_de_factura"])
            if not fechafact:
                logging.error("No se ha encontrado fecha de factura")
                print("No se ha encontrado fecha de factura")
                return False, None, None
               

        fechavenc = ""
        if "fecha_de_caducidad_o_vencimiento" in datos:
            fechavenc = formatear_fecha(datos["fecha_de_caducidad_o_vencimiento"])
              
        
        # Comprobar cifs
        if empresa and proveedor:
            logging.info("CIFS obtenidos")
            dades_emp = comprobar_cifs(empresa, proveedor)

            if dades_emp:
                # Comprobar numero factura
                n_factura_divisa = comprobar_n_factura(n_factura, dades_emp[4], dades_emp[5], data.split())
                if n_factura_divisa[0]:
                    n_factura = n_factura_divisa[1]
                    divisa = n_factura_divisa[2]
                else:
                    return False, None    

                print("Export")
                logging.info("EXPORT")

                print(dades_emp)
                logging.info(f"Datos de empresa: {dades_emp}")

                datos = [
                    n_factura, 
                    fechafact,
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
            
        # Se prueba la expresion regular
        logging.info("Probando expresion")
        print("Probando expresion")
        dades_emp = usar_expresion(empresa, proveedor, data, cif_size)
        print(dades_emp)

        if dades_emp[0]:
            # Comprobar numero factura
            n_factura_divisa = comprobar_n_factura(n_factura, dades_emp[1][4], dades_emp[1][5], data.split())
            if n_factura_divisa[0]:
                n_factura = n_factura_divisa[1]
                divisa = n_factura_divisa[2]

            else:
                return False, None   
        
            logging.info("EXPORT")
            print("Export")
            logging.info(f"Datos de empresa: {dades_emp[1]}")

            datos = [
                n_factura, 
                fechafact,
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
            logging.info("ERROR")
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
    

def limpiar_texto(texto :str):
    lineas = texto.split('\n')  

    lineas_filtradas = []
    for linea in lineas:
        if re.match(r'^[a-zA-Z\s]*$', linea):  
            continue  
        lineas_filtradas.append(linea)  
    
    texto_filtrado = '\n'.join(lineas_filtradas)
    return texto_filtrado    