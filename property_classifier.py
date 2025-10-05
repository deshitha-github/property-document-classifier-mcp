"""
Property Document Classifier MCP Server
Classifies property-related PDF documents using OCR and text extraction.
"""

import json
import os
import base64
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from mcp.server import Server
from mcp.types import Resource, Tool, TextContent, ImageContent, EmbeddedResource
import mcp.server.stdio

# PDF processing libraries
try:
    import PyPDF2
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False
    print("Warning: PyPDF2 not installed. Install with: pip install PyPDF2")

try:
    import pytesseract
    from PIL import Image
    import pdf2image
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False
    print("Warning: OCR libraries not installed. Install with: pip install pytesseract pillow pdf2image")
    print("Also install tesseract: brew install tesseract (macOS) or apt-get install tesseract-ocr (Ubuntu)")

# Initialize MCP server
app = Server("property-document-classifier")

# Configuration
BASE_DIR = Path(__file__).parent  # Get the directory where the script is
DOCUMENTS_DIR = BASE_DIR / "documents"
METADATA_FILE = BASE_DIR / "classifications.json"
OUTPUT_DIR = BASE_DIR / "classified_documents"

# Real property document categories
PROPERTY_CATEGORIES = [
    'Invoices',
    'Receipts',
    'Title Summary',
    'Chain Sheet',
    'Property Card(s)',
    'Tax Data',
    'Mobile Home Data',
    'Mortgage(s)',
    'Deeds',
    'Covenants',
    'Easements & Right of Ways',
    'Leases & Lease Assignments',
    'Plats',
    'Liens',
    'Judgments',
    'Estates',
    'Power of Attorney',
    'UCC Filings',
    'Miscellaneous',
    'Index / Check Sheets'
]


def load_metadata() -> dict:
    """Load existing classifications from JSON file"""
    if METADATA_FILE.exists():
        with open(METADATA_FILE, 'r') as f:
            return json.load(f)
    return {}


def save_metadata(metadata: dict) -> None:
    """Save classifications to JSON file"""
    with open(METADATA_FILE, 'w') as f:
        json.dump(metadata, f, indent=2)


def extract_text_from_pdf(filepath: Path) -> tuple[str, str]:
    """
    Extract text from PDF using multiple methods.
    Returns: (extracted_text, extraction_method)
    """
    text = ""
    method = "none"
    
    # Method 1: Try direct text extraction with PyPDF2
    if PDF_AVAILABLE:
        try:
            with open(filepath, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                for page_num, page in enumerate(reader.pages):
                    page_text = page.extract_text()
                    if page_text and page_text.strip():
                        text += f"\n--- Page {page_num + 1} ---\n{page_text}"
                
                if text.strip():
                    method = "direct_extraction"
                    return text, method
        except Exception as e:
            print(f"Direct extraction failed: {e}")
    
    # Method 2: If direct extraction failed or returned empty, try OCR
    if OCR_AVAILABLE and not text.strip():
        try:
            # Convert PDF to images
            images = pdf2image.convert_from_path(str(filepath))
            
            for page_num, image in enumerate(images):
                page_text = pytesseract.image_to_string(image)
                if page_text and page_text.strip():
                    text += f"\n--- Page {page_num + 1} (OCR) ---\n{page_text}"
            
            if text.strip():
                method = "ocr"
                return text, method
        except Exception as e:
            print(f"OCR extraction failed: {e}")
    
    # If both methods failed
    if not text.strip():
        return "[Unable to extract text from PDF. Ensure PyPDF2 and/or Tesseract OCR are installed.]", "failed"
    
    return text, method


def get_pdf_info(filepath: Path) -> dict:
    """Get basic PDF information"""
    info = {
        "filename": filepath.name,
        "size_mb": round(filepath.stat().st_size / (1024 * 1024), 2),
        "pages": "unknown",
        "readable": False
    }
    
    if PDF_AVAILABLE:
        try:
            with open(filepath, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                info["pages"] = len(reader.pages)
                info["readable"] = True
        except:
            pass
    
    return info


def move_to_category_folder(filepath: Path, category: str) -> Optional[Path]:
    """Move/copy document to categorized folder"""
    try:
        category_dir = OUTPUT_DIR / category.replace('/', '-')
        category_dir.mkdir(parents=True, exist_ok=True)
        
        destination = category_dir / filepath.name
        
        # If file with same name exists, add number
        counter = 1
        while destination.exists():
            stem = filepath.stem
            suffix = filepath.suffix
            destination = category_dir / f"{stem}_{counter}{suffix}"
            counter += 1
        
        # Copy file (not move, to preserve original)
        import shutil
        shutil.copy2(filepath, destination)
        
        return destination
    except Exception as e:
        print(f"Error moving file: {e}")
        return None


@app.list_resources()
async def list_resources() -> list[Resource]:
    """
    List all PDF documents in the documents directory as resources.
    This allows Claude to see what documents are available.
    """
    resources = []
    
    if not DOCUMENTS_DIR.exists():
        DOCUMENTS_DIR.mkdir(parents=True, exist_ok=True)
        return resources
    
    metadata = load_metadata()
    
    for file_path in DOCUMENTS_DIR.iterdir():
        if file_path.is_file() and file_path.suffix.lower() == '.pdf':
            # Get classification status
            classification = metadata.get(str(file_path), {})
            category = classification.get('category', 'Unclassified')
            
            resources.append(
                Resource(
                    uri=f"file:///{file_path}",
                    name=file_path.name,
                    mimeType="application/pdf",
                    description=f"Property document: {file_path.name} | Category: {category}"
                )
            )
    
    return resources


@app.read_resource()
async def read_resource(uri: str) -> str:
    """
    Read the content of a specific PDF document.
    Called when Claude wants to examine a document.
    Extracts text using PyPDF2 or OCR as fallback.
    """
    # Extract file path from URI
    file_path = Path(uri.replace("file:///", ""))
    
    if not file_path.exists():
        raise ValueError(f"Document not found: {file_path}")
    
    # Get PDF info
    pdf_info = get_pdf_info(file_path)
    
    # Build response
    response = f"=== DOCUMENT: {pdf_info['filename']} ===\n"
    response += f"Size: {pdf_info['size_mb']} MB\n"
    response += f"Pages: {pdf_info['pages']}\n\n"
    
    # Extract text
    if file_path.suffix.lower() == '.pdf':
        text, method = extract_text_from_pdf(file_path)
        response += f"Extraction Method: {method}\n\n"
        response += "=== DOCUMENT CONTENT ===\n"
        response += text
    else:
        response += "[Not a PDF file]\n"
    
    # Add classification info if available
    metadata = load_metadata()
    if str(file_path) in metadata:
        info = metadata[str(file_path)]
        response += f"\n\n=== CLASSIFICATION INFO ===\n"
        response += f"Category: {info['category']}\n"
        response += f"Confidence: {info['confidence']}\n"
        response += f"Method: {info.get('extraction_method', 'unknown')}\n"
        response += f"Classified on: {info['timestamp']}\n"
        if info.get('notes'):
            response += f"Notes: {info['notes']}\n"
        if info.get('organized_path'):
            response += f"Organized to: {info['organized_path']}\n"
    
    return response


@app.list_tools()
async def list_tools() -> list[Tool]:
    """
    Define the tools available to Claude.
    Tools are actions that Claude can invoke.
    """
    return [
        Tool(
            name="classify_document",
            description=f"Classify a property document into one of these categories: {', '.join(PROPERTY_CATEGORIES)}. Use 'Miscellaneous' if document doesn't fit any category.",
            inputSchema={
                "type": "object",
                "properties": {
                    "document_path": {
                        "type": "string",
                        "description": "Path to the document file"
                    },
                    "category": {
                        "type": "string",
                        "enum": PROPERTY_CATEGORIES,
                        "description": "Document category"
                    },
                    "confidence": {
                        "type": "string",
                        "enum": ["high", "medium", "low"],
                        "description": "Confidence level of classification"
                    },
                    "notes": {
                        "type": "string",
                        "description": "Additional notes about the classification or document content"
                    },
                    "organize": {
                        "type": "boolean",
                        "description": "Whether to copy the document to the categorized folder structure",
                        "default": True
                    }
                },
                "required": ["document_path", "category", "confidence"]
            }
        ),
        Tool(
            name="batch_classify",
            description="Analyze and classify all unclassified documents in the folder",
            inputSchema={
                "type": "object",
                "properties": {
                    "organize": {
                        "type": "boolean",
                        "description": "Whether to organize documents into folders after classification",
                        "default": True
                    }
                }
            }
        ),
        Tool(
            name="get_classifications",
            description="Get all document classifications with their details",
            inputSchema={
                "type": "object",
                "properties": {
                    "category_filter": {
                        "type": "string",
                        "description": "Optional: filter by specific category"
                    }
                }
            }
        ),
        Tool(
            name="search_by_category",
            description="Search documents by category",
            inputSchema={
                "type": "object",
                "properties": {
                    "category": {
                        "type": "string",
                        "enum": PROPERTY_CATEGORIES,
                        "description": "Category to search for"
                    }
                },
                "required": ["category"]
            }
        ),
        Tool(
            name="get_statistics",
            description="Get statistics about classified documents including category distribution",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        Tool(
            name="reclassify_document",
            description="Change the classification of a previously classified document",
            inputSchema={
                "type": "object",
                "properties": {
                    "document_path": {
                        "type": "string",
                        "description": "Path to the document file"
                    },
                    "new_category": {
                        "type": "string",
                        "enum": PROPERTY_CATEGORIES,
                        "description": "New category for the document"
                    },
                    "reason": {
                        "type": "string",
                        "description": "Reason for reclassification"
                    }
                },
                "required": ["document_path", "new_category"]
            }
        )
    ]


@app.call_tool()
async def call_tool(name: str, arguments: Any) -> list[TextContent]:
    """
    Handle tool calls from Claude.
    This is where the actual work happens.
    """
    
    if name == "classify_document":
        document_path = arguments["document_path"]
        category = arguments["category"]
        confidence = arguments["confidence"]
        notes = arguments.get("notes", "")
        organize = arguments.get("organize", True)
        
        file_path = Path(document_path)
        
        # Get extraction method
        _, extraction_method = extract_text_from_pdf(file_path) if file_path.exists() else ("", "unknown")
        
        # Load existing metadata
        metadata = load_metadata()
        
        # Organize file if requested
        organized_path = None
        if organize and category != "Miscellaneous":
            organized_path = move_to_category_folder(file_path, category)
        
        # Add new classification
        metadata[document_path] = {
            "category": category,
            "confidence": confidence,
            "notes": notes,
            "extraction_method": extraction_method,
            "timestamp": datetime.now().isoformat(),
            "organized_path": str(organized_path) if organized_path else None
        }
        
        # Save metadata
        save_metadata(metadata)
        
        result = f"✓ Document classified successfully!\n\n"
        result += f"📄 File: {Path(document_path).name}\n"
        result += f"📁 Category: {category}\n"
        result += f"⭐ Confidence: {confidence}\n"
        result += f"🔍 Extraction: {extraction_method}\n"
        if notes:
            result += f"📝 Notes: {notes}\n"
        if organized_path:
            result += f"✅ Organized to: {organized_path}\n"
        
        return [TextContent(type="text", text=result)]
    
    elif name == "batch_classify":
        organize = arguments.get("organize", True)
        metadata = load_metadata()
        
        # Get unclassified documents
        unclassified = []
        for file_path in DOCUMENTS_DIR.iterdir():
            if file_path.is_file() and file_path.suffix.lower() == '.pdf':
                if str(file_path) not in metadata:
                    unclassified.append(file_path)
        
        if not unclassified:
            return [TextContent(type="text", text="✓ All documents are already classified!")]
        
        result = f"Found {len(unclassified)} unclassified documents:\n\n"
        for doc in unclassified:
            result += f"• {doc.name}\n"
        
        result += f"\n💡 I'll need to read each document to classify them. "
        result += f"Would you like me to proceed with reading and classifying these {len(unclassified)} documents?"
        
        return [TextContent(type="text", text=result)]
    
    elif name == "get_classifications":
        metadata = load_metadata()
        category_filter = arguments.get("category_filter")
        
        if not metadata:
            return [TextContent(type="text", text="No documents have been classified yet.")]
        
        # Filter if requested
        if category_filter:
            metadata = {k: v for k, v in metadata.items() if v['category'] == category_filter}
            if not metadata:
                return [TextContent(type="text", text=f"No documents found in category: {category_filter}")]
        
        result = "=== CLASSIFIED DOCUMENTS ===\n\n"
        
        # Group by category
        by_category = {}
        for path, info in metadata.items():
            cat = info['category']
            if cat not in by_category:
                by_category[cat] = []
            by_category[cat].append((path, info))
        
        for category in sorted(by_category.keys()):
            result += f"\n📁 {category} ({len(by_category[category])} documents)\n"
            result += "─" * 50 + "\n"
            for path, info in by_category[category]:
                filename = Path(path).name
                result += f"  📄 {filename}\n"
                result += f"     Confidence: {info['confidence']}\n"
                result += f"     Date: {info['timestamp'][:10]}\n"
                if info.get('notes'):
                    result += f"     Notes: {info['notes']}\n"
                result += "\n"
        
        return [TextContent(type="text", text=result)]
    
    elif name == "search_by_category":
        category = arguments["category"]
        metadata = load_metadata()
        
        matches = [
            (path, info) for path, info in metadata.items()
            if info['category'] == category
        ]
        
        if not matches:
            return [TextContent(type="text", text=f"No documents found in category: {category}")]
        
        result = f"=== DOCUMENTS IN CATEGORY: {category} ===\n\n"
        result += f"Found {len(matches)} document(s)\n\n"
        
        for path, info in matches:
            filename = Path(path).name
            result += f"📄 {filename}\n"
            result += f"   Confidence: {info['confidence']}\n"
            result += f"   Date: {info['timestamp'][:10]}\n"
            if info.get('notes'):
                result += f"   Notes: {info['notes']}\n"
            if info.get('organized_path'):
                result += f"   Location: {info['organized_path']}\n"
            result += "\n"
        
        return [TextContent(type="text", text=result)]
    
    elif name == "get_statistics":
        metadata = load_metadata()
        
        if not metadata:
            return [TextContent(type="text", text="No documents have been classified yet.")]
        
        # Calculate statistics
        category_counts = {}
        confidence_counts = {"high": 0, "medium": 0, "low": 0}
        extraction_methods = {}
        
        for info in metadata.values():
            category = info['category']
            confidence = info['confidence']
            method = info.get('extraction_method', 'unknown')
            
            category_counts[category] = category_counts.get(category, 0) + 1
            confidence_counts[confidence] += 1
            extraction_methods[method] = extraction_methods.get(method, 0) + 1
        
        result = "=== CLASSIFICATION STATISTICS ===\n\n"
        result += f"📊 Total Documents: {len(metadata)}\n\n"
        
        result += "📁 Documents by Category:\n"
        for category, count in sorted(category_counts.items(), key=lambda x: x[1], reverse=True):
            percentage = (count / len(metadata)) * 100
            result += f"  • {category}: {count} ({percentage:.1f}%)\n"
        
        result += f"\n⭐ Confidence Levels:\n"
        for level, count in confidence_counts.items():
            if count > 0:
                percentage = (count / len(metadata)) * 100
                result += f"  • {level.capitalize()}: {count} ({percentage:.1f}%)\n"
        
        result += f"\n🔍 Extraction Methods:\n"
        for method, count in extraction_methods.items():
            percentage = (count / len(metadata)) * 100
            result += f"  • {method}: {count} ({percentage:.1f}%)\n"
        
        # Count miscellaneous (documents that couldn't be classified properly)
        misc_count = category_counts.get('Miscellaneous', 0)
        if misc_count > 0:
            result += f"\n⚠️  {misc_count} document(s) in Miscellaneous (couldn't be classified)\n"
        
        return [TextContent(type="text", text=result)]
    
    elif name == "reclassify_document":
        document_path = arguments["document_path"]
        new_category = arguments["new_category"]
        reason = arguments.get("reason", "No reason provided")
        
        metadata = load_metadata()
        
        if document_path not in metadata:
            return [TextContent(type="text", text=f"❌ Document not found in classifications: {document_path}")]
        
        old_category = metadata[document_path]['category']
        metadata[document_path]['category'] = new_category
        metadata[document_path]['reclassified'] = True
        metadata[document_path]['reclassification_reason'] = reason
        metadata[document_path]['reclassification_date'] = datetime.now().isoformat()
        metadata[document_path]['previous_category'] = old_category
        
        save_metadata(metadata)
        
        result = f"✓ Document reclassified!\n\n"
        result += f"📄 File: {Path(document_path).name}\n"
        result += f"📁 Old Category: {old_category}\n"
        result += f"📁 New Category: {new_category}\n"
        result += f"💭 Reason: {reason}\n"
        
        return [TextContent(type="text", text=result)]
    
    else:
        raise ValueError(f"Unknown tool: {name}")


async def main():
    """Run the MCP server"""
    # Ensure directories exist
    DOCUMENTS_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # Print status
    print("🚀 Property Document Classifier MCP Server")
    print(f"📁 Documents directory: {DOCUMENTS_DIR.absolute()}")
    print(f"📁 Output directory: {OUTPUT_DIR.absolute()}")
    print(f"✓ PDF extraction: {'Available' if PDF_AVAILABLE else 'NOT AVAILABLE'}")
    print(f"✓ OCR support: {'Available' if OCR_AVAILABLE else 'NOT AVAILABLE'}")
    print("=" * 60)
    
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options()
        )


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())