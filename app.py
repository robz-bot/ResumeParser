
from flask import Flask, request, jsonify
from flask_cors import CORS, cross_origin
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)  
CORS(app)

ALLOWED_EXTENSIONS = set(['pdf','doc','docx','zip'])

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
 
def get_file_info(file):
    extention = file.filename.rsplit('.', 1)[1].lower()
    if(extention == 'zip'):
        return "zip"
        # unzip logic goes here 
    if(extention == 'pdf'):
        # read pdf
        return "pdf"
    if(extention == 'doc'):
        # read pdf
        return "doc"
    if(extention == 'docx'):
        # read pdf
        return "docx"
    
    return ""

@app.route('/parse_table', methods=['POST'])
@cross_origin()
def upload_file():
    # delete you files under resume folder 
    print(request.files)
    if 'file' not in request.files:
        # print('no file in request')
        resp = jsonify({'isSuccess':'false', 'message': 'No file part in the request' })
        resp.status_code = 400
        return resp
    file = request.files['file']
    if file.filename == '':
        # print('no selected file')
        resp = jsonify({'isSuccess':'false', 'message': 'No file selected for uploading' })
        resp.status_code = 400
        return resp
    if file and allowed_file(file.filename):
        
        print("$$$$$$$$"+ext)

        filename = secure_filename(file.filename)
        file.save(os.path.join("resume", filename))

        ext = get_file_info(file)
        

        resp = jsonify({'isSuccess':'true', 'message': 'File processed', 'filename':filename })
        resp.status_code = 201
        return resp
    resp = jsonify({'message' : 'Allowed file types are doc, pdf, docx, zip'})
    resp.status_code = 400
    return resp



if __name__=='__main__':
   app.run()