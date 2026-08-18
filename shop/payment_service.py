# shop/payment_service.py

import random
import hashlib
import time
from decimal import Decimal
from django.db import transaction
from .models import Order, PaymentTransaction, Product

class MockPaymentProcessor:
    """
    A mock payment processor for learning purposes.
    Never use this with real money or real card details!
    """
    
    @staticmethod
    def validate_card(card_number, expiry_month, expiry_year, cvv):
        """
        Mock card validation - teaches you the logic without real processing
        """
        errors = []
        
        # Remove spaces
        card_number = card_number.replace(' ', '')
        
        # 1. Check card number length (16 digits for most cards)
        if not card_number or len(card_number) != 16:
            errors.append("Card number must be 16 digits")
        elif not card_number.isdigit():
            errors.append("Card number must contain only digits")
        
        # 2. Validate expiry date
        try:
            month = int(expiry_month)
            year = int(expiry_year)
            
            if month < 1 or month > 12:
                errors.append("Invalid expiry month")
            
            # Check if card is expired
            current_year = time.localtime().tm_year % 100
            current_month = time.localtime().tm_mon
            
            if year < current_year or (year == current_year and month < current_month):
                errors.append("Card has expired")
                
        except ValueError:
            errors.append("Invalid expiry date format")
        
        # 3. CVV validation (3-4 digits)
        if not cvv or not cvv.isdigit() or len(cvv) not in [3, 4]:
            errors.append("CVV must be 3-4 digits")
        
        # 4. Mock fraud detection
        if card_number.startswith('0000'):
            errors.append("Card rejected by fraud detection system")
        
        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'card_brand': MockPaymentProcessor._detect_card_brand(card_number),
            'last_four': card_number[-4:] if card_number else None
        }
    
    @staticmethod
    def _detect_card_brand(card_number):
        """Simple card brand detection based on first digits"""
        if not card_number:
            return 'Unknown'
        
        card_number = card_number.replace(' ', '')
        first_digit = card_number[0]
        first_two = card_number[:2]
        first_four = card_number[:4]
        
        if first_digit == '4':
            return 'Visa'
        elif first_two in ['51', '52', '53', '54', '55']:
            return 'Mastercard'
        elif first_two in ['34', '37']:
            return 'American Express'
        elif first_four == '6011':
            return 'Discover'
        else:
            return 'Unknown'
    
    @staticmethod
    def process_payment(order, card_details):
        """
        Process the payment (mock)
        """
        # Validate card first
        validation = MockPaymentProcessor.validate_card(
            card_details.get('card_number', ''),
            card_details.get('expiry_month', ''),
            card_details.get('expiry_year', ''),
            card_details.get('cvv', '')
        )
        
        if not validation['valid']:
            return {
                'success': False,
                'errors': validation['errors'],
                'transaction_id': None,
                'card_brand': validation.get('card_brand'),
                'last_four': validation.get('last_four')
            }
        
        # Simulate network latency (real-world feel)
        time.sleep(1.5)
        
        # Mock processing with random outcomes
        random_outcome = random.random()
        
        # 85% success, 7% insufficient funds, 8% technical error
        if random_outcome < 0.85:
            transaction_id = f"TXN-{hashlib.md5(f'{order.id}{time.time()}'.encode()).hexdigest()[:8].upper()}"
            
            return {
                'success': True,
                'transaction_id': transaction_id,
                'card_brand': validation['card_brand'],
                'last_four': validation['last_four'],
                'message': 'Payment successful!'
            }
        elif random_outcome < 0.92:
            return {
                'success': False,
                'errors': ['Insufficient funds in the account'],
                'transaction_id': None,
                'card_brand': validation.get('card_brand'),
                'last_four': validation.get('last_four')
            }
        else:
            return {
                'success': False,
                'errors': ['Payment gateway timeout. Please try again.'],
                'transaction_id': None,
                'card_brand': validation.get('card_brand'),
                'last_four': validation.get('last_four')
            }

class PaymentService:
    """
    Service layer for handling payments
    """
    
    @staticmethod
    def process_order_payment(order_id, card_details, idempotency_key=None):
        """
        Process payment for an order with idempotency support
        """
        try:
            order = Order.objects.get(id=order_id)
        except Order.DoesNotExist:
            return {
                'success': False,
                'error': 'Order not found'
            }
        
        # Idempotency check - prevent duplicate payments
        if idempotency_key:
            existing_payment = PaymentTransaction.objects.filter(
                order=order,
                transaction_id__contains=idempotency_key
            ).first()
            
            if existing_payment:
                return {
                    'success': existing_payment.status == 'success',
                    'message': 'Payment already processed',
                    'transaction_id': existing_payment.transaction_id,
                    'idempotent': True
                }
        
        # Check if order can be paid
        if not order.can_pay():
            return {
                'success': False,
                'error': f'Order cannot be paid. Current status: {order.get_payment_status_display()}'
            }
        
        # Process the payment in a database transaction
        with transaction.atomic():
            payment_result = MockPaymentProcessor.process_payment(order, card_details)
            
            # Record the transaction
            transaction_obj = PaymentTransaction.objects.create(
                order=order,
                amount=order.total_amount,
                status='success' if payment_result['success'] else 'failed',
                transaction_id=payment_result.get('transaction_id', f'FAILED-{int(time.time())}'),
                payment_method='card',
                card_last_four=payment_result.get('last_four', '0000'),
                card_brand=payment_result.get('card_brand', 'Unknown'),
                error_message='; '.join(payment_result.get('errors', [])) if not payment_result['success'] else ''
            )
            
            if payment_result['success']:
                # Update order
                order.payment_status = 'completed'
                order.status = 'paid'
                order.transaction_id = payment_result['transaction_id']
                order.card_last_four = payment_result['last_four']
                if idempotency_key:
                    order.idempotency_key = idempotency_key
                
                # Update product stock
                for item in order.items.all():
                    product = item.product
                    if product.stock >= item.quantity:
                        product.stock -= item.quantity
                        product.save()
                    else:
                        # Rollback if insufficient stock
                        raise Exception(f'Insufficient stock for {product.name}')
                
                order.save()
                
                return {
                    'success': True,
                    'transaction_id': payment_result['transaction_id'],
                    'message': 'Payment successful!',
                    'order_id': order.id
                }
            else:
                # Payment failed
                order.payment_status = 'failed'
                order.status = 'failed'
                order.save()
                
                return {
                    'success': False,
                    'errors': payment_result.get('errors', ['Payment processing failed']),
                    'transaction_id': transaction_obj.transaction_id
                }