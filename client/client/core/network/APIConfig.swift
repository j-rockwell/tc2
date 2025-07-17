import Foundation
import Combine

struct APIConfig {
    static let baseURL = URL(string: "http://localhost:8000")!
    static let timeout: TimeInterval = 30
}
