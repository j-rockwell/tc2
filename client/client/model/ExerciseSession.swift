import Foundation

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
    case complete = "complete"
}

enum WeightUnit: String, Codable {
    case kg
    case lb
}

enum DistanceUnit: String, Codable {
    case m
    case km
    case mi
    case yd
}

struct Weight: Codable {
    var value: Double
    var unit: WeightUnit = .lb
    
    var toKg: Double {
        unit == .lb ? value * 0.453592 : value
    }
    
    var toLb: Double {
        unit == .kg ? value / 0.453592 : value
    }
}

struct Distance: Codable {
    var value: Double
    var unit: DistanceUnit = .m
    
    var toMeters: Double {
        switch unit {
        case .m: return value
        case .km: return value * 1_000
        case .mi: return value * 1_609.34
        case .yd: return value * 0.9144
        }
    }
}

struct Duration: Codable {
    var value: Int
}

struct ExerciseSet: Codable, Identifiable {
    var id: String
    var order: Int = 1
    var reps: Int?
    var weight: Weight?
    var distance: Distance?
    var duration: Duration?
    var dropSets: [ExerciseSet] = []
    
    enum CodingKeys: String, CodingKey {
        case id, order, reps, weight, distance, duration
        case dropSets = "drop_sets"
    }
}

struct ExerciseItem: Codable, Identifiable {
    var kind: String = "exercise"
    var id: String
    var name: String
    var type: ExerciseType
    var sets: [ExerciseSet] = []
    
    enum CodingKeys: String, CodingKey {
        case id, name, type, sets
    }
}

struct ExerciseSuperSetItem: Codable, Identifiable {
    let kind: String = "superset"
    var id: String
    var exercises: [ExerciseItem]
    var note: String?
    
    enum CodingKeys: String, CodingKey {
        case kind, id, exercises, note
    }
}

enum SessionItem: Codable {
    case exercise(ExerciseItem)
    case superset(ExerciseSuperSetItem)
    
    private enum KindKey: String, CodingKey {
        case kind
    }
    
    init(from decoder: Decoder) throws {
        let container = try decoder.container(keyedBy: KindKey.self)
        let kind = try container.decode(String.self, forKey: .kind)
        switch kind {
            case "exercise":
                self = .exercise(try ExerciseItem(from: decoder))
            case "superset":
                self = .superset(try ExerciseSuperSetItem(from: decoder))
            default:
                throw DecodingError.dataCorruptedError(forKey: .kind,
                    in: container,
                    debugDescription: "Unknown SessionItem kind: \(kind)")
        }
    }

    func encode(to encoder: Encoder) throws {
        switch self {
        case .exercise(let item):
            try item.encode(to: encoder)
        case .superset(let superset):
            try superset.encode(to: encoder)
        }
    }
}

struct ExerciseSessionState: Codable {
    var sessionId: String
    var accountId: String
    var version: Int = 0
    var items: [SessionItem] = []
    var updatedAt: Date

    enum CodingKeys: String, CodingKey {
        case sessionId = "session_id"
        case accountId = "account_id"
        case version, items
        case updatedAt = "updated_at"
    }
}

struct ExerciseSessionParticipantCursor: Codable {
    var itemId: String
    var setId: String?

    enum CodingKeys: String, CodingKey {
        case itemId = "item_id"
        case setId  = "set_id"
    }
}

struct ExerciseSessionParticipant: Codable, Identifiable {
    var id: String
    var color: String
    var cursor: ExerciseSessionParticipantCursor?
}

struct ExerciseSessionInvite: Codable {
    var invitedId: String
    var invitedBy: String
    var invitedAt: Date

    enum CodingKeys: String, CodingKey {
        case invitedId = "invited_id"
        case invitedBy = "invited_by"
        case invitedAt = "invited_at"
    }
}

struct ExerciseSession: Codable {
    var ownerId: String
    var status: ExerciseSessionStatus = .draft
    var participants: [ExerciseSessionParticipant] = []
    var invites: [ExerciseSessionInvite] = []
    var createdAt: Date
    var updatedAt: Date

    enum CodingKeys: String, CodingKey {
        case ownerId = "owner_id"
        case status, participants, invites
        case createdAt = "created_at"
        case updatedAt = "updated_at"
    }
}
