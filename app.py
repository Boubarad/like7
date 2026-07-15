def load_accounts(server_name):
    """Load accounts from text file"""
    try:
        if server_name == "IND":
            filename = "account.ind.txt"
        elif server_name in {"BR", "US", "SAC", "NA"}:
            filename = "account.br.txt"
        elif server_name == "ME":
            filename = "account.me.txt"
        else:
            filename = "account.bd.txt"
        
        accounts = []
        if os.path.exists(filename):
            with open(filename, "r") as f:
                for line in f:
                    line = line.strip()
                    if ':' in line:
                        uid, password = line.split(':', 1)
                        accounts.append({"uid": uid.strip(), "password": password.strip()})
        return accounts
    except Exception as e:
        app.logger.error(f"Error loading accounts for {server_name}: {e}")
        return []

def save_tokens(server_name, tokens):
    """Save tokens to JSON file"""
    try:
        if server_name == "IND":
            filename = "token_ind.json"
        elif server_name in {"BR", "US", "SAC", "NA"}:
            filename = "token_br.json"
        elif server_name == "ME":
            filename = "token_me.json"
        else:
            filename = "token_bd.json"
        
        with open(filename, "w") as f:
            json.dump(tokens, f, indent=2)
        return True
    except Exception as e:
        app.logger.error(f"Error saving tokens for {server_name}: {e}")
        return False

def load_tokens(server_name):
    """Load tokens with auto-refresh if needed"""
    try:
        # Check if cache is valid
        if server_name in TOKEN_CACHE and server_name in TOKEN_CACHE_TIME:
            time_diff = (datetime.now() - TOKEN_CACHE_TIME[server_name]).total_seconds()
            if time_diff < TOKEN_REFRESH_INTERVAL:
                return TOKEN_CACHE[server_name]
        
        # Try to load from file
        if server_name == "IND":
            filename = "token_ind.json"
        elif server_name in {"BR", "US", "SAC", "NA"}:
            filename = "token_br.json"
        elif server_name == "ME":
            filename = "token_me.json"
        else:
            filename = "token_bd.json"
        
        if os.path.exists(filename):
            with open(filename, "r") as f:
                tokens = json.load(f)
                # Update cache
                TOKEN_CACHE[server_name] = tokens
                TOKEN_CACHE_TIME[server_name] = datetime.now()
                return tokens
        
        # If file doesn't exist, generate new tokens
        app.logger.info(f"No token file found for {server_name}, generating new tokens...")
        if refresh_tokens_for_server(server_name):
            return load_tokens(server_name)
        
        return None
    except Exception as e:
        app.logger.error(f"Error loading tokens for server {server_name}: {e}")
        return None

def auto_refresh_tokens():
    """Background thread to automatically refresh tokens"""
    while True:
        try:
            servers = ["IND", "BR", "US", "SAC", "NA", "BD", "ME"]
            for server in servers:
                app.logger.info(f"Auto-refreshing tokens for {server}...")
                refresh_tokens_for_server(server)
                time.sleep(5)  # Small delay between servers
            app.logger.info("Token refresh cycle completed. Next refresh in 2 hours.")
            time.sleep(TOKEN_REFRESH_INTERVAL)
        except Exception as e:
            app.logger.error(f"Error in auto_refresh_tokens: {e}")
            time.sleep(300)  # Wait 5 minutes on error

def make_request(encrypt, server_name, token):
    try:
        if server_name == "IND":
            url = "https://client.ind.freefiremobile.com/GetPlayerPersonalShow"
        elif server_name in {"BR", "US", "SAC", "NA"}:
            url = "https://client.us.freefiremobile.com/GetPlayerPersonalShow"
        elif server_name == "ME":
            url = "https://clientbp.ggpolarbear.com/GetPlayerPersonalShow"
        else:
            url = "https://clientbp.ggpolarbear.com/GetPlayerPersonalShow"
        edata = bytes.fromhex(encrypt)
        headers = {
            'User-Agent': "Dalvik/2.1.0 (Linux; U; Android 9; ASUS_Z01QD Build/PI)",
            'Connection': "Keep-Alive",
            'Accept-Encoding': "gzip",
            'Authorization': f"Bearer {token}",
            'Content-Type': "application/x-www-form-urlencoded",
            'Expect': "100-continue",
            'X-Unity-Version': "2018.4.11f1",
            'X-GA': "v1 1",
            'ReleaseVersion': "OB54"
        }
        response = requests.post(url, data=edata, headers=headers, verify=False)
        hex_data = response.content.hex()
        binary = bytes.fromhex(hex_data)
        decode = decode_protobuf(binary)
        if decode is None:
            app.logger.error("Protobuf decoding returned None.")
        return decode
    except Exception as e:
        app.logger.error(f"Error in make_request: {e}")
        return None

if server_name == "IND":
    url = "https://client.ind.freefiremobile.com/LikeProfile"
elif server_name in {"BR", "US", "SAC", "NA"}:
    url = "https://client.us.freefiremobile.com/LikeProfile"
elif server_name == "ME":
    url = "https://clientbp.ggpolarbear.com/LikeProfile"
else:
    url = "https://clientbp.ggpolarbear.com/LikeProfile"

@app.route('/token_status', methods=['GET'])
def token_status():
    """Check token status for all servers"""
    servers = ["IND", "BR", "US", "SAC", "NA", "BD", "ME"]
    status = {}
    for server in servers:
        tokens = load_tokens(server)
        if tokens:
            status[server] = {
                "count": len(tokens),
                "last_refresh": TOKEN_CACHE_TIME.get(server, "Never").isoformat() if server in TOKEN_CACHE_TIME else "Never"
            }
        else:
            status[server] = {"count": 0, "status": "No tokens found"}
    return jsonify(status)

if __name__ == '__main__':
    # Start auto-refresh thread
    refresh_thread = threading.Thread(target=auto_refresh_tokens, daemon=True)
    refresh_thread.start()
    app.logger.info("Auto-token refresher started. Tokens will be refreshed every 2 hours.")
    
    app.run(debug=True, use_reloader=False, host='0.0.0.0', port=5000)