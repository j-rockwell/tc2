import Foundation

// MARK - Create exercise session request
struct ExerciseSessionCreateNetworkRequest: NetworkRequest {
    typealias Response = ExerciseSessionCreateResponse
    
    var path: String { "/session/" }
    var method: HTTPMethod { .POST }
}

// MARK - Create exercise session invite request
struct ExerciseSessionInviteRequest: Codable {
    let account_id: String
}

struct ExerciseSessionInviteNetworkRequest: NetworkRequest {
    typealias Response = ExerciseSessionInviteResponse
    
    let request: ExerciseSessionInviteRequest
    
    var path: String { "/session/invite" }
    var method: HTTPMethod { .POST }
    var body: Data? {
        try? JSONEncoder().encode(request)
    }
}

// MARK - Accept exercise session invite request
struct ExerciseSessionInviteAcceptRequest: Codable {
    let session_id: String
}

struct ExerciseSessionInviteAcceptNetworkRequest: NetworkRequest {
    typealias Response = ExerciseSessionInviteAcceptResponse
    
    let request: ExerciseSessionInviteAcceptRequest
    
    var path: String { "/session/invite/accept" }
    var method: HTTPMethod { .POST }
    var body: Data? {
        try? JSONEncoder().encode(request)
    }
}
