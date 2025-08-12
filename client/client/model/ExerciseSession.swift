import Foundation

enum ExerciseSessionOperationType: String, CaseIterable, Codable {
    case sessionJoin = "session_join"
    case sessionLeave = "session_leave"
    case sessionUpdate = "session_update"
    case sessionSync = "session_sync"
    
    case exerciseAdd = "exercise_add"
    case exerciseUpdate = "exercise_update"
    case exerciseDelete = "exercise_delete"
    
    case setAdd = "set_add"
    case setUpdate = "set_update"
    case setDelete = "set_delete"
    case setComplete = "set_complete"
    
    case cursorMove = "cursor_move"
    case syncRequest = "sync_request"
    case syncResponse = "sync_response"
}

enum ExerciseType: String, Codable {
    case weightReps = "weight_reps"
    case weightTime = "weight_time"
    case distanceTime = "distance_time"
    case reps = "reps"
    case time = "time"
    case distance = "distance"
}

enum ExerciseSessionStatus: String, Codable {
    case draft = "draft"
    case active = "active"
}

enum ExerciseSessionStateItemType: String, Codable {
    case single = "single"
    case compound = "compound"
}

enum ExerciseSetType: String, Codable {
    case warmupSet = "warmup"
    case workingSet = "working"
    case dropSet = "drop"
    case superSet = "super"
    case failureSet = "failure"
}

enum WeightUnit: String, Codable {
    case kilogram = "kg"
    case pound = "lb"
}

enum DistanceUnit: String, Codable {
    case meter = "m"
    case kilometer = "km"
    case mile = "mi"
    case yard = "yd"
}

struct Weight: Codable {
    var value: Double
    var unit: WeightUnit
    
    var toKg: Double {
        unit == .pound ? value * 0.453592 : value
    }
    
    var toPound: Double {
        unit == .kilogram ? value / 0.453592 : value
    }
}

struct Distance: Codable {
    var value: Double
    var unit: DistanceUnit = .meter
    
    var toMeters: Double {
        switch unit {
        case .meter: return value
        case .kilometer: return value * 1_000
        case .mile: return value * 1_609.34
        case .yard: return value * 0.9144
        }
    }
}

struct Duration: Codable {
    var value: Int
}

struct ExerciseSessionParticipantCursor: Codable {
    var exerciseId: String
    var exerciseSetId: String
    
    enum CodingKeys: String, CodingKey {
        case exerciseId = "exercise_id"
        case exerciseSetId = "exercise_set_id"
    }
}

struct ExerciseSessionParticipant: Codable {
    var id: String
    var color: String
    var cursor: ExerciseSessionParticipantCursor?
}

struct ExerciseSessionInvitation: Codable {
    var invitedBy: String
    var invited: String
    var expires: Date?
    
    enum CodingKeys: String, CodingKey {
        case invitedBy = "invited_by"
        case invited
        case expires
    }
}

struct ExerciseSession: Codable {
    var id: String
    var name: String?
    var status: ExerciseSessionStatus
    var ownerId: String
    var createdAt: Date
    var updatedAt: Date
    var participants: [ExerciseSessionParticipant]
    var invitations: [ExerciseSessionInvitation]
    
    enum CodingKeys: String, CodingKey {
        case id = "id"
        case name
        case status
        case ownerId = "owner_id"
        case createdAt = "created_at"
        case updatedAt = "updated_at"
        case participants
        case invitations
    }
}

struct ExerciseSessionItemMeta: Codable {
    var internalId: String
    var name: String
    var type: ExerciseType
    
    enum CodingKeys: String, CodingKey {
        case internalId = "internal_id"
        case name
        case type
    }
}

struct ExerciseSessionStateItemMetric: Codable {
    var reps: Int?
    var weight: Weight?
    var duration: Duration?
    var distance: Distance?
}

struct ExerciseSessionStateItemSet: Codable, Identifiable {
    var id: String
    var order: Int
    var metrics: ExerciseSessionStateItemMetric
    var type: ExerciseSetType
    var complete: Bool
}

struct ExerciseSessionStateItem: Codable, Identifiable {
    var id: String
    var order: Int
    var participants: [String]
    var type: ExerciseSessionStateItemType
    var rest: Int?
    var meta: [ExerciseSessionItemMeta]
    var sets: [ExerciseSessionStateItemSet]
}

struct ExerciseSessionState: Codable {
    var sessionId: String
    var accountId: String
    var version: Int
    var items: [ExerciseSessionStateItem]
    
    enum CodingKeys: String, CodingKey {
        case sessionId = "session_id"
        case accountId = "account_id"
        case version
        case items
    }
}

struct ExerciseSessionMessage: WebSocketMessage, Codable {
    let id: String
    let type: ExerciseSessionOperationType
    let sessionId: String?
    let payload: [String: AnyCodable]
    let timestamp: Date
    let version: Int
    let correlationId: String?
    
    var action: String {
        return type.rawValue
    }
    
    enum CodingKeys: String, CodingKey {
        case id, type, payload, timestamp, version
        case sessionId = "session_id"
        case correlationId = "correlation_id"
    }
    
    init(
        id: String = UUID().uuidString,
        type: ExerciseSessionOperationType,
        sessionId: String? = nil,
        payload: [String: Any] = [:],
        version: Int = 0,
        correlationId: String? = nil
    ) {
        self.id = id
        self.type = type
        self.sessionId = sessionId
        self.payload = payload.mapValues { AnyCodable($0) }
        self.timestamp = Date()
        self.version = version
        self.correlationId = correlationId
    }
}

struct ExerciseSessionJoinMessage {
    static func create(sessionId: String) -> ExerciseSessionMessage {
        return ExerciseSessionMessage(
            type: .sessionJoin,
            sessionId: sessionId,
            payload: ["session_id": sessionId]
        )
    }
}

struct ExerciseSessionLeaveMessage {
    static func create(sessionId: String) -> ExerciseSessionMessage {
        return ExerciseSessionMessage(
            type: .sessionLeave,
            sessionId: sessionId,
            payload: ["session_id": sessionId]
        )
    }
}
