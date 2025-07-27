import Foundation

protocol TokenServiceProtocol {
    var accessToken: String? { get }
    var refreshToken: String? { get }
    
    func isAuthenticated() -> Bool
    func set(accessToken: String, refreshToken: String) -> Void
    func clear() -> Void
}

class TokenService: TokenServiceProtocol {
    private let keychainService: KeychainServiceProtocol
    
    private let akey = "access_token"
    private let rkey = "refresh_token"
    
    init(keychainService: KeychainServiceProtocol = KeychainService()) {
        self.keychainService = keychainService
    }
    
    var accessToken: String? {
        return keychainService.get(key: akey)
    }
    
    var refreshToken: String? {
        return keychainService.get(key: rkey)
    }
    
    func isAuthenticated() -> Bool {
        return accessToken != nil
    }
    
    func set(accessToken: String, refreshToken: String) {
        keychainService.set(key: akey, value: accessToken)
        keychainService.set(key: rkey, value: refreshToken)
    }
    
    func clear() {
        keychainService.delete(key: akey)
        keychainService.delete(key: rkey)
    }
}
