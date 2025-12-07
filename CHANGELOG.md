# Changelog

All notable changes to MIB Parser & Web Viewer will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.2.0] - 2025-12-07

### Added
- ✨ **Fullscreen Tree View Mode**: Dedicated fullscreen window for large tree structures
- 🔍 **Integrated Search in Fullscreen**: Real-time search with highlighting
- 📁 **Expand/Collapse All Controls**: Quick navigation controls for tree manipulation
- 🖨️ **Print Optimization**: Enhanced print layouts for documentation
- 🎨 **Color-Coded Depth Visualization**: Visual depth indicators for better navigation
- ⚡ **Performance Improvements**: Optimized rendering for large MIB trees
- 🔄 **Reset View Function**: New button to reset tree to initial state

### Changed
- 🐛 Fixed JavaScript error with missing resetZoom function
- 🔧 Improved tree rendering performance
- 📱 Enhanced responsive design for mobile devices
- 🎯 Better error handling for malformed MIB files

### Technical Details
- Uses URL parameters (`?fullscreen=true`) for fullscreen mode switching
- Maintains consistent styling between normal and fullscreen views
- Preserves tree state (expanded/collapsed) across view modes

## [1.1.0] - 2025-12-06

### Added
- 🌐 **Complete Web Interface**: Flask-based web application for MIB visualization
- 📱 **Responsive Design**: Mobile-friendly interface using Bootstrap
- 🔍 **Advanced Search**: Global search across all MIB files and OIDs
- 📊 **Statistics Dashboard**: Comprehensive analytics about MIB structures
- 👥 **Multi-Device Support**: Organize MIB files by network devices
- ⬆️ **Drag-and-Drop Upload**: Easy MIB file upload interface
- 🖨️ **Print-Friendly Layouts**: Optimized printing for documentation

### REST API
- `/api/devices` - List all devices
- `/api/devices/<device_name>` - Get device details
- `/api/devices/<device_name>/mibs` - List MIBs for a device
- `/api/mibs/<mib_name>` - Get specific MIB data
- `/api/search` - Search across all MIBs
- `/api/mibs/<mib_name>/tree` - Get tree structure

### Architecture
- MVC pattern implementation
- Service layer for business logic
- Template-based rendering with Jinja2
- Static asset management

## [1.0.0] - 2025-11-01

### Added
- 🚀 **Core MIB Parser**: High-performance parsing based on pysmi
- 📊 **JSON Export**: Structured data export functionality
- 🌳 **Tree Traversal**: Complete tree structure navigation tools
- 🔍 **Node Lookup**: Flexible OID and pattern matching
- 📁 **Batch Processing**: Support for directory parsing
- 🧪 **Test Suite**: Comprehensive unit test coverage
- 📚 **Documentation**: Complete API documentation and examples

### Core Library Features
- `MibParser` - Main parsing engine
- `JsonSerializer` - JSON export functionality
- `MibTree` - Tree manipulation and traversal
- Complete data models for MIB structures

### Supported MIB Features
- ASN.1 syntax parsing
- OID resolution and validation
- Import handling
- DESCRIPTION clauses
- SYNTAX definitions
- ACCESS specifications
- STATUS information

## [Unreleased]

### Planned
- 🔄 Real-time MIB file watching
- 📈 Enhanced analytics and reporting
- 🌐 Multi-language support
- 🔐 User authentication and permissions
- 📱 Native mobile application
- ☁️ Cloud deployment support
- 🔄 MIB version comparison tools
- 📊 Advanced visualization options (graphs, charts)

---

## Version History

- **1.2.0** (2025-12-07): Fullscreen tree view and enhanced navigation
- **1.1.0** (2025-12-06): Complete web interface and REST API
- **1.0.0** (2025-11-01): Initial release with core parser functionality