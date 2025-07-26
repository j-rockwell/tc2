import Foundation

struct CheckUsernameAvailabilityRequest: APIRequest {
    typealias Response = AvailabilityResponse
    
    let username: String
    
    var path: String { "/account/availability" }
    var method: HTTPMethod { .GET }
    var queryItems: [URLQueryItem]? {
        [URLQueryItem(name: "username", value: username)]
    }
}

struct CheckEmailAvailabilityRequest: APIRequest {
    typealias Response = AvailabilityResponse
    
    let email: String
    
    var path: String { "/account/availability" }
    var method: HTTPMethod { .GET }
    var queryItems: [URLQueryItem]? {
        [URLQueryItem(name: "email", value: email)]
    }
}
