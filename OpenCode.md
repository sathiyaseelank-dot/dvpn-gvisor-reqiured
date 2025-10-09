# OpenCode Configuration

## Build Commands
- **Android Build**: `./gradlew build` (from android/ or Decentralized-VPN/)
- **Android Debug**: `./gradlew assembleDebug`
- **Android Release**: `./gradlew assembleRelease`
- **Go Build (Firestack)**: `make intra` or `make android` (from firestack/)
- **Clean**: `./gradlew clean` or `make clean`

## Test Commands
- **Unit Tests**: `./gradlew test`
- **Android Tests**: `./gradlew connectedAndroidTest`
- **Single Test**: `./gradlew test --tests "com.example.yankdvpn.ExampleUnitTest"`
- **Go Tests**: `go test ./...` (from firestack/)

## Code Style Guidelines
- **Kotlin**: Use camelCase, explicit types for public APIs, prefer `val` over `var`
- **Imports**: Group Android, third-party, then project imports with blank lines
- **Naming**: Activities end with `Activity`, Services with `Service`, ViewModels with `ViewModel`
- **Error Handling**: Use `try-catch` with specific exceptions, log errors with `Log.e(TAG, message, exception)`
- **Coroutines**: Use `lifecycleScope.launch` for UI operations, `Dispatchers.IO` for network/file operations
- **Go**: Follow standard Go conventions, use `gofmt`, error handling with explicit checks
- **Comments**: Minimal comments, prefer self-documenting code, use KDoc for public APIs