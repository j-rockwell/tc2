import Foundation
import Security

protocol TokenManagerProtocol {
    var accessToken: String? { get }
    var refreshToken: String? { get }
    
    func store(accessToken: String, refreshToken: String)
    func clear()
    func isAuthenticated() -> Bool
}

class TokenManager: TokenManagerProtocol {
    static let shared = TokenManager()
    
    private let accessTokenKey = "access_token"
    private let refreshTokenKey = "refresh_token"
    
    private init() {}
    
    /// Read access token from keychain
    var accessToken: String? {
        return getFromKeychain(key: accessTokenKey)
    }
    
    /// Read refresh token from keychan
    var refreshToken: String? {
        return getFromKeychain(key: refreshTokenKey)
    }
    
    /// Write access token and refresh token to keychain
    func store(accessToken: String, refreshToken: String) {
        setInKeychain(key: accessTokenKey, value: accessToken)
        setInKeychain(key: refreshTokenKey, value: refreshToken)
    }
    
    /// Remove both access token and refresh token from keychain
    func clear() {
        deleteFromKeychain(key: accessTokenKey)
        deleteFromKeychain(key: refreshTokenKey)
    }
    
    /// Returns true if access token is not null
    /// This does not guarantee that the user has a valid session
    /// but can be assumed from this function unless an API call fails
    func isAuthenticated() -> Bool {
        return accessToken != nil
    }
    
    /// Read a value from the device's keychain by key
    private func getFromKeychain(key: String) -> String? {
        let query: [String: Any] = [
            kSecClass as String: kSecClassGenericPassword,
            kSecAttrAccount as String: key,
            kSecReturnData as String: true,
            kSecMatchLimit as String: kSecMatchLimitOne
        ]
        
        var result: AnyObject?
        let status = SecItemCopyMatching(query as CFDictionary, &result)
        
        guard status == errSecSuccess,
            let data = result as? Data,
            let string = String(data: data, encoding: .utf8) else {
                return nil
            }
        
        return string
    }
    
    /// Write a value to the device's keychain
    private func setInKeychain(key: String, value: String) {
        let data = value.data(using: .utf8)!
                
        let query: [String: Any] = [
            kSecClass as String: kSecClassGenericPassword,
            kSecAttrAccount as String: key,
            kSecValueData as String: data,
            kSecAttrAccessible as String: kSecAttrAccessibleWhenUnlockedThisDeviceOnly
        ]
                
        SecItemDelete(query as CFDictionary)
        SecItemAdd(query as CFDictionary, nil)
    }
    
    /// Remove a value from the device's keychain
    private func deleteFromKeychain(key: String) {
        let query: [String: Any] = [
            kSecClass as String: kSecClassGenericPassword,
            kSecAttrAccount as String: key
        ]
                
        SecItemDelete(query as CFDictionary)
    }
}
