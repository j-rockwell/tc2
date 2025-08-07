extension WebSocketService {
    static func exerciseSessionConfig() -> WebSocketConfig {
        return WebSocketConfig(
            id: "session",
            endpoint: "/session/channel",
            requiresAuth: true,
            autoReconnect: true
        )
    }
}
