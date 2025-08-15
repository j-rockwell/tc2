import Foundation
import Combine

@MainActor
class ExerciseSessionManager: ObservableObject {
    let logger = AppLogger(subsystem: "dev.jrockwell.client", category: "esm")
    
    @Published var currentSession: ExerciseSession? = nil
    @Published var currentState: ExerciseSessionState? = nil
    @Published var isLoading = true
    @Published var socketConnectionStatus: WebSocketConnectionState = .disconnected
    @Published var socketConnectionError: String? = nil
    
    private let tokenService: TokenServiceProtocol
    private let networkService: NetworkServiceProtocol
    private let socketService: any WebSocketServiceProtocol
    private var cancellables = Set<AnyCancellable>()
    
    private let connectionId = "exercise_session"
    
    init(
        tokenService: TokenServiceProtocol = TokenService(),
        networkService: NetworkServiceProtocol = NetworkService(),
        socketService: any WebSocketServiceProtocol = WebSocketService()
    ) {
        self.tokenService = tokenService
        self.networkService = networkService
        self.socketService = socketService
        
        setupSocketConnection()
    }
    
    func connectToSocket() async {
        do {
            try await socketService.connect(connectionId)
            logger.info("Connected to Exercise Session Web Socket")
        } catch {
            logger.error("Failed to connect to Web Socket: \(error)")
            socketConnectionError = error.localizedDescription
        }
    }
    
    func disconnectFromSocket() {
        socketService.disconnect(connectionId)
        logger.info("Disconnected from Exercise Session Web Socket")
    }
    
    func createOfflineSession() async {
        logger.info("Creating an offline session...")
        
        isLoading = true
        
        currentSession = ExerciseSession(
            id: "",
            name: "My Workout",
            status: .active,
            ownerId: "",
            createdAt: Date(),
            updatedAt: Date(),
            participants: [],
            invitations: [],
        )
        
        currentState = ExerciseSessionState(
            sessionId: "",
            accountId: "",
            version: 0,
            items: [],
        )
        
        isLoading = false
        
        logger.info("Finished creating an offline session")
    }
    
    func createSession() async {
        logger.info("Creating an online session...")
        
        isLoading = true
        
        do {
            let response = try await withCheckedThrowingContinuation { continuation in
                networkService.createSession()
                    .sink(
                        receiveCompletion: { completion in
                            if case .failure(let error) = completion {
                                continuation.resume(throwing: error)
                            }
                        },
                        receiveValue: { response in
                            continuation.resume(returning: response)
                        }
                    )
                    .store(in: &cancellables)
            }
            
            currentSession = response.session
            
            await connectToSocket()
            
            if let sessionId = currentSession?.id {
                await joinSession(sessionId: sessionId)
            }
        } catch {
            logger.error("Failed to create session: \(error)")
        }
        
        isLoading = false
        
        logger.info("Finished creating an online session")
    }
    
    func joinSession(sessionId: String) async {
        guard socketConnectionStatus == .connected else {
            logger.error("Cannot join session: Web Socket connection is closed")
            return
        }
        
        let message = ExerciseSessionJoinMessage.create(sessionId: sessionId)
        
        do {
            try await socketService.send(message, to: connectionId)
            logger.info("Sent a session join message")
            
            // TODO: Send sync request here
        } catch {
            logger.error("Failed to send a session join message: \(error)")
        }
    }
    
    private func setupSocketConnection() {
        let config = WebSocketService.exerciseSessionConfig()
        socketService.addConnection(config: config)
        
        socketService.observeConnectionStatus(for: connectionId)
            .receive(on: DispatchQueue.main)
            .sink { [weak self] isConnected in
                self?.socketConnectionStatus = isConnected ? .connected : .disconnected
                self?.logger.info("Web Socket connection status: \(isConnected)")
            }
            .store(in: &cancellables)
        
        socketService.observeConnectionState(for: connectionId)
            .receive(on: DispatchQueue.main)
            .sink { [weak self] state in
                switch state {
                case .failed(let error):
                    self?.logger.error("Web Socket connection failed: \(error)")
                case .connected:
                    self?.socketConnectionError = nil
                case .disconnected:
                    self?.socketConnectionError = nil
                default:
                    break
                }
            }
            .store(in: &cancellables)
        
        socketService.subscribe(to: ExerciseSessionMessage.self, on: connectionId)
            .receive(on: DispatchQueue.main)
            .sink { [weak self] message in
                self?.handleIncomingMessage(message)
            }
            .store(in: &cancellables)
    }
    
    // MARK: Session Updates
    func toggleSetComplete(eid: String, sid: String) {
        guard var state = currentState else { return }
        guard let itemIndex = state.items.firstIndex(where: {$0.id == eid}) else { return }
        guard let setIndex = state.items[itemIndex].sets.firstIndex(where: {$0.id == sid}) else { return }
        state.items[itemIndex].sets[setIndex].complete.toggle()
        currentState = state
    }
    
    func reorderSet(eid: String, fromSid: String, toSid: String) {
        guard let state = currentState else { return }
        guard let itemIndex = state.items.firstIndex(where: {$0.id == eid}) else { return }
        guard fromSid != toSid else { return }
        
        var sets = state.items[itemIndex].sets
        
        guard let fromIndex = sets.firstIndex(where: {$0.id == fromSid}) else { return }
        guard let toIndex = sets.firstIndex(where: {$0.id == toSid}) else { return }
        
        let movedSet = sets.remove(at: fromIndex)
        sets.insert(movedSet, at: toIndex)
        currentState = state
    }
    
    func updateSetOrders(eid: String) {
        guard var state = currentState else { return }
        guard let itemIndex = state.items.firstIndex(where: {$0.id == eid}) else { return }
        
        for (index, _) in state.items[itemIndex].sets.enumerated() {
            state.items[itemIndex].sets[index].order = index + 1
        }
        
        currentState = state
    }
    
    func updateExerciseMetrics(exerciseId: String, exerciseSetId: String, metrics: ExerciseSessionStateItemMetric) {
        guard var state = currentState else { return }
        guard let exerciseIndex = state.items.firstIndex(where: {$0.id == exerciseId}) else { return }
        guard let exerciseSetIndex = state.items[exerciseIndex].sets.firstIndex(where: {$0.id == exerciseSetId}) else { return }
        
        state.items[exerciseIndex].sets[exerciseSetIndex].metrics = metrics
        state.version += 1
        currentState = state
        
        if socketConnectionStatus == .connected, let sessionId = currentSession?.id {
            Task {
                // TODO: Send update message
            }
        }
    }
    
    private func handleIncomingMessage(_ message: ExerciseSessionMessage) {
        
    }
}
