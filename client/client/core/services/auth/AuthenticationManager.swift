import Foundation
import Combine
import os

@MainActor
class AuthenticationManager: ObservableObject {
    let logger = AppLogger(subsystem: "dev.jrockwell.client", category: "authentication")
    
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
        logger.info("AuthenticationManager::init")
    }
    
    deinit {
        refreshTask?.invalidate()
    }
    
    func checkStatus() {
        logger.info("Checking authentication status...")
        isLoading = true
        clearError()
        
        #if DEBUG
        tokenService.clear()
        logger.warning("Clearing stored tokens in debug mode")
        #endif
        
        defer {
            isLoading = false
            logger.info("Authentication status check complete.")
        }
        
        guard tokenService.isAuthenticated() else {
            completeAuthentication(status: false)
            logger.info("Not authenticated.")
            return
        }
        
        validateSession()
    }
    
    func performSignUp(username: String, email: String, password: String) async {
        logger.info("Attempting to register...")
        
        isLoading = true
        clearError()
        
        do {
            let registerRequest = RegisterRequest(username: username, email: email, password: password)
            let response = try await withCheckedThrowingContinuation { continuation in
                networkService.register(registerRequest)
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
            
            tokenService.set(
                accessToken: response.accessToken,
                refreshToken: response.refreshToken
            )
            
            await MainActor.run {
                self.account = Account(
                    id: response.data.id,
                    username: response.data.username,
                    email: response.data.email!,
                    profile: nil,
                    bio: nil,
                    metadata: nil
                )
                self.isAuthenticated = true
                self.initRefreshTask()
            }
            
            Task {
                try? await fetchAccount()
            }
        } catch NetworkError.httpError(429) {
            await MainActor.run {
                self.authError = "Too many login attempts. Please try again later"
                self.isAuthenticated = false
            }
        } catch NetworkError.httpError(403) {
            await MainActor.run {
                self.authError = "Additional verification required"
                self.isAuthenticated = false
            }
        } catch {
            await MainActor.run {
                logger.error("Failed to perform authentication request: \(error)")
                self.authError = "An error occurred. Please try again"
                self.isAuthenticated = false
            }
        }
        
        if authError != nil {
            logger.error("Failed to perform authentication: \(authError!)")
        }
    }
    
    func performSignIn(email: String, password: String) async {
        logger.info("Attempting to sign in...")
        
        isLoading = true
        clearError()
            
        do {
            let loginRequest = LoginRequest(email: email, password: password)
            let response = try await withCheckedThrowingContinuation { continuation in
                networkService.login(loginRequest)
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
                
                tokenService.set(
                    accessToken: response.accessToken,
                    refreshToken: response.refreshToken
                )
                
                await MainActor.run {
                    self.account = Account(
                        id: response.data.id,
                        username: response.data.username,
                        email: response.data.email!,
                        profile: nil,
                        bio: nil,
                        metadata: nil
                    )
                    self.isAuthenticated = true
                    self.initRefreshTask()
                }
                
                Task {
                    try? await fetchAccount()
                }
        } catch NetworkError.unauthorized {
            await MainActor.run {
                self.authError = "Invalid email or password"
                self.isAuthenticated = false
            }
        } catch NetworkError.httpError(423) {
            await MainActor.run {
                self.authError = "Account temporarily locked due to too many failed attempts"
                self.isAuthenticated = false
            }
        } catch NetworkError.httpError(429) {
            await MainActor.run {
                self.authError = "Too many login attempts. Please try again later"
                self.isAuthenticated = false
            }
        } catch NetworkError.httpError(403) {
            await MainActor.run {
                self.authError = "Additional verification required"
                self.isAuthenticated = false
            }
        } catch {
            await MainActor.run {
                logger.error("Failed to perform authentication request: \(error)")
                self.authError = "An error occurred. Please try again"
                self.isAuthenticated = false
            }
        }
        
        if authError != nil {
            logger.error("Failed to perform authentication: \(authError!)")
        }
    }
    
    func performSignOut() async {
        
    }
    
    private func validateSession() {
        logger.info("Attempting to validate session...")
        
        Task {
            do {
                try await fetchAccount()
            } catch NetworkError.unauthorized {
                logger.info("Session expired, attempting to refresh token...")
                let refreshSuccess = await refreshIfNeeded()
                
                if refreshSuccess {
                    logger.info("Token refresh successful, retrying account refresh...")
                    
                    do {
                        try await fetchAccount()
                    } catch {
                        logger.error("Account fetch failed after token refresh: \(error)")
                        await performSignOut()
                    }
                } else {
                    logger.error("Token refresh failed, signing out...")
                    await performSignOut()
                }
            } catch {
                completeAuthentication(status: false)
                logger.error("Session validation failed: \(error)")
            }
        }
    }
    
    private func fetchAccount() async throws {
        guard tokenService.isAuthenticated() else {
            logger.error("Could not fetch account: no valid token")
            completeAuthentication(status: false)
            return
        }
        
        do {
            let account = try await withCheckedThrowingContinuation { continuation in
                networkService.fetchAccount()
                    .sink(
                        receiveCompletion: { completion in
                            if case .failure(let error) = completion {
                                continuation.resume(throwing: error)
                            }
                        },
                        receiveValue: { account in
                            continuation.resume(returning: account)
                        }
                    )
                    .store(in: &cancellables)
            }
            
            await MainActor.run {
                self.account = account
                self.completeAuthentication(status: true)
                self.initRefreshTask()
                logger.info("Account fetched successfully. Welcome: \(account.username)")
            }
        } catch {
            if case NetworkError.unauthorized = error {
                logger.warning("Unauthorized while attempting to fetch account.")
                throw NetworkError.unauthorized
            } else {
                logger.error("Failed to fetch account: \(error)")
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
            refreshTask?.invalidate()
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
              let _ = tokenService.refreshToken else {
            return false
        }
        
        do {
            let response = try await performTokenRefresh()
            tokenService.set(accessToken: response.accessToken, refreshToken: response.refreshToken)
            return true
        } catch {
            await performSignOut()
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
