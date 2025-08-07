import Foundation
import Combine

protocol WebSocketServiceProtocol: ObservableObject {
    func addConnection(config: WebSocketConfig)
    func removeConnection(_ connectionId: String)
    func connect(_ connectionId: String) async throws
    func connectAll() async
    func disconnect(_ connectionId: String)
    func disconnectAll()
    func send<T: WebSocketMessage>(_ message: T, to connectionId: String) async throws
    func subscribe<T: Codable>(to messageType: T.Type, on connectionId: String) -> AnyPublisher<T, Never>
    func isConnected(_ connectionId: String) -> Bool
    func observeConnectionState(for connectionId: String) -> AnyPublisher<WebSocketConnectionState, Never>
    func observeConnectionStatus(for connectionId: String) -> AnyPublisher<Bool, Never>
}

class WebSocketService: WebSocketServiceProtocol {
    private let logger = AppLogger(subsystem: "dev.jrockwell.client", category: "websocket")
    
    @Published private(set) var connections: [String: WebSocketConnection]
    
    private let tokenService: TokenServiceProtocol
    private let urlSession: URLSession
    private let baseURL: URL
    private var cancellables = Set<AnyCancellable>()
    
    init(
        baseURL: URL = NetworkConfig.baseUrl,
        tokenService: TokenServiceProtocol = TokenService(),
        urlSession: URLSession = .shared
    ) {
        self.baseURL = baseURL
        self.tokenService = tokenService
        self.urlSession = urlSession
        self.connections = [:]
        self.cancellables = Set<AnyCancellable>()
        
        logger.info("WebSocketService::init")
    }
    
    deinit {
        cancellables.removeAll()
    }
    
    func addConnection(config: WebSocketConfig) {
        guard connections[config.id] == nil else {
            logger.warning("Connection with ID '\(config.id)' already exists")
            return
        }
        
        let connection = WebSocketConnection(
            config: config,
            tokenService: tokenService,
            urlSession: urlSession,
            logger: logger
        )
        
        connections[config.id] = connection
        logger.info("Added Web Socket connection: \(config.id)")
    }
    
    func removeConnection(_ connectionId: String) {
        if let connection = connections[connectionId] {
            connection.disconnect()
            connections.removeValue(forKey: connectionId)
            logger.info("Removed Web Socket connection: \(connectionId)")
        }
    }
    
    func connect(_ connectionId: String) async throws {
        guard let connection = connections[connectionId] else {
            throw WebSocketError.connectionNotFound(connectionId)
        }
        
        try await connection.connect(baseURL: baseURL)
    }
    
    func connectAll() async {
        for (id, connection) in connections {
            do {
                try await connection.connect(baseURL: baseURL)
            } catch {
                logger.error("Failed to connect \(id): \(error)")
            }
        }
    }
    
    func disconnect(_ connectionId: String) {
        connections[connectionId]?.disconnect()
    }
    
    func disconnectAll() {
        for connection in connections.values {
            connection.disconnect()
        }
    }
    
    func send<T: WebSocketMessage>(_ message: T, to connectionId: String) async throws {
        guard let connection = connections[connectionId] else {
            throw WebSocketError.connectionNotFound(connectionId)
        }
        
        try await connection.send(message)
    }
    
    func subscribe<T: Codable>(to messageType: T.Type, on connectionId: String) -> AnyPublisher<T, Never> {
        guard let connection = connections[connectionId] else {
            logger.error("Cannot subscribe: connection '\(connectionId)' not found")
            return Empty().eraseToAnyPublisher()
        }
        
        return connection.subscribe(to: messageType)
    }
    
    func observeConnectionState(for connectionId: String) -> AnyPublisher<WebSocketConnectionState, Never> {
        guard let connection = connections[connectionId] else {
            return Just(.disconnected).eraseToAnyPublisher()
        }
        
        return connection.$connectionState.eraseToAnyPublisher()
    }
    
    func observeConnectionStatus(for connectionId: String) -> AnyPublisher<Bool, Never> {
        guard let connection = connections[connectionId] else {
            return Just(false).eraseToAnyPublisher()
        }
        
        return connection.$isConnected.eraseToAnyPublisher()
    }
    
    func isConnected(_ connectionId: String) -> Bool {
        return connections[connectionId]?.isConnected ?? false
    }
    
    func getConnectionState(_ connectionId: String) -> WebSocketConnectionState {
        return connections[connectionId]?.connectionState ?? .disconnected
    }
    
    func getAllConnectionStates() -> [String: WebSocketConnectionState] {
        return connections.mapValues { $0.connectionState }
    }
    
    private func reconnectAuthenticatedConnections() async {
        for (id, connection) in connections where connection.config.requiresAuth && connection.isConnected {
            logger.info("Reconnecting authenticated connection: \(id)")
            connection.disconnect()
            
            try? await Task.sleep(nanoseconds: 500_000_000)
            
            do {
                try await connection.connect(baseURL: baseURL)
            } catch {
                logger.error("Failed to reconnect \(id) after token refresh: \(error)")
            }
        }
    }
}
