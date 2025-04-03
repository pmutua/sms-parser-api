import xml.etree.ElementTree as ET

def parse_sms_xml(xml_content):
    root = ET.fromstring(xml_content)
    sms_list = []
    
    for sms in root.findall('sms'):
        sms_data = {
            'address': sms.get('address'),
            'date': sms.get('date'),
            'type': sms.get('type'),
            'body': sms.get('body'),
            'read': sms.get('read'),
            'status': sms.get('status')
        }
        sms_list.append(sms_data)
    
    return sms_list

