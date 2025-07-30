import SwiftUI

struct LoginView: View {
    @EnvironmentObject private var authManager: AuthenticationManager
    @State private var email = ""
    @State private var password = ""
    
    var body: some View {
        VStack {
            VStack(spacing: Spacing.Semantic.inputGroup) {
                InputField("Email", text: $email, type: .email, errorMessage: nil)
                InputField("Password", text: $password, type: .password, errorMessage: nil)
            }
            
            Spacer()
            
            VStack(spacing: Spacing.Semantic.buttonGroup) {
                Button("Sign in", action: signIn).buttonStyle(PrimaryButtonStyle())
                Button("Forgot Password", action: {}).buttonStyle(SecondaryButtonStyle())
            }
        }.padding()
    }
    
    private func signIn() {
        Task {
            await authManager.performSignIn(email: email, password: password)
        }
    }
}

#Preview {
    LoginView()
}
