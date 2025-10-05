# Property Document Classifier - MCP Server

![MCP](https://img.shields.io/badge/MCP-Enabled-blue)
![Python](https://img.shields.io/badge/Python-3.10+-green)
![License](https://img.shields.io/badge/License-MIT-yellow)

An MCP (Model Context Protocol) server that automatically classifies property documents using Claude Desktop with OCR support.

## Read the Full Tutorial

 **[Building an AI Document Classifier with MCP - Medium Article](YOUR-MEDIUM-LINK)**

## What It Does

This MCP server connects Claude Desktop to your local property documents and enables:

- **Automatic classification** into 20+ property document categories
- **PDF text extraction** with PyPDF2
- **OCR support** for scanned documents using Tesseract
- **File organization** into categorized folders
- **Metadata tracking** with confidence scores
- **Search and statistics** tools

## Document Categories

The server classifies documents into 20 property-related categories:

- Invoices, Receipts, Title Summary
- Chain Sheet, Property Card(s), Tax Data
- Mobile Home Data, Mortgage(s), Deeds
- Covenants, Easements & Right of Ways
- Leases & Lease Assignments, Plats
- Liens, Judgments, Estates
- Power of Attorney, UCC Filings
- Miscellaneous, Index / Check Sheets

## Architecture

![Architecture](docs/screenshots/01-architecture-diagram.png)

User → Claude Desktop (Host)
↓
MCP Client (Protocol Handler)
↓
MCP Server (This Project)
↓
Local Documents (Your PDFs)

## 🚀 Quick Start

### Prerequisites

- Python 3.10 or higher
- Claude Desktop ([Download here](https://claude.ai/download))
- Tesseract OCR

### Installation

1. **Clone the repository**
```
git clone https://github.com/YOUR-USERNAME/property-document-classifier-mcp.git
cd property-document-classifier-mcp
```

Create virtual environment

```
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

Install dependencies

```
pip install -r requirements.txt
```

Install Tesseract OCR

macOS:
```
brew install tesseract
```
Ubuntu/Debian:
```
sudo apt-get update
```
```
sudo apt-get install tesseract-ocr poppler-utils
```
Windows:

Download from: https://github.com/UB-Mannheim/tesseract/wiki
Add to PATH

Create directories

```
mkdir documents classified_documents
```

Configure Claude Desktop

Get your absolute path:
bashpwd  # Copy this output
Edit Claude Desktop config:
macOS/Linux:
bashcode ~/Library/Application\ Support/Claude/claude_desktop_config.json
Windows:
bashnotepad %APPDATA%\Claude\claude_desktop_config.json
Add this configuration (replace paths with your actual paths):
json{
  "mcpServers": {
    "property-classifier": {
      "command": "/FULL/PATH/TO/venv/bin/python",
      "args": [
        "/FULL/PATH/TO/property_classifier.py"
      ]
    }
  }
}

Restart Claude Desktop

Completely quit (Cmd+Q / Alt+F4) and restart.

Test it!

In Claude Desktop:
Are you connected to any MCP servers?
You should see the property-classifier!
Usage Examples
Classify a Single Document
Can you classify Sample-Deed.pdf from the documents folder?
Batch Classification
Classify all unclassified documents
View Statistics
Show me classification statistics
Search by Category
Show me all Mortgage documents
Get All Classifications
List all classified documents grouped by category

### How It Works
Two-Stage PDF Processing

Direct Text Extraction (PyPDF2)

Fast processing for text-based PDFs
Works for digitally created documents


OCR Fallback (Tesseract)

Automatically triggered if no text found
Handles scanned documents and images
Converts PDF pages to images first

Automatic Organization
Classified documents are copied to:
classified_documents/
├── Deeds/
├── Mortgages/
├── Tax Data/
└── ...
Original files remain in documents/ folder.
Metadata Tracking
Each classification stores:

Document category
Confidence level (high/medium/low)
Extraction method used
Timestamp
Custom notes
Organized file path

Stored in classifications.json.
Performance
Typical processing times:

Text-based PDFs: ~1 second per document
Scanned PDFs (OCR): ~3-5 seconds per document
100 documents: ~3-4 minutes total

Security & Privacy

Local-first: All processing happens on your machine
No cloud uploads: Documents never leave your computer
User control: Claude asks permission before using tools
Transparent: All operations visible in Claude Desktop
Open source: Audit the code yourself

Troubleshooting
See TROUBLESHOOTING.md for common issues.
Quick Fixes
Server not connecting:

Verify paths in config are absolute
Check Python is in PATH
Restart Claude Desktop completely

OCR not working:
bash# Check Tesseract installation
tesseract --version

# macOS
brew install tesseract

# Ubuntu
sudo apt-get install tesseract-ocr
"Read-only file system" error:

Make sure documents/ folder exists
Check file permissions

Documentation

Installation Guide
Architecture Overview
Troubleshooting Guide
Medium Article - Full tutorial

Learning Resources
About MCP:

Official MCP Documentation
MCP Specification
[Anthropic's Announcement](https://www.anthropic.com/news/
