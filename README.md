# Power BI Analysis Tool

A comprehensive web application that helps you navigate, explore, and optimize your Power BI reports with advanced visualization and analysis tools.

![Power BI Analysis Tool](https://img.shields.io/badge/Power%20BI-Analysis%20Tool-217346?style=for-the-badge&logo=powerbi)
![Flask](https://img.shields.io/badge/Flask-Web%20App-0078D4?style=for-the-badge&logo=flask)
![License: Custom Non-Commercial](https://img.shields.io/badge/License-NonCommercial-red.svg?style=for-the-badge)

## 📋 Overview

The Power BI Analysis Tool provides an intuitive interface to explore the structure and components of your Power BI reports, helping you to understand complex data models, optimize measure usage, and identify opportunities for improvement.

## ✨ Key Features

- **Dashboard** - Get an overview of your report structure with key metrics
- **Visual Fields Explorer** - See all fields used across your report's visuals
- **Data Lineage Diagram** - Visualize relationships between measures and columns
- **DAX Explorer** - Browse and analyze DAX formulas with syntax highlighting
- **Source Explorer** - Examine the M queries that form your data sources
- **Unused Measures Detector** - Identify measures not used in any visuals

## 🖼️ Screenshots

*[Screenshots would appear here]*

## 🚀 Installation

### Prerequisites

- Python 3.7+
- Flask
- Modern web browser

### Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/PowerBI_AnalysisTool.git
   cd PowerBI_AnalysisTool
   ```

2. Create and activate a virtual environment (optional but recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Set up your data files:
   - Place your Power BI report JSON in `data/report.json`
   - Place your measure dependencies TSV in `data/MeasureDependencies.tsv`
   - Place your model JSON in `data/model.json`

5. Run the application:
   ```bash
   python app.py
   ```

6. Open a web browser and navigate to `http://localhost:5000`

## 🔍 Usage

### Dashboard

The dashboard provides a high-level overview of your report, including:
- Total number of visuals
- Number of measures
- Number of pages
- Number of unused measures
- Quick access to all analysis tools

### Visual Fields Table

Explore all fields used across visuals in your report with:
- Advanced filtering by page and visual type
- Search functionality
- Export to CSV capability
- Table and card view options

### Data Lineage

Visualize relationships between measures and columns to understand dependencies:
- Interactive network diagram
- Filter by measure or column
- Hierarchical or force-directed layout options
- Export lineage data

### DAX Explorer

Browse and analyze DAX formulas with:
- Syntax highlighting
- Search functionality
- Copy functionality
- Export capability

### Source Explorer

Examine the M queries that form your report's data sources:
- Syntax highlighting for M language
- Copy functionality

### Unused Measures

Identify measures not used in any visuals for optimization:
- List of all unused measures
- Generated Tabular Editor script to help manage them

## 🔧 Technical Details

The application is built with:
- **Flask** - Python web framework
- **Vis.js** - Network visualization
- **Prism.js** - Syntax highlighting
- **Modern HTML/CSS/JavaScript** - Responsive frontend

## 📁 Project Structure

```
PowerBI_AnalysisTool/
├── app.py                     # Main Flask application
├── config.py                  # Configuration settings
├── data_processor.py          # Processes Power BI report data
├── lineage_view.py            # Handles measure dependencies
├── static/                    # Static assets
│   ├── dax_explorer.js        # DAX explorer functionality
│   ├── lineage_view.js        # Network visualization
│   ├── modern.css             # Main styling
│   └── modern.js              # Core JavaScript functionality
├── templates/                 # HTML templates
│   ├── base.html              # Base template
│   ├── index.html             # Dashboard
│   ├── table_view.html        # Visual fields explorer
│   ├── lineage_view.html      # Data lineage visualization
│   ├── dax_expressions.html   # DAX explorer
│   ├── source_explorer.html   # Source code explorer
│   └── unused_measures.html   # Unused measures detector
├── data/                      # Data files (not included)
│   ├── report.json            # Power BI report JSON
│   ├── MeasureDependencies.tsv # Measure dependencies
│   └── model.json             # Model JSON
├── LICENSE                    # MIT license
└── README.md                  # This file
```

## 📄 License

This project is licensed under a Custom Non-Commercial License - see the [LICENSE](LICENSE) file for details. This license allows for personal and educational use but prohibits any commercial use or selling of this software or derivatives.

## 🌟 Future Enhancements

- Add more advanced DAX analysis features
- Support for automatic uploading of Power BI files
- Interactive editing of measures
- Performance optimization recommendations
- Integration with Power BI REST API

## 👥 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📞 Contact

For any questions or feedback, please open an issue in the GitHub repository.

---

© 2025 Dimitrios - PowerBI Analysis Tool