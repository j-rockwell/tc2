import SwiftUI

struct NavigationView: View {
    @EnvironmentObject var authManager: AuthenticationManager
    @EnvironmentObject var exerciseSessionManager: ExerciseSessionManager
    
    var body: some View {
        TabView {
            DashboardView()
                .tabItem {
                    Label("Dashboard", systemImage: "book")
                }
            
            SearchView()
                .tabItem {
                    Label("Search", systemImage: "magnifyingglass")
                }
            
            if exerciseSessionManager.currentSession != nil {
                SessionView(
                    session: exerciseSessionManager.currentSession!,
                    state: exerciseSessionManager.currentState!
                )
                    .tabItem {
                        Label("Session", systemImage: "dumbbell.fill")
                    }
                    .environmentObject(authManager)
                    .environmentObject(exerciseSessionManager)
            } else {
                NewSessionView()
                    .tabItem {
                        Label("New Session", systemImage: "dumbbell.fill")
                    }
                    .environmentObject(authManager)
                    .environmentObject(exerciseSessionManager)
            }
            
            AnalyticsView()
                .tabItem {
                    Label("Analytics", systemImage: "chart.bar.xaxis")
                }
            
            ProfileView()
                .tabItem {
                    Image("HappySun")
                    Text("Profile")
                }
        }
        .padding(.horizontal)
    }
}

#Preview {
    let mockAuthManager = AuthenticationManager()
    mockAuthManager.isAuthenticated = true
    mockAuthManager.account = Account(
        id: "123",
        username: "testuser",
        email: "test@trainingclub.com",
        profile: AccountProfile(name: "Test User", avatar: nil),
        bio: nil,
        metadata: nil,
    )
    
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
                ExerciseSessionStateItemSet(id: "set-id-1", order: 1, metrics: ExerciseSessionStateItemMetric(reps: 5, weight: Weight(value: 135.0, unit: .pound)), type: .workingSet, complete: false),
                ExerciseSessionStateItemSet(id: "set-id-2", order: 2, metrics: ExerciseSessionStateItemMetric(reps: 5, weight: Weight(value: 185.0, unit: .pound)), type: .workingSet, complete: false),
                ExerciseSessionStateItemSet(id: "set-id-3", order: 3, metrics: ExerciseSessionStateItemMetric(reps: 5, weight: Weight(value: 225.0, unit: .pound)), type: .workingSet, complete: false)
            ])
        ]
    )
    
    return NavigationView()
        .environmentObject(mockAuthManager)
        .environmentObject(mockExerciseManager)
}
