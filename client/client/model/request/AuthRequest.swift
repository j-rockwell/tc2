import Foundation

struct RefreshTokenRequest: Codable {
    let refreshToken: String
    
    enum CodingKeys: String, CodingKey {
        case refreshToken = "refresh_token"
    }
}

struct RefreshTokenNetworkRequest: NetworkRequest {
    typealias Response = RefreshTokenResponse
    
    let request: RefreshTokenRequest
    
    var path: String { "/auth/refresh" }
    var method: HTTPMethod { .POST }
    var body: Data? {
        try? JSONEncoder().encode(request)
    }
    
    var headers: [String: String] {
        ["Content-Type": "application/json"]
    }
}
