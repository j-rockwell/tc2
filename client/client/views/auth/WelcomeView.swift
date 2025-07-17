import SwiftUI

struct WelcomeView: View {
    var body: some View {
        WelcomeButtons()
    }
}

private struct WelcomeButtons: View {
    private func onCreateAccount() {
        print("Test")
    }

    private func onSignIn() {
        print("Test 2")
    }
    
    var body: some View {
        VStack(spacing: 8) {
            Button(action: onCreateAccount) {
                Text("Create Account")
                    .frame(maxWidth: .infinity)
                    .fontWeight(.semibold)
            }.buttonStyle(.borderedProminent)
            
            Button(action: onSignIn) {
                Text("Sign in")
                    .frame(maxWidth: .infinity)
            }.buttonStyle(.borderedProminent)
        }
    }
}

#Preview {
    WelcomeView()
}
