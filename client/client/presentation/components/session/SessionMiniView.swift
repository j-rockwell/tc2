import SwiftUI

struct SessionMiniView: View {
    @EnvironmentObject var exerciseSessionManager: ExerciseSessionManager
    
    private var nextExercise: NextExerciseData? {
        if exerciseSessionManager.currentSession == nil {
            return nil
        }
        
        if exerciseSessionManager.currentState == nil {
            return nil
        }
        
        return ExerciseSessionHelper(
            session: exerciseSessionManager.currentSession!,
            state: exerciseSessionManager.currentState!
        ).getNextIncompleteData()
    }
    
    var body: some View {
        if let exerciseData = nextExercise {
            HStack {
                VStack {
                    Text(exerciseData.meta.name)
                        .font(Typography.headline)
                        .frame(maxWidth: .infinity, alignment: .leading)
                    HStack {
                        Text("\(exerciseData.set.metrics.reps!)")
                        Text("@")
                        Text("\(exerciseData.set.metrics.weight!.value.formatted())")
                    }
                    .font(Typography.caption1)
                    .frame(maxWidth: .infinity, alignment: .leading)
                }
                
                Spacer()
                
                Button(action: { print("mark as complete") }) {
                    Label("", systemImage: "checkmark")
                }
            }
            .padding(Spacing.sm)
            .background(Colors.surface)
            .frame(maxWidth: .infinity, alignment: .leading)
            .clipShape(RoundedRectangle(cornerRadius: Radii.medium))
        }
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
        items: [ExerciseSessionStateItem(
            id: "123",
            order: 1,
            participants: [],
            type: .single,
            rest: 60,
            meta: [ExerciseSessionItemMeta(internalId: "internal-id", name: "Bench Press", type: .weightReps)],
            sets:
            [
                ExerciseSessionStateItemSet(id: "internal-id", metaId: "internal-id", order: 1, metrics: ExerciseSessionStateItemMetric(reps: 5, weight: Weight(value: 135.0, unit: .pound)), type: .workingSet, complete: false),
                ExerciseSessionStateItemSet(id: "set-id-2", metaId: "internal-id", order: 2, metrics: ExerciseSessionStateItemMetric(reps: 5, weight: Weight(value: 185.0, unit: .pound)), type: .workingSet, complete: false),
                ExerciseSessionStateItemSet(id: "set-id-3", metaId: "internal-id", order: 3, metrics: ExerciseSessionStateItemMetric(reps: 5, weight: Weight(value: 225.0, unit: .pound)), type: .workingSet, complete: false)
            ])
        ]
    )
    
    return SessionMiniView()
        .environmentObject(mockExerciseManager)
}
