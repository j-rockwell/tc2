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
    
    var accessToken: String? {
        return getFromKeychain(key: accessTokenKey)
    }
    
    var refreshToken: String? {
        return getFromKeychain(key: refreshTokenKey)
    }
    
    func store(accessToken: String, refreshToken: String) {
        setInKeychain(key: accessTokenKey, value: accessToken)
        setInKeychain(key: refreshTokenKey, value: refreshToken)
    }
    
    func clear() {
        deleteFromKeychain(key: accessTokenKey)
        deleteFromKeychain(key: refreshTokenKey)
    }
    
    func isAuthenticated() -> Bool {
        return accessToken != nil
    }
    
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
    
    private func deleteFromKeychain(key: String) {
        let query: [String: Any] = [
            kSecClass as String: kSecClassGenericPassword,
            kSecAttrAccount as String: key
        ]
                
        SecItemDelete(query as CFDictionary)
    }
}
