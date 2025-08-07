import Foundation

struct WebSocketConfig {
    let id: String
    let endpoint: String
    let requiresAuth: Bool
    let autoReconnect: Bool
    let maxReconnectAttempts: Int
    let reconnectDelay: TimeInterval
    let pingInterval: TimeInterval
    let connectionTimeout: TimeInterval
    let customHeaders: [String: String]
    
    init(
        id: String,
        endpoint: String,
        requiresAuth: Bool = true,
        autoReconnect: Bool = true,
        maxReconnectAttempts: Int = 5,
        reconnectDelay: TimeInterval = 2.0,
        pingInterval: TimeInterval = 30.0,
        connectionTimeout: TimeInterval = 10.0,
        customHeaders: [String: String] = [:]
    ) {
        self.id = id
        self.endpoint = endpoint
        self.requiresAuth = requiresAuth
        self.autoReconnect = autoReconnect
        self.maxReconnectAttempts = maxReconnectAttempts
        self.reconnectDelay = reconnectDelay
        self.pingInterval = pingInterval
        self.connectionTimeout = connectionTimeout
        self.customHeaders = customHeaders
    }
}
