import os
import socket
import csv
import json
import urllib.request
from datetime import datetime

OPENMES_URL = "http://192.168.40.1"
OPENMES_TOKEN = os.getenv("OPENMES_TOKEN")

if not OPENMES_TOKEN:
    raise RuntimeError("OPENMES_TOKEN environment variable is not set.")
WORK_ORDER_ID = 222

request = urllib.request.Request(
    f"{OPENMES_URL}/api/v1/work-orders/{WORK_ORDER_ID}",
    headers={
        "Accept": "application/json",
        "Authorization": f"Bearer {OPENMES_TOKEN}"
    }
)

with urllib.request.urlopen(request, timeout=5) as response:
    mes_data = json.load(response)["data"]

work_orders = {
    mes_data["order_no"]: {
        "product": mes_data["product_type"]["name"],
        "target_qty": mes_data["planned_qty"],
        "current_qty": mes_data["produced_qty"],
        "status": mes_data["status"]
    }
}

monitor_request = urllib.request.Request(
    f"{OPENMES_URL}/api/v1/machine-monitor",
    headers={
        "Accept": "application/json",
        "Authorization": f"Bearer {OPENMES_TOKEN}"
    }
)

with urllib.request.urlopen(monitor_request, timeout=5) as response:
    monitor_tiles = json.load(response)["data"]["tiles"]

machine = next(tile for tile in monitor_tiles if tile["id"] == 2)

runtime_request = urllib.request.Request(
    f"{OPENMES_URL}/api/v1/machine-connections/1/runtime",
    headers={
        "Accept": "application/json",
        "Authorization": f"Bearer {OPENMES_TOKEN}"
    }
)

with urllib.request.urlopen(runtime_request, timeout=5) as response:
    runtime = json.load(response)["data"]

communication = "HEALTHY" if runtime["alive"] else "HEARTBEAT LOST"
machine_state = machine["state"] if runtime["alive"] else "UNKNOWN"
good_display = machine["good"] if runtime["alive"] else f'{machine["good"]} (last known)'
reject_display = machine["reject"] if runtime["alive"] else f'{machine["reject"]} (last known)'

print("=== Shop-Floor Integration Lab ===")
print()

print("Available Work Orders:")
for wo, data in work_orders.items():
    print(f"{wo} | {data['product']} | Target Qty: {data['target_qty']}")

print()

selected_wo = input("Select Work Order: ").strip()

if selected_wo not in work_orders:
    print("ERROR: Work Order not found.")
    exit()

product = work_orders[selected_wo]["product"]

print()
print("Work Order Started")
print(f"WO: {selected_wo}")
print(f"Product: {product}")
print(f"Target Qty: {work_orders[selected_wo]['target_qty']}")
print(f"Current Qty: {work_orders[selected_wo]['current_qty']}")
print(f"Status: {work_orders[selected_wo]['status']}")
print()
print("Machine Status")
print(f"Machine: {machine['name']}")
print(f"Communication: {communication}")
print(f"State: {machine_state}")
print(f"Good: {good_display}")
print(f"Reject: {reject_display}")
print()

serial = input("Scan Product Serial Number: ").strip()

duplicate = False

with open("production_log.csv", "r", encoding="utf-8") as file:
    reader = csv.DictReader(file)

    for row in reader:
        if row["serial"] == serial:
            duplicate = True
            break

if duplicate:
    print(f"ERROR: Duplicate Serial Number: {serial}")
    exit()

print()
print(f"Serial detected: {serial}")

test_result = input("Test Result [PASS/FAIL]: ").strip().upper()

if test_result not in ["PASS", "FAIL"]:
    print("ERROR: Invalid test result.")
    exit()

with open("production_log.csv", "a", newline="", encoding="utf-8") as file:
    writer = csv.writer(file)
    writer.writerow([
        selected_wo,
        serial,
        test_result,
        datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ])

print()

if test_result == "PASS":
    print("Product accepted as GOOD.")
    print("Production record saved to CSV.")

    label = f"""
************************************
*** THIS IS PRINTER SIMULATION ****
************************************

Shop-Floor Integration Lab

Product: {product}
Work Order: {selected_wo}
Serial: {serial}

************************************
*********** TEST USE ONLY **********
************************************
"""

    with open("label.zpl", "w") as file:
        file.write(label)

    print("Printer simulation file generated: label.zpl")

    PRINTER_HOST = "127.0.0.1"
    PRINTER_PORT = 9100

    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as printer:
            printer.connect((PRINTER_HOST, PRINTER_PORT))

            with open("label.zpl", "rb") as file:
                printer.sendall(file.read())

        print(f"Print job sent to {PRINTER_HOST}:{PRINTER_PORT}")

    except ConnectionRefusedError:
        print("ERROR: Printer connection refused.")

    except Exception as error:
        print(f"ERROR: Printer communication failed: {error}")


else:
    print("Product marked as REJECT / HOLD.")
    print("Production record saved to CSV.")
    print("Label printing blocked.")
