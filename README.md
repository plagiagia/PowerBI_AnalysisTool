# Power BI Analysis Tool

![Power BI Analysis Tool](https://img.shields.io/badge/Power%20BI-Analysis%20Tool-217346?style=for-the-badge&logo=powerbi)
![Flask](https://img.shields.io/badge/Flask-Web%20App-0078D4?style=for-the-badge&logo=flask)
![License: Custom Non-Commercial](https://img.shields.io/badge/License-NonCommercial-red.svg?style=for-the-badge)

## 📋 Overview

The Power BI Analysis Tool provides an intuitive interface to explore the structure and components of your Power BI reports, helping you to understand complex data models, optimize measure usage, and identify opportunities for improvement.

## ✨ Key Features

- **Dashboard** - Get an overview of your report structure with key metrics including visual count, measure count, page count, and unused measures
- **Visual Fields Explorer** - See all fields used across your report's visuals with advanced filtering and search capabilities
- **Data Lineage Diagram** - Visualize relationships between measures and columns with interactive network diagrams
- **DAX Explorer** - Browse and analyze DAX formulas with syntax highlighting and similarity analysis
- **Source Explorer** - Examine the M queries that form your data sources with syntax highlighting
- **Unused Measures Detector** - Identify measures not used in any visuals with dependency chain analysis

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
   git clone https://github.com/plagiagia/PowerBI_AnalysisTool.git
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
- Most common visual type used in the report
- Quick access to all analysis tools

### Visual Fields Explorer

Explore all fields used across visuals in your report with:
- Advanced filtering by page and visual type
- Field-level search functionality
- Export to CSV capability
- Table view with sortable columns
- Color-coded visual types and field categories

### Data Lineage

Visualize relationships between measures and columns to understand dependencies:
- Interactive network diagram with hierarchical or force-directed layouts
- Filters for parent measures, final measures, and columns
- Focus on specific measures and their relationships
- Statistical breakdown of measure types and relationships
- Export lineage data to CSV

### DAX Explorer

Browse and analyze DAX formulas with:
- Syntax highlighting for DAX code
- Search functionality with highlighted matches
- Copy functionality for both measure names and full expressions
- Export capability for DAX expressions
- Measure similarity analysis to identify redundant measures

### Source Explorer

Examine the M queries that form your report's data sources:
- Syntax highlighting for M language (Power Query)
- Expandable/collapsible query view
- Search functionality across queries
- Copy capabilities for table names and query code
- Export functionality for M queries

### Unused Measures

Identify measures not used in any visuals for optimization:
- List of all unused measures
- Visualization of dependency chains
- Analysis of impact when removing measures
- Generated Tabular Editor script for managing unused measures
- Multi-level deletion approach to handle dependencies

## 🔧 Technical Details

The application is built with:
- **Flask** - Python web framework that handles the backend processing
- **Vis.js** - Network visualization library for creating interactive diagrams
- **Prism.js** - Syntax highlighting for DAX and M language code
- **Modern HTML/CSS/JavaScript** - Responsive frontend with dark mode support

## 📁 Project Structure

```
PowerBI_AnalysisTool/
├── app.py                     # Main Flask application
├── config.py                  # Configuration settings
├── data_processor.py          # Processes Power BI report data
├── lineage_view.py            # Handles measure dependencies
├── static/                    # Static assets
│   ├── modern.css             # Main styling
│   └── modern.js              # Core JavaScript functionality
├── templates/                 # HTML templates
│   ├── base.html              # Base template with navigation
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
├── LICENSE                    # Custom Non-Commercial license
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
- Extended chart visualizations for report metrics
- Support for PBIX file direct import
- Bulk optimization recommendations

## 👥 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📞 Contact

For any questions or feedback, please open an issue in the GitHub repository.

---

© 2025 Dimitrios - PowerBI Analysis Tool