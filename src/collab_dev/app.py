"""
collab.dev - Flask application for collaboration metrics
"""

from components.charts.chart_renderer import render_charts
from fetcher.store import get_all_repositories
from flask import Flask, render_template
from loader.load import load

app = Flask(__name__, template_folder=".", static_folder="./static")


@app.route("/")
def index():
    """Return welcome message and API info"""
    # Get list of all repositories
    repositories = get_all_repositories()

    return render_template("templates/index.html", repositories=repositories)


@app.route("/report/<path:repo_path>")
def repository_report(repo_path):
    """Show report for a specific repository"""
    # Split the repo path into owner and name
    parts = repo_path.split("/")
    if len(parts) != 2:
        return "Invalid repository path", 400

    owner, name = parts
    df = load(owner, name)
    charts = render_charts(df)
    return render_template(
        "templates/repository.html",
        df=df,
        repo=repo_path,
        charts=charts,
    )


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
