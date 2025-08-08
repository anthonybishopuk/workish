from flask import Flask, render_template, url_for

app = Flask(__name__)

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

@app.route("/jobs")
def jobs():
    return render_template(
        "jobs.html",
        show_hero=True,
        hero_image=url_for('static', filename='img/binoculars_search.jpg'),
        hero_heading="Search",
        hero_subtext="Find <em>your</em> future",
        hero_height="hero-default"
    )

if __name__ == "__main__":
    app.run(debug=True)
