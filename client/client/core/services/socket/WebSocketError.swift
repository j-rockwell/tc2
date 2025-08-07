import Foundation

enum WebSocketError: Error, LocalizedError {
    case invalidURL
    case connectionFailed
    case disconnected
    case authenticationRequired
    case encodingError(Error)
    case decodingError(Error)
    case serverError(String)
    case timeout
    case unauthorized
    case sessionExpired
    case connectionNotFound(String)
    
    var errorDescription: String? {
        switch self {
        case .invalidURL:
            return "Invalid WebSocket URL"
        case .connectionFailed:
            return "Failed to connect to WebSocket"
        case .disconnected:
            return "WebSocket disconnected"
        case .authenticationRequired:
            return "Authentication required"
        case .encodingError(let error):
            return "Encoding error: \(error.localizedDescription)"
        case .decodingError(let error):
            return "Decoding error: \(error.localizedDescription)"
        case .serverError(let message):
            return "Server error: \(message)"
        case .timeout:
            return "WebSocket connection timeout"
        case .unauthorized:
            return "Unauthorized access"
        case .sessionExpired:
            return "Session expired"
        case .connectionNotFound(let id):
            return "WebSocket connection not found: \(id)"
        }
    }
}
