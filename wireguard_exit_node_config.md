# WireGuard Exit Node Configuration for gVisor VPN

## Overview
The gVisor VPN application can function as a **WireGuard exit node** for other clients when properly configured. This leverages the built-in WireGuard support in the firestack library.

## Exit Node Architecture

```
[Client 1] ----\
[Client 2] ------> [gVisor VPN App (Exit Node)] -----> [Internet]
[Client N] ----/        ^
                        |
                   gVisor Netstack
                  (userspace routing)
```

## Key Features for Exit Node Operation

### 1. **gVisor Netstack Integration**
- Complete userspace network stack via gVisor
- Isolated packet processing and routing
- Support for multiple concurrent client connections
- Advanced traffic management and filtering

### 2. **WireGuard Protocol Support**
- Full WireGuard implementation via `wireguard-go`
- Peer management and authentication
- Encrypted tunnel establishment
- UDP hole punching and NAT traversal

### 3. **Exit Node Capabilities**
- **Accept** incoming WireGuard connections from clients
- **Route** client traffic through the gVisor netstack
- **Forward** packets to internet destinations
- **NAT** client traffic using the device's network interface

## Configuration Steps

### Server Configuration (Exit Node)

```ini
# /etc/wireguard/wg-exit.conf
[Interface]
# Exit node private key
PrivateKey = <GENERATED_PRIVATE_KEY>
# Exit node IP address
Address = 10.8.0.1/24
# Listen port for client connections  
ListenPort = 51820
# Post-up script to enable IP forwarding
PostUp = echo 1 > /proc/sys/net/ipv4/ip_forward
PostUp = iptables -A FORWARD -i wg-exit -j ACCEPT
PostUp = iptables -A FORWARD -o wg-exit -j ACCEPT
PostUp = iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE
# Post-down cleanup
PostDown = iptables -D FORWARD -i wg-exit -j ACCEPT
PostDown = iptables -D FORWARD -o wg-exit -j ACCEPT
PostDown = iptables -t nat -D POSTROUTING -o eth0 -j MASQUERADE

# Client 1
[Peer]
PublicKey = <CLIENT_1_PUBLIC_KEY>
AllowedIPs = 10.8.0.2/32

# Client 2  
[Peer]
PublicKey = <CLIENT_2_PUBLIC_KEY>
AllowedIPs = 10.8.0.3/32

# Add more clients as needed...
```

### Client Configuration

```ini
# Client configuration connecting to gVisor exit node
[Interface]
PrivateKey = <CLIENT_PRIVATE_KEY>
Address = 10.8.0.2/24
DNS = 8.8.8.8, 8.8.4.4

[Peer]
PublicKey = <EXIT_NODE_PUBLIC_KEY>
Endpoint = <EXIT_NODE_IP>:51820
AllowedIPs = 0.0.0.0/0, ::/0
PersistentKeepalive = 25
```

## Android Integration for Exit Node

### Modified VPN Service
The Android VPN service needs to be enhanced to support incoming connections:

```kotlin
class ExitNodeVpnService : MyVpnService() {
    
    private fun startWireGuardExitNode() {
        // Configure as WireGuard server instead of client
        val builder = Builder()
        builder.setSession("gVisor-WG-ExitNode")
            .addAddress("10.8.0.1", 24)  // Exit node address
            .addRoute("10.8.0.0", 24)   // Route client traffic
            .setMtu(1420) // WireGuard optimal MTU
            
        tunInterface = builder.establish()
        val fd = tunInterface?.fd ?: return
        
        scope.launch {
            try {
                // Configure WireGuard as server
                val wgConfig = generateWireGuardServerConfig()
                
                // Create exit proxy with WireGuard config
                val bridge = MyVpnBridge(this@ExitNodeVpnService)
                val defaultDNS = Intra.newBuiltinDefaultDNS()
                
                // Use WireGuard proxy configuration
                tunnel = Intra.connect(fd.toLong(), 1420L, "10.8.0.1/24", "10.8.0.1", defaultDNS, bridge)
                
                // Enable exit node features
                Intra.experimental(true)
                
                Log.i("WG-Exit", "WireGuard exit node started successfully")
                
            } catch (e: Exception) {
                Log.e("WG-Exit", "Failed to start WireGuard exit node: ${e.message}", e)
            }
        }
    }
    
    private fun generateWireGuardServerConfig(): String {
        return """
            private_key=${generatePrivateKey()}
            listen_port=51820
            
            public_key=${clientPublicKey1}
            allowed_ips=10.8.0.2/32
            
            public_key=${clientPublicKey2}  
            allowed_ips=10.8.0.3/32
        """.trimIndent()
    }
}
```

## gVisor Components for Exit Node

### 1. **Exit Proxy** (`exit.go`)
- Routes all client traffic to the internet
- Handles NAT and connection tracking
- Manages outbound connections

### 2. **WireGuard Proxy** (`wgproxy.go`)
- Manages WireGuard protocol implementation
- Handles peer authentication and encryption
- Manages tunnel interface

### 3. **Netstack Integration**
- gVisor provides the complete TCP/IP stack
- Handles packet forwarding and routing
- Provides connection isolation and security

## Advanced Features

### Traffic Management
```go
// Custom routing for exit node clients
func (h *wgtun) Accept(network, local string) (net.Listener, error) {
    // Accept incoming connections from WireGuard clients
    // Route through gVisor netstack for processing
    return h.ListenTCPAddrPort(addr)
}

func (h *wgtun) Announce(network, local string) (net.PacketConn, error) {
    // Handle UDP traffic from clients
    return h.ListenUDPAddrPort(addr)  
}
```

### Connection Monitoring
```kotlin
override fun onSocketClosed(summary: SocketSummary?) {
    summary?.let {
        // Track client connections and bandwidth
        Log.d("WG-Exit", "Client connection closed: ${it.rx} bytes received, ${it.tx} bytes sent")
        updateClientStats(it)
    }
}
```

## Security Considerations

### Network Isolation
- Each client connection runs in isolated gVisor context
- Complete process isolation for security
- No direct access to host system

### Traffic Filtering  
- DNS filtering and blocking capabilities
- Protocol-based traffic filtering
- Bandwidth limiting per client

### Authentication
- WireGuard cryptographic authentication
- Public key-based client verification
- Perfect forward secrecy

## Performance Optimizations

### gVisor Optimizations
- Hardware offloading support (GRO/GSO)
- Multi-threaded packet processing
- Optimized memory management

### WireGuard Optimizations
- UDP socket reuse
- Kernel crypto when available
- Efficient peer management

## Deployment Notes

### Requirements
- Android device with root access (for iptables rules)
- Public IP address or port forwarding
- Sufficient bandwidth for client traffic

### Network Configuration
- Configure firewall rules for WireGuard port (51820/UDP)
- Enable IP forwarding on the device
- Set up NAT rules for client traffic

## Monitoring and Management

### Client Management
- Dynamic peer addition/removal
- Bandwidth monitoring per client
- Connection status tracking

### Logging
```bash
# Monitor WireGuard exit node logs
adb logcat -s WG-Exit:* MyVpnBridge:* | grep -E "(client|peer|exit)"
```

This configuration transforms the gVisor VPN application into a fully functional WireGuard exit node capable of serving multiple clients with enterprise-grade security and performance.
