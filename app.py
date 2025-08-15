from flask import Flask, render_template, url_for, abort, request
import requests
import xml.etree.ElementTree as ET
from mappings import CURRENCY_MAP, PAY_PERIOD_MAP, COUNTIES
from bs4 import BeautifulSoup
import logging

FEED_URL = "https://www1.jobdiva.co.uk/employers/connect/listofportaljobs.jsp?a=2xjdnw8ba0qg7ajn5eqynyw1d90g51c352085d1xhqj8t6cv8cwsvrtbn9n6qjy2&fulldesc=1&&payrateinfo=1"

app = Flask(__name__)

jobs_cache = {}


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
        title = job.findtext("title", "Untitled")
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
            "title": title,
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

    return render_template(
        "jobs.html",
        jobs=jobs_list,
        show_hero=True,
        hero_image=url_for('static', filename='img/binoculars_search.jpg'),
        hero_heading="Search",
        hero_subtext="Find <em>your</em> future",
        hero_height="hero-default"
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

@app.route("/apply", methods=["POST"])
def apply():
    job_id = request.form["job_id"]
    name = request.form["name"]
    email = request.form["email"]
    cv_file = request.files["cv"]

    return "Application submitted!"

if __name__ == "__main__":
    app.run(debug=True)
