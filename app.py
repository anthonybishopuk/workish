from flask import Flask, render_template, url_for, abort, request, flash, redirect
import requests
import xml.etree.ElementTree as ET
from mappings import CURRENCY_MAP, PAY_PERIOD_MAP, COUNTIES
from bs4 import BeautifulSoup
import logging
import base64
import secrets
import os
from dotenv import load_dotenv

FEED_URL = "https://www1.jobdiva.co.uk/employers/connect/listofportaljobs.jsp?a=2xjdnw8ba0qg7ajn5eqynyw1d90g51c352085d1xhqj8t6cv8cwsvrtbn9n6qjy2&fulldesc=1&&payrateinfo=1"

app = Flask(__name__)

app.secret_key = secrets.token_hex(16)

load_dotenv()

JOBDIVA_AUTH = "https://api.jobdiva.co.uk/apiv2/authenticate"
JOBDIVA_APPLICATION_URL = "https://api.jobdiva.co.uk/apiv2/jobdiva/CreateJobApplicationWithResume"

CLIENT_ID = os.getenv("CLIENT_ID")
API_USERNAME = os.getenv("API_USERNAME")
API_PASSWORD = os.getenv("API_PASSWORD")

jobs_cache = {}

def get_token():
    params = {
        "clientid": CLIENT_ID,
        "username": API_USERNAME,
        "password": API_PASSWORD
    }

    r = requests.get(JOBDIVA_AUTH, params=params)

    if r.status_code != 200:
        print("Request sent:", r)
        print("Status Code:", r.status_code)
        print("Response text:", r.text)
        return None

    # The API returns token as plain text
    return r.text.strip()
    

@app.route("/")
def home():
    return render_template(
        "index.html",
        show_hero=True,
        hero_image=url_for('static', filename='img/workplace_image.jpg'),
        hero_heading="We are Work<em>ish</em>",
        hero_subtext="Connecting talent to opportunity",
        hero_height="hero-full"
    )

@app.route("/about")
def about():
    return render_template(
        "about.html",
        show_hero=True,
        hero_image=url_for('static', filename='img/high_five.avif'),
        hero_heading="Recruitment",
        hero_subtext="but <em>nicer</em>",
        hero_height="hero-default"
    )

@app.route("/contact")
def contact():
    return render_template(
        "contact.html",
        show_hero=True,
        hero_image=url_for('static', filename='img/telephone_wall.jpg'),
        hero_heading="Contact <em>Us</em>",
        hero_height="hero-default"
        )

def load_jobs():
    response = requests.get(FEED_URL)
    response.raise_for_status()

    root = ET.fromstring(response.content)
    jobs_list = []

    for job in root.findall("jobs/job"):
        job_id = job.findtext("jobdiva_no", "")
        jobdivaid = job.findtext("jobdivaid", "")
        title = job.findtext("title", "Untitled")
        division = job.findtext("internal_division", "")
        positiontype = job.findtext("positiontype", "")
        pay_min = job.findtext("payratemin")
        pay_max = job.findtext("payratemax")
        currency_symbol = CURRENCY_MAP.get(job.findtext("paycurrency"), "")
        pay_period = PAY_PERIOD_MAP.get(job.findtext("payrateper"), "")
        if pay_min and pay_max:
            if pay_min == pay_max:
                salary_str = f"{currency_symbol}{pay_min} {pay_period}"
            else:
                salary_str = f"{currency_symbol}{pay_min} - {currency_symbol}{pay_max} {pay_period}"
        else:
            salary_str = "Salary not specified"

        city = job.findtext("city", "")
        state_name = COUNTIES.get(job.findtext("state_abbr"), "")
        location = ", ".join(filter(None, [city, state_name]))

        desc_html = job.findtext("jobdescription", "")
        desc_text = BeautifulSoup(desc_html, "html.parser").get_text()
        preview = (desc_text[:120] + "...") if len(desc_text) > 120 else desc_text

        job_data = {
            "job_id": job_id,
            "jobdivaid": jobdivaid,
            "title": title,
            "division": division,
            "positiontype": positiontype,
            "description_preview": preview,
            "description_full": desc_html,
            "location": location,
            "salary": salary_str
        }

        jobs_list.append(job_data)

    jobs_cache.clear()
    for j in jobs_list:
        jobs_cache[j["job_id"]] = j

    return jobs_list


@app.route("/jobs")
def jobs():

    jobs_list = load_jobs()

    # Get filter values from query parameters
    selected_position_types = request.args.getlist("positiontype")  # list of selected job types
    selected_divisions = request.args.getlist("division")            # list of selected divisions
    location_search = request.args.get("location", "").strip().lower()

    # Filter jobs dynamically
    filtered_jobs = []
    for job in jobs_list:
        # Filter by position type
        if selected_position_types and job.get("positiontype") not in selected_position_types:
            continue
        # Filter by internal division
        if selected_divisions and job.get("division") not in selected_divisions:
            continue
        # Filter by location (city, county, or postcode)
        if location_search:
            job_location = job.get("location", "").lower()
            if location_search not in job_location:
                continue
        filtered_jobs.append(job)

    # Extract unique position types and divisions for checkbox rendering
    all_position_types = sorted({job.get("positiontype") for job in jobs_list if job.get("positiontype")})
    all_divisions = sorted({job.get("division") for job in jobs_list if job.get("division")})

    print(len(filtered_jobs))

    return render_template(
        "jobs.html",
        jobs=filtered_jobs,
        show_hero=True,
        hero_image=url_for('static', filename='img/binoculars_search.jpg'),
        hero_heading="Search",
        hero_subtext="Find <em>your</em> future",
        hero_height="hero-default",
        all_position_types=all_position_types,
        all_divisions=all_divisions,
        selected_position_types=selected_position_types,
        selected_divisions=selected_divisions,
        location_search=location_search
    )

@app.route("/job/<job_id>", methods=["GET", "POST"])
def job_detail(job_id):
    job = jobs_cache.get(job_id.strip())
    other_jobs = jobs_cache.get(job_id)

    if request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email")
        cv = request.files.get("cv")

    if not job:
        abort(404, description= "Job not found")

    return render_template(
        "job_detail.html", 
        job=job,
        other_jobs=other_jobs, 
        show_hero=True,
        hero_image=url_for('static', filename='img/bench.jpg'),
        hero_heading=job["title"],
        hero_height="hero-short"
    )

@app.route("/apply/<job_id>", methods=["POST"])
def apply(job_id):
    jobdivaid = request.form.get("jobdivaid")
    job_id = request.form.get("job_id")
    firstname = request.form.get("first_name")
    lastname = request.form.get("last_name")
    email = request.form.get("email")
    cv_file = request.files["cv_file"]

    if not jobdivaid or not firstname or not lastname or not email or not cv_file:
        flash("All fields are required.", "danger")
        return redirect(url_for("job_detail", job_id=job_id))

    # Encode file to base64
    cv_base64 = base64.b64encode(cv_file.read()).decode("utf-8")

    token = get_token()
    if not token:
        flash("Could not get JobDiva token.", "danger")
        print("No token")
        return redirect(url_for("job_detail", job_id=job_id))

    payload = {
        "filecontent": cv_base64,
        "filename": cv_file.filename,
        "jobid": int(jobdivaid),
        "resumesource": 10225,
        "firstname": firstname,
        "lastname": lastname,
        "email": email
    }

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    # Make API request
    response = requests.post(JOBDIVA_APPLICATION_URL, json=payload, headers=headers)

    if response.headers.get("Content-Type", "").startswith("application/json"):
        resp_json = response.json()
        app.logger.info(f"Application response JSON: {resp_json}")
    else:
        app.logger.info(f"Response is not JSON! Status code: {response.status_code}, Text: {response.text}")

    flash("Application submitted! Check logs for API response.", "info")
    app.logger.info(f"Redirecting to application_success for job_id: {job_id}")
    return redirect(url_for("application_success", job_id=job_id, firstname=firstname, lastname=lastname))


@app.route("/application-success/<job_id>")
def application_success(job_id):
    job = jobs_cache.get(job_id)

    firstname = request.args.get("firstname")
    lastname = request.args.get("lastname")

    return render_template(
        "application_success.html",
        show_hero=True,
        hero_image=url_for('static', filename='img/delivery.jpg'),
        hero_heading="You <em>did</em> it!",
        hero_height="hero-short",
        job=job,
        firstname=firstname,
        lastname=lastname
        )

if __name__ == "__main__":
    app.run(debug=True)
