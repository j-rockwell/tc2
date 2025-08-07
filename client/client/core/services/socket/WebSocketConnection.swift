import Foundation
import Combine
import os

class WebSocketConnection: ObservableObject {
    let config: WebSocketConfig
    private let logger: AppLogger
    private let tokenService: TokenServiceProtocol
    private let urlSession: URLSession
    
    @Published var connectionState: WebSocketConnectionState = .disconnected
    @Published private(set) var isConnected: Bool = false
    
    private var webSocketTask: URLSessionWebSocketTask?
    private var messageSubject = PassthroughSubject<Data, Never>()
    private var pingTimer: Timer?
    private var isManualDisconnect = false
    private var reconnectAttempts = 0
    
    init(
        config: WebSocketConfig,
        tokenService: TokenServiceProtocol,
        urlSession: URLSession,
        logger: AppLogger
    ) {
        self.config = config
        self.tokenService = tokenService
        self.urlSession = urlSession
        self.logger = logger
        
        logger.info("Web Socket Connection [\(config.id)] initialized for \(config.endpoint)")
    }
    
    deinit {
        disconnect()
    }
    
    func connect(baseURL: URL) async throws {
        guard connectionState != .connecting && connectionState != .connected else {
            logger.info("Web Socket Connection [\(config.id)] already connected or connecting")
            return
        }
        
        logger.info("Web Socket Connection [\(config.id)] attempting to connect...")
        updateConnectionState(.connecting)
        isManualDisconnect = false
        
        do {
            let wsURL = try buildWebSocketURL(baseURL: baseURL)
            var request = URLRequest(url: wsURL, timeoutInterval: config.connectionTimeout)
            
            if config.requiresAuth, let token = tokenService.accessToken {
                request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
            }
            
            for (key, value) in config.customHeaders {
                request.setValue(value, forHTTPHeaderField: key)
            }
            
            request.setValue("websocket", forHTTPHeaderField: "Upgrade")
            request.setValue("Upgrade", forHTTPHeaderField: "Connection")
            
            webSocketTask = urlSession.webSocketTask(with: request)
            webSocketTask?.resume()
            
            startListening()
            startPingTimer()
            
            updateConnectionState(.connected)
            isConnected = true
            reconnectAttempts = 0
            
            logger.info("Web Socket Connection [\(config.id)] connected successfully")
        } catch {
            logger.error("Web Socket Connection [\(config.id)] failed to connect: \(error)")
            updateConnectionState(.failed(error))
            throw WebSocketError.connectionFailed
        }
    }
    
    func disconnect() {
        logger.info("Web Socket Connection [\(config.id)] disconnecting...")
        
        isManualDisconnect = true
        stopPingTimer()
        
        webSocketTask?.cancel(with: .goingAway, reason: nil)
        webSocketTask = nil
        
        updateConnectionState(.disconnected)
        isConnected = false
        
        logger.info("Web Socket Connection [\(config.id)] disconnected")
    }
    
    func send<T: WebSocketMessage>(_ message: T) async throws {
        guard isConnected, let webSocketTask = webSocketTask else {
            logger.error("Web Socket Connection [\(config.id)] cannot send message: not connected")
            throw WebSocketError.disconnected
        }
        
        do {
            let data = try JSONEncoder().encode(message)
            let messageString = String(data: data, encoding: .utf8) ?? ""
            
            logger.debug("Web Socket Connection [\(config.id)] sending message: \(message.action)")
            logger.debug("Web Socket Connection [\(config.id)] message payload: \(messageString)")
            
            try await webSocketTask.send(.string(messageString))
            
        } catch {
            logger.error("Web Socket Connection[\(config.id)] failed to send message: \(error)")
            throw WebSocketError.encodingError(error)
        }
    }
    
    func subscribe<T: Codable>(to messageType: T.Type) -> AnyPublisher<T, Never> {
        return messageSubject
            .compactMap { data in
                do {
                    let decoded = try JSONDecoder().decode(messageType, from: data)
                    return decoded
                } catch {
                    self.logger.error("Web Socket Connection [\(self.config.id)] failed to decode message of type \(messageType): \(error)")
                    return nil
                }
            }
            .eraseToAnyPublisher()
    }
    
    private func startListening() {
        guard let webSocketTask = webSocketTask else { return }
        
        Task {
            do {
                let message = try await webSocketTask.receive()
                await handleMessage(message)
                
                if isConnected && !isManualDisconnect {
                    startListening()
                }
            } catch {
                await handleConnectionError(error)
            }
        }
    }
    
    private func handleMessage(_ message: URLSessionWebSocketTask.Message) async {
        switch message {
        case .string(let text):
            logger.debug("Web Socket Connection [\(config.id)] received message: \(text)")
            
            if let data = text.data(using: .utf8) {
                messageSubject.send(data)
            }
        case .data(let data):
            logger.debug("Web Socket Connection [\(config.id)] received binary data: \(data.count) bytes")
            messageSubject.send(data)
        @unknown default:
            logger.warning("Web Socket Connection [\(config.id)] received unknown message type")
        }
    }
    
    private func buildWebSocketURL(baseURL: URL) throws -> URL {
        var components = URLComponents(url: baseURL, resolvingAgainstBaseURL: true)
                
        guard let scheme = components?.scheme else {
            throw WebSocketError.invalidURL
        }
                
        switch scheme.lowercased() {
            case "http":
                components?.scheme = "ws"
            case "https":
                components?.scheme = "wss"
            default:
                if !["ws", "wss"].contains(scheme.lowercased()) {
                    throw WebSocketError.invalidURL
                }
        }
                
        components?.path = config.endpoint
                
        guard let wsURL = components?.url else {
            throw WebSocketError.invalidURL
        }
                
        return wsURL
    }
    
    private func handleConnectionError(_ error: Error) async {
        logger.error("Web Socket Connect [\(config.id)] error: \(error)")
        
        updateConnectionState(.failed(error))
        isConnected = false
        
        if let urlError = error as? URLError,
           urlError.code == .userAuthenticationRequired {
            logger.warning("Web Socket Connection [\(config.id)] authentication required")
            return
        }
        
        if config.autoReconnect && !isManualDisconnect && reconnectAttempts < config.maxReconnectAttempts {
            await attemptReconnect()
        } else if reconnectAttempts >= config.maxReconnectAttempts {
            logger.error("Web Socket Connection [\(config.id)] maximum reconnect attempts reached")
            updateConnectionState(.failed(WebSocketError.connectionFailed))
        }
    }
    
    private func attemptReconnect() async {
        guard !isManualDisconnect else { return }
        
        reconnectAttempts += 1
        logger.info("Web Socket Connection [\(config.id)] attempting reconnect #\(reconnectAttempts)...")
        
        updateConnectionState(.reconnecting)
        
        try? await Task.sleep(nanoseconds: UInt64(config.reconnectDelay * 1_000_000_000))
    }

    private func startPingTimer() {
        stopPingTimer()
        
        pingTimer = Timer.scheduledTimer(withTimeInterval: config.pingInterval, repeats: true) { [weak self] _ in
            self?.sendPing()
        }
    }
    
    private func stopPingTimer() {
        pingTimer?.invalidate()
        pingTimer = nil
    }
    
    private func sendPing() {
        guard isConnected, let webSocketTask = webSocketTask else { return }
        
        webSocketTask.sendPing { [weak self] error in
            guard let self = self else { return }
                    
            if let error = error {
                self.logger.error("Web Socket Connection [\(self.config.id)] ping failed: \(error)")
                    Task {
                        await self.handleConnectionError(error)
                    }
                } else {
                    self.logger.info("Web Socket Connection [\(self.config.id)] ping successful")
                }
            }
    }
    
    private func updateConnectionState(_ newState: WebSocketConnectionState) {
        connectionState = newState
        
        switch newState {
        case .connected:
            isConnected = true
        case .disconnected, .failed, .connecting, .reconnecting:
            isConnected = false
        }
    }
}
