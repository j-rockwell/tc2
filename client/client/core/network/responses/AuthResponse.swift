import Foundation

struct AuthResponse: Codable {
    let accessToken: String
    let refreshToken: String
    let data: Account
    
    enum CodingKeys: String, CodingKey {
        case accessToken = "access_token"
        case refreshToken = "refresh_token"
        case data
    }
}

struct RefreshResponse: Codable {
    let accessToken: String
    
    enum CodingKeys: String, CodingKey {
        case accessToken = "access_token"
    }
}
