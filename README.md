# Power BI Analytics Hub

![Power BI Analysis Tool](https://img.shields.io/badge/Power%20BI-Analytics%20Hub-217346?style=for-the-badge&logo=powerbi)
![Flask](https://img.shields.io/badge/Flask-Web%20App-0078D4?style=for-the-badge&logo=flask)
![Version](https://img.shields.io/badge/Version-2.0.0-brightgreen?style=for-the-badge)
![License: Custom Non-Commercial](https://img.shields.io/badge/License-NonCommercial-red.svg?style=for-the-badge)

## 📋 Overview

The **Power BI Analytics Hub** provides a modern, intuitive interface to explore the structure and components of your Power BI reports. With a completely redesigned user experience, it helps you understand complex data models, optimize measure usage, and identify opportunities for improvement.

## ✨ Key Features

### 🎯 **Core Analysis Tools**

- **📊 Modern Dashboard** - Comprehensive overview with animated metrics and clean UI
- **🔍 Visual Fields Explorer** - Advanced filtering and search capabilities for all report fields
- **🔗 Data Lineage Diagram** - Interactive network visualization of measure dependencies
- **💻 DAX Code Analyzer** - DAX analysis with syntax highlighting and similarity detection
- **🗃️ Source Query Explorer** - M query examination with code highlighting
- **⚡ Performance Optimizer** - Unused measure detection and optimization recommendations

### 🎨 **Modern User Experience (v2.0.0)**

- **Clean, Professional Interface** - Modern design following current UX trends
- **Responsive Design** - Works seamlessly on desktop, tablet, and mobile
- **Animated Interactions** - Smooth animations and hover effects
- **Color-Coded Organization** - Intuitive visual hierarchy and categorization
- **Accessibility Focused** - WCAG compliant design principles

## 🚀 Quick Start

### Prerequisites

- Python 3.7+
- Modern web browser
- Power BI report files (JSON format)

### Installation

1. **Clone the repository:**

   ```bash
   git clone https://github.com/plagiagia/PowerBI_AnalysisTool.git
   cd PowerBI_AnalysisTool
   ```

2. **Set up environment:**

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

4. **Configure your environment:**

   ```bash
   # Run the setup script
   python setup_env.py

   # Edit the generated .env file with your settings
   ```

5. **Prepare your data files:**

   - Place your Power BI report JSON in `data/report.json`
   - Place your measure dependencies TSV in `data/MeasureDependencies.tsv`
   - Place your model JSON in `data/model.json`

6. **Launch the application:**

   ```bash
   python app.py
   ```

7. **Open your browser** and navigate to `http://localhost:5000`

## 🔍 Feature Guide

### 📊 Dashboard

Your analytics command center featuring:

- **Real-time Metrics** - Visual count, measures, pages, and unused elements
- **Animated Counters** - Engaging data presentation
- **Quick Access Cards** - Direct links to all analysis tools
- **Modern Interface** - Clean, professional design

### 🔍 Visual Fields Explorer

Comprehensive field analysis with:

- **Smart Search** - Find fields across all visuals instantly
- **Advanced Filters** - Filter by page, visual type, and field category
- **Export Capabilities** - Download analysis results
- **Sortable Tables** - Organize data your way

### 🔗 Data Lineage Diagram

Understand your data relationships:

- **Interactive Network** - Visualize measure dependencies
- **Focus Mode** - Highlight specific relationships
- **Hierarchical Layout** - Clear dependency chains
- **Export Options** - Share lineage documentation

### 💻 DAX Code Analyzer

Master your DAX formulas:

- **Syntax Highlighting** - Professional code presentation
- **Similarity Detection** - Find redundant measures
- **Copy & Export** - Easy code sharing
- **Search & Filter** - Quickly find specific measures

### 🗃️ Source Query Explorer

M query insights:

- **Code Highlighting** - Clear M language syntax
- **Query Documentation** - Export for team sharing
- **Search Functionality** - Find specific queries quickly
- **Copy & Export** - Share query code easily

### ⚡ Performance Optimizer

Boost your report performance:

- **Unused Detection** - Find measures not in use
- **Impact Analysis** - Understand removal consequences
- **Cleanup Recommendations** - Identify optimization opportunities
- **Export Results** - Document unused measures

## 🔧 Configuration

### Environment Variables

Create a `.env` file with:

```env
# AI Features (optional)
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4o
AI_TEMPERATURE=0.7

# Flask Configuration
SECRET_KEY=your_secure_secret_key
FLASK_ENV=development

# Feature Toggles
ENABLE_AI_FEATURES=true
ENABLE_SOURCE_EXPLORER=true
ENABLE_DAX_EXPLORER=true
ENABLE_LINEAGE_VIEW=true
```

### File Paths

Default data file locations (configurable in `config.py`):

- `data/report.json` - Power BI report structure
- `data/MeasureDependencies.tsv` - Measure dependency data
- `data/model.json` - Power BI model metadata

## 📁 Project Structure

```
PowerBI_AnalysisTool/
├── 📄 app.py                     # Main Flask application
├── ⚙️ config.py                  # Configuration management
├── 🔧 setup_env.py               # Environment setup script
├── 📊 data_processor.py          # Report data processing
├── 🔗 lineage_view.py            # Dependency analysis
├── 🤖 ai_utils.py                # AI integration utilities
├── 📁 static/                    # Frontend assets
│   ├── 🎨 modern.css             # Modern UI styling
│   └── ⚡ modern.js              # Interactive features
├── 📁 templates/                 # HTML templates
│   ├── 🏠 base.html              # Base layout
│   ├── 📊 index.html             # Modern dashboard
│   ├── 🔍 table_view.html        # Visual fields explorer
│   ├── 🔗 lineage_view.html      # Data lineage
│   ├── 💻 dax_expressions.html   # DAX analyzer
│   ├── 🗃️ source_explorer.html   # M query explorer
│   └── ⚡ unused_measures.html   # Performance optimizer
├── 📁 data/                      # Data files directory
├── 📋 CHANGELOG.md               # Version history
├── 🐛 ISSUES.md                  # Issue tracking
├── 📜 LICENSE                    # License information
└── 📖 README.md                  # This documentation
```

## 🛡️ Security & Privacy

- **Local Processing** - All analysis runs on your machine
- **No Data Upload** - Your Power BI data stays private
- **Optional AI** - AI features can be disabled completely
- **Secure Headers** - Production-ready security configuration

## 🔄 Version History

### v2.0.0 (2024-12-19) - Major UI/UX Redesign

- ✨ Complete modern interface redesign
- 🎨 Enhanced metrics with animations
- 🔧 Improved mobile responsiveness
- 🛡️ Added security headers
- 📋 Comprehensive documentation
- 🐛 Fixed multiple UI issues

### v1.0.0 - Initial Release

- 🏗️ Core analysis features
- 🤖 Basic AI integration
- 📊 Essential reporting tools

## 🚀 Future Roadmap

### High Priority

- 🌙 **Dark Mode Support** - Toggle between light/dark themes
- 📤 **Export Functionality** - PDF/Excel report generation
- 🔄 **Real-time Refresh** - Live data updates

### Medium Priority

- 🔍 **Advanced Filtering** - Enhanced search capabilities
- 👤 **User Preferences** - Personalized settings
- 📈 **Performance Metrics** - Detailed analytics dashboard

See [ISSUES.md](ISSUES.md) for the complete roadmap.

## 🤝 Contributing

We welcome contributions! Please see our [CHANGELOG.md](CHANGELOG.md) for development guidelines.

1. Fork the repository
2. Create a feature branch
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
- 📚 **Documentation**: Check [CHANGELOG.md](CHANGELOG.md) and [ISSUES.md](ISSUES.md)

## 🌟 Acknowledgments

Built with ❤️ using:

- **Flask** - Python web framework
- **Vis.js** - Network visualization
- **Prism.js** - Syntax highlighting
- **OpenAI** - AI-powered features
- **Modern Web Standards** - HTML5, CSS3, ES6+

---

**Power BI Analytics Hub v2.0.0** - Transforming Power BI analysis with modern design and AI intelligence.

© 2024 Power BI Analytics Hub - Built for the Power BI Community
