import Foundation
import Combine

protocol NetworkServiceProtocol {
    func request<T: NetworkRequest>(_ request: T) -> AnyPublisher<T.Response, NetworkError>
}

class NetworkService: NetworkServiceProtocol {
    private let session: URLSession
    
    init(session: URLSession = .shared) {
        self.session = session
    }
    
    func request<T>(_ request: T) -> AnyPublisher<T.Response, NetworkError> where T : NetworkRequest {
        guard let url = buildURL(for: request) else {
            return Fail(error: NetworkError.invalidURL).eraseToAnyPublisher()
        }
        
        var urlRequest = URLRequest(url: url, timeoutInterval: NetworkConfig.timeout)
        urlRequest.httpMethod = request.method.rawValue
        urlRequest.httpBody = request.body
        
        for (key, value) in requests.headers {
            urlRequest.setValue(value, forHTTPHeaderField: key)
        }
    }
    
    private func buildURL<T: NetworkRequest>(for request: T) -> URL? {
        var components = URLComponents(url: NetworkConfig.baseUrl.appendingPathComponent(request.path), resolvingAgainstBaseURL: true)
        components?.queryItems = request.queryItems
        return components?.url
    }
}
