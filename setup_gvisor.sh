#!/bin/bash

# gVisor-based VPN Application Setup Script
# This script ensures the gVisor implementation is properly configured and optimized

set -e

echo "🚀 Setting up gVisor VPN Application..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check dependencies
print_status "Checking dependencies..."

if ! command -v go &> /dev/null; then
    print_error "Go is not installed. Please install Go 1.21+ first."
    exit 1
fi

if ! command -v java &> /dev/null; then
    print_error "Java is not installed. Please install Java 11+ first."
    exit 1
fi

# Check Android SDK
if [ -z "$ANDROID_HOME" ]; then
    print_warning "ANDROID_HOME is not set. Android builds may fail."
else
    print_success "Android SDK found at: $ANDROID_HOME"
fi

print_success "Dependencies check completed"

# Build gVisor-enabled firestack library
print_status "Building gVisor-enabled firestack library..."
cd firestack

# Clean previous builds
make clean || true

# Build the debug version with full gVisor support
print_status "Building firestack AAR with gVisor netstack..."
make intradebug

if [ -f "build/intra/tun2socks-debug.aar" ]; then
    print_success "Firestack AAR built successfully"
    
    # Copy to Android app
    print_status "Copying AAR to Android app..."
    mkdir -p ../android/app/libs
    cp build/intra/tun2socks-debug.aar ../android/app/libs/tun2socks.aar
    print_success "AAR copied to Android app"
else
    print_error "Failed to build firestack AAR"
    exit 1
fi

cd ..

# Build Android VPN application
print_status "Building Android VPN application with gVisor integration..."
cd android

# Clean and build
./gradlew clean
./gradlew assembleDebug

if [ -f "app/build/outputs/apk/debug/app-debug.apk" ]; then
    print_success "Android APK built successfully"
    print_status "APK location: android/app/build/outputs/apk/debug/app-debug.apk"
else
    print_error "Failed to build Android APK"
    exit 1
fi

cd ..

# Create gVisor configuration summary
print_status "Creating gVisor configuration summary..."

cat > gvisor_config_summary.md << EOF
# gVisor VPN Application Configuration Summary

## Application Overview
This application implements a full-featured VPN using Google's gVisor userspace network stack, providing:

### 🔧 gVisor Features Enabled:
- **Netstack**: Complete userspace TCP/IP stack implementation
- **Dual Stack**: IPv4 and IPv6 support (10.111.222.0/24 and fd66:f83a:c650::/120)
- **Protocol Support**: TCP, UDP, ICMP handling through gVisor
- **DNS Resolution**: Built-in DNS with DoH/DoT support
- **Socket Protection**: Android VPN socket bypass for tunnel traffic
- **Connection Tracking**: Full connection state management
- **Packet Filtering**: Traffic analysis and filtering capabilities

### 🚀 Performance Optimizations:
- **Experimental Features**: WireGuard support enabled
- **Transparency**: Endpoint-independent mapping and filtering
- **Loopback Handling**: Local connection support
- **Memory Management**: Optimized garbage collection and limits
- **Multi-threading**: Concurrent packet processing

### 📱 Android Integration:
- **VPN Service**: Proper Android VPN service implementation
- **Foreground Service**: Persistent VPN connection with notifications
- **Permission Handling**: Seamless VPN permission management
- **Bridge Interface**: Complete firestack bridge implementation

### 🔒 Security Features:
- **Traffic Isolation**: Complete network isolation through gVisor
- **DNS Privacy**: Secure DNS resolution
- **Connection Protection**: Socket-level protection
- **Process Isolation**: Sandboxed network operations

## Usage Instructions:

1. **Install the APK**: Install the built APK on your Android device
2. **Grant Permissions**: Allow VPN permission when prompted
3. **Start VPN**: Tap "Start gVisor VPN" to activate the tunnel
4. **Monitor**: Check logcat for detailed gVisor operation logs

## Files Modified:
- \`firestack/\`: Enhanced gVisor netstack implementation
- \`android/app/src/main/java/com/example/vpnapp/MyVpnService.kt\`: VPN service with gVisor integration
- \`android/app/src/main/java/com/example/vpnapp/MyVpnBridge.kt\`: Comprehensive bridge implementation
- \`android/app/src/main/AndroidManifest.xml\`: VPN permissions and service declaration

## gVisor Version: v0.0.0-20250816201027-ba3b9ca85f20

Built on: $(date)
EOF

print_success "Configuration summary created: gvisor_config_summary.md"

# Final status
print_success "🎉 gVisor VPN Application setup completed successfully!"
echo ""
print_status "Next steps:"
echo "  1. Install the APK: adb install android/app/build/outputs/apk/debug/app-debug.apk"
echo "  2. Enable VPN permission in the app"
echo "  3. Monitor logs: adb logcat -s VPN-Bridge:* MyVpnBridge:* MyVpnService:*"
echo ""
print_warning "Note: This is a debug build. For production, use 'make intra' instead of 'make intradebug'"