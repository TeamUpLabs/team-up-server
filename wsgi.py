from main import app
import uvicorn
from fastapi.middleware.wsgi import WSGIMiddleware
import socket
import requests

# This is for running with gunicorn
application = WSGIMiddleware(app)

# Function to get public IP address
def get_public_ip():
    try:
        return requests.get('https://api.ipify.org').text
    except:
        return "Could not determine public IP"

# Function to get local IP addresses
def get_local_ips():
    hostname = socket.gethostname()
    local_ips = []
    try:
        # Get all local IP addresses
        for ip in socket.gethostbyname_ex(hostname)[2]:
            if not ip.startswith("127."):
                local_ips.append(ip)
    except:
        pass
    
    # Add localhost
    local_ips.append("127.0.0.1")
    return local_ips

# This is for local development
if __name__ == "__main__":
    public_ip = get_public_ip()
    local_ips = get_local_ips()
    
    print("\n==== Server Access Information ====")
    print(f"Public IP (for external access): http://{public_ip}:8000")
    print("\nLocal IPs (for internal network):")
    for ip in local_ips:
        print(f"http://{ip}:8000")
    print("\nAPI Documentation: http://<server-ip>:8000/docs")
    print("================================\n")
    
    uvicorn.run("main:app", host="0.0.0.0", port=8000) 