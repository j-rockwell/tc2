import Foundation
import Combine

extension NetworkServiceProtocol {
    func createSession() -> AnyPublisher<ExerciseSessionCreateResponse, NetworkError> {
        let request = ExerciseSessionCreateNetworkRequest()
        return self.request(request)
    }
}
