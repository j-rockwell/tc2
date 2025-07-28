import Foundation
import Combine

@MainActor
class AuthenticationManager: ObservableObject {
    @Published var isAuthenticated: Bool = false
    @Published var isLoading = true
    @Published var account: Account?
    @Published var authError: String?
    
    private let tokenService: TokenServiceProtocol
    private let networkService: NetworkServiceProtocol
    private var cancellables = Set<AnyCancellable>()
    private var refreshTask: Timer?
    
    init(
        tokenService: TokenServiceProtocol = TokenService(), networkService: NetworkServiceProtocol = NetworkService()
    ) {
        self.tokenService = tokenService
        self.networkService = networkService
    }
    
    deinit {
        refreshTask?.invalidate()
    }
    
    func checkStatus() {
        isLoading = true
        clearError()
        defer { isLoading = false }
        
        guard tokenService.isAuthenticated() else {
            completeAuthentication(status: false)
            return
        }
        
        validateSession()
    }
    
    func performSignIn() {
        
    }
    
    func performSignOut() {
        
    }
    
    private func validateSession() {
        
    }
    
    private func fetchAccount() async {
        guard tokenService.isAuthenticated() else {
            completeAuthentication(status: false)
            return
        }
        
        do {
            
        } catch {
            if case NetworkError.unauthorized = error {
                
            } else {
                completeAuthentication(status: true)
                
            }
        }
    }
    
    private func completeAuthentication(status: Bool) {
        self.isAuthenticated = status
        self.isLoading = false
        
        if !isAuthenticated {
            tokenService.clear()
            account = nil
        }
    }
    
    private func performTokenRefresh() async throws -> RefreshTokenResponse {
        guard let refreshToken = tokenService.refreshToken else {
            throw NetworkError.unauthorized
        }
        
        return try await withCheckedThrowingContinuation { continuation in
            networkService.refreshToken(refreshToken)
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
    }
    
    private func refreshIfNeeded() async -> Bool {
        guard tokenService.isAuthenticated(),
              let refreshToken = tokenService.refreshToken else {
            return false
        }
        
        do {
            let response = try await performTokenRefresh()
            tokenService.set(accessToken: response.accessToken, refreshToken: response.refreshToken)
            return true
        } catch {
            performSignOut()
            return false
        }
    }
    
    private func initRefreshTask() {
        refreshTask?.invalidate()
        
        let checkInterval: TimeInterval = 300
                
        refreshTask = Timer.scheduledTimer(withTimeInterval: checkInterval, repeats: true) { [weak self] _ in
            Task { @MainActor in
                _ = await self?.refreshIfNeeded()
            }
        }
    }
    
    private func clearError() {
        authError = nil
    }
    
    private func handleAuthError(_ error: Error) {

    }
}
