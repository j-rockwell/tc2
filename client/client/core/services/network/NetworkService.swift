import Foundation
import Combine

protocol NetworkServiceProtocol {
    func request<T: NetworkRequest>(_ request: T) -> AnyPublisher<T.Response, NetworkError>
}

class NetworkService: NetworkServiceProtocol {
    private let logger: AppLogger = AppLogger(subsystem: "dev.jrockwell.client", category: "networking")
    private let session: URLSession
    private let tokenService: TokenServiceProtocol
    
    init(session: URLSession = .shared, tokenService: TokenServiceProtocol = TokenService()) {
        self.session = session
        self.tokenService = tokenService
        logger.info("NetworkService::init")
    }
    
    func request<T>(_ request: T) -> AnyPublisher<T.Response, NetworkError> where T : NetworkRequest {
        guard let url = buildURL(for: request) else {
            return Fail(error: NetworkError.invalidURL).eraseToAnyPublisher()
        }
        
        logger.info("--- Start Network Request")
        logger.info("Request url: \(url.absoluteString)")
        logger.info("Request method: \(request.method.rawValue)")
        logger.info("Request body: \(String(describing: String(data: request.body ?? Data(), encoding: .utf8)))")
        logger.info("--- End Network Request")
        
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
                    .tryMap { data, response in
                        guard let httpResponse = response as? HTTPURLResponse else {
                            throw NetworkError.networkError(URLError(.badServerResponse))
                        }
                        
                        if httpResponse.statusCode == 401 {
                            throw NetworkError.unauthorized
                        }
                        
                        if !(200...299).contains(httpResponse.statusCode) {
                            throw NetworkError.httpError(httpResponse.statusCode)
                        }
                        
                        return data
                    }
                    .decode(type: T.Response.self, decoder: JSONDecoder.customDecoder)
                    .mapError { error in
                        if error is DecodingError {
                            return NetworkError.decodingError(error)
                        } else if let networkError = error as? NetworkError {
                            return networkError
                        } else {
                            return NetworkError.networkError(error)
                        }
                    }
                    .eraseToAnyPublisher()
    }
    
    private func buildURL<T: NetworkRequest>(for request: T) -> URL? {
        var components = URLComponents(url: NetworkConfig.baseUrl.appendingPathComponent(request.path), resolvingAgainstBaseURL: true)
        components?.queryItems = request.queryItems
        return components?.url
    }
}
