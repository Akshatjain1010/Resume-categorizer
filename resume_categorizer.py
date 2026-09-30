import os
import time
from pathlib import Path #remove
from dotenv import load_dotenv
from groq import Groq
#import libraries further pydantic, json, pypdf, python-docx
load_dotenv()
api=os.getenv("GROQ_API_KEY")

if not api:
    raise ValueError("GROQ_API_KEY ni mili")

client = Groq(api_key=api)
model="openai/gpt-oss-20b"
# role="user"
# prompt="Do you know carryminati. in one word." #ye role and prompt abhi use ni kar rahe




########################## Seted the API and Client --Now-- Job description wala agent ############################



#ye job description likhli 
job_description = """Do you want to solve real customer problems through innovative technology? Do you enjoy working on scalable
services in a collaborative team environment? Do you want to see your code directly impact millions of customers
worldwide?

At Amazon, we hire the best minds in technology to innovate and build on behalf of our customers. Customer
obsession is part of our company DNA, which has made us one of the world's most beloved brands.

Our Software Development Engineers (SDEs) use modern technology to solve complex problems while seeing
their work's impact first-hand. The challenges SDEs solve at Amazon are meaningful and influence millions of
customers, sellers, and products globally. We seek individuals passionate about creating new products, features,
and services while managing ambiguity in an environment where development cycles are measured in weeks, not
years.

At Amazon, we believe in ownership at every level. As an SDE-I, you'll own the entire lifecycle of your code - from
design through deployment and ongoing operations. This ownership mindset, combined with our commitment to
operational excellence, ensures we deliver the highest quality solutions for our customers.

We're looking for curious minds who think big and want to define tomorrow's technology. At Amazon, you'll grow
into the high-impact engineer you know you can be, supported by a culture of learning and mentorship. Every
day brings exciting new challenges and opportunities for personal growth."""

from pydantic import BaseModel
class JobDescription(BaseModel): #pydantic se basemodel inherit karke jobdescription ko json schema me karne ke liye ek class banai
    role: str | None
    required_skills: list[str] | None #list me none likhne se change ni aata/kuch ni hota empty list hi aati h 
    preferred_skills: list[str] | None
    minimum_experience: float | None
    education_requirements: list[str] | None
    responsibilities: list[str] | None

job_schema = JobDescription.model_json_schema() #jobdescription class ka schema generate kiya then usko system prompt me use karenge, then json output ko again class me convert karenge

#system prompt me job_schema ko use kiya schema batane ke liye, json_schema variable dene ke baad bhi usko explicitly "json" word dena padega ni api side error aata h
system_prompt= f"""You are an expert HR assistant.

Your job is to analyze job descriptions and extract
structured information from them.
                                          
Return ONLY valid JSON matching this schema:

{job_schema}
IMPORTANT:
Do NOT return the schema itself.
Do NOT return fields like I"properties", "title" or "type".
Fill the schema with actual information extracted from the job description.

If minimum experience is not mentioned, return null.
If information for a list is missing, return an empty list.
Do not invent information.
"""
user_prompt= f"""Here is a job description:
{job_description}""" #user prompt me job description analyze karne ko bola

system_message= {
    "role": "system",
    "content": system_prompt,
}
user_message= {
    "role": "user",
    "content": user_prompt,
} 
# message= {    #ye role and prompt abhi use ni kar rahe
#     "role": role,
#     "content": prompt,
# }
response_format = {
    "type": "json_object", #system prompt me schema batane ke baad ye banaya "response=client.chat.completions.create()"" me response_format api level pe dene ke liye or its like implicit instrucion ki json me output dena h
}
messages=[system_message, user_message]

response= client.chat.completions.create(model= model, messages= messages, response_format= response_format)

raw_json_answer= response.choices[0].message.content #json me answer aaya then usko save kiya 
# print(raw_json_answer)       #abhi pura message print ni kiya comment kar diya 

import json 
parsed_json_dictionary = json.loads(raw_json_answer) #raw_json_answer ko dictionary me convert kiya so that hum usko class me convert kar sake, direct ni kar sakte 
job_description_obj = JobDescription(**parsed_json_dictionary) #**parsed_json_dictionary dictionary ko keyword arguments me expand karta hai. class me convert karke uski details print kar di
# job_description_obj = JobDescription.model_validate_json(raw_json_answer) 
#bhi kiya ja sakta h raw_json_answer ko direct json job_decription class me convert karne ke liye

print(job_description_obj.role)
print(job_description_obj.required_skills)
print(job_description_obj.preferred_skills)
print(job_description_obj.minimum_experience)
print(job_description_obj.education_requirements)
print(job_description_obj.responsibilities)



####################### Now job description has parsed and got the ouput from first agent #########################



class match_results(BaseModel): #final_score fxn me use karne ke liye json schema define
    score: float | None
    details: dict[str, object] | None
class Experience(BaseModel):
    company: str | None = None
    role: str | None = None
    duration: str | None = None #duration ko string me rakha h kyuki kuch log 2 years 3 months ya 1.5 years ya 6 months likhte h, so float me convert karne me problem aayegi
    description: str | None = None #description bhi list ki jagah str me rakha h 
    skills_used: list[str] = []
class resume(BaseModel):
    name: str | None = None
    email: str | None = None
    phone: str | None = None
    total_experience_years: float | None = None
    skills: list[str] = []
    experience: list[Experience] = []
    education: list[str] = []
    certifications: list[str] = []
    projects: list[str] = []

resume_schema= resume.model_json_schema() 

def final_score(job, resume):
    match_schema= match_results.model_json_schema() #match result ka schema upar class me pydantic ka basemodel inherit karke banaya tha yha usko initialize kar diya  

    prompt= f"""
    You are an HR recruiter.

    Compare the candidate's resume with the job description.

    {job.model_dump_json(indent=2)}

    CANDIDATE RESUME:
    {resume.model_dump_json(indent=2)}
    Return JSON matching this schema:

    {match_schema}

    Give me:

    1. Candidate name
    2. Matching skills
    3. Missing important skills
    4. Whether experience requirement is met
    5. Overall match percentage from 0 to 100

    JOB DESCRIPTION:

    keep the response concise and easy to read. 
    """
    user_message= {
        "role": "user",
        "content": prompt
    }
    message= [user_message]
    response_format={
        "type": "json_object"
   }
    response= client.chat.completions.create(model= model, messages= message, response_format= response_format)
    data= json.loads(response.choices[0].message.content) #json ko dictoinary me load kiya
    return match_results(**data) #match_result class joki pydantic ke basemodel ko inherit karti h usko de diya
    # match_results = response.model_validate_json(raw_json_answer) 
    #bhi kiya ja sakta h "data" ko direct json match_results class me convert karne ke liye



################ Final score/verdict ke liye fxn bana liya, now resume ko parse karne ka fxn ######################

from pypdf import PdfReader
from docx import Document

def extract_text_from_pdf(file_path): #agar pdf ho to 
    reader = PdfReader(file_path)
    text = ""
    for page in reader.pages:
        text += page.extract_text() + "\n"
    return text
    # for page in reader.pages:           #this can also be used
    #     page_text = page.extract_text()
    #     if page_text:
    #         text += page_text + "\n"
    # return text

def extract_text_from_docx(file_path): #agar word doc ho to 
    doc = Document(file_path)
    text = ""
    for paragraph in doc.paragraphs:
        if paragraph.text.strip():  # Check if the paragraph is not empty
            text += paragraph.text + "\n"
    
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells: #here we are iterating through each cell in the row of the table
                if cell.text.strip():  # Check if the cell is not empty
                    text += cell.text + "\n"
    return text

def read_resume(file_path):
    if file_path.suffix.lower() == '.pdf': #file_path.suffix.lower() se bhi same kaam kar sakte
        return extract_text_from_pdf(file_path)
    elif file_path.suffix.lower() == '.docx':
        return extract_text_from_docx(file_path)
    else:
        raise ValueError("Unsupported file format. Please provide a PDF or DOCX file.")


##################################### Resume read karne wali sare fxn ban gaye ####################################


def parse_resume(resumetext):
    system_prompt= f"""You are an expert resume parser.

    Extract information from the resume based on its meaning,
    not only based on exact section headings.

    Different resumes may use different headings.

    For example:
    - Experience
    - Professional Experience
    - Work History
    Employment
    Internships

    These may all contain relevant experience.

    Skills may also appear in the skills section, work experience,
    internships or projects.

    Return exactly one complete JSON object matching this schema:
    {resume_schema}
    Important rules:

    1. Do not invent information.
    2. If a value is not available, return null.
    3. If a list has no information, return an empty list.
    4. Include internships inside experiences.
    5. Extract skills mentioned across the entire resume.
    6. Do not use Markdown or code fences.
    """

    user_prompt= f"""Parse the following resume: 
    {resume_text}"""

    system_message= {
        "role": "system",
        "content": system_prompt,
    }
    user_message= {
        "role": "user",
        "content": user_prompt,
    }
    response_format={
        "type": "json_object"
    }

    messages=[system_message, user_message]
    response=client.chat.completions.create(
        model= model,
        messages= messages,
        response_format= response_format,
        temperature=0,
        max_completion_tokens=1500,
    )
    raw_output= response.choices[0].message.content
    data=json.loads(raw_output)
    parsed_resume= resume(**data) #json resume after converting raw_output to dictionary then giving it to resume class (schema)
    return parsed_resume


########################### Parse json resume banane ke liye fxn bana liya ########################################


resume_folder = Path(__file__).parent / "resumes" #script ke folder me resumes read karne ke liye
all_results = []

for resume_file in resume_folder.iterdir(): #resume_folder me files ko iterate karega and resume_file me file ka path aa jayega
    if resume_file.is_file() and resume_file.suffix.lower() in ['.pdf', '.docx']: #agar bo file h and resume_file.suffix.lower() .pdf ya .docx me h to fir print command run hogi
        print(f"Processing resume: {resume_file.name}") #ye resume_file.name us path me se sirf resume file ka name dega
        resume_text = read_resume(resume_file)
        # print(resume_text[:500])  # Print the first 500 characters of the resume text
        parsed_resume=parse_resume(resume_text) #resume parse karne ke liye llm call 1 then adding sleep time
        time.sleep(5)
        result= final_score(job_description_obj, parsed_resume) #final_score ke liye llm call2 then adding sleep time
        time.sleep(5) #final_score match_results ke class ko return karta h isliye print(result.score) se match_results ka score print ho jayega
        print(result.score) #result me final_score wale json schema me se score ko print karwa diya
        all_results.append({"name": parsed_resume.name, #direct bhi result print ke sath name print karwa sakte the lekin results ko varable me append karenge
                            "score": result.score,
                            "details": result.details})

    else: 
        print(f"Skipping unsupported file: {resume_file.name}")
    
all_results.sort(
            key=lambda candidate: candidate["score"] if candidate["score"] is not None else float("-inf"),
            reverse= True
        )
top_2 = all_results[:2]
worst_2 = all_results[-2:]
print("Top 2 candidates")
for candidate in top_2:
    print(candidate["name"], "-", candidate["score"],"%")
    print(candidate["details"])
print("Lowest 2 candidates")
for candidate in worst_2:
    print(candidate["name"], "-", candidate["score"], "%")
    print(candidate["details"])


