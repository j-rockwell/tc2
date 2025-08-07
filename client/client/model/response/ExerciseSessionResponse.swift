struct ExerciseSessionCreateResponse: Codable {
    let session: ExerciseSession
}

struct ExerciseSessionInviteResponse: Codable {}

struct ExerciseSessionInviteAcceptResponse: Codable {
    let session: ExerciseSession
    let participant: ExerciseSessionParticipant
}
