from flask import Flask, request, jsonify
from flask_cors import CORS, cross_origin
import os
from werkzeug.utils import secure_filename
import pandas as pd
from pyresparser import ResumeParser
from zipfile import ZipFile
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity

app = Flask(__name__)
CORS(app)

ALLOWED_EXTENSIONS = {'pdf', 'docx', 'zip'}


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def get_file_info(file, filename):
    ac_dict = {}
    re_dict = {}
    extention = file.filename.rsplit('.', 1)[1].lower()

    if extention == 'zip':
        # unzip logic goes here
        with ZipFile('resume/' + filename, 'r') as zip_:
            # printing all the contents of the zip file
            zip_.printdir()
            file_names = zip_.namelist()
            print("file_names", file_names)
            zip_.extractall("resume")
            name = []
            email = []
            phone = []
            mk = []
            candis_df = pd.DataFrame(columns=["Total Experience", "Skills", "Designation"])
            k = 0
            for j in file_names:
                mk.append(k)
                if j.endswith('.pdf') or j.endswith('.docx'):
                    data = ResumeParser('resume/' + j).get_extracted_data()
                    print(data)
                    dict_ = {}
                    selected_dict = {}
                    if "name" in data:
                        if data["name"] is not None:
                            n = data["name"]
                            name.append(n)
                        else:
                            n = "Not Available"
                            name.append(n)
                    else:
                        n = "Not Available"
                        name.append(n)

                    if "email" in data:
                        if data["email"] is not None:
                            n = data["email"]
                            email.append(n)
                        else:
                            n = "Not Available"
                            email.append(n)
                    else:
                        n = "Not Available"
                        email.append(n)

                    if "mobile_number" in data:
                        if data["mobile_number"] is not None:
                            n = data["mobile_number"]
                            phone.append(n)
                        else:
                            n = "Not Available"
                            phone.append(n)
                    else:
                        n = "Not Available"
                        phone.append(n)

                    for l_, m in data.items():
                        dict_.update({l_: m})
                        if l_ == "total_experience":
                            if type(m) is float:
                                # m = str(m)
                                selected_dict.update({l_: m})
                            else:
                                m = float(m)
                                selected_dict.update({l_: m})
                        if l_ == "skills":
                            if m is not None:
                                m = " ".join(m)
                                # selected_dict.update({l_: str(m)[1:-1]})
                                selected_dict.update({l_: m})
                            else:
                                m = "Not Available"
                                selected_dict.update({l_: m})

                        if l_ == "designation":
                            if m is not None:
                                m = " ".join(m)
                                # selected_dict.update({l_: str(m)[1:-1]})
                                selected_dict.update({l_: m})
                            else:
                                m = "Not Available"
                                selected_dict.update({l_: m})

                    emp_df = pd.DataFrame(selected_dict, index=[k])
                    # print(emp_df)

                    emp_df.rename(columns={'total_experience': 'Total Experience', 'skills': 'Skills',
                                           'designation': 'Designation'},
                                  inplace=True)
                    emp_df["Total Experience"].fillna("Not Available", inplace=True)
                    emp_df["Designation"].fillna("Not Available", inplace=True)
                    emp_df["Skills"].fillna("Not Available", inplace=True)

                    candis_df = pd.concat([candis_df, emp_df], axis=0)
                    k += 1
                else:
                    print("File Not Supported")
        ac_dict, re_dict = customZip_ner(candis_df, name, email, phone, mk)
        print(mk)
        return ac_dict, re_dict

    if extention == 'pdf':
        # read pdf
        data = ResumeParser('resume/' + filename).get_extracted_data()
        custom_ner(data)
        ac_dict, re_dict = custom_ner(data)
        return ac_dict, re_dict

    if extention == 'docx':
        # read docx
        data = ResumeParser('resume/' + filename).get_extracted_data()
        custom_ner(data)
        ac_dict, re_dict = custom_ner(data)
        return ac_dict, re_dict
    return ac_dict, re_dict


@app.route('/parse_table', methods=['POST'])
@cross_origin()
def upload_file():
    # delete you files under resume folder
    print(request.files)
    if 'file' not in request.files:
        # print('no file in request')
        resp = jsonify({'isSuccess': 'false', 'message': 'No file part in the request'})
        resp.status_code = 400
        return resp
    file = request.files['file']
    if file.filename == '':
        # print('no selected file')
        resp = jsonify({'isSuccess': 'false', 'message': 'No file selected for uploading'})
        resp.status_code = 400
        return resp
    if file and allowed_file(file.filename):
        # print("$$$$$$$$" + ext)

        file_name = secure_filename(file.filename)
        file.save(os.path.join("resume", file_name))

        shortlisted, notShortlisted = get_file_info(file, file_name)
        # print("ext:", shortlisted, "ext2:", notShortlisted)
        resp = jsonify({'isSuccess': 'true', 'message': 'File processed', 'filename': file_name,
                        'Shortlisted': [shortlisted], 'NotShortlisted': [notShortlisted]})
        resp.status_code = 201
        print('resp', resp)
        return resp
    resp = jsonify({'message': 'Allowed file types are doc, pdf, docx, zip'})
    resp.status_code = 400
    return resp


def custom_ner(data):
    dict_ = {}
    selected_dict = {}
    for l_, m in data.items():
        dict_.update({l_: m})
        if l_ == "total_experience":
            if type(m) is float:
                # m = str(m)
                selected_dict.update({l_: m})
            else:
                m = float(m)
                selected_dict.update({l_: m})
        if l_ == "designation":
            if m is not None:
                # m = " ".join(m)
                selected_dict.update({l_: str(m)[1:-1]})
            else:
                m = "Not Available"
                selected_dict.update({l_: m})

        if l_ == "skills":
            if m is not None:
                # m = " ".join(m)
                selected_dict.update({l_: str(m)[1:-1]})
            else:
                m = "Not Available"
                selected_dict.update({l_: m})

    # creating dataframe for cos_sim

    # creating data frame with required features
    emp_df = pd.DataFrame(selected_dict, index=[0])

    emp_df.rename(columns={'total_experience': 'Total Experience', 'skills': 'Skills', 'designation': 'Designation'},
                  inplace=True)

    emp_df["Total Experience"].fillna("Not Available", inplace=True)
    emp_df["Designation"].fillna("Not Available", inplace=True)
    emp_df["Skills"].fillna("Not Available", inplace=True)

    jd_file_ = 'JD/Java_Developer.docx'

    if jd_file_.endswith('.docx'):
        jd_file = jd_file_
        job_dict = {}
        jd_data = ResumeParser(jd_file).get_extracted_data()
        print("jd_data:", jd_data)
        for l_, m in jd_data.items():
            if l_ == "total_experience":
                if type(m) is float:
                    # m = str(m)
                    job_dict.update({l_: m})
                else:
                    m = float(m)
                    job_dict.update({l_: m})
            if l_ == "skills":
                if m is not None:
                    # m = " ".join(m)
                    job_dict.update({l_: str(m)[1:-1]})
                else:
                    m = "Not Mentioned"
                    job_dict.update({l_: m})
            if l_ == "designation":
                if m is not None:
                    # m = " ".join(m)
                    job_dict.update({l_: str(m)[1:-1]})
                else:
                    m = "Not Mentioned"
                    job_dict.update({l_: m})

        # creating data frame with required features
        job_desc = pd.DataFrame(job_dict, index=[0])

        job_desc.rename(
            columns={"total_experience": "Total Experience", "skills": "Skills", "designation": "Designation"},
            inplace=True)

        # if job_desc["Total Experience"].equals(emp_df["Total Experience"]):
        if job_desc.loc[0, "Total Experience"] <= emp_df.loc[0, "Total Experience"]:
            df_combined = pd.DataFrame(columns=["Total Experience", "Skills", "Designation"])
            df_combined = pd.concat([df_combined, job_desc, emp_df], axis=0)
            df_combined.reset_index(inplace=True, drop=True)
            df_combined['Total Experience'] = df_combined['Total Experience'].astype(str)
            df_combined = df_combined[["Total Experience", "Skills", "Designation"]]
            df_combined["Total Experience"].fillna("Not Mentioned", inplace=True)
            df_combined["Designation"].fillna("Not Mentioned", inplace=True)
            df_combined["Skills"].fillna("Not Mentioned", inplace=True)
            print(df_combined)
            a_list = []
            for j in range((df_combined.shape[0])):
                cur_row = []
                for k in range(df_combined.shape[1]):
                    cur_row.append(df_combined.iat[j, k])
                a_list.append(cur_row)

            res = [' '.join(ele) for ele in a_list]
            print(res)

            text = [res[0], res[1]]
            # print(text)
            cv = CountVectorizer()
            count_matrix = cv.fit_transform(text)

            cos_sim = round(cosine_similarity(count_matrix)[0][1] * 100, 2)
            cos = cos_sim + 30
            # cos.append(cos_)

            status = []
            remarks = []
            # percent = int(input("Enter the threshold: "))
            if cos >= 50:
                sta = "Selected"
                status.append(sta)
                remark = "JD is matched with Candidate's skills set"
                remarks.append(remark)
            else:
                sta = "Not Selected"
                status.append(sta)
                remark = "JD is not matched with Candidate's skills set"
                remarks.append(remark)

            cosColumn_df = pd.DataFrame(columns=["Name", "Similarity", "Status"])
            name = []
            email = []
            phone = []
            gender = []
            if "name" in data:
                if data["name"] is not None:
                    n = data["name"]
                    name.append(n)
                else:
                    n = "Not Available"
                    name.append(n)
            else:
                n = "Not Available"
                name.append(n)

            if "email" in data:
                if data["email"] is not None:
                    n = data["email"]
                    email.append(n)
                else:
                    n = "Not Available"
                    email.append(n)
            else:
                n = "Not Available"
                email.append(n)

            if "mobile_number" in data:
                if data["mobile_number"] is not None:
                    n = data["mobile_number"]
                    phone.append(n)
                else:
                    n = "Not Available"
                    phone.append(n)
            else:
                n = "Not Available"
                phone.append(n)

            g = 'Not Available'

            gender.append(g)
            mk = int(1)
            cos__df = pd.DataFrame()
            cos__df['index'] = pd.Series(mk)
            cos__df["Name"] = pd.Series(name)
            cos__df['Similarity'] = pd.Series(cos)
            cos__df['Status'] = pd.Series(status)
            cos__df['Remark'] = pd.Series(remarks)
            cos__df['Email id'] = pd.Series(email)
            cos__df['Phone No'] = pd.Series(phone)
            cos__df['Gender'] = pd.Series(gender)
            cos__df["Name"].fillna("Not Available", inplace=True)
            cos__df[['FirstName', 'LastName']] = cos__df.Name.str.split(expand=True)

            cosine_df = pd.concat([cosColumn_df, cos__df], axis=0, ignore_index=True)

            cosine_df = cosine_df[['index', 'FirstName', 'LastName', 'Email id', 'Phone No', 'Status', 'Similarity',
                                   'Remark']]

            cosine_df.index = cosine_df.index + 1
            cosine_df['index'] = cosine_df['index'].astype(int)
            ac_df = cosine_df.loc[cosine_df['Status'] == "Selected"]
            re_df = cosine_df.loc[cosine_df['Status'] == "Not Selected"]
            print(ac_df)
            print(re_df)
            ac_df = ac_df[['index', 'FirstName', 'LastName', 'Email id', 'Phone No', 'Similarity', 'Remark']]
            re_df = re_df[['index', 'FirstName', 'LastName', 'Email id', 'Phone No', 'Similarity', 'Remark']]

            # ac_dict = ac_df.to_dict('index')
            # re_dict = re_df.to_dict('index')

            ac_dict = ac_df.to_dict('record')
            re_dict = re_df.to_dict('record')

            # l1 = ['NotShortlisted:', re_dict]
            # l2 = ['Shortlisted:', ac_dict]
            # l3 = l1 + l2
            # print(cosine_df)
            # print(ac_dict)
            # print(re_dict)
            # res = dict({"res": l3})
            # print(res)
            # print(l1)
            print(ac_dict, re_dict)
            return ac_dict, re_dict
        else:
            df_combined = pd.DataFrame(columns=["Total Experience", "Skills", "Designation"])
            df_combined = pd.concat([df_combined, job_desc, emp_df], axis=0)
            df_combined.reset_index(inplace=True, drop=True)
            df_combined['Total Experience'] = df_combined['Total Experience'].astype(str)
            df_combined = df_combined[["Total Experience", "Skills", "Designation"]]
            df_combined["Total Experience"].fillna("Not Mentioned", inplace=True)
            df_combined["Designation"].fillna("Not Mentioned", inplace=True)
            df_combined["Skills"].fillna("Not Mentioned", inplace=True)

            a_list = []
            for j in range((df_combined.shape[0])):
                cur_row = []
                for k in range(df_combined.shape[1]):
                    cur_row.append(df_combined.iat[j, k])
                a_list.append(cur_row)

            res = [' '.join(ele) for ele in a_list]
            print(res)

            text = [res[0], res[1]]
            # print(text)
            cv = CountVectorizer()
            count_matrix = cv.fit_transform(text)

            cos_sim = round(cosine_similarity(count_matrix)[0][1] * 100, 2)
            cos = cos_sim + 30
            # cos.append(cos_)

            status = "Not Selected"
            remarks = "Total Experience is not meeting the JD's Requirements"

            cosColumn_df = pd.DataFrame(columns=["Name", "Similarity", "Status"])
            name = []
            email = []
            phone = []
            gender = []
            if "name" in data:
                if data["name"] is not None:
                    n = data["name"]
                    name.append(n)
                else:
                    n = "Not Available"
                    name.append(n)
            else:
                n = "Not Available"
                name.append(n)

            if "email" in data:
                if data["email"] is not None:
                    n = data["email"]
                    email.append(n)
                else:
                    n = "Not Available"
                    email.append(n)
            else:
                n = "Not Available"
                email.append(n)

            if "mobile_number" in data:
                if data["mobile_number"] is not None:
                    n = data["mobile_number"]
                    phone.append(n)
                else:
                    n = "Not Available"
                    phone.append(n)
            else:
                n = "Not Available"
                phone.append(n)
            g = 'Not Available'
            gender.append(g)

            mk = int(1)

            cos__df = pd.DataFrame()
            cos__df['index'] = pd.Series(mk)
            cos__df["Name"] = pd.Series(name)
            cos__df['Similarity'] = pd.Series(cos)
            cos__df['Status'] = pd.Series(status)
            cos__df['Remark'] = pd.Series(remarks)
            cos__df['Email_id'] = pd.Series(email)
            cos__df['Phone No'] = pd.Series(phone)
            cos__df["Name"].fillna("Not Available", inplace=True)

            cos__df[['FirstName', 'LastName']] = cos__df.Name.str.split(expand=True)
            cosine_df = pd.concat([cosColumn_df, cos__df], axis=0, ignore_index=True)

            cosine_df['index'] = cosine_df['index'].astype(int)

            cosine_df = cosine_df[['index', 'FirstName', 'LastName', 'Email id', 'Phone No', 'Status', 'Similarity',
                                   'Remark']]

            cosine_df.index = cosine_df.index + 1

            print(cosine_df)

            ac_df = cosine_df.loc[cosine_df['Status'] == "Selected"]
            re_df = cosine_df.loc[cosine_df['Status'] == "Not Selected"]

            ac_df = ac_df[['index', 'FirstName', 'LastName', 'Email id', 'Phone No', 'Similarity', 'Remark']]
            re_df = re_df[['index', 'FirstName', 'LastName', 'Email id', 'Phone No', 'Similarity', 'Remark']]

            # ac_dict = ac_df.to_dict('index')
            # re_dict = re_df.to_dict('index')

            # df.to_dict(orient='records')
            ac_dict = ac_df.to_dict('record')
            re_dict = re_df.to_dict('record')

            print(re_dict, ac_dict)
            return ac_dict, re_dict
    else:
        print("File Not Supported")


def customZip_ner(candis_df, name, email, phone, mk):
    jd_file_ = 'JD/Java_Developer.docx'
    if jd_file_.endswith('.docx'):
        jd_file = jd_file_
        job_dict = {}
        jd_data = ResumeParser(jd_file).get_extracted_data()
        for l_, m in jd_data.items():
            if l_ == "total_experience":
                if type(m) is float:
                    # m = str(m)
                    job_dict.update({l_: m})
                else:
                    m = float(m)
                    job_dict.update({l_: m})
            if l_ == "skills":
                if m is not None:
                    m = " ".join(m)
                    # job_dict.update({l_: str(m)[1:-1]})
                    job_dict.update({l_: m})
                else:
                    m = "Not Mentioned"
                    job_dict.update({l_: m})

            if l_ == "designation":
                if m is not None:
                    m = " ".join(m)
                    # job_dict.update({l_: str(m)[1:-1]})
                    job_dict.update({l_: m})
                else:
                    m = "Not Mentioned"
                    job_dict.update({l_: m})

        # creating data frame with required features
        job_desc = pd.DataFrame(job_dict, index=[0])

        job_desc.rename(
            columns={"total_experience": "Total Experience", "skills": "Skills", "designation": "Designation"},
            inplace=True)

        status = []
        cos = []
        remarks = []
        for i in range(len(candis_df)):
            if job_desc.loc[0, "Total Experience"] <= candis_df.loc[i, "Total Experience"]:
                df_combined = pd.DataFrame(columns=["Total Experience", "Skills", "Designation"])
                df_combined = pd.concat([df_combined, job_desc, candis_df.iloc[[i]]], axis=0)
                df_combined.reset_index(inplace=True, drop=True)
                df_combined = df_combined[["Total Experience", "Skills", "Designation"]]
                df_combined['Total Experience'] = df_combined['Total Experience'].astype(str)
                df_combined["Total Experience"].fillna("Not Mentioned", inplace=True)
                df_combined["Designation"].fillna("Not Mentioned", inplace=True)
                df_combined["Skills"].fillna("Not Mentioned", inplace=True)

                a_list = []
                for j in range((df_combined.shape[0])):
                    cur_row = []
                    for k in range(df_combined.shape[1]):
                        cur_row.append(df_combined.iat[j, k])
                    a_list.append(cur_row)

                res = [' '.join(ele) for ele in a_list]

                text = [res[0], res[1]]
                print(text)
                cv = CountVectorizer()
                count_matrix = cv.fit_transform(text)

                cos_sim = round(cosine_similarity(count_matrix)[0][1] * 100, 2)
                cos_ = cos_sim + 30
                cos.append(cos_)
                # for i in range(len(cos)):
                if cos_ > 50:
                    sta = "Selected"
                    status.append(sta)
                    remark = "JD is matched with Candidate's skills set"
                    remarks.append(remark)
                else:
                    sta = "Not Selected"
                    status.append(sta)
                    remark = "JD is not matched with Candidate's skills set"
                    remarks.append(remark)
            else:
                df_combined = pd.DataFrame(columns=["Total Experience", "Skills", "Designation"])
                df_combined = pd.concat([df_combined, job_desc, candis_df.iloc[[i]]], axis=0)
                df_combined.reset_index(inplace=True, drop=True)
                df_combined = df_combined[["Total Experience", "Skills", "Designation"]]
                df_combined['Total Experience'] = df_combined['Total Experience'].astype(str)
                df_combined["Total Experience"].fillna("Not Mentioned", inplace=True)
                df_combined["Designation"].fillna("Not Mentioned", inplace=True)
                df_combined["Skills"].fillna("Not Mentioned", inplace=True)

                a_list = []
                for j in range((df_combined.shape[0])):
                    cur_row = []
                    for k in range(df_combined.shape[1]):
                        cur_row.append(df_combined.iat[j, k])
                    a_list.append(cur_row)

                res = [' '.join(ele) for ele in a_list]

                text = [res[0], res[1]]
                print(text)
                cv = CountVectorizer()
                count_matrix = cv.fit_transform(text)

                cos_sim = round(cosine_similarity(count_matrix)[0][1] * 100, 2)
                cos_ = cos_sim + 30
                cos.append(cos_)

                sta = "Not Selected"
                status.append(sta)

                remark = "Total Experience is not meeting the JD's Requirements"
                remarks.append(remark)

        cos_df = pd.DataFrame(columns=['index', 'Name', 'Similarity', 'Status', 'Remark', 'Email id', 'Phone No'])
        print(cos_df)
        cos_df['index'] = pd.Series(mk)
        cos_df['Name'] = pd.Series(name)
        cos_df['Similarity'] = pd.Series(cos)
        cos_df['Status'] = pd.Series(status)
        cos_df['Remark'] = pd.Series(remarks)
        cos_df['Email id'] = pd.Series(email)
        cos_df['Phone No'] = pd.Series(phone)

        cos_df['index'] = cos_df['index'].astype(int)

        cos_df = cos_df[['index', 'Name', 'Similarity', 'Status', 'Remark', 'Email id', 'Phone No']]

        cos_df[['FirstName', 'LastName']] = cos_df.Name.str.split(" ", n=1, expand=True)

        cos_df = cos_df[['index', 'FirstName', 'LastName', 'Email id', 'Phone No', 'Similarity', 'Status', 'Remark']]

        cos_df['index'] = cos_df['index'] + 1
        cos_df.drop_duplicates(keep="first", inplace=True)
        cos_df.reset_index(inplace=True)
        ac_df = cos_df.loc[cos_df['Status'] == "Selected"]
        re_df = cos_df.loc[cos_df['Status'] == "Not Selected"]

        ac_df = ac_df[['index', 'FirstName', 'LastName', 'Email id', 'Phone No', 'Similarity', 'Remark']]
        re_df = re_df[['index', 'FirstName', 'LastName', 'Email id', 'Phone No', 'Similarity', 'Remark']]

        ac_dict = ac_df.to_dict('record')
        re_dict = re_df.to_dict('record')

        print(re_dict, ac_dict)
        return ac_dict, re_dict
    else:
        print("File Not Supported")


if __name__ == '__main__':
    app.run()
