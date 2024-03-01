import requests, os, uuid, json

from flask import Flask, redirect, url_for, request, render_template, session
from dotenv import load_dotenv
from azure.storage.blob import BlobServiceClient, BlobClient, ContainerClient
from azure.identity import DefaultAzureCredential, ClientSecretCredential

load_dotenv()

app = Flask(__name__)

@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')

@app.route('/translator', methods=['GET'])
def translator():
    return render_template('translator.html')

@app.route('/upload/azfun', methods=['GET'])
def upload_azfun():
    return render_template('upload_azfun.html')

@app.route('/upload/azfunmd', methods=['GET'])
def upload_azfunmd():
    return render_template('upload_azfunmd.html')

@app.route('/upload/azlib', methods=['GET'])
def upload_azlib():
    return render_template('upload_azlib.html')


@app.route('/translator', methods=['POST'])
def translator_post():
    # Read the values from the form
    original_text = request.form['text']
    target_language = request.form['language']

    # Load the values from .env
    key = os.environ['KEY']
    endpoint = os.environ['ENDPOINT']
    location = os.environ['LOCATION']

    # Indicate that we want to translate and the API version (3.0) and the target language
    path = '/translate?api-version=3.0'
    # Add the target language parameter
    target_language_parameter = '&to=' + target_language
    # Create the full URL
    constructed_url = endpoint + path + target_language_parameter

    # Set up the header information, which includes our subscription key
    headers = {
        'Ocp-Apim-Subscription-Key': key,
        'Ocp-Apim-Subscription-Region': location,
        'Content-type': 'application/json',
        'X-ClientTraceId': str(uuid.uuid4())
    }

    # Create the body of the request with the text to be translated
    body = [{ 'text': original_text }]

    # Make the call using post
    translator_request = requests.post(constructed_url, headers=headers, json=body)
    # Retrieve the JSON response
    translator_response = translator_request.json()
    # Retrieve the translation
    translated_text = translator_response[0]['translations'][0]['text']

    # Call render template, passing the translated text,
    # original text, and target language to the template
    return render_template(
        'results.html',
        translated_text=translated_text,
        original_text=original_text,
        target_language=target_language
    )


@app.route('/upload/azfun', methods=['POST'])
def upload_azfun_post():
    file = request.files['file']
    file_content = file.read()

    azure_function_url = 'https://owjh-funcapp-py-1.azurewebsites.net/api/save_file_container'
    #azure_function_url = 'http://localhost:7071/api/save_file_container'
    params = {"file_name": file.filename}
    headers = {"Content-Type": file.content_type}

    response = requests.post(azure_function_url, params=params, headers=headers, data=file_content)

    if response.status_code == 200:
        return 'File uploaded successfully'
    else:
        return f'[Failed to upload file] {response.text}', 400

@app.route('/upload/azfunmd', methods=['POST'])
def upload_azfunmd_post():
    default_metadata = {
        'nemo_submitter':'wDanGunne',
        'nemo_submitter_first':'wDan',
        'nemo_submitter_last':'wGunne',
        'nemo_submitter_email':'wDanGunne@domain.com',
        'original_name':'wMyFileName',
        'submission_id':'w12345'        
    }

    file = request.files['file']

    # sending file content also works. In both cases, files is sent as a stream, not as data. 
    # So, if using file content, it sends an stream to the content that is already in the browser here
    # and if using file.stream, it sends an stream to and stream that is active in the browser here 
    #file_content = file.read()

    files = {
        "file": (file.filename, file.stream)
        #"file": (file.filename, file_content)
    }

    #azure_function_url = 'http://127.0.0.1:5000/upload/azfunmd_test'
    azure_function_url = 'http://localhost:7071/api/save_file_container_with_metadata'
    #azure_function_url = 'https://owjh-funcapp-py-1.azurewebsites.net/api/save_file_container_with_metadata'
    
    response = requests.post(azure_function_url, files=files, data=default_metadata)

    if response.status_code == 200:
        return 'File uploaded successfully'
    else:
        return 'Failed to upload file', 400

@app.route('/upload/azfunmd_test', methods=['POST'])
def upload_azfun_test_post():
    file = request.files.get('file') ## is equivalent to: request.files['file']
    file_name = file.filename
    metadata = request.form

    storageAccUrl = 'DefaultEndpointsProtocol=https;AccountName=owjhstorageaccount1a;EndpointSuffix=core.windows.net'
    credential = DefaultAzureCredential()

    blobServiceClient = BlobServiceClient.from_connection_string(storageAccUrl, credential)

    container_name = 'test-container-1'
    blob_client = blobServiceClient.get_blob_client(container_name, file_name)

    try:
        blob_client.upload_blob(file, metadata=metadata)
        #blob_client.set_blob_metadata(default_metadata)

        return f'File {file_name} uploaded successfully.'
    except Exception as e:
        return f'Failed to upload file: {str(e)}', 400


@app.route('/upload/azlib', methods=['POST'])
def upload_azlib_post():
    file = request.files['file']
    file_name = file.filename
    file_content = file.read()

    my_dev_storageAccount = 'DefaultEndpointsProtocol=https;AccountName=owigseusnemodev;EndpointSuffix=core.windows.net'
    umb_dev_storageAccount = 'DefaultEndpointsProtocol=https;AccountName=igseusnemodev;AccountKey=ZCVVl4UfLmMEamlZaqG5b1smJs/GXMgB37QyNtuKlvKyAy2R5NaaMHtagoI0Ofi3M1RPj7EzcJIp+AStKFcTbg==;EndpointSuffix=core.windows.net'

    target = request.form['target']

    if target == 'umbDev':
        storageAccUrl = umb_dev_storageAccount
    else:
        storageAccUrl = my_dev_storageAccount

    credential = DefaultAzureCredential()

    blobServiceClient = BlobServiceClient.from_connection_string(storageAccUrl, credential)

    container_name = 'nemo-manifest-submissions'
    blob_client = blobServiceClient.get_blob_client(container_name, file_name)

    default_metadata = {
        'nemo_submitter':'wDanGunne',
        'nemo_submitter_first':'wDan',
        'nemo_submitter_last':'wGunne',
        'nemo_submitter_email':'wDanGunne@domain.com',
        'original_name':'wMyFileName',
        'submission_id':'w12345'        
    }

    try:
        blob_client.upload_blob(file_content, metadata=default_metadata, overwrite=True)
        #blob_client.set_blob_metadata(default_metadata)

        return f'File {file_name} uploaded successfully to {target}'
    except Exception as e:
        return f'Failed to upload file: {str(e)} to {target}', 400
