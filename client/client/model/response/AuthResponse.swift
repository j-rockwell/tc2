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

struct RefreshTokenNetworkResponse: NetworkRequest {
    typealias Response = RefreshTokenResponse
    var path: String { "/auth/refresh" }
    var method: HTTPMethod { .POST }
}
