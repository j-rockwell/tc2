import Foundation
import Combine

extension NetworkServiceProtocol {
    func refreshToken(_ refreshToken: String) -> AnyPublisher<RefreshTokenResponse, NetworkError> {
        let request = RefreshTokenNetworkRequest(request: RefreshTokenRequest(refreshToken: refreshToken))
        return self.request(request)
    }
    
    func login(_ request: LoginRequest) -> AnyPublisher<AuthenticatedResponse, NetworkError> {
        let request = LoginNetworkRequest(request: request)
        return self.request(request)
    }
    
    func register(_ request: RegisterRequest) -> AnyPublisher<AuthenticatedResponse, NetworkError> {
        let request = RegisterNetworkRequest(request: request)
        return self.request(request)
    }
    
    // TODO: Refactor - Move this to Account ext instead
    func fetchAccount() -> AnyPublisher<Account, NetworkError> {
        let request = FetchAccountNetworkRequest()
        return self.request(request)
    }
}

