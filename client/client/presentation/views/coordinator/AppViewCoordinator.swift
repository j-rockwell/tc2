import SwiftUI

struct AppViewCoordinator: View {
    @StateObject private var authManager = AuthenticationManager()
    @State private var isInit = false
    
    var body: some View {
        Group {
            if !isInit {
                SplashView()
                    .environmentObject(authManager)
            } else if authManager.isAuthenticated {
                NavigationView()
                    .environmentObject(authManager)
            } else {
                AuthFlowView()
                    .environmentObject(authManager)
            }
        }
        .onAppear {
            initApp()
        }
    }
    
    private func initApp() {
        DispatchQueue.main.asyncAfter(deadline: .now() + 1.0) {
            authManager.checkStatus()
            isInit = true
        }
    }
}

#Preview {
    AppViewCoordinator()
}
