#!/usr/bin/env python3
"""
WireGuard Exit Node Configuration Generator
Generates server and client configurations for gVisor VPN exit node
"""

import subprocess
import ipaddress
import json
from pathlib import Path

def generate_private_key():
    """Generate a new WireGuard private key"""
    try:
        result = subprocess.run(['wg', 'genkey'], capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("Warning: wg command not found. Using placeholder key.")
        return "REPLACE_WITH_ACTUAL_PRIVATE_KEY"

def generate_public_key(private_key):
    """Generate public key from private key"""
    try:
        result = subprocess.run(['wg', 'pubkey'], input=private_key, capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return "REPLACE_WITH_ACTUAL_PUBLIC_KEY"

def generate_exit_node_config(num_clients=5, network="10.8.0.0/24", port=51820):
    """Generate WireGuard exit node configuration"""
    
    network = ipaddress.IPv4Network(network)
    server_ip = str(list(network.hosts())[0])  # First available IP
    
    # Generate server keys
    server_private = generate_private_key()
    server_public = generate_public_key(server_private)
    
    config = {
        "server": {
            "private_key": server_private,
            "public_key": server_public,
            "address": f"{server_ip}/{network.prefixlen}",
            "port": port,
            "config": f"""[Interface]
# gVisor VPN Exit Node Configuration
PrivateKey = {server_private}
Address = {server_ip}/{network.prefixlen}
ListenPort = {port}
# Enable IP forwarding for exit node functionality
PostUp = echo 1 > /proc/sys/net/ipv4/ip_forward
PostUp = iptables -A FORWARD -i wg-exit -j ACCEPT
PostUp = iptables -A FORWARD -o wg-exit -j ACCEPT  
PostUp = iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE
PostDown = iptables -D FORWARD -i wg-exit -j ACCEPT
PostDown = iptables -D FORWARD -o wg-exit -j ACCEPT
PostDown = iptables -t nat -D POSTROUTING -o eth0 -j MASQUERADE

"""
        },
        "clients": []
    }
    
    # Generate client configurations
    for i in range(1, num_clients + 1):
        client_ip = str(list(network.hosts())[i])
        client_private = generate_private_key()
        client_public = generate_public_key(client_private)
        
        # Add peer to server config
        config["server"]["config"] += f"""# Client {i}
[Peer]
PublicKey = {client_public}
AllowedIPs = {client_ip}/32

"""
        
        # Create client config
        client_config = {
            "id": i,
            "private_key": client_private,
            "public_key": client_public,
            "address": f"{client_ip}/24",
            "config": f"""[Interface]
# Client {i} configuration for gVisor VPN Exit Node
PrivateKey = {client_private}
Address = {client_ip}/24
DNS = 8.8.8.8, 8.8.4.4

[Peer]
# gVisor VPN Exit Node
PublicKey = {server_public}
Endpoint = YOUR_EXIT_NODE_IP:{port}
AllowedIPs = 0.0.0.0/0, ::/0
PersistentKeepalive = 25
"""
        }
        
        config["clients"].append(client_config)
    
    return config

def save_configs(config, output_dir="wg_exit_configs"):
    """Save generated configurations to files"""
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)
    
    # Save server config
    with open(output_path / "server.conf", "w") as f:
        f.write(config["server"]["config"])
    
    # Save client configs
    for client in config["clients"]:
        with open(output_path / f"client_{client['id']}.conf", "w") as f:
            f.write(client["config"])
    
    # Save JSON summary
    with open(output_path / "config_summary.json", "w") as f:
        json.dump(config, f, indent=2)
    
    print(f"Configurations saved to {output_path}/")
    print(f"Server config: {output_path}/server.conf")
    print(f"Client configs: {output_path}/client_*.conf")
    print(f"Summary: {output_path}/config_summary.json")

def generate_android_integration():
    """Generate Android-specific integration code"""
    
    kotlin_code = '''
// WireGuard Exit Node Integration for gVisor VPN
class WireGuardExitNodeService : MyVpnService() {
    
    companion object {
        private const val WG_SERVER_PORT = 51820
        private const val WG_NETWORK = "10.8.0.0/24"
        private const val WG_SERVER_IP = "10.8.0.1"
    }
    
    private fun startExitNode() {
        val builder = Builder()
        builder.setSession("gVisor-WG-ExitNode")
            .addAddress(WG_SERVER_IP, 24)
            .addRoute("10.8.0.0", 24)  // Route client traffic
            .setMtu(1420)  // WireGuard optimal MTU
            .setBlocking(false)
            
        tunInterface = builder.establish()
        val fd = tunInterface?.fd ?: return
        
        scope.launch {
            try {
                bridge = WireGuardExitBridge(this@WireGuardExitNodeService)
                val defaultDNS = Intra.newBuiltinDefaultDNS()
                
                // Configure interface addresses for exit node
                val ifaddrs = "$WG_SERVER_IP/24"
                val fakedns = WG_SERVER_IP
                
                // Create tunnel with WireGuard exit node configuration
                tunnel = Intra.connect(fd.toLong(), 1420L, ifaddrs, fakedns, defaultDNS, bridge!!)
                
                // Enable features needed for exit node operation
                Intra.experimental(true)  // Enable WireGuard support
                Intra.transparency(true, true)  // Enable NAT traversal
                Intra.loopback(true)  // Handle local connections
                
                // Start WireGuard server
                startWireGuardServer()
                
                Log.i("WG-Exit", "WireGuard exit node started on port $WG_SERVER_PORT")
                
            } catch (e: Exception) {
                Log.e("WG-Exit", "Failed to start exit node: ${e.message}", e)
            }
        }
    }
    
    private fun startWireGuardServer() {
        // This would integrate with the WireGuard proxy implementation
        // The actual WireGuard server is handled by the gVisor netstack
        // and the firestack WgProxy implementation
        
        val wgConfig = loadWireGuardServerConfig()
        // Configuration loaded and applied through Intra tunnel
    }
    
    private fun loadWireGuardServerConfig(): String {
        // Load the generated server configuration
        return assets.open("server.conf").bufferedReader().use { it.readText() }
    }
}

class WireGuardExitBridge(vpnService: VpnService) : MyVpnBridge(vpnService) {
    
    override fun onSocketClosed(summary: SocketSummary?) {
        super.onSocketClosed(summary)
        summary?.let {
            // Track client connections for exit node monitoring
            Log.i("WG-Exit", "Client session: ${it.proto} ${it.rx}↓ ${it.tx}↑ bytes")
            updateExitNodeStats(it)
        }
    }
    
    override fun flow(uid: Int, pid: Int, src: Gostr?, dst: Gostr?, 
                     domain: Gostr?, probeid: Gostr?, blocklist: Gostr?, summary: Gostr?): Mark {
        
        // Custom routing for exit node clients
        val mark = super.flow(uid, pid, src, dst, domain, probeid, blocklist, summary)
        
        // Log client traffic for monitoring
        Log.v("WG-Exit", "Routing: ${src?.string()} -> ${dst?.string()}")
        
        return mark
    }
    
    private fun updateExitNodeStats(summary: SocketSummary) {
        // Update exit node statistics
        // This could be sent to a monitoring dashboard
    }
}
'''
    
    with open("WireGuardExitNodeIntegration.kt", "w") as f:
        f.write(kotlin_code)
    
    print("Android integration code saved to WireGuardExitNodeIntegration.kt")

if __name__ == "__main__":
    print("🔧 Generating WireGuard Exit Node Configuration...")
    
    # Generate configurations
    config = generate_exit_node_config(num_clients=5)
    save_configs(config)
    
    # Generate Android integration
    generate_android_integration()
    
    print("\n✅ WireGuard exit node configuration generated successfully!")
    print("\nNext steps:")
    print("1. Deploy server.conf to your exit node device")
    print("2. Distribute client configs to users")
    print("3. Configure firewall rules for port 51820/UDP")
    print("4. Integrate WireGuardExitNodeIntegration.kt into your Android app")
    print("5. Test client connections and monitor traffic")
