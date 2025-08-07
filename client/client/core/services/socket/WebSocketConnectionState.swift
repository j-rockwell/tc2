import Foundation

enum WebSocketConnectionState: Equatable {
    case disconnected
    case connecting
    case connected
    case reconnecting
    case failed(Error)
    
    static func == (lhs: WebSocketConnectionState, rhs: WebSocketConnectionState) -> Bool {
        switch (lhs, rhs) {
            case (.disconnected, .disconnected),
                 (.connecting, .connecting),
                 (.connected, .connected),
                 (.reconnecting, .reconnecting):
                return true
            case (.failed(let lhsError), .failed(let rhsError)):
                return lhsError.localizedDescription == rhsError.localizedDescription
            default:
                return false
        }
    }
}
