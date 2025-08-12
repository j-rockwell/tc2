import Foundation

@MainActor
protocol ExerciseSessionMessageHandlerProtocol: AnyObject {
    /// Called when the current user successfully joins a session
    func handleSessionJoin(id: String, sessionId: String, accountId: String, payload: SessionJoinPayload, timestamp: Date, version: Int, correlationId: String?)
    
    /// Called when the current user leaves a session
    func handleSessionLeave(id: String, sessionId: String, accountId: String, timestamp: Date, version: Int, correlationId: String?)
    
    /// Called when session status updates (connected, disconnected, errors)
    /* func handleSessionUpdate(id: String, sessionId: String, accountId: String, payload: SessionUpdatePayload, timestamp: Date, version: Int, correlationId: String?) */
    
    /// Called when receiving a state synchronization from the server
    func handleSessionSync(id: String, sessionId: String, accountId: String, payload: SessionSyncPayload, timestamp: Date, version: Int, correlationId: String?)
    
    /// Called when an exercise is added to the session
    func handleExerciseAdd(id: String, sessionId: String, accountId: String, payload: AddExercisePayload, timestamp: Date, version: Int, correlationId: String?)
    
    /// Called when an exercise is updated in the session
    /* func handleExerciseUpdate(id: String, sessionId: String, accountId: String, payload: ExerciseUpdatePayload, timestamp: Date, version: Int, correlationId: String?) */
    
    /// Called when an exercise is deleted from the session
    /* func handleExerciseDelete(id: String, sessionId: String, accountId: String, payload: ExerciseDeletePayload, timestamp: Date, version: Int, correlationId: String?) */
    
    /// Called when a set is added to an exercise
    /* func handleSetAdd(id: String, sessionId: String, accountId: String, payload: SetAddPayload, timestamp: Date, version: Int, correlationId: String?) */
    
    /// Called when a set is marked as complete
    /* func handleSetComplete(id: String, sessionId: String, accountId: String, payload: SetCompletePayload, timestamp: Date, version: Int, correlationId: String?) */
    
    /// Called when a participant moves their cursor to a different exercise/set
    /* func handleCursorMove(id: String, sessionId: String, accountId: String, payload: CursorMovePayload, timestamp: Date, version: Int, correlationId: String?) */
    
    /// Called when another participant joins the session
    /* func handleParticipantJoin(id: String, sessionId: String, accountId: String, payload: ParticipantJoinPayload, timestamp: Date, version: Int, correlationId: String?) */
    
    /// Called when another participant leaves the session
    /* func handleParticipantLeave(id: String, sessionId: String, accountId: String, payload: ParticipantLeavePayload, timestamp: Date, version: Int, correlationId: String?) */
    
    /// Called when someone requests a sync (usually handled by server)
    /* func handleSyncRequest(id: String, sessionId: String, accountId: String, timestamp: Date, version: Int, correlationId: String?) */
    
    /// Called when receiving a full sync response with all session data
    /* func handleSyncResponse(id: String, sessionId: String, accountId: String, payload: SyncResponsePayload, timestamp: Date, version: Int, correlationId: String?) */
    
    /// Called when an unknown or unparseable message is received
    /* func handleUnknownMessage(_ message: ExerciseSessionMessage) */
}

extension ExerciseSessionManager: ExerciseSessionMessageHandlerProtocol {
    func handleSessionJoin(id: String, sessionId: String, accountId: String, payload: SessionJoinPayload, timestamp: Date, version: Int, correlationId: String?) {
        logger.info("Session join: \(accountId) joined session \(sessionId)")
        
        // Update participant list if needed
        if let session = currentSession,
           !session.participants.contains(where: { $0.id == accountId }) {
            // Add new participant
            var updatedSession = session
            let newParticipant = ExerciseSessionParticipant(
                id: accountId,
                color: ParticipantColorGenerator.generateParticipantColor(),
                cursor: nil
            )
            updatedSession.participants.append(newParticipant)
            currentSession = updatedSession
        }
    }
    
    func handleSessionLeave(id: String, sessionId: String, accountId: String, timestamp: Date, version: Int, correlationId: String?) {
        logger.info("Session leave: \(accountId) left session \(sessionId)")
        
        // Remove participant from list
        if var session = currentSession {
            session.participants.removeAll { $0.id == accountId }
            currentSession = session
        }
    }
    
    /* func handleSessionUpdate(id: String, sessionId: String, accountId: String, payload: SessionUpdatePayload, timestamp: Date, version: Int, correlationId: String?) {
        logger.info("Session update: status=\(payload.status ?? "unknown")")
        
        if let error = payload.error {
            logger.error("Session error: \(error) (type: \(payload.errorType ?? "unknown"))")
            socketConnectionError = error
        } else {
            socketConnectionError = nil
        }
        
        if let status = payload.status {
            switch status {
            case "connected":
                socketConnectionStatus = .connected
                logger.info("WebSocket connected with ID: \(payload.connectionId ?? "unknown")")
            case "disconnected":
                socketConnectionStatus = .disconnected
            default:
                logger.warning("Unknown session status: \(status)")
            }
        }
    } */
    
    func handleSessionSync(id: String, sessionId: String, accountId: String, payload: SessionSyncPayload, timestamp: Date, version: Int, correlationId: String?) {
        logger.info("Session sync received (version: \(payload.state.version))")
        currentState = payload.state
        logger.debug("Synced state: \(payload.state.items.count) exercises")
    }
    
    func handleExerciseAdd(id: String, sessionId: String, accountId: String, payload: AddExercisePayload, timestamp: Date, version: Int, correlationId: String?) {
        logger.info("Exercise added by \(accountId): \(payload.exercise.id)")
        
        if var state = currentState {
            let order = state.items.count + 1
            let newExercise = ExerciseSessionStateItem(id: payload.exercise.id, order: order, participants: [], type: payload.exercise.type, rest: payload.exercise.rest, meta: payload.exercise.meta, sets: [])
            state.items.append(newExercise)
            // state.version = payload.version
            currentState = state
        }
        
        objectWillChange.send()
    }
    
    /* func handleExerciseUpdate(id: String, sessionId: String, accountId: String, payload: ExerciseUpdatePayload, timestamp: Date, version: Int, correlationId: String?) {
        logger.info("Exercise updated by \(accountId): \(payload.exerciseId)")
        
        // Update local state version
        if var state = currentSessionState {
            state.version = payload.version
            currentSessionState = state
        }
        
        // Note: The actual exercise updates should come through a sync message
        // This just notifies us that an update occurred
    } */
    
    /* func handleExerciseDelete(id: String, sessionId: String, accountId: String, payload: ExerciseDeletePayload, timestamp: Date, version: Int, correlationId: String?) {
        logger.info("Exercise deleted by \(accountId): \(payload.exerciseId)")
        
        // Remove from local state
        if var state = currentSessionState {
            state.items.removeAll { $0.id == payload.exerciseId }
            state.version = payload.version
            currentSessionState = state
        }
        
        // Notify UI of change
        objectWillChange.send()
    } */
    
    /* func handleSetAdd(id: String, sessionId: String, accountId: String, payload: SetAddPayload, timestamp: Date, version: Int, correlationId: String?) {
        logger.info("Set added to exercise \(payload.exerciseId) by \(accountId)")
        
        // Update local state
        if var state = currentSessionState,
           let exerciseIndex = state.items.firstIndex(where: { $0.id == payload.exerciseId }) {
            state.items[exerciseIndex].sets.append(payload.set)
            state.version = payload.version
            currentSessionState = state
        }
        
        // Notify UI of change
        objectWillChange.send()
    } */
    
    /* func handleSetComplete(id: String, sessionId: String, accountId: String, payload: SetCompletePayload, timestamp: Date, version: Int, correlationId: String?) {
        logger.info("Set \(payload.setId) completed in exercise \(payload.exerciseId) by \(accountId)")
        
        // Update local state
        if var state = currentSessionState,
           let exerciseIndex = state.items.firstIndex(where: { $0.id == payload.exerciseId }),
           let setIndex = state.items[exerciseIndex].sets.firstIndex(where: { $0.id == payload.setId }) {
            state.items[exerciseIndex].sets[setIndex].complete = true
            state.version = payload.version
            currentSessionState = state
        }
        
        // Notify UI of change
        objectWillChange.send()
    } */
    
    /* func handleCursorMove(id: String, sessionId: String, accountId: String, payload: CursorMovePayload, timestamp: Date, version: Int, correlationId: String?) {
        logger.debug("Cursor moved by \(accountId) to exercise: \(payload.cursor.exerciseId)")
        
        // Update participant cursor
        if var session = currentSession,
           let participantIndex = session.participants.firstIndex(where: { $0.id == accountId }) {
            session.participants[participantIndex].cursor = payload.cursor
            currentSession = session
        }
    } */
    
    /* func handleParticipantJoin(id: String, sessionId: String, accountId: String, payload: ParticipantJoinPayload, timestamp: Date, version: Int, correlationId: String?) {
        logger.info("Participant \(payload.accountId) joined the session")
        
        // Add participant if not already present
        if var session = currentSession,
           !session.participants.contains(where: { $0.id == payload.accountId }) {
            let newParticipant = ExerciseSessionParticipant(
                id: payload.accountId,
                color: generateParticipantColor(),
                cursor: nil
            )
            session.participants.append(newParticipant)
            currentSession = session
            
            // Notify UI
            objectWillChange.send()
        }
    } */
    
    /* func handleParticipantLeave(id: String, sessionId: String, accountId: String, payload: ParticipantLeavePayload, timestamp: Date, version: Int, correlationId: String?) {
        logger.info("Participant \(payload.accountId) left the session")
        
        // Remove participant
        if var session = currentSession {
            session.participants.removeAll { $0.id == payload.accountId }
            currentSession = session
            
            // Notify UI
            objectWillChange.send()
        }
    } */
    
    /* func handleSyncRequest(id: String, sessionId: String, accountId: String, timestamp: Date, version: Int, correlationId: String?) {
        logger.debug("Sync request from \(accountId)")
        // Server handles sync requests, client typically doesn't need to respond
    } */
    
    /* func handleSyncResponse(id: String, sessionId: String, accountId: String, payload: SyncResponsePayload, timestamp: Date, version: Int, correlationId: String?) {
        logger.info("Full sync response received")
        
        // Update session
        currentSession = payload.session
        
        // Update our state
        currentSessionState = payload.state
        
        // Store other participant states if needed (add this property to ExerciseSessionManager if you want to track them)
        // otherParticipantStates = payload.participantStates
        
        logger.info("Synced: \(payload.session.participants.count) participants, \(payload.state.items.count) exercises, version \(payload.version)")
        
        // Notify UI of major update
        objectWillChange.send()
    } */
    
    /* func handleUnknownMessage(_ message: ExerciseSessionMessage) {
        logger.warning("Received unknown message type: \(message.type.rawValue)")
    } */
}
