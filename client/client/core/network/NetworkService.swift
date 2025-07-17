import Foundation
import Combine

protocol NetworkServiceProtocol {
    func request<T: APIRequest>(_ request: T) -> AnyPublisher<T.Response, NetworkError>
}

class NetworkService: NetworkServiceProtocol {
    private let session: URLSession
    private let tokenManager: TokenManagerProtocol
    
    init(session: URLSession = .shared, tokenManager: TokenManagerProtocol = TokenManager.shared) {
        self.session = session
        self.tokenManager = tokenManager;
    }
    
    func request<T: APIRequest>(_ request: T) -> AnyPublisher<T.Response, NetworkError> {
        guard let url = buildURL(for: request) else {
            return Fail(error: NetworkError.invalidURL)
                .eraseToAnyPublisher()
        }
        
        var urlRequest = URLRequest(url: url, timeoutInterval: APIConfig.timeout)
        urlRequest.httpMethod = request.method.rawValue
        urlRequest.httpBody = request.body
        
        for (key, value) in request.headers {
            urlRequest.setValue(value, forHTTPHeaderField: key)
        }
        
        if let token = tokenManager.accessToken {
            urlRequest.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
        }
        
        return session.dataTaskPublisher(for: urlRequest)
            .map(\.data)
            .decode(type: T.Response.self, decoder: JSONDecoder())
            .mapError { error in
                if error is DecodingError {
                    return NetworkError.decodingError(error)
                }
                return NetworkError.networkFailure(error)
            }
            .eraseToAnyPublisher()
    }
    
    private func buildURL<T: APIRequest>(for request: T) -> URL? {
            var components = URLComponents(url: APIConfig.baseURL.appendingPathComponent(request.path), resolvingAgainstBaseURL: true)
            components?.queryItems = request.queryItems
            return components?.url
    }
}
