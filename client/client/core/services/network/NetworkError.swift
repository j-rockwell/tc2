import Foundation
import Combine

enum NetworkError: Error, LocalizedError {
    case invalidURL
    case noData
    case decodingError(Error)
    case httpError(Int)
    case networkError(Error)
    case unauthorized
    case serverError
    
    var errorDescription: String? {
        switch self {
        case .invalidURL:
            return "Invalid URL"
        case .noData:
            return "No data received"
        case .decodingError(let error):
            return "Decoding error: \(error.localizedDescription)"
        case .httpError(let statusCode):
            return "HTTP error with status code: \(statusCode)"
        case .networkError(let error):
            return "Network error: \(error.localizedDescription)"
        case .unauthorized:
            return "Unauthorized access"
        case .serverError:
            return "Server error"
        }
    }
}
