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

## Demo

![Demo GIF](docs/screenshots/demo.gif)

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
