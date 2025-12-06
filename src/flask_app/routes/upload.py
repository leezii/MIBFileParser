"""
Routes for file upload and device management functionality.
"""

import zipfile
import tempfile
import shutil
from pathlib import Path
from flask import Blueprint, request, jsonify, render_template, session, current_app
from werkzeug.utils import secure_filename

from ..services.device_service import DeviceService

upload_bp = Blueprint('upload', __name__)

# Allowed file extensions
ALLOWED_EXTENSIONS = {'mib', 'txt', 'zip'}
MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 50MB max upload size


def allowed_file(filename):
    """Check if file has allowed extension."""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@upload_bp.route('/upload', methods=['GET', 'POST'])
def upload_page():
    """Upload page for MIB files."""
    device_service = DeviceService()

    if request.method == 'GET':
        devices = device_service.list_devices()
        current_device = device_service.get_current_device()

        return render_template('upload.html',
                             devices=devices,
                             current_device=current_device)

    # Handle POST request for file upload
    return handle_file_upload(device_service)


def handle_file_upload(device_service):
    """Handle the actual file upload process."""
    try:
        # Get form data
        device_type = request.form.get('device_type', '').strip()
        new_device_name = request.form.get('new_device_name', '').strip()
        new_device_display = request.form.get('new_device_display', '').strip()
        action = request.form.get('action', 'replace')  # 'replace' or 'append'
        description = request.form.get('description', '').strip()

        # Determine device
        if device_type == '__new__' and new_device_name:
            # Create new device
            if not new_device_name:
                return jsonify({
                    'success': False,
                    'error': 'Device name is required'
                }), 400

            display_name = new_device_display or new_device_name.replace('-', ' ').replace('_', ' ').title()

            if not device_service.create_device(new_device_name, display_name, description):
                return jsonify({
                    'success': False,
                    'error': 'Device already exists or invalid name'
                }), 400

            device_name = new_device_name
        elif device_type and device_type != '__new__':
            device_name = device_type
        else:
            return jsonify({
                'success': False,
                'error': 'Please select or create a device type'
            }), 400

        # Handle file uploads
        if 'files' not in request.files:
            return jsonify({
                'success': False,
                'error': 'No files selected'
            }), 400

        files = request.files.getlist('files')
        if not files or all(f.filename == '' for f in files):
            return jsonify({
                'success': False,
                'error': 'No files selected'
            }), 400

        # Process uploaded files
        mib_files = []
        temp_dir = None

        try:
            temp_dir = tempfile.mkdtemp()

            for file in files:
                if file and file.filename and allowed_file(file.filename):
                    filename = secure_filename(file.filename)
                    file_path = Path(temp_dir) / filename
                    file.save(str(file_path))

                    # Handle ZIP files
                    if filename.lower().endswith('.zip'):
                        extracted_files = extract_zip_file(file_path, temp_dir)
                        mib_files.extend(extracted_files)
                    else:
                        mib_files.append(file_path)

            if not mib_files:
                return jsonify({
                    'success': False,
                    'error': 'No valid MIB files found in upload'
                }), 400

            # Get device MIB service and process files
            mib_service = device_service.get_device_mib_service(device_name)

            if action == 'replace':
                result = mib_service.replace_device_mibs(mib_files, device_name)
            else:
                result = mib_service.add_uploaded_files(mib_files, device_name)

            # Update device metadata
            success_count = result.get('success_count', 0)
            current_app.logger.info(f"Debug: result type: {type(result)}, success_count: {success_count} (type: {type(success_count)})")
            current_app.logger.info(f"Debug: result keys: {list(result.keys()) if isinstance(result, dict) else 'Not a dict'}")

            if not isinstance(success_count, int):
                current_app.logger.error(f"Error: success_count is not int: {success_count} (type: {type(success_count)})")
                success_count = 0

            device_service.update_device_metadata(device_name, success_count)

            # Set current device to the one we just uploaded to
            current_app.logger.info(f"Debug: Setting current device to {device_name}")
            current_device_result = device_service.set_current_device(device_name)
            current_app.logger.info(f"Debug: set_current_device returned: {current_device_result} (type: {type(current_device_result)})")

            # Update session
            current_app.logger.info(f"Debug: Updating session")
            session['current_device'] = device_name

            # Prepare response data
            current_app.logger.info(f"Debug: Preparing response")
            success_files = result.get('success', [])
            errors = result.get('errors', [])
            current_app.logger.info(f"Debug: success_files type: {type(success_files)}, length: {len(success_files) if hasattr(success_files, '__len__') else 'no len'}")
            current_app.logger.info(f"Debug: errors type: {type(errors)}, length: {len(errors) if hasattr(errors, '__len__') else 'no len'}")

            return jsonify({
                'success': True,
                'device_name': device_name,
                'results': {
                    'success_count': result.get('success_count', len(success_files) if hasattr(success_files, '__len__') else 0),
                    'error_count': result.get('error_count', len(errors) if hasattr(errors, '__len__') else 0),
                    'success_files': success_files,
                    'errors': errors
                },
                'action': action
            })

        finally:
            # Clean up temporary files
            if temp_dir and Path(temp_dir).exists():
                shutil.rmtree(temp_dir, ignore_errors=True)

    except Exception as e:
        import traceback
        current_app.logger.error(f"Upload error: {str(e)}")
        current_app.logger.error(f"Full traceback: {traceback.format_exc()}")
        return jsonify({
            'success': False,
            'error': f'Upload failed: {str(e)}'
        }), 500


def extract_zip_file(zip_path, extract_dir):
    """Extract MIB files from a ZIP archive."""
    extracted_files = []

    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            for file_info in zip_ref.infolist():
                if not file_info.is_dir():
                    filename = file_info.filename.lower()

                    # Check if it's a MIB file (look at extension and content)
                    if filename.endswith(('.mib', '.txt')):
                        extracted_path = Path(extract_dir) / Path(file_info.filename).name

                        # Extract file
                        with zip_ref.open(file_info) as source, open(extracted_path, 'wb') as target:
                            shutil.copyfileobj(source, target)

                        # Basic validation - check if it looks like a MIB file
                        if is_likely_mib_file(extracted_path):
                            extracted_files.append(extracted_path)
                        else:
                            extracted_path.unlink()  # Remove if not a MIB file

    except Exception as e:
        current_app.logger.error(f"Error extracting ZIP {zip_path}: {str(e)}")

    return extracted_files


def is_likely_mib_file(file_path):
    """Basic validation to check if file is likely a MIB file."""
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read(1000).upper()  # Read first 1000 chars

            # Look for common MIB patterns
            mib_patterns = [
                'DEFINITIONS ::= BEGIN',
                'ORGANIZATION',
                'CONTACT-INFO',
                'DESCRIPTION',
                '::= {',
                'OBJECT-TYPE',
                'MODULE-IDENTITY'
            ]

            return any(pattern in content for pattern in mib_patterns)

    except Exception:
        return False


# API Routes

@upload_bp.route('/api/devices', methods=['GET'])
def list_devices():
    """API endpoint to list all devices."""
    device_service = DeviceService()
    devices = device_service.list_devices()
    current_device = device_service.get_current_device()

    return jsonify({
        'devices': [vars(device) for device in devices],
        'current_device': current_device
    })


@upload_bp.route('/api/devices', methods=['POST'])
def create_device():
    """API endpoint to create a new device."""
    try:
        data = request.get_json()

        device_name = data.get('name', '').strip()
        display_name = data.get('display_name', '').strip()
        description = data.get('description', '').strip()

        if not device_name:
            return jsonify({'error': 'Device name is required'}), 400

        device_service = DeviceService()

        if device_service.create_device(device_name, display_name or None, description or None):
            return jsonify({
                'success': True,
                'device': vars(device_service.get_device_info(device_name))
            })
        else:
            return jsonify({'error': 'Device already exists or invalid name'}), 400

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@upload_bp.route('/api/devices/<device_name>', methods=['DELETE'])
def delete_device(device_name):
    """API endpoint to delete a device."""
    try:
        device_service = DeviceService()

        if device_service.delete_device(device_name):
            return jsonify({'success': True})
        else:
            return jsonify({'error': 'Device not found'}), 404

    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@upload_bp.route('/api/devices/<device_name>/switch', methods=['POST'])
def switch_device(device_name):
    """API endpoint to switch to a specific device."""
    try:
        device_service = DeviceService()

        if device_service.set_current_device(device_name):
            session['current_device'] = device_name
            return jsonify({'success': True, 'current_device': device_name})
        else:
            return jsonify({'error': 'Device not found'}), 404

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@upload_bp.route('/api/upload', methods=['POST'])
def upload_files():
    """API endpoint for file upload."""
    device_service = DeviceService()
    return handle_file_upload(device_service)


@upload_bp.route('/devices', methods=['GET'])
def device_management():
    """Device management page."""
    device_service = DeviceService()
    devices = device_service.list_devices()
    current_device = device_service.get_current_device()

    return render_template('devices.html',
                         devices=devices,
                         current_device=current_device)