import psycopg2
from psycopg2.extras import RealDictCursor


class Candidate:
    id: str
    name: str
    email: str
    phone: str
    skills: list[str]


def get_candidate_data(candidate_id: str):
    "take from db the cv_filename of the candidate then call the api to get the semantic profile of the cv"
    query = "SELECT name, surname FROM candidate_applications_view WHERE candidate_id = %s"
    try:
        result = execute_query(query, (candidate_id,))
    except Exception as e:
       print(f"Error fetching candidate skills data: {e}")
       return {}
    return result

def get_job_requirements(job_id: str):
    "take from db the job description"
    query = "SELECT jobdescription FROM candidate_applications_view WHERE job_id = %s"
    try:
        result = execute_query(query, (job_id,))
    except Exception as e:
       print(f"Error fetching job requirements: {e}")
       return {}
    return result

def get_user_data_by_email(email: str) -> dict:
    "get user data from db by email"
    query = "SELECT name, surname, semantic_profile, jobdescription FROM candidate_applications_view WHERE email = %s"
    try:
        result = execute_query(query, (email,))
    except Exception as e:
        print(f"Error fetching user data: {e}")
        return {}
    return result



def execute_query(query: str, params: tuple = ()):
    try:
        conn = psycopg2.connect(
            dbname="hrrecruit",
            user="postgres",
            password="postgres",
            host="localhost",
            port="5432"
        )
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute(query, params)
        
        if query.strip().lower().startswith("select"):
            result = cur.fetchone()
        else:
            conn.commit()
            result = cur.rowcount
        
        cur.close()
        conn.close()
        return result
    except Exception as e:
        print(f"Errore: {e}")
        return None
    
    

# def updateDatabaseData():
#     """this function connects to a api and updates the database"""
#     base_url = "https://openkeiretsu.it/cvscan-api"
#     url = f"{base_url}/api/VectorCv/list-titles?password=pwd111"
#     """
#     update candidate table by fetching data from the api to populate the following fields:
#         - name 
#         - surname
#         - email
#         - phone
#     update jobs table by fetching data from the api to populate the following fields:
#         - title
#         - description
#     update candidate_applications table by fetching data from the api to populate the following fields:
#         - candidate_id
#         - job_id
#         - cv_filename
#     """


if __name__ == "__main__":
    # candidate_data = get_candidate_skills_data("C01")
    # job_data = get_job_requirements("J001")
    # print(candidate_data)
    # # Accessing attributes from the fetched data
    # # Assuming the query returns: [(id, name, email, phone, skills), ...]
    # if candidate_data:
    #     candidate_id, name, email, phone, skills = candidate_data[0]
    #     print(name)  # Prints the name of the candidate with ID 1
    print("\n", get_user_data_by_email("mario.rossi@example.com"))