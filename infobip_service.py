import requests
import logging
from models import SystemSetting, NotificationLog, db

class InfobipService:
    @staticmethod
    def send_notification(device, trigger_type='ready'):
        """
        Main entry point for sending notifications.
        Checks active channel and dispatches to appropriate method.
        """
        settings = SystemSetting.query.first()
        if not settings:
            logging.warning("Infobip Warning: No settings found.")
            return False, "No settings"

        # 1. Determine Message Content & Recipient
        # Template selection based on trigger
        template = ""
        if trigger_type == 'registration':
            template = settings.template_registration
        elif trigger_type == 'ready':
            template = settings.template_ready
        elif trigger_type == 'delivered':
            template = settings.template_delivered
        
        if not template:
            return False, "No template"

        try:
            message_text = template.format(
                customer_name=device.customer.name,
                model=device.model,
                tracking_id=device.tracking_id,
                status=device.status
            )
        except Exception as e:
            logging.error(f"Infobip Template Error: {e}")
            message_text = template # Fallback

        # Normalize Phone (Greece Default)
        phone = device.customer.phone.replace(" ", "")
        if not phone.startswith("+"):
            phone = "+30" + phone if not phone.startswith("00") else "+" + phone.lstrip("00")

        # 2. Dispatch based on Active Channel
        channel = settings.active_channel # sms, whatsapp, viber
        success = False
        error_msg = None

        if channel == 'sms':
            success, error_msg = InfobipService._send_sms(settings, phone, message_text)
        elif channel == 'whatsapp':
            success, error_msg = InfobipService._send_whatsapp(settings, phone, device)
        elif channel == 'viber':
            success, error_msg = InfobipService._send_viber(settings, phone, message_text)
        else:
            return False, f"Unknown channel: {channel}"

        # 3. Log Result
        log_status = 'SENT' if success else 'FAILED'
        log_msg = message_text if success else f"Err: {error_msg}"
        
        try:
            log = NotificationLog(
                device_id=device.id,
                channel=channel.upper(),
                status=log_status,
                message_content=log_msg
            )
            db.session.add(log)
            db.session.commit()
        except Exception as e:
            logging.error(f"Logging Error: {e}")

        return success, error_msg

    @staticmethod
    def _send_sms(settings, phone, text):
        if not settings.infobip_api_key_sms or not settings.infobip_base_url_sms:
            return False, "SMS Credentials missing"

        url = f"https://{settings.infobip_base_url_sms}/sms/2/text/advanced"
        headers = {
            'Authorization': f'App {settings.infobip_api_key_sms}',
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        payload = {
            "messages": [
                {
                    "destinations": [{"to": phone}],
                    "from": settings.infobip_sender_id_sms or "InfoSMS",
                    "text": text
                }
            ]
        }
        
        try:
            response = requests.post(url, json=payload, headers=headers)
            if response.status_code == 200:
                return True, None
            return False, f"HTTP {response.status_code}: {response.text}"
        except Exception as e:
            return False, str(e)

    @staticmethod
    def _send_whatsapp(settings, phone, device):
        """
        Sends WhatsApp Template Message (Infobip).
        Adapted to use 'test_whatsapp_template_en' with customer name placeholder.
        """
        if not settings.infobip_api_key_wa or not settings.infobip_base_url_wa:
            return False, "WhatsApp Credentials missing"

        # Construct URL (User provided "jrd1e4.api.infobip.com" -> https://jrd1e4.api.infobip.com/whatsapp/1/message/template)
        # We use strict base_url from settings to allow flexibility.
        url = f"https://{settings.infobip_base_url_wa}/whatsapp/1/message/template"
        
        headers = {
            'Authorization': f'App {settings.infobip_api_key_wa}',
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        
        # User defined template: "test_whatsapp_template_en"
        # Placeholder: Customer Name
        customer_name = device.customer.name.upper() if device.customer and device.customer.name else "CUSTOMER"

        payload = {
            "messages": [
                {
                    "from": settings.infobip_number_wa,
                    "to": phone,
                    "content": {
                        "templateName": "test_whatsapp_template_en", 
                        "templateData": {
                            "body": {
                                "placeholders": [customer_name]
                            }
                        },
                        "language": "en"
                    }
                }
            ]
        }

        try:
            response = requests.post(url, json=payload, headers=headers)
            # 200 OK means received by Infobip
            if response.status_code == 200:
                return True, None
            return False, f"HTTP {response.status_code}: {response.text}"
        except Exception as e:
            return False, f"Request Error: {str(e)}"

    @staticmethod
    def _send_viber(settings, phone, text):
        if not settings.infobip_api_key_viber or not settings.infobip_base_url_viber:
            return False, "Viber Credentials missing"
            
        url = f"https://{settings.infobip_base_url_viber}/viber/1/message/text"
        headers = {
            'Authorization': f'App {settings.infobip_api_key_viber}',
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        payload = {
            "from": settings.infobip_sender_viber,
            "to": phone,
            "content": {"text": text}
        }

        try:
            response = requests.post(url, json=payload, headers=headers)
            if response.status_code == 200:
                return True, None
            return False, f"HTTP {response.status_code}: {response.text}"
        except Exception as e:
            return False, str(e)
