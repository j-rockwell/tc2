import SwiftUI

struct NavigationView: View {
    @EnvironmentObject var authManager: AuthenticationManager
    @EnvironmentObject var exerciseSessionManager: ExerciseSessionManager
    
    @State private var selectedView = 0
    
    var body: some View {
        TabView(selection: $selectedView) {
            DashboardView()
                .tabItem {
                    Label("Dashboard", systemImage: "book")
                }
                .tag(0)
            
            SearchView()
                .tabItem {
                    Label("Search", systemImage: "magnifyingglass")
                }
                .tag(1)
            
            if exerciseSessionManager.currentSession != nil {
                SessionView(
                    session: exerciseSessionManager.currentSession!,
                    state: exerciseSessionManager.currentState!)
                    .tabItem {
                        Label("Session", systemImage: "dumbbell.fill")
                    }
                    .tag(2)
                    .environmentObject(authManager)
                    .environmentObject(exerciseSessionManager)
            } else {
                NewSessionView()
                    .tabItem {
                        Label("New Session", systemImage: "dumbbell.fill")
                    }
                    .tag(2)
                    .environmentObject(authManager)
                    .environmentObject(exerciseSessionManager)
            }
            
            AnalyticsView()
                .tabItem {
                    Label("Analytics", systemImage: "chart.bar.xaxis")
                }
                .tag(3)
            
            ProfileView()
                .tabItem {
                    Image("HappySun")
                    Text("Profile")
                }
                .tag(4)
        }
        .padding(.horizontal)
        .onChange(of: selectedView) { oldValue, newValue in
            print("old value: \(oldValue), new value: \(newValue)")
        }
        .safeAreaInset(edge: .bottom, spacing: 0) {
            if shouldSessionMinicardBeShown() {
                SessionMiniView()
                    .environmentObject(exerciseSessionManager)
                    .onTapGesture { selectedView = 2 }
                    .transition(.move(edge: .bottom).combined(with: .opacity))
                    .padding(.horizontal)
                    .padding(.bottom, 54)
            }
        }
        .animation(.easeInOut(duration: 0.25), value: shouldSessionMinicardBeShown())
        .ignoresSafeArea(.keyboard, edges: .bottom)
    }
    
    private func shouldSessionMinicardBeShown() -> Bool {
        return exerciseSessionManager.currentSession != nil && exerciseSessionManager.currentState != nil && selectedView != 2
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
                ExerciseSessionStateItemSet(id: "set-id-1", metaId: "internal-id", order: 1, metrics: ExerciseSessionStateItemMetric(reps: 5, weight: Weight(value: 135.0, unit: .pound)), type: .workingSet, complete: false),
                ExerciseSessionStateItemSet(id: "set-id-2", metaId: "internal-id", order: 2, metrics: ExerciseSessionStateItemMetric(reps: 5, weight: Weight(value: 185.0, unit: .pound)), type: .workingSet, complete: false),
                ExerciseSessionStateItemSet(id: "set-id-3", metaId: "internal-id", order: 3, metrics: ExerciseSessionStateItemMetric(reps: 5, weight: Weight(value: 225.0, unit: .pound)), type: .workingSet, complete: false)
            ])
        ]
    )
    
    return NavigationView()
        .environmentObject(mockAuthManager)
        .environmentObject(mockExerciseManager)
}
