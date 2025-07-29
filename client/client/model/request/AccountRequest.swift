import Foundation
import Combine

// MARK - Fetch Account Network Request
struct FetchAccountNetworkRequest: NetworkRequest {
    typealias Response = Account
    
    var path: String { "/account/me/profile" }
    var method: HTTPMethod { .GET }
}
