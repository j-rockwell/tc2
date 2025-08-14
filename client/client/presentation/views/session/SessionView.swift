import SwiftUI

struct GridConfiguration {
    static func columnsForType(_ type: ExerciseType) -> [GridItem] {
        switch type {
        case .weightReps:
            return [
                GridItem(.fixed(45)),
                GridItem(.flexible(minimum: 80)),
                GridItem(.flexible(minimum: 60)),
                GridItem(.fixed(44))
            ]
        case .weightTime:
            return [
                GridItem(.fixed(45)),
                GridItem(.flexible(minimum: 80)),
                GridItem(.flexible(minimum: 80)),
                GridItem(.fixed(44))
            ]
        case .distanceTime:
            return [
                GridItem(.fixed(45)),
                GridItem(.flexible(minimum: 80)),
                GridItem(.flexible(minimum: 80)),
                GridItem(.fixed(44))
            ]
        case .reps:
            return [
                GridItem(.fixed(45)),
                GridItem(.flexible(minimum: 80)),
                GridItem(.fixed(44))
            ]
        case .time:
            return [
                GridItem(.fixed(45)),
                GridItem(.flexible(minimum: 100)),
                GridItem(.fixed(44))
            ]
        case .distance:
            return [
                GridItem(.fixed(45)),
                GridItem(.flexible(minimum: 100)),
                GridItem(.fixed(44))
            ]
        }
    }
    
    static func headersForType(_ type: ExerciseType) -> [String] {
        switch type {
        case .weightReps:
            return ["Set", "Weight", "Reps", ""]
        case .weightTime:
            return ["Set", "Weight", "Time", ""]
        case .distanceTime:
            return ["Set", "Distance", "Time", ""]
        case .reps:
            return ["Set", "Reps", ""]
        case .time:
            return ["Set", "Time", ""]
        case .distance:
            return ["Set", "Distance", ""]
        }
    }
}

struct SessionView: View {
    @EnvironmentObject var exerciseSessionManager: ExerciseSessionManager
    let session: ExerciseSession
    let state: ExerciseSessionState
    
    var body: some View {
        ScrollView {
            VStack(spacing: Spacing.md) {
                PageTitleView(title: session.name ?? "Workout Session")
                
                if state.items.isEmpty {
                    EmptySessionView()
                        .padding(.top, Spacing.xl)
                } else {
                    ForEach(state.items) { item in
                        ExerciseItemCard(item: item)
                    }
                }
            }
        }
    }
}

struct EmptySessionView: View {
    var body: some View {
        VStack(spacing: Spacing.md) {
            Image(systemName: "dumbbell.fill")
                .font(.system(size: 48))
                .foregroundColor(Colors.onSurface.opacity(0.3))
            
            Text("No exercises yet")
                .font(Typography.headline)
                .foregroundColor(Colors.onSurface.opacity(0.6))
            
            Text("Add your first exercise to get started")
                .font(Typography.caption1)
                .foregroundColor(Colors.onSurface.opacity(0.5))
        }
        .frame(maxWidth: .infinity)
        .padding(.vertical, Spacing.xl)
    }
}

struct ExerciseItemCard: View {
    @EnvironmentObject var exerciseSessionManager: ExerciseSessionManager
    
    let item: ExerciseSessionStateItem
    
    private func getDisplayName() -> String {
        if item.meta.count > 1 {
            return item.meta.map { $0.name }.joined(separator: " / ")
        }
        return item.meta.first?.name ?? "Exercise"
    }
    
    private func getExerciseType() -> ExerciseType {
        return item.meta.first?.type ?? .reps
    }
    
    var body: some View {
        VStack {
            Text(getDisplayName())
                .font(Typography.title2)
                .foregroundColor(Colors.onSurface)
                .frame(maxWidth: .infinity, alignment: .leading)
                .padding(.bottom, Spacing.sm)
            
            ExerciseItemCardGrid(item: item, exerciseType: getExerciseType())
        }
        .padding(.horizontal, Spacing.md)
        .padding(.vertical, Spacing.md)
        .background(Colors.surface)
        .cornerRadius(Radii.small)
    }
}

struct ExerciseItemCardGrid: View {
    @EnvironmentObject var exerciseSessionManager: ExerciseSessionManager
    let item: ExerciseSessionStateItem
    let exerciseType: ExerciseType
    
    private var gridColumns: [GridItem] {
        GridConfiguration.columnsForType(exerciseType)
    }
    
    private var headers: [String] {
        GridConfiguration.headersForType(exerciseType)
    }
    
    var body: some View {
        VStack {
            ExerciseItemCardRowHeader(headers: headers, columns: gridColumns)
            
            Divider()
                .padding(.vertical, Spacing.xs)
            
            VStack {
                ForEach(item.sets) { exerciseSet in
                    ExerciseItemCardSetRowContainer(
                        exerciseSet: exerciseSet,
                        exerciseId: item.id,
                        exerciseType: exerciseType,
                        columns: gridColumns)
                }
            }
        }
    }
}

struct CompleteSetButton: View {
    @EnvironmentObject var exerciseSessionManager: ExerciseSessionManager
    let isComplete: Bool
    let exerciseId: String
    let setId: String
    
    var body: some View {
        Button(action: toggleComplete) {
            Image(systemName: isComplete ? "checkmark.circle.fill" : "circle")
                .foregroundColor(isComplete ? Colors.primary : Colors.onSurface.opacity(0.5))
                .imageScale(.medium)
        }
        .buttonStyle(PlainButtonStyle())
    }
    
    private func toggleComplete() {
        exerciseSessionManager.toggleSetComplete(eid: exerciseId, sid: setId)
    }
}


struct ExerciseItemCardRowHeader: View {
    let headers: [String]
    let columns: [GridItem]
    
    var body: some View {
        LazyVGrid(columns: columns) {
            ForEach(headers, id: \.self) { header in
                Text(header)
                    .font(Typography.caption1)
                    .fontWeight(.semibold)
                    .foregroundColor(Colors.onSurface)
                    .frame(maxWidth: .infinity, alignment: header == "Set" ? .leading : .center)
            }
        }
    }
}

struct ExerciseItemCardSetRowContainer: View {
    @EnvironmentObject var exerciseSessionManager: ExerciseSessionManager
    let exerciseSet: ExerciseSessionStateItemSet
    let exerciseId: String
    let exerciseType: ExerciseType
    let columns: [GridItem]
    
    var body: some View {
        LazyVGrid(columns: columns) {
            SetNumberView(value: exerciseSet.order, type: exerciseSet.type, isComplete: exerciseSet.complete)
            
            switch exerciseType {
            case .reps:
                    RepsInputView(reps: exerciseSet.metrics.reps, isComplete: exerciseSet.complete, exerciseId: exerciseId, exerciseSetId: exerciseSet.id)
                default: EmptyView()
            }
            
            CompleteSetButton(isComplete: exerciseSet.complete, exerciseId: exerciseId, setId: exerciseSet.id)
        }
    }
}

struct SetNumberView: View {
    let value: Int
    let type: ExerciseSetType
    let isComplete: Bool
    
    private var indicator: (text: String, color: Color)? {
        guard type != .workingSet else { return nil }
        
        switch type {
        case .warmupSet: return ("W", .orange)
        case .dropSet: return ("D", .red)
        case .superSet: return ("S", .blue)
        case .failureSet: return ("F", .red)
        default: return nil
        }
    }
    
    var body: some View {
        HStack(spacing: 4) {
            if let indicator = indicator {
                Text(indicator.text)
                    .foregroundColor(indicator.color)
            } else {
                Text("\(value)")
                    .font(Typography.body)
                    .foregroundColor(Colors.onSurface)
            }
        }
        .frame(maxWidth: .infinity, alignment: .leading)
    }
}

#Preview {
    let mockExerciseSessionManager = ExerciseSessionManager()
    
    mockExerciseSessionManager.currentSession = ExerciseSession(
        id: "123",
        name: "W1D1",
        status: .active,
        ownerId: "456",
        createdAt: Date(),
        updatedAt: Date(),
        participants: [],
        invitations: []
    )
    
    mockExerciseSessionManager.currentState = ExerciseSessionState(
        sessionId: "123",
        accountId: "user-id-here",
        version: 0,
        items: [
            ExerciseSessionStateItem(
            id: "123",
            order: 1,
            participants: [],
            type: .single,
            rest: 60,
            meta: [ExerciseSessionItemMeta(internalId: "internal-id", name: "Bench Press", type: .reps)],
            sets:
            [
                ExerciseSessionStateItemSet(id: "set-id-1", metaId: "internal-id", order: 1, metrics: ExerciseSessionStateItemMetric(reps: 5, weight: Weight(value: 185.0, unit: .pound), distance: Distance(value: 1.0, unit: .mile)), type: .warmupSet, complete: false),
                ExerciseSessionStateItemSet(id: "set-id-2", metaId: "internal-id", order: 2, metrics: ExerciseSessionStateItemMetric(reps: 6, weight: Weight(value: 185.0, unit: .pound)), type: .dropSet, complete: false),
                ExerciseSessionStateItemSet(id: "set-id-3", metaId: "internal-id", order: 3, metrics: ExerciseSessionStateItemMetric(reps: 7, weight: Weight(value: 225.0, unit: .pound)), type: .workingSet, complete: false)
            ]),
            ExerciseSessionStateItem(
            id: "456",
            order: 2,
            participants: [],
            type: .single,
            rest: 60,
            meta: [ExerciseSessionItemMeta(internalId: "internal-id", name: "Run", type: .distanceTime)],
            sets:
            [
                ExerciseSessionStateItemSet(id: "internal-id", metaId: "internal-id", order: 1, metrics: ExerciseSessionStateItemMetric(reps: 8, weight: Weight(value: 135, unit: .pound), duration: Duration(value: 3600), distance: Distance(value: 1, unit: .mile)), type: .workingSet, complete: false),
            ])
        ]
    )
    
    return SessionView(session: mockExerciseSessionManager.currentSession!, state: mockExerciseSessionManager.currentState!)
        .environmentObject(mockExerciseSessionManager)
}
