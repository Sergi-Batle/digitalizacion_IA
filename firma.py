import asyncio
from pyhanko.sign import signers
from pyhanko.pdf_utils.incremental_writer import IncrementalPdfFileWriter
import aiofiles



async def async_demo(signer, archivo_pdf):
    with open(archivo_pdf, 'rb') as doc:
        w = IncrementalPdfFileWriter(doc, strict=False)
        out = await signers.async_sign_pdf(
            w, signers.PdfSignatureMetadata(field_name='angel24'),
            signer=signer,
        )
        # Guardar el PDF firmado
        with open(archivo_pdf, 'wb') as f_out:
            f_out.write(out.getbuffer())


async def main(ruta_certificat, ruta_clave, archivo_pdf):
    async with aiofiles.open(ruta_clave, 'rb') as archivo:
        clave = await archivo.readline()
        clave = clave.strip()

    cms_signer = signers.SimpleSigner.load_pkcs12(
        ruta_certificat,
        passphrase=clave
    )

    await async_demo(cms_signer, archivo_pdf)


def firmar_pdf(ruta_certificat, ruta_clave, ruta_archivo_pdf):
    asyncio.run(main(ruta_certificat, ruta_clave, ruta_archivo_pdf))




# from pyhanko.sign.fields import SigFieldSpec, append_signature_field
# from pyhanko.sign.validation import validate_pdf_signature
# from pyhanko_certvalidator.context import ValidationContext
# from pyhanko.pdf_utils.reader import PdfFileReader


# def is_pdf_signed(pdf_path):
#     with open(pdf_path, 'rb') as f:
#         reader = PdfFileReader(f)
#         signatures = reader.embedded_signatures

#         if not signatures:
#             print("El PDF no contiene firmas digitales.")
#             return False

#         vc = ValidationContext(allow_fetching=True)

#         for sig in signatures:
#             print(f"Verificando firma en el campo: {sig.field_name}")
#             status = validate_pdf_signature(sig, vc)

#             if status.intact and status.valid:
#                 print(f"La firma en el campo '{sig.field_name}' es válida.")
#             else:
#                 print(f"La firma en el campo '{sig.field_name}' no es válida.")

#         return True if signatures else False


# # Verificar el PDF firmado
# pdf_path = rf'test_firma\Andreu Oliver Jaume_5550000_2024-05-28_9_35_b22e40e7-8bb2-4e26-9816-bce09b38b8f1.pdf'
# if is_pdf_signed(pdf_path):
#     print("El PDF está firmado.")
# else:
#     print("El PDF no está firmado.")
