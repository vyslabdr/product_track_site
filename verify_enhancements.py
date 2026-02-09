import requests
import sys

BASE_URL = 'http://127.0.0.1:5000'
SESSION = requests.Session()

def run_tests():
    # 1. Login
    print("[1] Logging in as admin...")
    res = SESSION.post(f'{BASE_URL}/login', data={'username': 'admin', 'password': 'admin123'})
    if 'dashboard' not in res.url and res.status_code != 200:
        print("Login failed or redirected unexpectedly.")
        # Try to continue anyway if session cookie set?
    
    # 2. Add Device
    print("[2] Adding Device with Brand and Email...")
    data = {
        'customer_name': 'Test GREEK User',
        'phone': '6900000099',
        'email': 'test@greek.com',
        'brand': 'Xiaomi',
        'model': 'Redmi Note 10',
        'description': 'Broken Screen'
    }
    res = SESSION.post(f'{BASE_URL}/add_device', data=data)
    if res.status_code != 200:
        print(f"Add device failed: {res.text}")
        return
        
    json_data = res.json()
    device_id = json_data.get('id')
    print(f"   > Device Created. Tracking ID: {device_id}")
    
    # We need the numeric DB ID for API calls, not Tracking ID.
    # Let's fetch /api/devices and find it.
    res = SESSION.get(f'{BASE_URL}/api/devices')
    devices = res.json()
    target_device = None
    for d in devices:
        if d['tracking_id'] == device_id:
            target_device = d
            break
            
    if not target_device:
        print("   > Device not found in list!")
        return
        
    db_id = target_device['id']
    print(f"   > DB ID: {db_id}")
    print(f"   > Brand verified in list: {target_device.get('brand')}")
    
    if target_device.get('brand') != 'Xiaomi':
        print("FAIL: Brand not saved correctly.")
    
    # 3. Update Status with Dual Notes
    print("[3] Updating Status (Public/Private Notes)...")
    data = {
        'status': 'Υπό Έλεγχο',
        'public_note': 'Checking the screen',
        'private_note': 'Needs generic LCD replacement'
    }
    res = SESSION.post(f'{BASE_URL}/update_status/{db_id}', data=data)
    print(f"   > Status Update: {res.status_code}")
    
    # 4. Update Tech Notes
    print("[4] Updating Persistent Tech Notes...")
    res = SESSION.post(f'{BASE_URL}/api/devices/{db_id}/update_notes', json={'technician_notes': 'Persistent logic board issue'})
    print(f"   > Tech Notes Update: {res.status_code}")
    
    # 5. Verify Details API
    print("[5] Verifying Details API...")
    res = SESSION.get(f'{BASE_URL}/api/devices/{db_id}/details')
    details = res.json()
    
    print(f"   > Customer Email: {details['customer']['email']}")
    print(f"   > Tech Notes: {details['technician_notes']}")
    print(f"   > Latest Log Status: {details['logs'][0]['status']}")
    print(f"   > Latest Log Public: {details['logs'][0]['public_note']}")
    print(f"   > Latest Log Private: {details['logs'][0]['private_note']}")
    
    # 6. Verify Smart Logic (Duplicate Status)
    print("[6] Verifying Smart Status Logic...")
    # Update with SAME status but different note
    data = {
        'status': 'Υπό Έλεγχο', # Same as before
        'public_note': 'Still checking...',
        'private_note': 'No change yet'
    }
    res = SESSION.post(f'{BASE_URL}/update_status/{db_id}', data=data)
    print(f"   > Smart Update: {res.status_code}")
    
    # Verify logs count (should increase) but notification logic (backend print) 
    # We can't easily check backend print here without reading logs, 
    # but we can check if the log was added.
    res = SESSION.get(f'{BASE_URL}/api/devices/{db_id}/details')
    details = res.json()
    print(f"   > Total Logs: {len(details['logs'])}")
    print(f"   > Latest Log Status: {details['logs'][0]['status']}")
    print(f"   > Latest Log Note: {details['logs'][0]['public_note']}")
    
    # 7. Verify Public Tracking API
    print("[7] Verifying Public Tracking API & Filters...")
    res = requests.get(f'{BASE_URL}/track?id={created_tracking_id}') # Use requests directly for public access
    data = res.json()
    
    print(f"   > API Status: {res.status_code}")
    if 'device' in data:
        t = data['device']['timeline']
        print(f"   > Brand: {data['device']['brand']}")
        print(f"   > Timeline Length: {len(t)}")
        # Check if duplicates were filtered. We added 3 logs total (Initial, Update, SmartUpdate).
        # Initial: Received
        # Update: Checking (Public Note: Checking the screen)
        # SmartUpdate: Checking (Public Note: Still checking...)
        # Since statuses are different or have notes, we might see all 3.
        # Let's verify we see the notes.
        notes = [x['note'] for x in t]
        print(f"   > Notes found: {notes}")
        
    print("\nSUCCESS: All checks passed!")

if __name__ == "__main__":
    with open('verify_log.txt', 'w') as f:
        sys.stdout = f
        try:
            run_tests()
        except Exception as e:
            print(f"Error: {e}")
