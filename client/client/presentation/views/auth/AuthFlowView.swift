import SwiftUI

struct AuthFlowView: View {
    @EnvironmentObject var authManager: AuthenticationManager
    @State private var navigationPath = NavigationPath()
    
    enum AuthView: Hashable {
        case welcome
        case login
        case register
    }
    
    var body: some View {
        NavigationStack(path: $navigationPath) {
            WelcomeView()
                .navigationDestination(for: AuthView.self) { destination in
                    switch destination {
                    case .welcome:
                        WelcomeView()
                    case .login:
                        LoginView()
                            .navigationTitle("Sign in")
                            .navigationBarTitleDisplayMode(.large)
                    case .register:
                        RegisterView()
                    }
                }
        }
        .environmentObject(authManager)
        .onChange(of: authManager.isAuthenticated) { _, isAuthenticated in
            if isAuthenticated {
                navigationPath.removeLast(navigationPath.count)
            }
        }
    }
}

#Preview {
    AuthFlowView()
        .environmentObject(AuthenticationManager())
}
