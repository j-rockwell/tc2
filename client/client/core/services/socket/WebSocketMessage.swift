protocol WebSocketMessage: Codable {
    var action: String { get }
}
