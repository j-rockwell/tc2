import Foundation
import Combine

protocol NetworkServiceProtocol {
    func request<T: APIRequest>(_ request: T) -> AnyPublisher<T.Response, NetworkError>
}
