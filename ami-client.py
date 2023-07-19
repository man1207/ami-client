import asterisk.manager
import argparse
import sys
import time
import os
import signal
import re
import xml.etree.ElementTree as ET

parser = argparse.ArgumentParser(description='Process ami-client parameters')
parser.add_argument('--login', type=str, required=True, help='Login for ami-client')
parser.add_argument('--secret', type=str, required=True, help='Secret for ami-client')
parser.add_argument('--asteriskip', type=str, required=True, help='IP address for Asterisk')
parser.add_argument('--config', type=str, required=True, help='Path to the config file')
parser.add_argument('--debug', action='store_true', help='Enable debug mode')

args = parser.parse_args()

debug = args.debug
username = args.login
secret = args.secret
asteriskip = args.asteriskip
config = args.config

def load_events_from_xml(xml_file):
    tree = ET.parse(xml_file)
    root = tree.getroot()

    event_groups = []
    for group in root.findall('group'):
        event_group = []
        for event in group.findall('event'):
            event_data = {}
            event_data['name'] = event.get('name')
            event_data['checked'] = False
            event_data['type'] = event.get('type')
            event_data['data'] = {k: v for k, v in event.find('data').attrib.items()}
            event_data['regex_fields'] = [field.text for field in event.find('regex_fields').findall('field')]
            event_group.append(event_data)
        event_groups.append(event_group)

    return event_groups

event_groups = load_events_from_xml(config)

current_group = 0

def check_events():
    global current_group
    return current_group == len(event_groups)

def proceed_event(event):
    global event_groups, current_group
    if current_group < len(event_groups):
        for item in event_groups[current_group]:
            if item["type"].lower() == event.name.lower():
                checked = True
                for header, value in item["data"].items():
                    event_header_value = event.get_header(header)
                    if header in item["regex_fields"]:
                        if not re.match(value, event_header_value, re.IGNORECASE):
                            checked = False
                            break
                    else:  
                        if not event_header_value.lower() == value.lower():
                            checked = False
                            break
                if checked:
                    item["checked"] = True
                    print("Event checked: {}".format(item["data"]))
                    if all(item["checked"] for item in event_groups[current_group]):
                        current_group += 1

def handle_sigterm(*args):
    raise KeyboardInterrupt()

def event_notification(event, manager):
    global events
    if (debug):
        print("Event received: {}".format(event.name))
    proceed_event(event)

def handle_shutdown(event, manager):
    if (debug):
        print("Event received: {}".format(event.name))
    manager.close()

signal.signal(signal.SIGTERM, handle_sigterm)

manager = asterisk.manager.Manager()
try:
    try:
        manager.connect(asteriskip)
        manager.login(username, secret)
        manager.register_event('Shutdown', handle_shutdown)
        manager.register_event('*', event_notification)

        while not check_events():
            time.sleep(1)

        manager.logoff()
    except asterisk.manager.ManagerSocketException as e:
        print("Error connecting to manager: {}".format(e))
    except asterisk.manager.ManagerAuthException as e:
        print("Error logging to manager: {}".format(e))
    except asterisk.manager.ManagerException as e:
        print("Error: {}".format(e))
except (KeyboardInterrupt, SystemExit):
    manager.close()
