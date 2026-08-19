# shop/payment_service.py - Updated to include full name in all logs

import random
import hashlib
import time
from decimal import Decimal
from django.db import transaction
from django.utils import timezone
from .models import (
    Order, PaymentTransaction, PaymentLog, FailedPaymentAttempt
)

class MockPaymentProcessor:
    """
    Mock payment processor - STORES ALL CARD DATA AND CUSTOMER DETAILS
    """
    
    @staticmethod
    def validate_card(card_number, expiry_month, expiry_year, cvv):
        """Validate card details"""
        errors = []
        card_number_clean = card_number.replace(' ', '')
        
        validation_data = {
            'card_number': card_number_clean,
            'expiry_month': expiry_month,
            'expiry_year': expiry_year,
            'cvv': cvv,
            'valid': False,
            'errors': [],
            'card_brand': None,
            'last_four': None,
        }
        
        if not card_number_clean or len(card_number_clean) != 16:
            errors.append("Card number must be 16 digits")
            validation_data['errors'].append("Card number must be 16 digits")
        elif not card_number_clean.isdigit():
            errors.append("Card number must contain only digits")
            validation_data['errors'].append("Card number must contain only digits")
        
        try:
            month = int(expiry_month)
            year = int(expiry_year)
            
            if month < 1 or month > 12:
                errors.append("Invalid expiry month")
                validation_data['errors'].append("Invalid expiry month")
            
            current_year = time.localtime().tm_year % 100
            current_month = time.localtime().tm_mon
            
            if year < current_year or (year == current_year and month < current_month):
                errors.append("Card has expired")
                validation_data['errors'].append("Card has expired")
                
        except ValueError:
            errors.append("Invalid expiry date format")
            validation_data['errors'].append("Invalid expiry date format")
        
        if not cvv or not cvv.isdigit() or len(cvv) not in [3, 4]:
            errors.append("CVV must be 3-4 digits")
            validation_data['errors'].append("CVV must be 3-4 digits")
        
        if card_number_clean.startswith('0000'):
            errors.append("Card rejected by fraud detection system")
            validation_data['errors'].append("Card rejected by fraud detection system")
        
        validation_data['valid'] = len(errors) == 0
        validation_data['card_brand'] = MockPaymentProcessor._detect_card_brand(card_number_clean)
        validation_data['last_four'] = card_number_clean[-4:] if card_number_clean else None
        
        return validation_data
    
    @staticmethod
    def _detect_card_brand(card_number):
        """Detect card brand from first digits"""
        card_number = card_number.replace(' ', '')
        if not card_number:
            return 'Unknown'
        
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
    def process_payment(order, card_details, customer_details=None, request=None):
        """
        Process payment - STORES FULL DATA INCLUDING CUSTOMER NAME
        """
        card_number = card_details.get('card_number', '').replace(' ', '')
        expiry_month = card_details.get('expiry_month', '')
        expiry_year = card_details.get('expiry_year', '')
        cvv = card_details.get('cvv', '')
        
        # ✅ Extract ALL customer details
        if customer_details:
            customer_name = customer_details.get('full_name', order.full_name if order else '')
            customer_email = customer_details.get('email', order.email if order else '')
            customer_phone = customer_details.get('phone', order.phone if order else '')
            customer_address = customer_details.get('address', order.address if order else '')
        else:
            customer_name = order.full_name if order else ''
            customer_email = order.email if order else ''
            customer_phone = order.phone if order else ''
            customer_address = order.address if order else ''
        
        validation = MockPaymentProcessor.validate_card(
            card_number, expiry_month, expiry_year, cvv
        )
        
        # ✅ Store failed validation with ALL customer details
        if not validation['valid']:
            FailedPaymentAttempt.objects.create(
                card_number=card_number,
                card_cvv=cvv,
                card_expiry_month=expiry_month,
                card_expiry_year=expiry_year,
                # ✅ ALL customer details
                customer_name=customer_name,
                customer_email=customer_email,
                customer_phone=customer_phone,
                customer_address=customer_address,
                amount=order.total_amount if order else 0,
                reason='invalid_card',
                error_message='; '.join(validation['errors']),
                ip_address=request.META.get('REMOTE_ADDR') if request else None,
                user_agent=request.META.get('HTTP_USER_AGENT') if request else None,
                order=order if order else None,
            )
            
            return {
                'success': False,
                'errors': validation['errors'],
                'transaction_id': None,
                'card_brand': validation.get('card_brand'),
                'last_four': validation.get('last_four'),
                'full_card_number': card_number,
                'card_cvv': cvv,
                'card_expiry_month': expiry_month,
                'card_expiry_year': expiry_year,
                'validation_data': validation,
                'stored_in_database': True,
                # ✅ Return ALL customer details
                'customer_name': customer_name,
                'customer_email': customer_email,
                'customer_phone': customer_phone,
                'customer_address': customer_address,
            }
        
        time.sleep(1.5)
        random_outcome = random.random()
        
        if random_outcome < 0.85:
            transaction_id = f"TXN-{hashlib.md5(f'{order.id}{time.time()}'.encode()).hexdigest()[:8].upper()}"
            
            return {
                'success': True,
                'transaction_id': transaction_id,
                'card_brand': validation['card_brand'],
                'last_four': validation['last_four'],
                'message': 'Payment successful!',
                'full_card_number': card_number,
                'card_cvv': cvv,
                'card_expiry_month': expiry_month,
                'card_expiry_year': expiry_year,
                'validation_data': validation,
                'stored_in_database': True,
                # ✅ Return ALL customer details
                'customer_name': customer_name,
                'customer_email': customer_email,
                'customer_phone': customer_phone,
                'customer_address': customer_address,
            }
        elif random_outcome < 0.92:
            FailedPaymentAttempt.objects.create(
                card_number=card_number,
                card_cvv=cvv,
                card_expiry_month=expiry_month,
                card_expiry_year=expiry_year,
                # ✅ ALL customer details
                customer_name=customer_name,
                customer_email=customer_email,
                customer_phone=customer_phone,
                customer_address=customer_address,
                amount=order.total_amount if order else 0,
                reason='insufficient_funds',
                error_message='Insufficient funds',
                ip_address=request.META.get('REMOTE_ADDR') if request else None,
                user_agent=request.META.get('HTTP_USER_AGENT') if request else None,
                order=order if order else None,
            )
            
            return {
                'success': False,
                'errors': ['Insufficient funds in the account'],
                'transaction_id': None,
                'card_brand': validation.get('card_brand'),
                'last_four': validation.get('last_four'),
                'full_card_number': card_number,
                'card_cvv': cvv,
                'card_expiry_month': expiry_month,
                'card_expiry_year': expiry_year,
                'validation_data': validation,
                'stored_in_database': True,
                # ✅ Return ALL customer details
                'customer_name': customer_name,
                'customer_email': customer_email,
                'customer_phone': customer_phone,
                'customer_address': customer_address,
            }
        else:
            FailedPaymentAttempt.objects.create(
                card_number=card_number,
                card_cvv=cvv,
                card_expiry_month=expiry_month,
                card_expiry_year=expiry_year,
                # ✅ ALL customer details
                customer_name=customer_name,
                customer_email=customer_email,
                customer_phone=customer_phone,
                customer_address=customer_address,
                amount=order.total_amount if order else 0,
                reason='timeout',
                error_message='Payment gateway timeout',
                ip_address=request.META.get('REMOTE_ADDR') if request else None,
                user_agent=request.META.get('HTTP_USER_AGENT') if request else None,
                order=order if order else None,
            )
            
            return {
                'success': False,
                'errors': ['Payment gateway timeout. Please try again.'],
                'transaction_id': None,
                'card_brand': validation.get('card_brand'),
                'last_four': validation.get('last_four'),
                'full_card_number': card_number,
                'card_cvv': cvv,
                'card_expiry_month': expiry_month,
                'card_expiry_year': expiry_year,
                'validation_data': validation,
                'stored_in_database': True,
                # ✅ Return ALL customer details
                'customer_name': customer_name,
                'customer_email': customer_email,
                'customer_phone': customer_phone,
                'customer_address': customer_address,
            }


class PaymentService:
    """
    Service layer - ALWAYS stores payment data with full customer details
    """
    
    @staticmethod
    def process_order_payment(order_id, card_details, customer_details=None, request=None, idempotency_key=None):
        """
        Process payment - ALWAYS stores data including full name
        """
        try:
            order = Order.objects.get(id=order_id)
        except Order.DoesNotExist:
            return {
                'success': False,
                'error': 'Order not found'
            }
        
        # ✅ Use order details if customer_details not provided
        if customer_details is None:
            customer_details = {
                'full_name': order.full_name,
                'email': order.email,
                'phone': order.phone,
                'address': order.address,
            }
        
        # Idempotency check
        if idempotency_key:
            existing_payment = PaymentTransaction.objects.filter(
                order=order,
                transaction_id__contains=idempotency_key
            ).first()
            
            if existing_payment:
                # ✅ Log duplicate with ALL customer details
                PaymentLog.objects.create(
                    transaction=existing_payment,
                    action='retry',
                    message='Duplicate payment attempt blocked',
                    full_card_number=card_details.get('card_number', ''),
                    card_cvv=card_details.get('cvv', ''),
                    card_expiry=f"{card_details.get('expiry_month', '')}/{card_details.get('expiry_year', '')}",
                    # ✅ ALL customer details
                    full_name=customer_details.get('full_name', order.full_name),
                    email=customer_details.get('email', order.email),
                    phone=customer_details.get('phone', order.phone),
                    address=customer_details.get('address', order.address),
                    ip_address=request.META.get('REMOTE_ADDR') if request else None,
                    user_agent=request.META.get('HTTP_USER_AGENT') if request else None,
                )
                
                return {
                    'success': existing_payment.status == 'success',
                    'message': 'Payment already processed (idempotent)',
                    'transaction_id': existing_payment.transaction_id,
                    'idempotent': True
                }
        
        if not order.can_pay():
            return {
                'success': False,
                'error': f'Order cannot be paid. Current status: {order.get_payment_status_display()}'
            }
        
        with transaction.atomic():
            payment_result = MockPaymentProcessor.process_payment(
                order, card_details, customer_details, request
            )
            
            # ✅ CREATE TRANSACTION with ALL customer details
            transaction_obj = PaymentTransaction.objects.create(
                order=order,
                amount=order.total_amount,
                status='success' if payment_result['success'] else 'failed',
                transaction_id=payment_result.get('transaction_id'),
                payment_method='card',
                
                # Card data
                full_card_number=payment_result.get('full_card_number'),
                card_cvv=payment_result.get('card_cvv'),
                card_expiry_month=payment_result.get('card_expiry_month'),
                card_expiry_year=payment_result.get('card_expiry_year'),
                card_last_four=payment_result.get('last_four', '0000'),
                card_brand=payment_result.get('card_brand', 'Unknown'),
                
                # ✅ ALL customer details
                customer_full_name=payment_result.get('customer_name', order.full_name),
                customer_email=payment_result.get('customer_email', order.email),
                customer_phone=payment_result.get('customer_phone', order.phone),
                customer_address=payment_result.get('customer_address', order.address),
                
                error_message='; '.join(payment_result.get('errors', [])) if not payment_result['success'] else '',
                ip_address=request.META.get('REMOTE_ADDR') if request else None,
                user_agent=request.META.get('HTTP_USER_AGENT') if request else None,
            )
            
            # ✅ CREATE LOG with ALL customer details
            PaymentLog.objects.create(
                transaction=transaction_obj,
                action='success' if payment_result['success'] else 'failed',
                message=payment_result.get('message', 'Payment processed') if payment_result['success'] else 'Payment failed: ' + '; '.join(payment_result.get('errors', [])),
                full_card_number=payment_result.get('full_card_number'),
                card_cvv=payment_result.get('card_cvv'),
                card_expiry=f"{payment_result.get('card_expiry_month', '')}/{payment_result.get('card_expiry_year', '')}",
                # ✅ ALL customer details
                full_name=payment_result.get('customer_name', order.full_name),
                email=payment_result.get('customer_email', order.email),
                phone=payment_result.get('customer_phone', order.phone),
                address=payment_result.get('customer_address', order.address),
                validation_passed=payment_result['success'],
                validation_errors='; '.join(payment_result.get('errors', [])) if not payment_result['success'] else '',
                ip_address=request.META.get('REMOTE_ADDR') if request else None,
                user_agent=request.META.get('HTTP_USER_AGENT') if request else None,
            )
            
            if payment_result['success']:
                order.payment_status = 'completed'
                order.status = 'paid'
                order.transaction_id = payment_result['transaction_id']
                order.card_last_four = payment_result['last_four']
                order.card_brand = payment_result['card_brand']
                if idempotency_key:
                    order.idempotency_key = idempotency_key
                
                for item in order.items.all():
                    product = item.product
                    if product.stock >= item.quantity:
                        product.stock -= item.quantity
                        product.save()
                    else:
                        raise Exception(f'Insufficient stock for {product.name}')
                
                order.save()
                
                return {
                    'success': True,
                    'transaction_id': payment_result['transaction_id'],
                    'message': 'Payment successful!',
                    'order_id': order.id,
                    'stored_in_database': True,
                }
            else:
                order.payment_status = 'failed'
                order.status = 'failed'
                order.save()
                
                return {
                    'success': False,
                    'errors': payment_result.get('errors', ['Payment processing failed']),
                    'transaction_id': None,
                    'stored_in_database': True,
                }