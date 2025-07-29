import Foundation

struct RefreshTokenResponse: Codable {
    let accessToken: String
    let refreshToken: String
    let expiresIn: Int
    
    enum CodingKeys: String, CodingKey {
        case accessToken = "access_token"
        case refreshToken = "refresh_token"
        case expiresIn = "expires_in"
    }
}

struct AuthenticatedResponse: Codable {
    let accessToken: String
    let refreshToken: String
    let data: BasicAccountData
    
    enum CodingKeys: String, CodingKey {
        case accessToken = "access_token"
        case refreshToken = "refresh_token"
        case data
    }
}

struct LogoutResponse: Codable {
    let message: String
    let success: Bool
}

struct RefreshTokenNetworkResponse: NetworkRequest {
    typealias Response = RefreshTokenResponse
    var path: String { "/auth/refresh" }
    var method: HTTPMethod { .POST }
}

struct LoginNetworkResponse: NetworkRequest {
    typealias Response = AuthenticatedResponse
    
    let request: LoginRequest
    
    var path: String { "/auth/login" }
    var method: HTTPMethod { .POST }
    var body: Data? {
        try? JSONEncoder().encode(request)
    }
    var headers: [String: String] {
        ["Content-Type": "application/json"]
    }
}
