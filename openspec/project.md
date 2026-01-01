# Project Context

## Purpose
MIB File Parser is a comprehensive tool for parsing, visualizing, and managing SNMP MIB (Management Information Base) files. It provides both a Python library for programmatic MIB parsing and a web-based interface for interactive exploration. The tool enables network engineers and developers to browse complex MIB tree structures, search OIDs, manage device-specific MIBs, and annotate nodes for better documentation.

## Tech Stack

### Backend
- **Python 3.9+** - Primary language
- **Flask 3.1+** - Web framework
- **Flask-CORS** - Cross-origin resource sharing
- **Gunicorn** - Production WSGI server
- **pysmi 0.3.4+** - MIB file parsing engine
- **pysnmp 4.4.12+** - SNMP library

### Frontend
- **HTML5/CSS3** - Template structure
- **Vanilla JavaScript** - Client-side interactivity
- **Bootstrap** - Responsive UI framework (localized for internal network deployment)
- **Jinja2** - Template rendering

### Development Tools
- **pytest** - Testing framework
- **pytest-cov** - Code coverage reporting
- **black** - Code formatting (line length: 88)
- **flake8** - Linting
- **mypy** - Static type checking
- **uv** - Package manager
- **hatchling** - Build backend

### Desktop Application (Optional)
- **Electron** - Desktop framework
- **Node.js/npm** - Frontend build tools

## Project Conventions

### Code Style
- **Python**: Follow PEP 8, enforced by black with 88 character line length
- **Type Hints**: Strict type checking enabled with mypy (`disallow_untyped_defs = true`)
- **Imports**: Organized with clear separation between third-party and local imports
- **Naming**:
  - Modules: `snake_case`
  - Classes: `PascalCase`
  - Functions/Variables: `snake_case`
  - Constants: `UPPER_SNAKE_CASE`

### Architecture Patterns

#### Backend (MVC + Service Layer)
- **Routes** (`src/flask_app/routes/`): Request handling and URL routing
  - `main.py` - Dashboard and main pages
  - `api.py` - REST API endpoints
  - `upload.py` - File upload handling
  - `oid_lookup.py` - OID lookup and search
  - `annotation.py` - Annotation management

- **Services** (`src/flask_app/services/`): Business logic layer
  - `mib_service.py` - MIB parsing and caching
  - `device_service.py` - Device management
  - `tree_service.py` - Tree visualization logic
  - `mib_table_service.py` - MIB table data handling
  - `annotation_service.py` - Annotation CRUD operations

- **Models** (`src/mib_parser/models.py`): Data structures
  - `MibNode` - Represents MIB tree nodes
  - `MibData` - Container for parsed MIB data

#### Core Parser Library
- **parser.py**: Core MIB file parsing using pysmi
- **serializer.py**: JSON export functionality
- **tree.py**: Tree traversal and manipulation tools
- **leaf_extractor.py**: Extract leaf nodes from MIB trees
- **dependency_resolver.py**: Handle MIB import dependencies

#### Storage Organization
```
storage/
├── devices/           # Device-specific MIB files (organized by device name)
├── global/            # Global/standard MIBs (SNMPv2-SMI, SNMPv2-TC, etc.)
├── annotations/       # User annotations for leaf nodes
├── leaf_nodes/        # Extracted leaf node data
└── device_registry.json # Device configuration registry
```

### Testing Strategy
- **Unit Tests**: All core functionality must have pytest tests
- **Coverage Target**: Report generated in `htmlcov/` directory
- **Test Location**: `tests/` directory with `test_*.py` naming
- **Fixtures**: Test MIB files in `tests/fixtures/`
- **Run Tests**: `uv run pytest`

### Git Workflow
- **Main Branch**: `main` - stable production code
- **Commit Messages**: Clear, descriptive messages following conventional format
- **Recent Focus**:
  - Annotation system for user-added string labels
  - OID Lookup page optimization
  - Frontend dependency localization for internal deployment
  - Device registry management

## Domain Context

### MIB Files & SNMP
- **MIB (Management Information Base)**: Hierarchical database describing managed objects in a network device
- **OID (Object Identifier)**: Numerical identifier for each node in the MIB tree (e.g., `1.3.6.1.2.1.1.1`)
- **SNMP**: Protocol for managing network devices using MIBs
- **MIB Tree Structure**: Hierarchical organization with parent-child relationships
- **Leaf Nodes**: Terminal nodes in the MIB tree that contain actual data (not subtrees)
- **Index Fields**: Used in MIB tables to identify rows (critical for table operations)

### Key Concepts
- **pysmi**: Python library for parsing MIB files (ASN.1 syntax)
- **OID Lookup**: Searching for nodes by OID or name across loaded MIBs
- **Annotations**: User-provided labels/comments for specific OIDs to improve documentation
- **Device Registry**: JSON configuration mapping device names to their MIB files
- **Tree Visualization**: Interactive display of MIB hierarchy with expand/collapse functionality

## Important Constraints

### Technical Constraints
- **Python Version**: Must support Python 3.9+
- **Browser Compatibility**: Must work on Chrome/Edge, Firefox, Safari, and mobile browsers
- **Network Deployment**: Frontend dependencies are localized (no external CDN access required)
- **File Upload**: Handle MIB files via drag-and-drop interface
- **Performance**: Must handle large MIB trees with optimized rendering

### Storage Constraints
- **Device-specific MIBs**: Stored separately in `storage/devices/<device_name>/`
- **Global MIBs**: Shared across all devices in `storage/global/`
- **Annotations**: Persisted in JSON format for quick lookup
- **Device Registry**: Central JSON file for device configuration

### Business Constraints
- **Internal Network Deployment**: Application designed to run on isolated networks without internet access
- **Multi-Device Support**: Must support multiple network devices with different MIB sets
- **User Annotations**: Support persistent user-added annotations for OIDs
- **OID Lookup**: Critical feature for network engineers to find and document OIDs

## External Dependencies

### Python Packages
- **pysmi** (`>=0.3.4`): MIB file parsing engine
- **pysnmp** (`>=4.4.12`): SNMP operations
- **flask** (`>=3.1.2`): Web framework
- **flask-cors** (`>=6.0.1`): CORS support
- **gunicorn** (`>=23.0.0`): Production server

### Frontend Dependencies (Localized)
- **Bootstrap**: CSS framework (local copy in `src/flask_app/static/`)
- **jQuery**: DOM manipulation (local copy)
- **Other JavaScript libraries**: All localized for internal network use

### System Dependencies
- **Python Environment**: Managed via `uv` package manager
- **Storage**: Filesystem-based JSON storage (no database required)

## Key Features by Version

### v1.2.0 (Current)
- Fullscreen tree view mode
- Integrated search in fullscreen
- Expand/collapse all controls
- Print optimization
- Color-coded depth visualization

### v1.1.0
- Complete web interface
- REST API endpoints
- Multi-device support
- Advanced search capabilities

### v1.0.0
- Core MIB parser
- JSON export
- Tree traversal tools
- Batch directory processing

## Configuration Files
- **`pyproject.toml`**: Project dependencies and tool configuration
- **`storage/device_registry.json`**: Device configuration
- **`wsgi.py`**: WSGI entry point for production deployment
- **Environment Variables**:
  - `FLASK_HOST`: Server host (default: 0.0.0.0)
  - `FLASK_PORT`: Server port (default: 8080)
  - `FLASK_DEBUG`: Debug mode flag
  - `DESKTOP_MODE`: Enable desktop application features
