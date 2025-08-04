import SwiftUI

struct RegisterView: View {
    @EnvironmentObject private var authManager: AuthenticationManager
    @State private var username: String = ""
    @State private var email: String = ""
    @State private var password: String = ""
    @State private var password2: String = ""
    
    var body: some View {
        VStack {
            VStack(spacing: Spacing.Semantic.inputGroup) {
                InputField("Username", text: $username, type: .plain, errorMessage: nil)
                InputField("Email", text: $email, type: .email, errorMessage: nil)
                InputField("Password", text: $password, type: .password, errorMessage: nil)
                InputField("Confirm Password", text: $password2, type: .password, errorMessage: nil)
                
            }
            
            Spacer()
            
            Button("Create Account", action: register).buttonStyle(PrimaryButtonStyle())
        }.padding()
    }
    
    private func register() {
        Task {
            await authManager.performSignUp(username: username, email: email, password: password)
        }
    }
}

#Preview {
    RegisterView()
}
