import Foundation
import Combine

struct NetworkConfig {
    static let devUrl = URL(string: "http://localhost:8000")!
    static let prodUrl = URL(string: "http://localhost:8000") // TODO: Add prod url
    
    static let timeout: TimeInterval = 10
    
    static var baseUrl: URL {
        #if DEBUG
        return devUrl
        #else
        return prodUrl
        #endif
    }
}
