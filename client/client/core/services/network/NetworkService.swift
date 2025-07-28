import Foundation
import Combine

protocol NetworkServiceProtocol {
    func request<T: NetworkRequest>(_ request: T) -> AnyPublisher<T.Response, NetworkError>
    func refreshToken(_ refreshToken: String) -> AnyPublisher<RefreshTokenResponse, NetworkError>
}

class NetworkService: NetworkServiceProtocol {
    private let session: URLSession
    private let tokenService: TokenServiceProtocol
    
    init(session: URLSession = .shared, tokenService: TokenServiceProtocol = TokenService()) {
        self.session = session
        self.tokenService = tokenService
    }
    
    func request<T>(_ request: T) -> AnyPublisher<T.Response, NetworkError> where T : NetworkRequest {
        guard let url = buildURL(for: request) else {
            return Fail(error: NetworkError.invalidURL).eraseToAnyPublisher()
        }
        
        var urlRequest = URLRequest(url: url, timeoutInterval: NetworkConfig.timeout)
        urlRequest.httpMethod = request.method.rawValue
        urlRequest.httpBody = request.body
        
        for (key, value) in request.headers {
            urlRequest.setValue(value, forHTTPHeaderField: key)
        }
        
        if let token = tokenService.accessToken {
            urlRequest.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
        }
        
        return session.dataTaskPublisher(for: urlRequest)
            .map(\.data)
            .decode(type: T.Response.self, decoder: JSONDecoder())
            .mapError { error in
                if error is DecodingError {
                    return NetworkError.decodingError(error)
                }
                return NetworkError.networkError(error)
            }
            .eraseToAnyPublisher()
    }
    
    // TODO: Move this to its own service this sucks
    func refreshToken(_ refreshToken: String) -> AnyPublisher<RefreshTokenResponse, NetworkError> {
        let refreshRequest = RefreshTokenRequest(refreshToken: refreshToken)
        let request = RefreshTokenNetworkRequest(request: refreshRequest)
            
        guard let url = buildURL(for: request) else {
            return Fail(error: NetworkError.invalidURL).eraseToAnyPublisher()
        }
            
        var urlRequest = URLRequest(url: url, timeoutInterval: NetworkConfig.timeout)
        urlRequest.httpMethod = request.method.rawValue
        urlRequest.httpBody = request.body
            
        for (key, value) in request.headers {
            urlRequest.setValue(value, forHTTPHeaderField: key)
        }
            
        return session.dataTaskPublisher(for: urlRequest)
            .map(\.data)
            .decode(type: RefreshTokenResponse.self, decoder: JSONDecoder())
            .mapError { error in
                if error is DecodingError {
                    return NetworkError.decodingError(error)
                }
                return NetworkError.networkError(error)
            }
            .eraseToAnyPublisher()
    }
    
    private func buildURL<T: NetworkRequest>(for request: T) -> URL? {
        var components = URLComponents(url: NetworkConfig.baseUrl.appendingPathComponent(request.path), resolvingAgainstBaseURL: true)
        components?.queryItems = request.queryItems
        return components?.url
    }
}
