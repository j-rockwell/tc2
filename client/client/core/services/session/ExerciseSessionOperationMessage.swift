import Foundation

struct ExerciseSessionOperationMessage: WebSocketMessage {
    let action: String
    let payload: [String: Any]
    
    enum CodingKeys: String, CodingKey {
        case action, payload
    }
    
    init(action: String, payload: [String: Any] = [:]) {
        self.action = action
        self.payload = payload
    }
    
    func encode(to encoder: Encoder) throws {
        var container = encoder.container(keyedBy: CodingKeys.self)
        try container.encode(action, forKey: .action)
        
        let jsonData = try JSONSerialization.data(withJSONObject: payload)
        let jsonObject = try JSONSerialization.jsonObject(with: jsonData)
        try container.encode(AnyCodable(jsonObject), forKey: .payload)
    }
    
    init(from decoder: Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        action = try container.decode(String.self, forKey: .action)
        
        let anyPayload = try container.decode(AnyCodable.self, forKey: .payload)
        if let dict = anyPayload.value as? [String: Any] {
            payload = dict
        } else {
            payload = [:]
        }
    }
}
