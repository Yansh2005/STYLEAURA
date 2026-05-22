from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
import random
import time

chat_bp = Blueprint('chat', __name__)

# Chatbot responses database
CHAT_RESPONSES = {
    'hello': "Hello! Welcome to StyleAura! I'm here to help you with any questions about our fashion advice services.",
    'pricing': "Our basic style analysis is free! Premium features like personalized shopping recommendations start at ₹2,199/month.",
    'how_it_works': "StyleAura uses AI to analyze your photos and provide personalized fashion recommendations. Just upload a photo, get analyzed, and receive outfit suggestions!",
    'recommendations': "We provide personalized outfit recommendations based on your body type, style preferences, and occasion. Each recommendation includes specific items and where to buy them.",
    'analysis': "Our AI analyzes your face shape, body type, skin tone, and style personality to provide accurate fashion advice.",
    'contact': "You can reach us at 23dcs120@charusat.edu.in or visit our development center in Vadodara, Gujarat.",
    'shipping': "We partner with major retailers for fast shipping. Most items arrive within 3-5 business days.",
    'returns': "Return policies vary by retailer. We'll help you find the best return options for your purchases.",
    'account': "You can create an account to save your analysis history and preferences. Just click the Sign Up button on our homepage!",
    'security': "We take your privacy seriously. All photos are processed securely and deleted after analysis. Your data is never shared with third parties.",
    'accuracy': "Our AI has been trained on thousands of fashion examples and provides recommendations with over 90% accuracy rate.",
    'styles': "We cover all major style types including casual, formal, business, athletic, and special occasion wear.",
    'sizes': "Our recommendations include size suggestions based on your body analysis and preferred fit.",
    'brands': "We partner with over 100 major brands and retailers to give you the best options at various price points starting from ₹999.",
    'default': "That's a great question! Let me help you with that. You can ask me about our services, pricing, how StyleAura works, contact information, account features, security, accuracy, styles, sizes, or brand partnerships."
}

@chat_bp.route('/message', methods=['POST'])
@jwt_required()
def send_message():
    """Send a message to the chatbot and get a response"""
    try:
        data = request.get_json()
        user_message = data.get('message', '').strip()
        
        if not user_message:
            return jsonify({'error': 'Message cannot be empty'}), 400
        
        # Get user identity for personalization
        user_id = get_jwt_identity()
        
        # Simulate typing delay
        time.sleep(random.uniform(0.5, 1.5))
        
        # Get bot response
        bot_response = get_bot_response(user_message)
        
        # Log the conversation (for analytics)
        print(f"User {user_id}: {user_message}")
        print(f"Bot: {bot_response}")
        
        return jsonify({
            'response': bot_response,
            'timestamp': time.time()
        })
        
    except Exception as e:
        return jsonify({'error': 'Failed to process message'}), 500

def get_bot_response(user_message):
    """Generate bot response based on user message"""
    lower_message = user_message.lower()
    
    # Check for exact keyword matches first
    if 'hello' in lower_message or 'hi' in lower_message or 'hey' in lower_message:
        return CHAT_RESPONSES['hello']
    if 'price' in lower_message or 'cost' in lower_message or 'pricing' in lower_message:
        return CHAT_RESPONSES['pricing']
    if 'how it works' in lower_message or 'how does it work' in lower_message or 'process' in lower_message:
        return CHAT_RESPONSES['how_it_works']
    if 'recommendation' in lower_message or 'suggestion' in lower_message or 'outfit' in lower_message:
        return CHAT_RESPONSES['recommendations']
    if 'analysis' in lower_message or 'analyze' in lower_message or 'ai' in lower_message:
        return CHAT_RESPONSES['analysis']
    if 'contact' in lower_message or 'email' in lower_message or 'phone' in lower_message or 'address' in lower_message:
        return CHAT_RESPONSES['contact']
    if 'shipping' in lower_message or 'delivery' in lower_message or 'delivery time' in lower_message:
        return CHAT_RESPONSES['shipping']
    if 'return' in lower_message or 'refund' in lower_message or 'exchange' in lower_message:
        return CHAT_RESPONSES['returns']
    if 'account' in lower_message or 'signup' in lower_message or 'register' in lower_message:
        return CHAT_RESPONSES['account']
    if 'security' in lower_message or 'privacy' in lower_message or 'safe' in lower_message:
        return CHAT_RESPONSES['security']
    if 'accuracy' in lower_message or 'precise' in lower_message or 'correct' in lower_message:
        return CHAT_RESPONSES['accuracy']
    if 'styles' in lower_message or 'style type' in lower_message or 'fashion' in lower_message:
        return CHAT_RESPONSES['styles']
    if 'sizes' in lower_message or 'fit' in lower_message or 'measurement' in lower_message:
        return CHAT_RESPONSES['sizes']
    if 'brands' in lower_message or 'retailers' in lower_message or 'companies' in lower_message:
        return CHAT_RESPONSES['brands']
    
    # Return default response if no keywords match
    return CHAT_RESPONSES['default']

@chat_bp.route('/history', methods=['GET'])
@jwt_required()
def get_chat_history():
    """Get chat history for the current user"""
    try:
        # In a real implementation, this would fetch from database
        # For now, return empty history
        return jsonify({
            'history': [],
            'message': 'Chat history feature coming soon!'
        })
    except Exception as e:
        return jsonify({'error': 'Failed to fetch chat history'}), 500
