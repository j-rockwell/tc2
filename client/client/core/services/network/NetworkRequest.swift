import Foundation
import Combine

enum HTTPMethod: String {
    case GET = "GET"
    case POST = "POST"
    case PUT = "PUT"
    case DELETE = "DELETE"
    case PATH = "PATH"
}

protocol NetworkRequest {
    associatedtype Response: Codable
    
    var path: String { get }
    var method: HTTPMethod { get }
    var headers: [String: String] { get }
    var body: Data? { get }
    var queryItems: [URLQueryItem]? { get }
}


extension NetworkRequest {
    var headers: [String: String] {
        ["Content-Type": "application/json"]
    }
    
    var queryItems: [URLQueryItem]? { nil }
    var body: Data? { nil }
}
