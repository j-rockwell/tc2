import Foundation

// MARK - Refresh Token Network Request
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
}

// MARK - Login Network Request
struct LoginRequest: Codable {
    let email: String
    let password: String
}

struct LoginNetworkRequest: NetworkRequest {
    typealias Response = AuthenticatedResponse
    
    let request: LoginRequest
    
    var path: String { "/auth/login" }
    var method: HTTPMethod { .POST }
    var body: Data? {
        try? JSONEncoder().encode(request)
    }
}

// MARK - Register Network Request
struct RegisterRequest: Codable {
    let username: String
    let email: String
    let password: String
}

struct RegisterNetworkRequest: NetworkRequest {
    typealias Response = AuthenticatedResponse
    
    let request: RegisterRequest
    
    var path: String { "/account" }
    var method: HTTPMethod { .POST }
    var body: Data? {
        try? JSONEncoder().encode(request)
    }
}
