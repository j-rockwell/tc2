import Foundation

extension JSONDecoder {
    static let customDecoder: JSONDecoder = {
            let decoder = JSONDecoder()
            let formatter = DateFormatter()
        
            formatter.calendar = Calendar(identifier: .iso8601)
            formatter.locale = Locale(identifier: "en_US_POSIX")
            formatter.timeZone = TimeZone(secondsFromGMT: 0)
            
            decoder.dateDecodingStrategy = .custom { decoder in
                let container = try decoder.singleValueContainer()
                let dateString = try container.decode(String.self)
                
                // Try different ISO 8601 formats
                let formats = [
                    "yyyy-MM-dd'T'HH:mm:ss.SSSZZZZZ",  // With milliseconds and timezone
                    "yyyy-MM-dd'T'HH:mm:ssZZZZZ",      // Without milliseconds, with timezone
                    "yyyy-MM-dd'T'HH:mm:ss'Z'",        // UTC with Z
                    "yyyy-MM-dd'T'HH:mm:ss.SSS'Z'",    // UTC with milliseconds and Z
                    "yyyy-MM-dd'T'HH:mm:ss"            // No timezone
                ]
                
                for format in formats {
                    formatter.dateFormat = format
                    if let date = formatter.date(from: dateString) {
                        return date
                    }
                }
                
                // Fallback
                let isoFormatter = ISO8601DateFormatter()
                isoFormatter.formatOptions = [.withInternetDateTime, .withFractionalSeconds]
                if let date = isoFormatter.date(from: dateString) {
                    return date
                }
                
                isoFormatter.formatOptions = [.withInternetDateTime]
                if let date = isoFormatter.date(from: dateString) {
                    return date
                }
                
                throw DecodingError.dataCorrupted(
                    DecodingError.Context(
                        codingPath: decoder.codingPath,
                        debugDescription: "Unable to decode date string: \(dateString)"
                    )
                )
            }
            
            return decoder
        }()
    
    static let webSocketDecoder: JSONDecoder = {
            let decoder = JSONDecoder()
            let formatter = ISO8601DateFormatter()
            formatter.formatOptions = [.withInternetDateTime, .withFractionalSeconds]
            
            decoder.dateDecodingStrategy = .custom { decoder in
                let container = try decoder.singleValueContainer()
                let dateString = try container.decode(String.self)
                
                if let date = formatter.date(from: dateString) {
                    return date
                }

                formatter.formatOptions = [.withInternetDateTime]
                if let date = formatter.date(from: dateString) {
                    return date
                }
                
                let dateFormatter = DateFormatter()
                dateFormatter.dateFormat = "yyyy-MM-dd'T'HH:mm:ss.SSSSSSZZZZZ"
                if let date = dateFormatter.date(from: dateString) {
                    return date
                }
                
                dateFormatter.dateFormat = "yyyy-MM-dd'T'HH:mm:ssZZZZZ"
                if let date = dateFormatter.date(from: dateString) {
                    return date
                }
                
                throw DecodingError.dataCorrupted(
                    DecodingError.Context(
                        codingPath: decoder.codingPath,
                        debugDescription: "Unable to decode date: \(dateString)"
                    )
                )
            }
            
            return decoder
        }()
}
