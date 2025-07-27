struct RefreshTokenResponse: Codable {
    let accessToken: String
    
    enum CodingKeys: String, CodingKey {
        case accessToken = "access_token"
    }
}

struct RefreshTokenNetworkResponse: NetworkRequest {
    typealias Response = RefreshTokenResponse
    var path: String { "/auth/refresh" }
    var method: HTTPMethod { .POST }
}
