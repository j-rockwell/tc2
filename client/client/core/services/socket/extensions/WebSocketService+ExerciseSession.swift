extension WebSocketService {
    static func exerciseSessionConfig() -> WebSocketConfig {
        return WebSocketConfig(
            id: "exercise_session",
            endpoint: "/session/ws/",
            requiresAuth: true,
            autoReconnect: true,
            maxReconnectAttempts: 3,
            reconnectDelay: 2.0,
            pingInterval: 30.0,
            connectionTimeout: 10.0,
        )
    }
}
