import Foundation

class AuthenticationManager: ObservableObject {
    @Published var isAuthenticated: Bool = false
    @Published var currentAccount: Account?
    @Published var isLoading = false
    @Published var errorMessage: String?
    
    private let tokenManager: TokenManagerProtocol
    private let baseURL: String
    private var refreshTask: Task<Void, Never>?
    
    init(tokenManager: TokenManagerProtocol = TokenManager.shared) {
        self.tokenManager = tokenManager
        self.baseURL = APIConfig.baseURL.absoluteString
        
        if tokenManager.isAuthenticated() {
            
        }
    }
    
    deinit {
        refreshTask?.cancel()
    }
    
    func performSignIn() async {
        
    }
    
    func performSignOut() async {
        
    }
    
    func refreshIfNeeded() async {
        guard !isLoading && tokenManager.isAuthenticated() else {
            return
        }
        
        await refreshTokens()
    }
    
    private func refreshTokens() async {
        guard let refreshToken = tokenManager.refreshToken else {
            await performSignOut()
            return
        }
        
        do {
            var request = URLRequest(url: URL(string: "\(baseURL)/auth/refresh")!)
            request.httpMethod = "POST"
            request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        }
    }
    
    private func startRefreshTokenTask() {
        refreshTask?.cancel()
        
        refreshTask = Task {
            while !Task.isCancelled && isAuthenticated {
                try? await Task.sleep(nanoseconds: 20 * 60 * 1_000_000_000)
                if !Task.isCancelled {
                    await refreshIfNeeded()
                }
            }
        }
    }
}
