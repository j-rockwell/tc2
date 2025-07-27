import Foundation

protocol TokenServiceProtocol {
    var accessToken: String? { get }
    var refreshToken: String? { get }
    
    func isAuthenticated() -> Bool
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
    
    func clear() {
        keychainService.delete(key: akey)
        keychainService.delete(key: rkey)
    }
}
