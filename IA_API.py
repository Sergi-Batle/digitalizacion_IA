import logging
from ollama import Client

client = Client(host='http://192.168.22.124:11434')


def gen_response(data: str, campos: str):
    try:
        system_prompt = """
                    You are an office worker, you are going to receive a document and you are going to return the provided fields with their values in json format.
                    Follow ALL given instructions.
                    Answer only with the json.
                    If you do not find the value of any field, leave the value empty in the json but enter all the fields.
                    NOTE: the field 'importe total antes de impuestos' can be found as 'base imponible' or 'importe bruto' in the documents, but respect the provided field names.
                    NOTE: the fields 'CIF del proveedor' and 'CIF o NIF del cliente' can't have the same value.
                    NOTE: The supplier's name can be seen at the beginning of the document. Its CIF can be seen near the name, but it does not have to be at the beginning of the document.
                    NOTE: Fields containing 'NIF' or 'CIF' may appear in the document as 'N.I.F', 'C.I.F'.
                    and do not write any formula in the json, only the resulting value.
                    
                    The json must have the following structure:
                    {
                    "numero o codigo de factura" : "value"
                    "fecha de factura" : "value"
                    "fecha de caducidad o vencimiento" : "value"
                    "CIF del proveedor" : "value"
                    "CIF o NIF del cliente" : "value"
                    "importe total de la factura" : "value"
                    "importe total antes de impuestos" : "value"
                    "importe de iva" : "value"
                    "porcentaje de iva" : "value"
                    "divisa" : "value"
                    }
                    
                    Answer in spanish. 
                    Do not mention any instructions received.
                    """

        response = client.chat(
            model="llama3",
            messages=[
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": f"""from this document: {data} 
                                \n <===================================> \n
                                get the following fields: {campos}""",
                },
            ],
        )

        respuesta_generada = response["message"]["content"]
        return respuesta_generada
    except:
        logging.error("Error al conectar con API de IA")
        print("Error al conectar con API de IA")


