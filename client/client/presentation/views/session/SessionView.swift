import SwiftUI

struct SessionView: View {
    let session: ExerciseSession
    let state: ExerciseSessionState
    
    var body: some View {
        VStack {
            PageTitleView(title: session.name!)
            
            ForEach(state.items) { item in
                ExerciseItemCard(item: item)
            }
            
            Spacer()
        }
    }
}

struct ExerciseItemCard: View {
    let item: ExerciseSessionStateItem
    
    // TODO: Merge all the different names here for a better looking display name
    private func getDisplayName() -> String {
        return item.meta[0].name
    }
    
    var body: some View {
        VStack {
            Text(getDisplayName())
                .font(Typography.title2)
                .foregroundColor(Colors.onSurface)
                .frame(maxWidth: .infinity, alignment: .leading)
                .padding(.bottom, Spacing.sm)
            
            VStack(spacing: Spacing.sm) {
                ForEach(item.sets) { set in
                    ExerciseItemCardSetItem(item: set)
                }
            }
        }
        .padding(.horizontal, Spacing.md)
        .padding(.vertical, Spacing.md)
        .background(Colors.surface)
        .cornerRadius(Radii.small)
    }
}

struct ExerciseItemCardSetItem: View {
    let item: ExerciseSessionStateItemSet
    
    var body: some View {
        HStack {
            Text("#\(item.order)")
            
            Spacer()
            
            if item.metrics.weight != nil {
                Text("\(item.metrics.weight!.value.formatted()) \(item.metrics.weight!.unit.rawValue)")
                    .foregroundColor(Colors.onSurface)
            }
            
            Spacer()
            
            if item.metrics.reps != nil {
                Text("\(item.metrics.reps!) reps")
                    .foregroundColor(Colors.onSurface)
            }
        }
        .frame(maxWidth: .infinity, alignment: .leading)
    }
}

#Preview {
    SessionView(session: ExerciseSession(
        id: "test-id",
        name: "Example Session",
        status: .active,
        ownerId: "user-id-here",
        createdAt: Date(),
        updatedAt: Date(),
        participants: [],
        invitations: [],
    ), state: ExerciseSessionState(
        sessionId: "123",
        accountId: "user-id-here",
        version: 0,
        items: [ExerciseSessionStateItem(
            id: "123",
            order: 2,
            participants: [],
            type: .single,
            rest: 60,
            meta: [ExerciseSessionItemMeta(internalId: "internal-id", name: "Bench Press", type: .weightReps)],
            sets:
            [
                ExerciseSessionStateItemSet(id: "set-id-1", metaId: "internal-id", order: 1, metrics: ExerciseSessionStateItemMetric(reps: 5, weight: Weight(value: 135.0, unit: .pound)), type: .workingSet, complete: false),
                ExerciseSessionStateItemSet(id: "set-id-2", metaId: "internal-id", order: 2, metrics: ExerciseSessionStateItemMetric(reps: 5, weight: Weight(value: 185.0, unit: .pound)), type: .workingSet, complete: false),
                ExerciseSessionStateItemSet(id: "set-id-3", metaId: "internal-id", order: 3, metrics: ExerciseSessionStateItemMetric(reps: 5, weight: Weight(value: 225.0, unit: .pound)), type: .workingSet, complete: false)
            ])
        ])
    )
}
