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
                    Label("Search", systemImage: "book")
                }
            
            NewSessionView()
                .tabItem {
                    Label("Session", systemImage: "globe")
                }
            
            ProfileView()
                    .tabItem {
                      Image("HappySun")
                      Text("Profile")
                    }
        }
    }
}

#Preview {
    NavigationView()
}
