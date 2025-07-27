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
        let isValidToken = tokenService.isAuthenticated()
    }
    
    private func fetchAccount() {
        
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
        return try await withCheckedThrowingContinuation { continuation in
            let request = RefreshTokenNetwork
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
                
        guard let tokenInfo = tokenService.getTokenInfo(),
              let timeUntilExpiration = tokenInfo.timeUntilExpiration,
              timeUntilExpiration > 0 else { return }
                
        let refreshTime = max(timeUntilExpiration - (5 * 60), 60)
                
        refreshTask = Timer.scheduledTimer(withTimeInterval: 25 * 60, repeats: true) { [weak self] _ in
                    Task { @MainActor in
                        _ = await self?.refreshIfNeeded()
                    }
                }
        
    }
    
    private func clearError() {
        authError = nil
    }
}
