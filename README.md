# MIB Parser & Web Viewer

A comprehensive MIB (Management Information Base) file parser and web-based visualization tool. Built with pysmi for high-performance parsing and Flask for an intuitive web interface.

## Features

### Core Parser
- 🚀 High-performance MIB file parsing based on pysmi
- 📊 Export MIB data to structured JSON format
- 🌳 Complete tree structure traversal and manipulation tools
- 🔍 Flexible node lookup and pattern matching
- 📁 Support for single file or batch directory parsing

### Web Interface
- 🌐 Intuitive web-based MIB viewer and explorer
- 📱 Responsive design for desktop and mobile devices
- 🔍 Advanced search capabilities with real-time filtering
- 🌳 Interactive tree visualization with expand/collapse
- 📊 Comprehensive statistics and analytics
- 🖥️ **Fullscreen tree view mode for better visualization**
- 👥 Multi-device support with device-specific MIB management
- ⬆️ Drag-and-drop MIB file upload
- 🖨️ Print-friendly layouts

### Fullscreen Tree View Features
- 🖥️ Dedicated fullscreen mode for large tree structures
- 🔍 Integrated search functionality
- 📁 Expand/collapse all nodes
- 🎨 Color-coded depth visualization
- 🖨️ Print optimization for documentation
- ⚡ Fast loading and responsive navigation

## Installation

### As a Python Library

Install using uv:

```bash
uv add mib-parser
```

Or using pip:

```bash
pip install mib-parser
```

### As a Web Application

Clone the repository and install dependencies:

```bash
git clone <repository-url>
cd MIBFileParser
uv install
```

## Quick Start

### Using the Web Interface

Start the Flask web application:

```bash
# Run Flask module directly
uv run python -m flask_app.app

# With custom host/port
FLASK_HOST=0.0.0.0 FLASK_PORT=8080 uv run python -m flask_app.app
```

Then open your browser and navigate to `http://localhost:8080` (or your custom port)

#### Web Interface Features
- **Dashboard**: Overview of all loaded MIB files and devices
- **MIB Upload**: Drag and drop MIB files for parsing
- **Tree Viewer**: Interactive tree visualization with search and filtering
- **Fullscreen Mode**: Click the fullscreen button for dedicated tree view
- **Device Management**: Organize MIB files by device
- **Search**: Global search across all MIB files and OIDs
- **Statistics**: Detailed analytics about MIB structures

#### Using Fullscreen Tree View
1. Navigate to any MIB tree view
2. Click the green **Fullscreen** button
3. Use the new window features:
   - Search for specific nodes or OIDs
   - Expand/collapse all nodes
   - Print the tree structure
   - Close to return to normal view

### Basic Library Usage

```python
from mib_parser import MibParser, JsonSerializer, MibTree

# Parse MIB file
parser = MibParser()
mib_data = parser.parse_mib_file('path/to/your/mib_file.mib')

# Export to JSON
serializer = JsonSerializer()
serializer.serialize(mib_data, 'output.json')

# Use tree tools
tree = MibTree(mib_data)
node = tree.find_node_by_oid('1.3.6.1.2.1.1.1')
if node:
    print(f"Node name: {node.name}")
    print(f"Description: {node.description}")
```

### Advanced Usage

```python
from mib_parser import MibParser, JsonSerializer, MibTree

# Parse MIB file
parser = MibParser()
mib_data = parser.parse_mib_file('path/to/your/mib_file.mib')

# Export to JSON
serializer = JsonSerializer()
serializer.serialize(mib_data, 'output.json')

# Use tree tools
tree = MibTree(mib_data)
node = tree.find_node_by_oid('1.3.6.1.2.1.1.1')
if node:
    print(f"Node name: {node.name}")
    print(f"Description: {node.description}")
```

### Batch Directory Parsing

```python
from mib_parser import MibParser

parser = MibParser()
mib_data_list = parser.parse_mib_directory('/path/to/mibs', recursive=True)

for mib_data in mib_data_list:
    print(f"Parsed MIB: {mib_data.name} with {len(mib_data.nodes)} nodes")
```

## Project Structure

```
MIBFileParser/
├── pyproject.toml              # Project configuration and dependencies
├── README.md                  # Project documentation
├── src/
│   ├── mib_parser/            # Core parser library
│   │   ├── __init__.py        # Package initialization
│   │   ├── parser.py          # Core MIB parser
│   │   ├── serializer.py      # JSON serializer
│   │   ├── tree.py            # Tree traversal tools
│   │   └── models.py          # Data models
│   └── flask_app/             # Web application
│       ├── __init__.py
│       ├── app.py             # Flask application factory
│       ├── routes/            # Application routes
│       │   ├── __init__.py
│       │   ├── main.py        # Main page and dashboard
│       │   ├── api.py         # API endpoints
│       │   └── upload.py      # File upload handling
│       ├── services/          # Business logic
│       │   ├── __init__.py
│       │   ├── mib_service.py # MIB processing
│       │   ├── device_service.py # Device management
│       │   └── tree_service.py # Tree visualization
│       ├── static/            # Static assets
│       │   ├── css/
│       │   │   └── style.css  # Main stylesheet
│       │   ├── js/
│       │   │   ├── main.js    # Main JavaScript
│       │   │   └── tree.js    # Tree visualization
│       │   └── images/
│       └── templates/         # HTML templates
│           ├── base.html      # Base template
│           ├── index.html     # Dashboard
│           ├── tree_view.html # Tree visualization (with fullscreen support)
│           ├── search.html    # Search results
│           ├── devices.html   # Device management
│           ├── upload.html    # File upload
│           ├── statistics.html # Analytics
│           ├── about.html     # About page
│           └── error.html     # Error handling
├── tests/                     # Test suite
│   ├── __init__.py
│   ├── test_parser.py         # Parser tests
│   ├── test_serializer.py     # Serializer tests
│   ├── test_tree.py           # Tree tools tests
│   ├── test_models.py         # Model tests
│   └── fixtures/              # Test MIB files
├── storage/                   # Data storage
│   ├── devices/               # Device-specific MIB files
│   ├── parsed/                # Parsed MIB data (JSON)
│   ├── annotations/           # User annotations and metadata
│   └── device_registry.json   # Device configuration
```

## Architecture

### Web Application Architecture
- **MVC Pattern**: Clear separation between routes (controllers), services (models), and templates (views)
- **RESTful API**: Clean API endpoints for MIB operations
- **Responsive Design**: Mobile-first approach with Bootstrap
- **Interactive UI**: Dynamic tree visualization with JavaScript
- **Fullscreen Mode**: Dedicated viewing experience for large tree structures

### Key Components
- **MIB Service**: Handles MIB file parsing and caching
- **Tree Service**: Manages tree visualization and navigation
- **Device Service**: Organizes MIB files by network devices
- **Fullscreen Viewer**: Standalone window for focused tree exploration

## Web API

### REST Endpoints

The web application provides a RESTful API for programmatic access:

```bash
# Get all devices
GET /api/devices

# Get device details
GET /api/devices/<device_name>

# Get all MIBs for a device
GET /api/devices/<device_name>/mibs

# Get specific MIB data
GET /api/mibs/<mib_name>

# Search across all MIBs
GET /api/search?q=<query>

# Get tree data for a MIB
GET /api/mibs/<mib_name>/tree
```

### Fullscreen Mode URL Parameters

The fullscreen tree view can be accessed directly:

```bash
# Normal tree view
http://localhost:8080/tree/<device_name>/<mib_name>

# Fullscreen tree view
http://localhost:8080/tree/<device_name>/<mib_name>?fullscreen=true
```

## Browser Support

- **Chrome/Edge**: Full support including all fullscreen features
- **Firefox**: Full support
- **Safari**: Full support (note: popup blocker may need to be configured)
- **Mobile**: Responsive design works on all modern mobile browsers

## Configuration

### Environment Variables

```bash
# Flask configuration
FLASK_HOST=0.0.0.0          # Host to bind to
FLASK_PORT=8080              # Port to listen on
FLASK_DEBUG=False           # Debug mode
```

### Device Configuration

Devices are configured in `storage/device_registry.json`:

```json
{
  "devices": {
    "router1": {
      "name": "Main Router",
      "description": "Core network router",
      "vendor": "Cisco",
      "model": "ISR4331"
    }
  }
}
```

## Recent Updates

### v1.2.0 - Fullscreen Tree View
- ✨ Added fullscreen tree view mode for better visualization
- 🖱️ Enhanced tree navigation with expand/collapse controls
- 🔍 Integrated search in fullscreen mode
- 🖨️ Print optimization for documentation
- 🎨 Color-coded depth visualization
- ⚡ Performance improvements for large tree structures

### v1.1.0 - Web Interface
- 🌐 Complete web-based MIB viewer
- 📱 Responsive design
- 🔍 Advanced search capabilities
- 📊 Statistics and analytics
- 👥 Multi-device support

## License

This project is licensed under the MIT License.