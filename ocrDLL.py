import os
import requests


def convertPdfToText(uploadedFileUrl, destinationFile):
    """Converts PDF To Text using PDF.co Web API"""
    BASE_URL = "https://api.pdf.co/v1"
    API_KEY = "tales@angel24.es_D8My7i3qlI1P8u5Pl7Zu16e1cq1gJ5j3lhGctOAs98X8qdrJjW570AS4gIB3Mv0nfAL3a3Um8ue1CiW884V6Gpq8qb2CENo4bPvzmUetkv76Q2hUqAf3A472xvCMrl97qM0CSu56ShoFx6iPfFnZDt7651"
    # PDF document password. Leave empty for unprotected documents.
    Password = ""
    # Comma-separated list of page indices (or ranges) to process. Leave empty for all pages. Example: '0,2-5,7-'.
    Pages = ""

    # Prepare requests params as JSON
    # See documentation: https://apidocs.pdf.co
    parameters = {}
    parameters["name"] = os.path.basename(destinationFile)
    parameters["password"] = Password
    parameters["pages"] = Pages
    parameters["url"] = uploadedFileUrl

    # Prepare URL for 'PDF To Text' API request
    url = "{}/pdf/convert/to/text".format(BASE_URL)

    # Execute request and get response as JSON
    response = requests.post(url, data=parameters, headers={"x-api-key": API_KEY})
    if response.status_code == 200:
        json = response.json()

        if json["error"] == False:
            #  Get URL of result file
            resultFileUrl = json["url"]
            # Download result file
            r = requests.get(resultFileUrl, stream=True)
            if r.status_code == 200:
                txt = ""
                with open(destinationFile, "wb") as file:
                    for chunk in r:
                        file.write(chunk)
                        txt = txt + chunk.decode("utf-8")
                print(f'Result file saved as "{destinationFile}" file.')
                return txt
            else:
                print(f"Request error: {response.status_code} {response.reason}")
        else:
            # Show service reported error
            print(json["message"])
    else:
        print(f"Request error: {response.status_code} {response.reason}")


def uploadFile(fileName):
    """Uploads file to the cloud"""
    BASE_URL = "https://api.pdf.co/v1"
    API_KEY = "tales@angel24.es_D8My7i3qlI1P8u5Pl7Zu16e1cq1gJ5j3lhGctOAs98X8qdrJjW570AS4gIB3Mv0nfAL3a3Um8ue1CiW884V6Gpq8qb2CENo4bPvzmUetkv76Q2hUqAf3A472xvCMrl97qM0CSu56ShoFx6iPfFnZDt7651"
    # PDF document password. Leave empty for unprotected documents.
    Password = ""
    # 1. RETRIEVE PRESIGNED URL TO UPLOAD FILE.

    # Prepare URL for 'Get Presigned URL' API request
    url = "{}/file/upload/get-presigned-url?contenttype=application/octet-stream&name={}".format(
        BASE_URL, os.path.basename(fileName)
    )

    # Execute request and get response as JSON
    response = requests.get(url, headers={"x-api-key": API_KEY})
    if response.status_code == 200:
        json = response.json()

        if json["error"] == False:
            # URL to use for file upload
            uploadUrl = json["presignedUrl"]
            # URL for future reference
            uploadedFileUrl = json["url"]

            # 2. UPLOAD FILE TO CLOUD.
            with open(fileName, "rb") as file:
                requests.put(
                    uploadUrl,
                    data=file,
                    headers={
                        "x-api-key": API_KEY,
                        "content-type": "application/octet-stream",
                    },
                )

            return uploadedFileUrl
        else:
            # Show service reported error
            print(json["message"])
    else:
        print(f"Request error: {response.status_code} {response.reason}")

    return None


def ocr(file):
    # Source TXT file name
    SourceFile = file
    # Destination TXT file name
    DestinationFile = ".\\test.txt"

    uploadedFileUrl = uploadFile(SourceFile)
    if uploadedFileUrl != None:
        return convertPdfToText(uploadedFileUrl, DestinationFile)

