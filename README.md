# Power BI Analytics Hub

![Power BI Analysis Tool](https://img.shields.io/badge/Power%20BI-Analytics%20Hub-217346?style=for-the-badge&logo=powerbi)
![Flask](https://img.shields.io/badge/Flask-Web%20App-0078D4?style=for-the-badge&logo=flask)
![Version](https://img.shields.io/badge/Version-2.0.0-brightgreen?style=for-the-badge)
![License: Custom Non-Commercial](https://img.shields.io/badge/License-NonCommercial-red.svg?style=for-the-badge)

## 📋 Overview

The **Power BI Analytics Hub** is a web-based tool that analyzes exported Power BI report files to help you understand report structure, measure dependencies, and identify optimization opportunities. It provides a modern interface to explore your Power BI reports offline using extracted JSON and TSV files.

## ✨ Key Features

### 🎯 **Core Analysis Tools**

- **📊 Interactive Dashboard** - Overview with key metrics about your Power BI report
- **🔍 Visual Fields Explorer** - Detailed table of all fields used across visuals with advanced filtering
- **🔗 Data Lineage Diagram** - Interactive network visualization showing measure dependencies and relationships
- **💻 DAX Code Analyzer** - Browse DAX expressions with syntax highlighting and similarity analysis
- **🗃️ Source Query Explorer** - Examine M queries from data sources with code highlighting
- **⚡ Performance Optimizer** - Identify unused measures to optimize report performance
- **🏗️ Model Insights** - Comprehensive model analysis including tables, relationships, roles, RLS, and data quality
- **📑 Report Insights** - Report-level analysis covering themes, bookmarks, layouts, and formatting patterns

### 🎨 **Modern User Experience**

- **Clean, Professional Interface** - Modern web design with smooth animations
- **Responsive Design** - Works on desktop, tablet, and mobile devices
- **Interactive Visualizations** - Clickable network diagrams and sortable tables
- **Export Capabilities** - Download analysis results as CSV files
- **Search & Filter** - Find specific measures, visuals, or fields quickly

## 📋 Requirements

### Data Files Needed

To use this tool, you need to extract the following files from your Power BI environment:

1. **`report.json`** - Power BI report structure (exported from Power BI Service or Desktop)
2. **`MeasureDependencies.tsv`** - Measure dependency data (can be generated using Tabular Editor or similar tools)
3. **`model.json`** - Power BI model metadata (exported from Power BI Desktop or Service)

### System Requirements

- Python 3.7+
- Modern web browser
- 100MB+ free disk space for data files

## 🚀 Quick Start

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/plagiagia/PowerBI_AnalysisTool.git
   cd PowerBI_AnalysisTool
   ```

2. **Set up Python environment:**
   ```bash
   # Create virtual environment
   python -m venv venv

   # Activate (Windows)
   venv\Scripts\activate

   # Activate (macOS/Linux)
   source venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Prepare your data files:**
   - Create a `data/` directory in the project root
   - Place your Power BI files:
     - `data/report.json` - Your Power BI report structure
     - `data/MeasureDependencies.tsv` - Measure dependencies
     - `data/model.json` - Model metadata

5. **Launch the application:**
   ```bash
   python app.py
   ```

6. **Open your browser** and navigate to `http://localhost:5000`

## 🔍 Feature Guide

### 📊 Dashboard

Your analytics command center featuring:
- **Report Metrics** - Total visuals, measures, pages, and unused measures
- **Model Health** - Tables, columns, relationships, roles, and hidden objects overview
- **Experience & Navigation** - Bookmarks, navigation visuals, and filtering insights
- **Visual Mix & Styling** - Visual type distribution and custom formatting analysis
- **Quick Navigation** - Direct access to all analysis tools

### 🔍 Visual Fields Explorer (`/table-view`)

Comprehensive field analysis with:
- **Complete Field Inventory** - Every field used across all visuals
- **Advanced Filtering** - Filter by page, visual type, or field name
- **Search Functionality** - Find specific fields instantly
- **Export Options** - Download filtered results as CSV

### 🔗 Data Lineage Diagram (`/lineage-view`)

Understand measure relationships:
- **Interactive Network Graph** - Visual representation of measure dependencies
- **Hierarchical Layout** - Clear parent-child relationships
- **Focus Mode** - Highlight specific measure chains
- **Measure Details** - View DAX code and dependencies for selected measures

### 💻 DAX Code Analyzer (`/dax-expressions`)

Explore your DAX formulas:
- **Syntax Highlighting** - Professional DAX code presentation
- **Similarity Analysis** - Find potentially duplicate or similar measures
- **Search & Filter** - Quickly locate specific measures
- **Copy & Export** - Easy code sharing and documentation

### 🗃️ Source Query Explorer (`/source-explorer`)

M query analysis:
- **M Language Highlighting** - Clear syntax highlighting for M queries
- **Query Structure** - Understand data transformation logic
- **Search Functionality** - Find specific tables or transformations
- **Export Options** - Download queries for documentation

### ⚡ Performance Optimizer (`/unused-measures`)

Identify optimization opportunities:
- **Unused Measure Detection** - Find measures not referenced in any visuals
- **Cascade Detection** - Identifies measures that become unused after removing their dependencies
- **Comprehensive Analysis** - Multi-level impact analysis with deletion chains
- **Cleanup Recommendations** - Suggestions for performance improvement
- **Tabular Editor Scripts** - Generate scripts to help with cleanup
- **Impact Analysis** - Understand what would be affected by removing measures

### 🏗️ Model Insights (`/model-insights`)

Deep dive into your data model:
- **Table Overview** - Complete inventory of tables with column counts and hidden status
- **Relationship Analysis** - View all relationships with cardinality and filtering behavior
- **Row-Level Security** - Analyze RLS roles and table permissions
- **Data Quality Gaps** - Identify measures without descriptions or format strings
- **Column Analysis** - Find columns missing data categories
- **Hidden Objects** - Track hidden tables, columns, and measures
- **Annotations** - Review model-level annotations and metadata

### 📑 Report Insights (`/report-insights`)

Analyze report-level design and interactivity:
- **Theme Analysis** - Review active theme and color scheme
- **Bookmark Explorer** - Examine bookmarks with filters and target visuals
- **Layout Analysis** - Visual positioning, sizing, and z-order by page
- **Query Patterns** - Review OrderBy, GroupBy, and Where clauses in visual queries
- **Formatting Audit** - Identify custom tooltips, titles, backgrounds, borders, and shadows
- **Navigation Tracking** - Catalog buttons, page navigators, and interactive elements
- **Top Limits** - Discover visuals using Top N filtering

## 🔧 Configuration

### Basic Configuration

The application uses these default file paths (configurable in `config.py`):
- `data/report.json` - Power BI report structure
- `data/MeasureDependencies.tsv` - Measure dependency data  
- `data/model.json` - Power BI model metadata

### Optional Environment Variables

Create a `.env` file for custom settings:
```env
# Flask Configuration
SECRET_KEY=your_secure_secret_key
FLASK_ENV=development

# Feature Toggles
ENABLE_SOURCE_EXPLORER=true
ENABLE_DAX_EXPLORER=true
ENABLE_LINEAGE_VIEW=true
ENABLE_MODEL_INSIGHTS=true
ENABLE_REPORT_INSIGHTS=true
```

## 📁 Project Structure

```
PowerBI_AnalysisTool/
├── 📄 app.py                     # Main Flask application
├── ⚙️ config.py                  # Configuration settings
├── 📊 data_processor.py          # Report data processing logic
├── 🔗 lineage_view.py            # Measure dependency analysis
├── 🏗️ model_processor.py         # Model metadata processing
├── 📁 static/                    # Frontend assets
│   ├── 🎨 modern.css             # UI styling
│   └── ⚡ modern.js              # Interactive features
├── 📁 templates/                 # HTML templates
│   ├── 🏠 base.html              # Base layout template
│   ├── 📊 index.html             # Dashboard
│   ├── 🔍 table_view.html        # Visual fields explorer
│   ├── 🔗 lineage_view.html      # Data lineage diagram
│   ├── 💻 dax_expressions.html   # DAX analyzer
│   ├── 🗃️ source_explorer.html   # M query explorer
│   ├── ⚡ unused_measures.html   # Performance optimizer
│   ├── 🏗️ model_insights.html    # Model insights page
│   ├── 📑 report_insights.html   # Report insights page
│   └── ❌ error.html              # Error handling page
├── 📁 data/                      # Data files directory (user-provided)
├── 📋 requirements.txt           # Python dependencies
├── 📜 LICENSE                    # License information
└── 📖 README.md                  # Documentation
```

## 📥 Getting Your Data Files

### Extracting report.json
1. Open Power BI Desktop
2. Go to File → Export → Export report as JSON (or use Power BI REST API)
3. Save as `report.json` in the `data/` folder

### Creating MeasureDependencies.tsv
You can generate this using tools like:
- **Tabular Editor** - Export measure dependencies
- **DAX Studio** - Query model metadata
- **Power BI External Tools** - Various community tools

Expected TSV format:
```
Measure	DAXExpression	ParentMeasures	ChildMeasures	Table	Columns
Sales	SUM(Sales[Amount])			Sales	Sales[Amount]
Profit	[Sales] - [Costs]	Sales;Costs		Sales	
```

### Extracting model.json
1. Use Power BI REST API to get model metadata
2. Or export from Tabular Editor
3. Save as `model.json` in the `data/` folder

## 🛡️ Security & Privacy

- **Local Processing** - All analysis runs on your local machine
- **No Cloud Dependencies** - Works completely offline
- **Data Privacy** - Your Power BI data never leaves your computer
- **No External APIs** - All processing is done locally

## ❓ Common Issues

### Missing Data Files
**Error**: "Report data file not found"
**Solution**: Ensure you have placed the required JSON/TSV files in the `data/` directory

### Empty Visualizations
**Issue**: Lineage diagram or tables show no data
**Cause**: Data files may be malformed or empty
**Solution**: Verify your exported files contain the expected data structure

### Performance Issues
**Issue**: Slow loading with large reports
**Solution**: The tool is designed for offline analysis; large reports may take time to process

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/new-feature`)
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under a **Custom Non-Commercial License**. See [LICENSE](LICENSE) for details.

- ✅ **Allowed**: Personal use, education, research, open source contributions
- ❌ **Prohibited**: Commercial use, selling, redistribution for profit

## 🆘 Support

- 🐛 **Bug Reports**: [GitHub Issues](https://github.com/plagiagia/PowerBI_AnalysisTool/issues)
- 💡 **Feature Requests**: [GitHub Discussions](https://github.com/plagiagia/PowerBI_AnalysisTool/discussions)
- 📚 **Documentation**: Check code comments and templates

## 🌟 Acknowledgments

Built with:
- **Flask** - Python web framework
- **Vis.js** - Network visualization library
- **Prism.js** - Syntax highlighting
- **Modern Web Standards** - HTML5, CSS3, JavaScript ES6+

---

**Power BI Analytics Hub v2.0.0** - Offline Power BI report analysis with modern web interface.

© 2025 Power BI Analytics Hub - Non-commercial educational tool