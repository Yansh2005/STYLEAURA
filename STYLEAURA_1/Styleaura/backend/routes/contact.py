from flask import Blueprint, request, jsonify
from database import mongo, contact_messages_collection
from datetime import datetime

contact_bp = Blueprint('contact', __name__)

@contact_bp.route('/', methods=['POST'])
def submit_contact():
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['name', 'email', 'subject', 'message']
        for field in required_fields:
            if not data.get(field) or not data.get(field).strip():
                return jsonify({'error': f'{field.replace("_", " ").title()} is required'}), 400
        
        name = data['name'].strip()
        email = data['email'].strip().lower()
        subject = data['subject'].strip()
        message = data['message'].strip()
        
        # Basic email validation
        if '@' not in email or '.' not in email.split('@')[-1]:
            return jsonify({'error': 'Invalid email format'}), 400
        
        # Create contact message
        contact_message = {
            'name': name,
            'email': email,
            'subject': subject,
            'message': message,
            'created_at': datetime.utcnow(),
            'status': 'new'
        }
        
        # Save to database
        if mongo.is_connected():
            # MongoDB storage
            result = contact_messages_collection.insert_one(contact_message)
            contact_message['_id'] = str(result.inserted_id)
        else:
            # In-memory storage
            message_id = f"msg_{len(contact_messages_collection) + 1}"
            contact_message['id'] = message_id
            contact_messages_collection[message_id] = contact_message
        
        return jsonify({
            'message': 'Contact message submitted successfully',
            'contact_message': {
                'id': contact_message.get('_id') or contact_message.get('id'),
                'name': contact_message['name'],
                'email': contact_message['email'],
                'subject': contact_message['subject'],
                'created_at': contact_message['created_at'].isoformat()
            }
        }), 201
        
    except Exception as e:
        print(f"Error submitting contact form: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@contact_bp.route('/', methods=['GET'])
def get_contact_messages():
    try:
        # This could be used for an admin panel to view messages
        if mongo.is_connected():
            messages = list(contact_messages_collection.find().sort('created_at', -1))
            for message in messages:
                message['_id'] = str(message['_id'])
        else:
            messages = list(contact_messages_collection.values())
        
        return jsonify({'messages': messages}), 200
        
    except Exception as e:
        print(f"Error fetching contact messages: {e}")
        return jsonify({'error': 'Internal server error'}), 500
