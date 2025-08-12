struct ExercisePayloadData: Codable {
    let id: String
    let type: ExerciseSessionStateItemType
    let rest: Int?
    let meta: [ExerciseSessionItemMeta]
    let participants: [String]?
}

struct SessionJoinPayload: Codable {
    let sessionId: String
    
    enum CodingKeys: String, CodingKey {
        case sessionId = "session_id"
    }
}

struct SessionSyncPayload: Codable {
    let state: ExerciseSessionState
}

struct AddExercisePayload: Codable {
    let exercise: ExercisePayloadData
}
