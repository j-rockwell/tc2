import Foundation

struct NetworkResponse<T: Codable>: Codable {
    let success: Bool
    let data: T?
    let message: String?
    let errorCode: String?
    
    enum CodingKeys: String, CodingKey {
        case success, data, message
        case errorCode = "error_code"
    }
}
