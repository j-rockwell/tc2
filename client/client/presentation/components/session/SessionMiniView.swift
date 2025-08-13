import SwiftUI

struct SessionMiniView: View {
    @EnvironmentObject private var exerciseSessionManager: ExerciseSessionManager
    
    private var nextExercise: NextExerciseData? {
        guard
            let session = exerciseSessionManager.currentSession,
            let state   = exerciseSessionManager.currentState
        else { return nil }
        
        return ExerciseSessionHelper(session: session, state: state)
            .getNextIncompleteData()
    }
    
    var body: some View {
        if let exerciseData = nextExercise {
            HStack {
                VStack(alignment: .leading) {
                    Text(exerciseData.meta.name)
                        .font(Typography.headline)
                        .frame(maxWidth: .infinity, alignment: .leading)
                    
                    SessionMiniExerciseValueView(data: exerciseData)
                        .font(Typography.caption1)
                        .frame(maxWidth: .infinity, alignment: .leading)
                        .monospacedDigit()
                }
                
                Spacer()
                
                Button(action: completeExercise) {
                    Image(systemName: "checkmark.square.fill")
                        .imageScale(.large)
                        .foregroundColor(Colors.onSurface)
                }
            }
            .padding(Spacing.sm)
            .background(Colors.surface)
            .frame(maxWidth: .infinity, alignment: .leading)
            .clipShape(RoundedRectangle(cornerRadius: Radii.medium))
        } else {
            HStack {
                VStack(alignment: .leading) {
                    Text("Exercise Complete")
                        .font(Typography.headline)
                        .frame(maxWidth: .infinity, alignment: .leading)
                    
                    Text("Great Work!")
                        .font(Typography.caption1)
                        .frame(maxWidth: .infinity, alignment: .leading)
                }
                
                Spacer()
                
                Image(systemName: "checkmark.square.fill")
                    .imageScale(.large)
                    .foregroundColor(Colors.secondary)
            }
            .padding(Spacing.sm)
            .background(Colors.surface)
            .frame(maxWidth: .infinity, alignment: .leading)
            .clipShape(RoundedRectangle(cornerRadius: Radii.medium))
        }
    }
    
    private func completeExercise() {
        guard let nextExercise else { return }
        exerciseSessionManager.toggleSetComplete(
            eid: nextExercise.exercise.id,
            sid: nextExercise.set.id
        )
    }
}

private struct SessionMiniExerciseValueView: View {
    let data: NextExerciseData
    
    var body: some View {
        let m = data.set.metrics
        
        switch data.meta.type {
        case .weightReps:
            if let w = m.weight, let r = m.reps {
                Text("\(w.value.formatted())\(w.unit.rawValue) for \(r) reps")
            }
            
        case .weightTime:
            if let w = m.weight {
                Text("\(w.value.formatted())\(w.unit.rawValue) in \(timeString())")
            }
            
        case .time:
            Text(timeString())
            
        case .distance:
            if let d = m.distance {
                Text("\(d.value.formatted()) \(d.unit)")
            }
            
        case .distanceTime:
            if let d = m.distance {
                Text("\(d.value.formatted()) \(d.unit) in \(timeString())")
            }
            
        case .reps:
            Text("\(m.reps ?? 0) reps")
        }
    }
    
    private func timeString() -> String {
        let seconds = data.set.metrics.duration?.value ?? 0
        let s = max(0, seconds)
        let hh = s / 3600
        let mm = (s % 3600) / 60
        let ss = s % 60
        return String(format: "%02d:%02d:%02d", hh, mm, ss)
    }
}

#Preview {
    let mockExerciseManager = ExerciseSessionManager()

    mockExerciseManager.currentSession = ExerciseSession(
        id: "123",
        name: "Example Session",
        status: .active,
        ownerId: "user-id-here",
        createdAt: Date(),
        updatedAt: Date(),
        participants: [],
        invitations: []
    )
    
    mockExerciseManager.currentState = ExerciseSessionState(
        sessionId: "123",
        accountId: "user-id-here",
        version: 0,
        items: [
            ExerciseSessionStateItem(
            id: "456",
            order: 1,
            participants: [],
            type: .single,
            rest: 60,
            meta: [ExerciseSessionItemMeta(internalId: "internal-id", name: "Generic Exercise", type: .weightReps)],
            sets:
            [
                ExerciseSessionStateItemSet(id: "internal-id", metaId: "internal-id", order: 1, metrics: ExerciseSessionStateItemMetric(reps: 8, weight: Weight(value: 135, unit: .pound), duration: Duration(value: 3600), distance: Distance(value: 1, unit: .mile)), type: .workingSet, complete: false),
            ]),
            ExerciseSessionStateItem(
            id: "123",
            order: 2,
            participants: [],
            type: .single,
            rest: 60,
            meta: [ExerciseSessionItemMeta(internalId: "internal-id", name: "Bench Press", type: .weightReps)],
            sets:
            [
                ExerciseSessionStateItemSet(id: "internal-id", metaId: "internal-id", order: 1, metrics: ExerciseSessionStateItemMetric(reps: 5, weight: Weight(value: 135.0, unit: .pound)), type: .workingSet, complete: false),
                ExerciseSessionStateItemSet(id: "set-id-2", metaId: "internal-id", order: 2, metrics: ExerciseSessionStateItemMetric(reps: 6, weight: Weight(value: 185.0, unit: .pound)), type: .workingSet, complete: false),
                ExerciseSessionStateItemSet(id: "set-id-3", metaId: "internal-id", order: 3, metrics: ExerciseSessionStateItemMetric(reps: 7, weight: Weight(value: 225.0, unit: .pound)), type: .workingSet, complete: false)
            ]),
        ]
    )
    
    return SessionMiniView()
        .environmentObject(mockExerciseManager)
}
