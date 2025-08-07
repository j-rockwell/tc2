enum SessionOperationType: String, CaseIterable {
    case createSession = "create_session"
    case inviteSession = "invite_session"
    case joinSession = "join_session"
    case addExercise = "add_exercise"
    case updateExercise = "update_exercise"
    case deleteExercise = "delete_exercise"
    case addSet = "add_set"
    case updateSet = "update_set"
    case deleteSet = "delete_set"
    case updateStatus = "update_status"
    case updateParticipant = "update_participant"
}

struct SessionMessageFactory {
    static func addExercise(exercise: String) -> ExerciseSessionOperationMessage {
        return ExerciseSessionOperationMessage(
            action: SessionOperationType.addExercise.rawValue,
            payload: [
                "exercise": exercise
            ]
        )
    }
}
