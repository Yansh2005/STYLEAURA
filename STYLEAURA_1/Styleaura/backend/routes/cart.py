from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from database import User
import time
import uuid

cart_bp = Blueprint('cart', __name__)

# In-memory cart storage (in production, use Redis or database)
user_carts = {}

@cart_bp.route('/items', methods=['GET'])
@jwt_required()
def get_cart_items():
    """Get all items in the user's shopping cart"""
    try:
        user_id = get_jwt_identity()
        
        # Get user's cart from storage
        cart = user_carts.get(user_id, {'items': [], 'created_at': time.time()})
        
        return jsonify({
            'items': cart['items'],
            'total_items': len(cart['items']),
            'total_price': sum(item.get('price', 0) * item.get('quantity', 1) for item in cart['items'])
        })
        
    except Exception as e:
        return jsonify({'error': 'Failed to fetch cart items'}), 500

@cart_bp.route('/add', methods=['POST'])
@jwt_required()
def add_to_cart():
    """Add items to the shopping cart"""
    try:
        data = request.get_json()
        items = data.get('items', [])
        
        if not items:
            return jsonify({'error': 'No items provided'}), 400
        
        user_id = get_jwt_identity()
        
        # Initialize user cart if doesn't exist
        if user_id not in user_carts:
            user_carts[user_id] = {'items': [], 'created_at': time.time()}
        
        cart_items = []
        total_price = 0.0
        
        for item in items:
            cart_item = {
                'id': str(uuid.uuid4()),
                'name': item.get('name', 'Unknown Item'),
                'price': item.get('price', 0.0),
                'outfit_id': item.get('outfitId'),
                'outfit_title': item.get('outfitTitle'),
                'quantity': 1,
                'added_at': time.time(),
                'image': item.get('image', '👔')
            }
            user_carts[user_id]['items'].append(cart_item)
            cart_items.append(cart_item)
            total_price += cart_item['price']
        
        return jsonify({
            'message': f'Added {len(items)} items to cart',
            'items_added': cart_items,
            'total_items': len(user_carts[user_id]['items']),
            'total_price': total_price
        })
        
    except Exception as e:
        return jsonify({'error': 'Failed to add items to cart'}), 500

@cart_bp.route('/remove/<item_id>', methods=['DELETE'])
@jwt_required()
def remove_from_cart(item_id):
    """Remove an item from the shopping cart"""
    try:
        user_id = get_jwt_identity()
        
        if user_id not in user_carts:
            return jsonify({'error': 'Cart not found'}), 404
        
        # Remove item from cart
        original_length = len(user_carts[user_id]['items'])
        user_carts[user_id]['items'] = [
            item for item in user_carts[user_id]['items'] 
            if item['id'] != item_id
        ]
        
        if len(user_carts[user_id]['items']) == original_length:
            return jsonify({'error': 'Item not found in cart'}), 404
        
        return jsonify({
            'message': 'Item removed from cart',
            'item_id': item_id,
            'remaining_items': len(user_carts[user_id]['items'])
        })
        
    except Exception as e:
        return jsonify({'error': 'Failed to remove item from cart'}), 500

@cart_bp.route('/update/<item_id>', methods=['PUT'])
@jwt_required()
def update_cart_item(item_id):
    """Update quantity of an item in the shopping cart"""
    try:
        data = request.get_json()
        new_quantity = data.get('quantity', 1)
        
        if new_quantity < 1:
            return jsonify({'error': 'Quantity must be at least 1'}), 400
        
        user_id = get_jwt_identity()
        
        if user_id not in user_carts:
            return jsonify({'error': 'Cart not found'}), 404
        
        # Find and update item
        for item in user_carts[user_id]['items']:
            if item['id'] == item_id:
                item['quantity'] = new_quantity
                return jsonify({
                    'message': 'Item quantity updated',
                    'item_id': item_id,
                    'new_quantity': new_quantity
                })
        
        return jsonify({'error': 'Item not found in cart'}), 404
        
    except Exception as e:
        return jsonify({'error': 'Failed to update item quantity'}), 500

@cart_bp.route('/clear', methods=['DELETE'])
@jwt_required()
def clear_cart():
    """Clear all items from the shopping cart"""
    try:
        user_id = get_jwt_identity()
        
        if user_id in user_carts:
            user_carts[user_id]['items'] = []
        
        return jsonify({
            'message': 'Cart cleared successfully'
        })
        
    except Exception as e:
        return jsonify({'error': 'Failed to clear cart'}), 500

@cart_bp.route('/checkout', methods=['POST'])
@jwt_required()
def checkout():
    """Process checkout"""
    try:
        data = request.get_json()
        shipping_address = data.get('shipping_address', {})
        payment_method = data.get('payment_method', {})
        
        user_id = get_jwt_identity()
        
        if user_id not in user_carts or not user_carts[user_id]['items']:
            return jsonify({'error': 'Cart is empty'}), 400
        
        cart_items = user_carts[user_id]['items']
        total_price = sum(item.get('price', 0) * item.get('quantity', 1) for item in cart_items)
        
        # Create order
        order_id = f"order_{int(time.time())}_{user_id[:8]}"
        
        # In a real implementation, this would:
        # 1. Validate shipping address
        # 2. Process payment
        # 3. Create order in database
        # 4. Send confirmation email
        # 5. Clear cart
        
        # Clear cart after successful order
        user_carts[user_id]['items'] = []
        
        return jsonify({
            'message': 'Order placed successfully!',
            'order_id': order_id,
            'total_amount': total_price,
            'estimated_delivery': '3-5 business days',
            'confirmation_sent': True,
            'order_summary': {
                'items': cart_items,
                'total_items': len(cart_items),
                'total_price': total_price
            }
        })
        
    except Exception as e:
        return jsonify({'error': 'Failed to process checkout'}), 500

@cart_bp.route('/summary', methods=['GET'])
@jwt_required()
def get_cart_summary():
    """Get cart summary without full item details"""
    try:
        user_id = get_jwt_identity()
        
        if user_id not in user_carts:
            return jsonify({
                'total_items': 0,
                'total_price': 0.0
            })
        
        cart = user_carts[user_id]
        total_items = len(cart['items'])
        total_price = sum(item.get('price', 0) * item.get('quantity', 1) for item in cart['items'])
        
        return jsonify({
            'total_items': total_items,
            'total_price': total_price
        })
        
    except Exception as e:
        return jsonify({'error': 'Failed to fetch cart summary'}), 500
