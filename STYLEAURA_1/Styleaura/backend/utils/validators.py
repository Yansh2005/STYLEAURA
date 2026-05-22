import re

def validate_email(email):
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_password(password):
    """Validate password strength"""
    if len(password) < 8:
        return {'valid': False, 'message': 'Password must be at least 8 characters long'}
    
    if not re.search(r'[A-Z]', password):
        return {'valid': False, 'message': 'Password must contain at least one uppercase letter'}
    
    if not re.search(r'[a-z]', password):
        return {'valid': False, 'message': 'Password must contain at least one lowercase letter'}
    
    if not re.search(r'\d', password):
        return {'valid': False, 'message': 'Password must contain at least one digit'}
    
    return {'valid': True, 'message': 'Password is valid'}

def allowed_file(filename, allowed_extensions):
    """Check if file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in allowed_extensions

def validate_image_file(file):
    """Validate uploaded image file"""
    if not file:
        return {'valid': False, 'message': 'No file provided'}
    
    if file.filename == '':
        return {'valid': False, 'message': 'No file selected'}
    
    # Check file size (max 10MB)
    file.seek(0, 2)  # Seek to end
    file_size = file.tell()
    file.seek(0)  # Reset pointer
    
    if file_size > 10 * 1024 * 1024:  # 10MB
        return {'valid': False, 'message': 'File size must be less than 10MB'}
    
    # Check file extension
    allowed_extensions = {'png', 'jpg', 'jpeg', 'webp'}
    if not allowed_file(file.filename, allowed_extensions):
        return {'valid': False, 'message': 'Invalid file type. Allowed types: PNG, JPG, JPEG, WEBP'}
    
    # Check MIME type
    allowed_mimes = {'image/png', 'image/jpeg', 'image/webp'}
    if file.mimetype not in allowed_mimes:
        return {'valid': False, 'message': 'Invalid MIME type'}
    
    return {'valid': True, 'message': 'File is valid'}
