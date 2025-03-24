# 🍩 collab.dev

## Open Source Collaboration Metrics for Code Reviews

Cloud edition: <https://collab.dev>

**collab-dev** is an open-source tool that generates collaboration metrics and insights from GitHub pull request data. Use it to analyze collaboration patterns, review workflow, process efficiency, and more.

## Features

- **Data Collection:** Fetches pull request data from any public or private GitHub repository (requires GitHub token).
- **Visualization:** Generate interactive charts using Plotly.
- **Command Line Interface:** Run analysis with a single command.
- **Portable & Minimal:** Designed to work with CSV data to keep things simple.
- **Extensible:** Add new charts by adding them to the chart modules list.

---

## Getting Started

### Prerequisites

- Python 3.12+
- Python Dependency Manager (`pdm`) - [Installation Instructions](https://pdm.fming.dev/latest/#installation)
- A GitHub Personal Access Token with repository read permissions

### Installation

1. Clone the repository:
  
  ```bash
  git clone https://github.com/pullflow/collab-dev.git
  cd collab-dev
  ```
  
2. Install dependencies:
  
  ```bash
  pdm install
  ```
  
3. Set up your GitHub API token as an environment variable:
  
  ```bash
  export GITHUB_TOKEN=your_token_here
  ```
  
---

## Usage

### Fetch Pull Request Data

To download data from a GitHub repository, run:

```bash
pdm collect owner/repo_name
```

This will generate CSV files with pull request data in the `data/` directory.

You can specify the number of PRs to fetch using the `-n` flag:

```bash
pdm collect -n 100 owner/repo_name
```

For example, to collect 100 PRs from the React repository using your GitHub token:

```bash
GITHUB_TOKEN=your_token pdm run collect -n 100 facebook/react
```

Alternatively, you can save your GitHub token in a `.env` file.

### View Metrics & Insights

To analyze the data and view the results:

1. Start the Flask application:

```bash
pdm serve
```

2. Open your browser and navigate to:

<http://127.0.0.1:8700>

3. You'll see a list of repositories you've collected data for using the collect script.

4. Click on any repository to view its detailed metrics and visualizations at `/report/owner/repo`.

---

## Data Structure

collab-dev organizes collected data in a hierarchical file structure:

```
./data/
├── {owner}/
│   ├── {repo_name}/
│   │   ├── repository.csv       # Repository metadata
│   │   ├── pull_requests.csv    # All PR data for this repo
│   │   ├── all_events.csv       # Consolidated events from all PRs
│   │   ├── pr_{number}/
│   │   │   └── events.csv       # Events for specific PR
│   │   ├── pr_{number}/
│   │   │   └── events.csv
│   │   └── ...
```

### Data Files

- **repository.csv**: Contains metadata about the GitHub repository
- **pull_requests.csv**: Stores information about all pull requests collected from the repository
- **all_events.csv**: Consolidates timeline events from all PRs for easier analysis
- **events.csv**: In each PR subdirectory, stores the timeline events for that specific PR

This structure allows for efficient data collection, storage, and analysis while maintaining a clear organization based on GitHub's repository hierarchy.

---

## Customization

Charts are defined in the `CHART_MODULES` list in `src/collab_dev/components/charts/chart_renderer.py`. To add a custom chart:

1. Create a new module in `src/collab_dev/components/charts/`
2. Implement a `render(repo_df)` function in your module
3. Add your module to the `CHART_MODULES` list in `chart_renderer.py`

Existing chart types include:

- Workflow (Sankey diagram)
- Contributor distribution patterns
- Bot contribution analysis
- Review coverage metrics
- Review funnel analysis
- Review turnaround time
- Request Approval time analysis
- Merge time distribution

---

## Development

### Code Style

We use `ruff` for code formatting and linting:

```bash
# Run linter
pdm lint

# Format code
pdm format

# Fix auto-fixable issues
pdm lint-fix
```

---

## Contributing

We're looking for help in the following areas:

- **Validate and improve data and calculations:** Help ensure our metrics are accurate and meaningful.
- **Improve current charts and other visualizations:** Enhance the clarity and usefulness of existing visualizations.
- **Add new charts that help measure collaboration:** Develop new metrics and visualizations that provide insights into team collaboration patterns.

To contribute:

1. Fork the repository
2. Create your branch:
  
  ```bash
  git checkout -b feature/my-new-feature
  ```
  
3. Commit your changes:
  
  ```bash
  git commit -m "Add some feature"
  ```
  
4. Push to the branch:
  
  ```bash
  git push origin feature/my-new-feature
  ```
  
5. Open a Pull Request

---

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

---

## Support

For issues and feature requests, please use the [GitHub Issues](https://github.com/pullflow/collab-dev/issues) page.
