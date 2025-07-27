struct Account: Codable, Identifiable {
    let id: String
    let username: String
    let email: String
    let profile: AccountProfile?
    let bio: AccountBiometrics?
    let metadata: AccountMetadata?
    
    enum CodingKeys: String, CodingKey {
        case id, username, email, profile, bio, metadata
    }
}

struct AccountProfile: Codable {
    let name: String?
    let avatar: String?
}

struct AccountBiometrics: Codable {
    let dob: String?
    let gender: String?
    let weight: Double?
    let height: Double?
}

struct AccountMetadata: Codable {
    let createdAt: String
    let lastActive: String
    let emailConfirmed: Bool
    
    enum CodingKeys: String, CodingKey {
        case createdAt = "created_at"
        case lastActive = "last_active"
        case emailConfirmed = "email_confirmed"
    }
}
