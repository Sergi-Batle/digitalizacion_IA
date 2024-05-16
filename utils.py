import os, shutil, re, logging, sys, csv
from database import check_existe, comprobar_cifs
from datetime import datetime


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


def correct_number(number: str):
    number = (
        number.lower()
        .replace("o", "0")
        .replace("s", "5")
        .replace("i", "1")
        .replace("b", "3")
    )
    return number


def clean_cif(string: str):
    result = string[0:-8]
    for char in string[-8:]:
        result += correct_number(char)

    return result


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


def limpiar_importe(numero :str):
    fragments=[]
    if check_last_three_digits(numero) == 'punto':
        fragments=numero.split(".")
        numero = ''.join(fragments[0:-1]).replace(",", "").replace(".", "") + "." + fragments[-1]
        
    elif check_last_three_digits(numero) == 'coma':
        fragments=numero.split(",")
        numero = ''.join(fragments[0:-1]).replace(",", "").replace(".", "") + "." + fragments[-1]
    else:
        numero += ".00"

    return numero



def comprobar_importes(total :str, base :str, iva_cant :str, iva_percent :str):
    total = limpiar_importe(total)
    base = limpiar_importe(base)
    iva_cant = limpiar_importe(iva_cant)
    iva_percent = limpiar_importe(iva_percent)

    total = float(total)
    base = float(base)
    iva_cant = float(iva_cant)
    iva_percent = float(iva_percent)

    con1 = (total == (iva_cant + base))
    con2 = (total == (base + (base * (iva_percent / 100))))
    con3 = ((total == base) and iva_cant != 0)

    if base > total:
        base = total - iva_cant
        if total == (base + iva_cant):
            total = "{:,.5f}".format(total).replace(',', 'X').replace('.', ',').replace('X', '.')
            base = "{:,.2f}".format(base).replace(',', 'X').replace('.', ',').replace('X', '.')
            iva_cant = "{:,.2f}".format(iva_cant).replace(',', 'X').replace('.', ',').replace('X', '.')
            iva_percent = "{:.2f}".format(iva_percent).replace(".", ",")
            return True, (total, base, iva_cant, iva_percent)
        

    if con1:
        total = "{:,.5f}".format(total).replace(',', 'X').replace('.', ',').replace('X', '.')
        base = "{:,.2f}".format(base).replace(',', 'X').replace('.', ',').replace('X', '.')
        iva_cant = "{:,.2f}".format(iva_cant).replace(',', 'X').replace('.', ',').replace('X', '.')
        iva_percent = "{:.2f}".format(iva_percent).replace(".", ",")
        return True, (total, base, iva_cant, iva_percent)
    
    
    if con2:
        iva_cant = base * (iva_percent / 100)
        
        if con1:
            total = "{:,.5f}".format(total).replace(',', 'X').replace('.', ',').replace('X', '.')
            base = "{:,.2f}".format(base).replace(',', 'X').replace('.', ',').replace('X', '.')
            iva_cant = "{:,.2f}".format(iva_cant).replace(',', 'X').replace('.', ',').replace('X', '.')
            iva_percent = "{:.2f}".format(iva_percent).replace(".", ",")
            return True, (total, base, iva_cant, iva_percent)
        
    if con3:
        base = total - iva_cant
        
        if con1:
            total = "{:,.5f}".format(total).replace(',', 'X').replace('.', ',').replace('X', '.')
            base = "{:,.2f}".format(base).replace(',', 'X').replace('.', ',').replace('X', '.')
            iva_cant = "{:,.2f}".format(iva_cant).replace(',', 'X').replace('.', ',').replace('X', '.')
            iva_percent = "{:.2f}".format(iva_percent).replace(".", ",")
            return True, (total, base, iva_cant, iva_percent)

    
    
    print("Error de importes")
    logging.error("Error de importes")
    return False, None




def buscar_cifs(palabras: str, cif_size):
    posibles_cifs = []
    for palabra in palabras:
        palabra_limpiada = re.sub(r"[^0-9]", "", palabra)
        
        if palabra_limpiada and (len(palabra_limpiada) <= cif_size[0] and len(palabra_limpiada) >= cif_size[1]):
            posibles_cifs.append(palabra_limpiada)

    return posibles_cifs



def usar_expresion(cif_1, cif_2, texto :str, cifs_size):
    empresa = cif_1 if cif_1 and check_existe(cif_1) else None
    proveedor = cif_2 if cif_2 and check_existe(cif_2) else None
    palabras = texto.split()
    
    if not empresa or not proveedor:
        cifs_encontrados = buscar_cifs(palabras, cifs_size)
        if not empresa:
            empresa = cifs_encontrados
        if not proveedor:
            proveedor = cifs_encontrados

    empresa = [empresa] if isinstance(empresa, str) else empresa
    proveedor = [proveedor] if isinstance(proveedor, str) else proveedor
    nom1=""
    nom2=""

    for cif1 in empresa:
        for cif2 in proveedor:

            if cif1 != cif2:
                result = comprobar_cifs(cif1, cif2)
                if result:
                    palabras = [s.lower() for s in palabras]
                    nom1 = comprobar_abrev(str(result[0]).replace(".", " ")).lower()
                    nom2 = comprobar_abrev(str(result[1]).replace(".", " ")).lower()

                    print(cif1)
                    print(cif2)

                    print("NOMS:")
                    print(nom1)
                    print(nom2)
                        
                    if (nom1 and nom2) and (nom1 in texto.lower() and nom2 in texto.lower()):
                        print("Nombres encontrados")
                        return True, result

    return False, None


def comprobar_abrev(cadena : str):
    cadenas = cadena.split(" ")
    return max(cadenas, key=len)
    

def clean_json(datos, useOcr):
    try:
        datos["cif_del_proveedor"] = re.sub(
            r"[^0-9]", "", str(datos["cif_del_proveedor"])
        )
        
        datos["cif_del_proveedor"] = clean_cif(datos["cif_del_proveedor"]) if useOcr else datos["cif_del_proveedor"]

        datos["cif_o_nif_del_cliente"] = re.sub(
            r"[^0-9]", "", str(datos["cif_o_nif_del_cliente"])
        )

        datos["cif_o_nif_del_cliente"] = clean_cif(datos["cif_o_nif_del_cliente"]) if useOcr else datos["cif_o_nif_del_cliente"]

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


def save_json(input_file_path, new_text):
    with open(input_file_path, "a") as file:
        file.write("\n" + str(new_text))        



def write_csv(nombre_archivo, csv_line):
    archivo_existente = os.path.exists(nombre_archivo)
    with open(nombre_archivo, 'a', newline='', encoding='utf-8') as archivo_csv:
        escritor_csv = csv.writer(archivo_csv)

        if not archivo_existente:
            nombres = "numero_factura, cif_proveedor, nombre_proveedor, cif_empresa, nombre_empresa, fecha_factura, tipo, total, divisa, base_sin_iva, irpf, tipo_irpf, base_imponible, importe_iva, percent_iva, base_iva2, importe_iva2, tipo_iva2, base_iva3, importe_iva3, tipo_iva3, archivo, datavenc, dataentreg, cod_empresa, cod_proveedor, datarec, tipo_registro"
            nombres_columnas = nombres.split(",")
            escritor_csv.writerow(nombres_columnas)

        valores = csv_line.split(", ")
        escritor_csv.writerow(valores)

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
    "diciembre": "12", "dic": "12"
}

def formatear_fecha(fecha_str :str):
    fecha_str = fecha_str.replace(".", "-").replace("/", "-").replace(" ", "-")

    partes = fecha_str.split("-")
    if not re.fullmatch(r'\d+', partes[1]):
        partes[1] = meses[partes[1]]


    if len(partes[0]) > 2:
        aux = partes[0]
        partes[0] = partes[2]
        partes[2] = aux       

    if len(partes[2]) == 2:
        partes[2] = "20" + partes[2]     

    fecha_str = "-".join(partes)
    try:
        fecha = datetime.strptime(fecha_str, "%d-%m-%Y")
    except ValueError:
        return fecha_str

    return fecha.strftime("%Y-%m-%d")



