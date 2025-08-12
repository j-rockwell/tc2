import Foundation

struct NextExerciseData {
    let exercise: ExerciseSessionStateItem
    let set: ExerciseSessionStateItemSet
    let meta: ExerciseSessionItemMeta
}

class ExerciseSessionHelper {
    let session: ExerciseSession
    let state: ExerciseSessionState
    
    init(session: ExerciseSession, state: ExerciseSessionState) {
        self.session = session
        self.state = state
    }
    
    /// Returns next incomplete exercise data if it is available
    func getNextIncompleteData() -> NextExerciseData? {
        let sortedExercises = getSortedParentExercises()
        var incompleteExercise: ExerciseSessionStateItem? = nil
        var incompleteSet: ExerciseSessionStateItemSet? = nil
        var incompleteMeta: ExerciseSessionItemMeta? = nil
        
        for exercise in sortedExercises {
            if isExerciseComplete(exercise: exercise) {
                continue
            }
            
            if let set = getNextIncompleteSet(exercise: exercise) {
                incompleteExercise = exercise
                incompleteSet = set
                incompleteMeta = getExerciseMetaForSet(exercise: exercise, exerciseSet: set)
                break
            }
        }
        
        if incompleteExercise == nil || incompleteSet == nil || incompleteMeta == nil {
            return nil
        }
        
        return NextExerciseData(exercise: incompleteExercise!, set: incompleteSet!, meta: incompleteMeta!)
    }
    
    /// Returns the Exercise Meta associated with the exercise/set combo
    func getExerciseMetaForSet(exercise: ExerciseSessionStateItem, exerciseSet: ExerciseSessionStateItemSet) -> ExerciseSessionItemMeta? {
        guard exercise.meta.isEmpty == false else {
            return nil
        }
        
        for meta in exercise.meta {
            if meta.internalId == exerciseSet.metaId {
                return meta
            }
        }
        
        return nil
    }
    
    /// Returns an array of parent exercises sorted by order number
    func getSortedParentExercises() -> [ExerciseSessionStateItem] {
        let result: [ExerciseSessionStateItem] = state.items
            .sorted { $0.order < $1.order }
        
        return result
    }
    
    /// Returns an array of exercise sets sorted by order number
    func getSortedExerciseSets(item: ExerciseSessionStateItem) -> [ExerciseSessionStateItemSet] {
        let result: [ExerciseSessionStateItemSet] = item.sets
            .sorted { $0.order < $1.order }
        
        return result
    }
    
    /// Returns true if the provided exercise state item has no incomplete sets
    func isExerciseComplete(exercise: ExerciseSessionStateItem) -> Bool {
        guard exercise.sets.isEmpty == false else {
            return true
        }
        
        for set in exercise.sets {
            if !set.complete {
                return false
            }
        }
        
        return true
    }
    
    /// Returns the next incomplete set in the provided exercise state item
    func getNextIncompleteSet(exercise: ExerciseSessionStateItem) -> ExerciseSessionStateItemSet? {
        guard isExerciseComplete(exercise: exercise) == false else {
            return nil
        }
        
        let sortedSets = getSortedExerciseSets(item: exercise)
        
        guard sortedSets.isEmpty == false else {
            return nil
        }
        
        for set in sortedSets {
            if set.complete {
                continue
            }
            
            return set
        }
        
        return nil
    }
}
