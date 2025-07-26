import Foundation
import Combine

protocol NetworkServiceProtocol {
    func request<T: APIRequest>(_ request: T) async throws -> T.Response
}

class NetworkService: NetworkServiceProtocol {
    private let session: URLSession
    private let tokenManager: TokenManagerProtocol
    
    init(session: URLSession = .shared, tokenManager: TokenManagerProtocol = TokenManager.shared) {
        self.session = session
        self.tokenManager = tokenManager;
    }
    
    func request<T: APIRequest>(_ request: T) async throws -> T.Response {
        guard let url = buildURL(for: request) else {
            throw NetworkError.invalidURL
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
        
        let (data, response) = try await session.data(for: urlRequest)
        
        guard let httpResponse = response as? HTTPURLResponse else {
            throw NetworkError.networkFailure(URLError(.badServerResponse))
        }
        
        guard 200...299 ~= httpResponse.statusCode else {
            if httpResponse.statusCode == 401 {
                throw NetworkError.unauthorized
            }
            throw NetworkError.serverError(httpResponse.statusCode)
        }
        
        do {
            return try JSONDecoder().decode(T.Response.self, from: data)
        } catch {
            throw NetworkError.decodingError(error)
        }
    }
    
    private func buildURL<T: APIRequest>(for request: T) -> URL? {
            var components = URLComponents(url: APIConfig.baseURL.appendingPathComponent(request.path), resolvingAgainstBaseURL: true)
            components?.queryItems = request.queryItems
            return components?.url
    }
}
