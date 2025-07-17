import Foundation

struct LoginAPIRequest: APIRequest {
    typealias Response = AuthResponse
    
    let email: String
    let password: String
    
    var path: String { "/auth/login" }
    var method: HTTPMethod { .POST }
    
    var body: Data? {
        let request = LoginRequest(email: email, password: password)
        return try? JSONEncoder().encode(request)
    }
}

struct RegisterAPIRequest: APIRequest {
    typealias Response = AuthResponse
    
    let username: String
    let email: String
    let password: String
    
    var path: String { "/account/" }
    var method: HTTPMethod { .POST }
    
    var body: Data? {
        let request = RegisterRequest(username: username, email: email, password: password)
        return try? JSONEncoder().encode(request)
    }
}


struct LogoutAPIRequest: APIRequest {
    typealias Response = APIResponse<String>
    
    var path: String { "/auth/logout" }
    var method: HTTPMethod { .POST }
}

