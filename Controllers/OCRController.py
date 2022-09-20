import yaml
from app.constants.http_status_code import HTTP_200_OK, HTTP_201_CREATED, HTTP_400_BAD_REQUEST, HTTP_401_UNAUTHORIZED, HTTP_409_CONFLICT, HTTP_500_INTERNAL_SERVER_ERROR
import os
from flask_jwt_extended import create_access_token, create_refresh_token, get_jwt_identity, jwt_required
import validators
from werkzeug.security import check_password_hash, generate_password_hash
from PyPDF2 import PdfFileReader, PdfFileWriter
from flask import current_app, Blueprint, request, jsonify, json
from app.Services.methods import *
import scandir, zipfile, time
from invoice2data import extract_data
from invoice2data.extract.loader import read_templates
from app import db
from app.models import *

ocr_blueprint =  Blueprint('ocr', __name__,url_prefix = '/api' )


@ocr_blueprint.route('/register', methods=['POST'])
def register():
    username = request.json['username']
    email = request.json['email']
    password = request.json['password']

    if len(password) < 6:
        return jsonify({'error': "Password is too short"}), HTTP_400_BAD_REQUEST

    if len(username) < 3:
        return jsonify({'error': "User is too short"}), HTTP_400_BAD_REQUEST

    if not username.isalnum() or " " in username:
        return jsonify({'error': "Username should be alphanumeric, also no spaces"}), HTTP_400_BAD_REQUEST

    if not validators.email(email):
        return jsonify({'error': "Email is not valid"}), HTTP_400_BAD_REQUEST

    if User.query.filter_by(email=email).first() is not None:
        return jsonify({'error': "Email is taken"}), HTTP_409_CONFLICT

    if User.query.filter_by(username=username).first() is not None:
        return jsonify({'error': "username is taken"}), HTTP_409_CONFLICT

    pwd_hash = generate_password_hash(password)

    user = User(username=username, password=pwd_hash, email=email)
    db.session.add(user)
    db.session.flush()
    db.session.commit()

    return jsonify({
        'message': "User created",
        'user': {
            'username': username, "email": email
        }

    }), HTTP_201_CREATED

@ocr_blueprint.route('/login', methods=['POST'])
def login():
    email = request.json.get('email', '')
    password = request.json.get('password', '')

    user = User.query.filter_by(email=email).first()

    if user:
        is_pass_correct = check_password_hash(user.password, password)

        if is_pass_correct:
            refresh = create_refresh_token(identity=user.id)
            access = create_access_token(identity=user.id)

            return jsonify({
                'user': {
                    'refresh': refresh,
                    'access': access,
                    'username': user.username,
                    'email': user.email
                }

            }), HTTP_200_OK

    return jsonify({'error': 'Wrong credentials'}), HTTP_401_UNAUTHORIZED

@ocr_blueprint.route('/token/refresh', methods=['GET'])
@jwt_required(refresh=True)
def refresh_users_token():
    identity = get_jwt_identity()
    access = create_access_token(identity=identity)

    return jsonify({
        'access': access
    }), HTTP_200_OK

# https://www.youtube.com/watch?v=0E2Gj2Ba6PQ&t=637s a guide to build basic regex templates for invoice2data

@ocr_blueprint.route("/temps", methods=["POST"])
def custom_template():
    resp = request.json

    if not must_include(['issuer', 'keywords', 'fields'], resp):
        return jsonify({
            'error': 'Json must include all these keys [issuer, keywords, fields]'
        }), HTTP_400_BAD_REQUEST

    elif not must_include(['amount', 'invoice_number', 'date'], resp['fields']):
        return jsonify({
            'error': 'Fields object must include all these keys [amount, invoice_number, date]'
        }), HTTP_400_BAD_REQUEST

    elif type(resp["keywords"]) != list:
        return jsonify({
                'error': 'Keywords object must be a list'
            }), HTTP_400_BAD_REQUEST

    else:
        with open(current_app.config['CUSTOM_YAML_TEMPLATES'] + resp['issuer'] + '.yml', 'w') as yamlf:
            yaml.dump(resp, yamlf, allow_unicode=True)       
        return jsonify({
                "message":"Yaml document generated!"
            }), HTTP_201_CREATED

@ocr_blueprint.route("/ocr", methods=["POST"])
@jwt_required()
def page_name_post():
    if 'data_file' not in request.files:
        resp = jsonify({'message' : 'No file part in the request'})
        return resp, HTTP_400_BAD_REQUEST

    errors = {}
    success = False
    zip_finder = False
    files = request.files.getlist('data_file')
    for file in files:
        if (file and allowed_file(file.filename)) == False:
            errors =  errors[file.filename] = 'File type is not allowed'
            break
        else:
            success = True
            if file.filename[file.filename.rfind('.'):] != '.zip':
                zip_finder = True

    if success == False:
        resp = jsonify(errors)
        return resp, HTTP_500_INTERNAL_SERVER_ERROR

    else:
        path = current_app.config['TMP_PATH'] + "/" + str(get_jwt_identity())
        if not os.path.exists(path=path):
            os.mkdir(path)
        if zip_finder:
            date_dir_path2 = path + "/" + str(create_date_dir())
            os.mkdir(date_dir_path2) 

        for file in files:                 
            if file.filename.endswith('.zip'):
                date_dir_path = path + "/" + str(create_date_dir())
                os.mkdir(date_dir_path)
                file_like_object = file.stream._file  
                zipfile_ob = zipfile.ZipFile(file_like_object)
                file_names = zipfile_ob.namelist()
                file_names = [file_name for file_name in file_names if file_name.endswith((".pdf",".png",".jpeg",".jpg"))]
                for name in file_names:
                    zipfile_ob.extract(name, date_dir_path)

            elif file.filename.endswith('.pdf'):
                readpdf = PdfFileReader(file)
                output = PdfFileWriter()
                for i in range(readpdf.numPages):
                    output.addPage(readpdf.getPage(i))
                with open(date_dir_path2 + "/" + file.filename, "wb") as outputStream:
                    output.write(outputStream)
                time.sleep(1)
            else:
                file.save(os.path.join(date_dir_path2, file.filename))
                time.sleep(1)

        lists = []
        for paths, dirs, files in scandir.walk(current_app.config['TMP_PATH']):
            for file2 in files:
                templates = read_templates(current_app.config['YAML_TEMPLATES_PATH'])
                result = extract_data(paths + '/' + str(file2), templates=templates)
                if type(result) is not dict:
                    lists.append({"statusCode": 400, 'message': "There is no template for this file : {}".format(str(file2))})

                else:
                    invoice = Invoice(
                        amount=result['amount'],
                        issuer=result['issuer'],
                        date_invoice=result['date'],
                        currency=result['currency'],
                        invoice_number=result['invoice_number'],
                        user_id=get_jwt_identity())

                    db.session.add(invoice)
                    lists.append({"statusCode": 201, 'message': "{} extracted successfully !".format(str(file2))})

        db.session.commit()
        response = lists
        return {
                'statusCode': 200,
                'body': json.dumps(response)
                }