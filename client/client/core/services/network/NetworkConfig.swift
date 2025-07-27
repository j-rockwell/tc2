import Foundation
import Combine

struct NetworkConfig {
    static let devUrl = URL(string: "https://jsonplaceholder.typicode.com")!
    static let prodUrl = URL(string: "")
    
    static let timeout: TimeInterval = 10
    
    static var baseUrl: URL {
        #if DEBUG
        return devUrl
        #else
        return prodUrl
        #endif
    }
}
