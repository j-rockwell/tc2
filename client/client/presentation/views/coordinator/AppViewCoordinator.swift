import SwiftUI

struct AppViewCoordinator: View {
    @StateObject private var authManager = AuthenticationManager()
    @State private var isInit = false
    
    var body: some View {
        Group {
            if !isInit {
                SplashView()
                    .environmentObject(authManager)
                    .transition(.asymmetric(
                        insertion: .move(edge: .trailing),
                        removal: .move(edge: .leading)
                    ))
            } else if authManager.isAuthenticated {
                NavigationView()
                    .environmentObject(authManager)
                    .transition(.asymmetric(
                        insertion: .move(edge: .leading),
                        removal: .move(edge: .trailing)
                    ))
            } else {
                AuthFlowView()
                    .environmentObject(authManager)
            }
        }
        .onAppear {
            initApp()
        }
        .animation(.easeInOut(duration: 0.3), value: authManager.isAuthenticated)
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
