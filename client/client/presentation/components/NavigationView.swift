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
            
            NewSessionView()
                .tabItem {
                    Label("New Session", systemImage: "dumbbell.fill")
                }
                .environmentObject(authManager)
                .environmentObject(exerciseSessionManager)
            
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
    
    return NavigationView()
        .environmentObject(mockAuthManager)
        .environmentObject(mockExerciseManager)
}
