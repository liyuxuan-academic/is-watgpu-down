from monitor import check_http, check_ssh, check_ping, URL, SSH_HOST, SSH_PORT

def test_current_status():
    print(f"Checking status for WatGPU...")
    print(f"URL: {URL}")
    print(f"SSH: {SSH_HOST}:{SSH_PORT}")
    print("-" * 30)

    # Check HTTP
    print("Checking HTTP...", end=" ", flush=True)
    http_status = check_http(URL)
    print(f"{'✅ UP' if http_status else '❌ DOWN'}")

    # Check SSH
    print("Checking SSH...", end=" ", flush=True)
    ssh_status = check_ssh(SSH_HOST, SSH_PORT)
    print(f"{'✅ UP' if ssh_status else '❌ DOWN'}")

    # Check Ping
    print("Checking Ping...", end=" ", flush=True)
    ping_status = check_ping(SSH_HOST)
    print(f"{'✅ UP' if ping_status else '❌ DOWN'}")

if __name__ == "__main__":
    test_current_status()

