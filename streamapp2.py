import streamlit as st
from pyresparser import ResumeParser
from zipfile import ZipFile
import pandas as pd
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import pymongo
from pymongo import MongoClient

st.sidebar.title('Upload the data')
st.title('PRECISION')
st.text('Enterprise edition 2022.')

jd_file_ = st.sidebar.file_uploader('Upload the JD here*')
if jd_file_:
    if jd_file_.name.endswith('.docx'):
        st.sidebar.success('JD Uploaded!')
    else:
        st.sidebar.warning('Upload a docx File')

input_resumes = st.sidebar.file_uploader('Upload the resumes here*')
if input_resumes:
    if input_resumes.name.endswith('.docx') or input_resumes.name.endswith('.pdf') or input_resumes.name.endswith('.zip'):
        st.sidebar.success('JD Uploaded!')
    else:
        st.sidebar.warning('Upload Failed')


def get_data(candis_resumes):
    if candis_resumes.name.endswith('.docx'):
        data = ResumeParser(candis_resumes).get_extracted_data()
        print(data)
        custom_ner(data)
    # running through every page
    # pdf
    elif candis_resumes.name.endswith('.pdf'):
        data = ResumeParser(candis_resumes).get_extracted_data()
        print(data)
        custom_ner(data)

    # Processing Zip File
    elif candis_resumes.name.endswith('.zip'):
        for_zip(candis_resumes)
    else:
        print("File Not Supported")
        st.write("File Not Supported")


def for_zip(candis_resumes):
    with ZipFile(candis_resumes, 'r') as zip_:
        # printing all the contents of the zip file
        zip_.printdir()
        file_names = zip_.namelist()
        zip_.extractall()
        name = []
        email = []
        phone = []
        candis_df = pd.DataFrame(columns=["Total Experience", "Skills", "Designation"])
        candis_df = read_zip(candis_df, email, file_names, name, phone)
        customZip_ner(candis_df, name, email, phone)
        return candis_df, name, email, phone


def read_zip(candis_df, email, file_names, name, phone):
    k = 0
    for j in file_names:
        if j.endswith('.pdf') or j.endswith('.docx'):
            data = ResumeParser(j).get_extracted_data()
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
    return candis_df


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

    if jd_file_.name.endswith('.docx'):
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

        # print(job_desc)

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

            cos__df = pd.DataFrame()
            cos__df["Name"] = pd.Series(name)
            cos__df['Similarity'] = pd.Series(cos)
            cos__df['Status'] = pd.Series(status)
            cos__df['Remarks'] = pd.Series(remarks)
            cos__df['Email id'] = pd.Series(email)
            cos__df['Phone No'] = pd.Series(phone)
            cos__df["Name"].fillna("Not Available", inplace=True)

            cosine_df = pd.concat([cosColumn_df, cos__df], axis=0, ignore_index=True)
            cosine_df.index = cosine_df.index + 1
            ac_df = cosine_df.loc[cosine_df['Status'] == "Selected"]
            re_df = cosine_df.loc[cosine_df['Status'] == "Not Selected"]

            # Connect with the portnumber and host
            client = MongoClient("mongodb://localhost:27017/")

            # Access database
            db = client["CandidatesResume"]

            # Access collection of the database
            mycollection = db["CosineDF"]
            cos_dict = cosine_df.to_dict()
            # mycollection.insert_many([cosine_df.to_dict()])

            cosine_df.reset_index(inplace=True)  # Reset Index
            data_dict = cosine_df.to_dict("records")  # Convert to dictionary
            mycollection.insert_one({"index": "resume_data", "data": data_dict})  # inesrt into DB

            results(cosine_df, ac_df, re_df)
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

            cos__df = pd.DataFrame()
            cos__df["Name"] = pd.Series(name)
            cos__df['Similarity'] = pd.Series(cos)
            cos__df['Status'] = pd.Series(status)
            cos__df['Remark'] = pd.Series(remarks)
            cos__df['Email_id'] = pd.Series(email)
            cos__df['Phone No'] = pd.Series(phone)
            cos__df["Name"].fillna("Not Available", inplace=True)

            cosine_df = pd.concat([cosColumn_df, cos__df], axis=0, ignore_index=True)
            cosine_df.index = cosine_df.index + 1

            ac_df = cosine_df.loc[cosine_df['Status'] == "Selected"]
            re_df = cosine_df.loc[cosine_df['Status'] == "Not Selected"]

            # Connect with the portnumber and host
            client = MongoClient("mongodb://localhost:27017/")

            # Access database
            db = client["CandidatesResume"]

            # Access collection of the database
            mycollection = db["CosineDF"]
            cos_dict = cosine_df.to_json()

            cosine_df.reset_index(inplace=True)  # Reset Index
            data_dict = cosine_df.to_dict("records")  # Convert to dictionary
            mycollection.insert_one({"index": "SPY", "data": data_dict})  # inesrt into DB


            # mycollection.insert_many([cosine_df.to_dict()])

            results(cosine_df, ac_df, re_df)
    else:
        print("File Not Supported")


def customZip_ner(candis_df, name, email, phone):
    if jd_file_.name.endswith('.docx'):
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

        cos_df = pd.DataFrame(columns=['Name', 'Similarity', 'Status', 'Remark', 'Email id', 'Phone No'])
        print(cos_df)
        cos_df['Name'] = pd.Series(name)
        cos_df['Similarity'] = pd.Series(cos)
        cos_df['Status'] = pd.Series(status)
        cos_df['Remark'] = pd.Series(remarks)
        cos_df['Email id'] = pd.Series(email)
        cos_df['Phone No'] = pd.Series(phone)
        # cos_df["Name"].fillna("Not Available", inplace=True)

        cos_df = cos_df[['Name', 'Similarity', 'Status', 'Remark', 'Email id', 'Phone No']]
        cos_df.index = cos_df.index + 1
        cos_df.drop_duplicates(keep="first", inplace=True)
        print(cos_df)
        ac_df = cos_df.loc[cos_df['Status'] == "Selected"]
        re_df = cos_df.loc[cos_df['Status'] == "Not Selected"]

        # Connect with the portnumber and host
        client = MongoClient("mongodb://localhost:27017/")

        # Access database
        db = client["CandidatesResume"]

        # Access collection of the database
        mycollection = db["CosineDF"]
        cos_dict = cos_df.to_json()
        # mycollection.insert_many([cos_df.to_dict()])

        cos_df.reset_index(inplace=True)  # Reset Index
        data_dict = cos_df.to_dict("records")  # Convert to dictionary
        mycollection.insert_one({"index": "resume_data", "data": data_dict})  # inesrt into DB

        results(cos_df, ac_df, re_df)
    else:
        print("File Not Supported")


def results(cos_df, ac_df, re_df):
    table_df = cos_df.to_csv(index=False).encode('utf-8')
    options = st.sidebar.radio("", options=['Stand by mode', 'Show result', 'Accepted resumes', 'Rejected resumes'])
    hide_dataframe_row_index = '''
                        <style>
                        .row_heading.level0 {display:none}
                        .blank {display:none}
                        </style>
                        '''
    # Inject CSS with Markdown
    st.markdown(hide_dataframe_row_index, unsafe_allow_html=True)
    if options == 'Show result':
        st.subheader('Resume Results')
        st.dataframe(cos_df)
        # Display an interactive table
        st.download_button(
            label="Download data as CSV",
            data=table_df,
            file_name='Candidates_Resume.csv',
            mime='text/csv',
        )
    elif options == 'Accepted resumes':
        st.subheader("Accepted Resumes, Matching with JD's requirements")
        st.dataframe(ac_df)
    elif options == 'Rejected resumes':
        st.subheader("Rejected Resumes, Not-Matching with JD's requirements")
        st.dataframe(re_df)


def run():
    if jd_file_ and input_resumes:
        print(input_resumes)
        get_data(input_resumes)


if __name__ == "__main__":
    run()
