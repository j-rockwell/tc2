import Foundation

struct BasicAccountData: Codable {
    let id: String
    let username: String
    let email: String?
    
    enum CodingKeys: String, CodingKey {
        case id, username, email
    }
}
