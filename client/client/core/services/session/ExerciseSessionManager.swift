import Foundation
import Combine

protocol ExerciseSessionManagerProtocol {
    func performCreateSession() async
    func performSessionInvite(accountId: String) async
    func performSessionJoin(sessionId: String) async
}

@MainActor
class ExerciseSessionManager: ObservableObject {
    let logger = AppLogger(subsystem: "dev.jrockwell.client", category: "exercise-sessions")

    @Published var isLoading = true
    @Published var session: ExerciseSession?
    
    private let tokenService: TokenServiceProtocol
    private let networkService: NetworkServiceProtocol
    private let websocketService: any WebSocketServiceProtocol
    private var cancellables = Set<AnyCancellable>()
    
    init(
        tokenService: TokenServiceProtocol = TokenService(),
        networkService: NetworkServiceProtocol = NetworkService(),
        websocketService: any WebSocketServiceProtocol = WebSocketService()
    ) {
        self.tokenService = tokenService
        self.networkService = networkService
        self.websocketService = websocketService
        logger.info("ExerciseSessionManager::init")
    }
    
    func performCreateSession() async {
        logger.info("Attempting to create exercise session...")
        
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
            
            await MainActor.run {
                self.session = response.session
            }
        } catch {
            await MainActor.run {
                logger.error("Failed to perform create exercise session request: \(error)")
            }
        }
    }
    
    func performSessionInvite(accountId: String) async {
        
    }
    
    func performSessionJoin(sessionId: String) async {
        
    }
}
