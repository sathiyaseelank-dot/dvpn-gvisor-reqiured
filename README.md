# gVisor-Based VPN Application

This application implements a comprehensive VPN solution using Google's gVisor userspace network stack. The implementation provides a secure, high-performance tunnel with advanced networking capabilities.

## Architecture Overview

### Core Components

1. **Firestack Library (Go)**
   - Complete gVisor netstack integration
   - TCP/UDP/ICMP protocol handling
   - DNS resolution with DoH/DoT support
   - Connection tracking and management
   - Packet filtering and routing

2. **Android VPN Service (Kotlin)**
   - Android VPN service implementation
   - TUN interface management
   - Socket protection for tunnel traffic
   - Foreground service with notifications

3. **Bridge Interface**
   - Communication bridge between Go and Android
   - Traffic flow monitoring
   - DNS query/response handling
   - Connection lifecycle management

## gVisor Integration Details

### Netstack Features
- **User-space TCP/IP stack**: Complete network protocol implementation in userspace
- **Protocol support**: IPv4/IPv6, TCP, UDP, ICMP
- **Connection tracking**: Full connection state management
- **Packet filtering**: Advanced traffic analysis and filtering
- **DNS handling**: Built-in secure DNS resolution

### Network Configuration
```
IPv4: 10.111.222.1/24 (Interface) -> 10.111.222.3 (DNS)
IPv6: fd66:f83a:c650::1/120 (Interface) -> fd66:f83a:c650::3 (DNS)
MTU: 1500 bytes
Routes: 0.0.0.0/0, ::/0 (All traffic)
```

### Performance Optimizations
- **Experimental features enabled**: Including WireGuard support
- **Endpoint-independent mapping/filtering**: Transparent NAT behavior
- **Loopback handling**: Support for local connections
- **Memory optimization**: Tuned garbage collection and memory limits
- **Concurrent processing**: Multi-threaded packet handling

## Building and Installation

### Prerequisites
- Go 1.21+ 
- Android SDK with NDK
- Java 11+
- Android device with API level 24+

### Build Process
```bash
# Make the setup script executable and run it
chmod +x setup_gvisor.sh
./setup_gvisor.sh
```

Or manually:
```bash
# Build the firestack library
cd firestack
make intradebug

# Copy AAR to Android project
cp build/intra/tun2socks-debug.aar ../android/app/libs/tun2socks.aar

# Build Android app
cd ../android
./gradlew assembleDebug
```

### Installation
```bash
# Install on connected Android device
adb install android/app/build/outputs/apk/debug/app-debug.apk
```

## Usage

1. **Launch the app** on your Android device
2. **Grant VPN permission** when prompted
3. **Tap "Start gVisor VPN"** to activate the tunnel
4. **Monitor connection** via notification and logs

## Monitoring and Debugging

### Logcat Monitoring
```bash
# Monitor VPN service logs
adb logcat -s MyVpnService:* MyVpnBridge:*

# Monitor gVisor netstack logs
adb logcat | grep -E "(gVisor|netstack|Firestack)"

# Monitor all VPN related logs
adb logcat -s VPN:*
```

### Connection Status
The app provides real-time connection information including:
- Tunnel status (connected/disconnected)
- Traffic statistics (bytes sent/received)
- Active connections count
- DNS query statistics
- Protocol distribution (TCP/UDP/ICMP)

## Advanced Configuration

### DNS Configuration
The implementation supports various DNS configurations:
- **Built-in resolver**: System DNS with privacy enhancements
- **DoH/DoT support**: Secure DNS over HTTPS/TLS
- **Custom resolvers**: Configure specific DNS servers
- **DNS filtering**: Block unwanted domains

### Traffic Management
- **Flow control**: Monitor and control traffic flows
- **Connection tracking**: Track all network connections
- **Protocol filtering**: Filter by protocol type
- **Bandwidth monitoring**: Track data usage

### Security Features
- **Process isolation**: Each connection runs in isolation
- **Socket protection**: Prevent tunnel traffic loops
- **DNS privacy**: Encrypted DNS queries
- **Traffic encryption**: All tunnel traffic is protected

## Troubleshooting

### Common Issues

1. **VPN Permission Denied**
   - Ensure the app has VPN permission in Android settings
   - Try restarting the app and granting permission again

2. **Connection Fails**
   - Check Android logs for specific error messages
   - Verify network connectivity
   - Ensure TUN interface creation succeeds

3. **Poor Performance**
   - Monitor memory usage and adjust limits if needed
   - Check for high CPU usage in logs
   - Verify MTU settings are appropriate

### Debug Builds vs Production
- **Debug builds** include verbose logging and debugging symbols
- **Production builds** are optimized for performance and size
- Use `make intra` for production builds instead of `make intradebug`

## Development Notes

### Code Structure
```
firestack/
├── intra/              # Core gVisor integration
│   ├── netstack/       # Network stack implementation  
│   ├── tunnel/         # Tunnel management
│   └── backend/        # Backend interfaces
android/
└── app/src/main/java/com/example/vpnapp/
    ├── MyVpnService.kt     # VPN service implementation
    ├── MyVpnBridge.kt      # Go-Android bridge
    └── MainActivity.kt     # UI and permissions
```

### Key Dependencies
- `gvisor.dev/gvisor`: Core gVisor netstack
- `golang.org/x/sys`: System call interface
- `golang.org/x/net`: Network utilities
- Android VpnService API

### Extension Points
The implementation provides several extension points for customization:
- **DNS resolvers**: Add custom DNS providers
- **Traffic filters**: Implement custom filtering logic
- **Proxy support**: Add proxy server integration
- **Protocol handlers**: Extend protocol support

## License
This implementation builds upon the Firestack project and includes components from gVisor, both of which have their respective open-source licenses.