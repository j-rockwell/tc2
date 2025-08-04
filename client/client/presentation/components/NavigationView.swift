import SwiftUI

struct NavigationView: View {
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
                    Label("Session", systemImage: "dumbbell.fill")
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
        }.padding(.horizontal)
    }
}

#Preview {
    NavigationView()
}
